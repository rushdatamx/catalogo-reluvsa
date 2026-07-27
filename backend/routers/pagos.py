"""
Router de pagos con Stripe Checkout para el catálogo RELUVSA.

Flujo (login-only, pickup en sucursal por ahora):
  1. Usuario autenticado (JWT) arma un carrito y llama POST /api/checkout.
  2. El backend REVALIDA precio e inventario contra la BD (nunca confía en el
     frontend), crea una Checkout Session hosted de Stripe y devuelve la URL.
  3. Stripe cobra y redirige a /success o /cancel del frontend.
  4. El webhook POST /api/webhooks/stripe (sin auth, con verificación de firma)
     confirma el pago, marca la orden como 'pagado' y descuenta inventario.

Notas Stripe (best practices oficiales, API 2026-06-24.dahlia):
  - Se usa Checkout Sessions API (hosted) para pagos únicos.
  - NUNCA se pasa `payment_method_types`: omitirlo activa dynamic payment
    methods. Tarjeta/OXXO/SPEI se habilitan desde el Dashboard sin tocar código.
  - Para métodos async (OXXO/SPEI) el inventario se descuenta solo cuando el
    pago se confirma (async_payment_succeeded), no al crear la sesión.
  - Idempotencia por stripe_session_id (UNIQUE) + verificación de firma.
"""
import os
import sqlite3
from typing import List, Optional

import stripe
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel, Field

from database import get_db
from pedidos_db import get_pedidos_db, init_pedidos_db
from routers.auth import get_current_user, require_admin, UserInfo

router = APIRouter(prefix="/api", tags=["pagos"])

# --- Configuración Stripe ---------------------------------------------------
# Usar restricted API key (rk_...) preferentemente. En test usar la clave de test.
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
# URL del frontend para las redirecciones de éxito/cancelación.
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Moneda: pesos mexicanos. Los precios en BD ya vienen CON IVA.
CURRENCY = "mxn"

# Sucursales válidas para pickup (deben coincidir con las de la tabla inventario).
SUCURSALES_PICKUP = {"Carrera", "Berriozabal", "CEDIS", "31 Juarez", "E-commerce"}


# Garantizar las tablas de la BD de pedidos (separada de catalogo.db) al importar.
# Ver pedidos_db.py: las órdenes viven en un volumen persistente para que las
# actualizaciones de catálogo (que sobrescriben catalogo.db) NO las borren.
init_pedidos_db()


# --- Modelos ----------------------------------------------------------------
class CarritoItem(BaseModel):
    sku: str
    cantidad: int = Field(gt=0, le=999)


class CheckoutRequest(BaseModel):
    items: List[CarritoItem] = Field(min_length=1)
    tipo_entrega: str = "pickup"              # por ahora solo 'pickup'
    sucursal_pickup: Optional[str] = None     # requerido si tipo_entrega == 'pickup'


class CheckoutResponse(BaseModel):
    checkout_url: str
    order_id: int


class PedidoResponse(BaseModel):
    """Respuesta de un pedido sin pago en línea (solicitud de cotización)."""
    order_id: int
    total: float
    num_productos: int


# --- Helpers ----------------------------------------------------------------
def _resolver_precio(row: sqlite3.Row) -> float:
    """Punto único de resolución de precio. Hoy: siempre precio_publico (con IVA).
    A futuro aquí se puede meter lógica de mayoreo por rol de usuario."""
    return row["precio_publico"] or 0.0


def _get_or_create_stripe_customer(user: UserInfo) -> tuple[Optional[str], Optional[str]]:
    """Devuelve (stripe_customer_id, nombre_empresa) para usuarios de BD (proveedores).

    Crea el Customer en Stripe en el primer checkout del proveedor y lo persiste
    en usuarios.stripe_customer_id — así en el dashboard de Stripe todos los pagos
    de un proveedor quedan agrupados bajo su cliente. El admin (usuario semilla de
    env vars, sin registro en BD) paga sin Customer, igual que antes."""
    with get_pedidos_db() as pconn:
        cursor = pconn.cursor()
        cursor.execute(
            "SELECT stripe_customer_id, nombre_empresa, contacto FROM usuarios WHERE username = ?",
            (user.username,),
        )
        row = cursor.fetchone()

    if row is None:
        return None, None  # admin semilla u otro usuario sin registro en BD

    empresa = row["nombre_empresa"]
    if row["stripe_customer_id"]:
        return row["stripe_customer_id"], empresa

    try:
        customer = stripe.Customer.create(
            name=empresa or user.username,
            description=f"Proveedor RELUVSA — usuario: {user.username}",
            metadata={"username": user.username, "empresa": empresa or ""},
        )
    except stripe.StripeError:
        # No bloquear el checkout por esto: la orden ya queda ligada por username.
        return None, empresa

    with get_pedidos_db() as pconn:
        pconn.execute(
            "UPDATE usuarios SET stripe_customer_id = ? WHERE username = ? AND stripe_customer_id IS NULL",
            (customer.id, user.username),
        )
    return customer.id, empresa


def _validar_carrito(data: CheckoutRequest) -> tuple[list, list, float]:
    """Revalida el carrito contra la BD y arma line_items (Stripe) + order_items.

    Devuelve (line_items, order_items_data, subtotal).

    Reporta TODOS los productos con problema, no solo el primero: un carrito de
    cientos de renglones abortando de uno en uno obligaría al proveedor a
    reintentar decenas de veces para descubrir qué falla.
    """
    if data.tipo_entrega != "pickup":
        raise HTTPException(status_code=400, detail="Solo se admite entrega tipo 'pickup' por ahora")
    if not data.sucursal_pickup or data.sucursal_pickup not in SUCURSALES_PICKUP:
        raise HTTPException(status_code=400, detail="Debe seleccionar una sucursal de pickup válida")

    # Consolidar cantidades por SKU (evita líneas duplicadas del mismo producto).
    cantidades: dict[str, int] = {}
    for item in data.items:
        cantidades[item.sku] = cantidades.get(item.sku, 0) + item.cantidad

    line_items: list = []
    order_items_data: list = []
    problemas: list[str] = []
    subtotal = 0.0

    with get_db() as conn:
        cursor = conn.cursor()

        for sku, cantidad in cantidades.items():
            cursor.execute(
                """SELECT id, sku, nombre_producto, tipo_producto, marca,
                          precio_publico, inventario_total
                   FROM productos WHERE sku = ?""",
                (sku,),
            )
            prod = cursor.fetchone()
            if prod is None:
                problemas.append(f"{sku}: no encontrado")
                continue

            precio = _resolver_precio(prod)
            inventario = prod["inventario_total"] or 0

            # Regla AGOTADO: no se puede comprar si precio 0 o sin stock.
            if precio <= 0:
                problemas.append(f"{sku}: sin precio en línea (consultar precio)")
                continue
            if inventario <= 0:
                problemas.append(f"{sku}: agotado")
                continue
            if cantidad > inventario:
                problemas.append(f"{sku}: solo hay {int(inventario)} (pediste {cantidad})")
                continue

            nombre = prod["nombre_producto"] or prod["tipo_producto"] or prod["sku"]
            subtotal += precio * cantidad

            line_items.append({
                "price_data": {
                    "currency": CURRENCY,
                    "product_data": {
                        "name": f"{nombre} ({prod['marca']})" if prod["marca"] else nombre,
                        "metadata": {"sku": prod["sku"]},
                    },
                    # Stripe cobra en la unidad mínima (centavos).
                    "unit_amount": round(precio * 100),
                },
                "quantity": cantidad,
            })
            order_items_data.append({
                "producto_id": prod["id"],
                "sku": prod["sku"],
                "nombre": nombre,
                "cantidad": cantidad,
                "precio_unitario": precio,
            })

    if problemas:
        MAX_LISTADOS = 10
        listados = "; ".join(problemas[:MAX_LISTADOS])
        extra = f" (y {len(problemas) - MAX_LISTADOS} más)" if len(problemas) > MAX_LISTADOS else ""
        raise HTTPException(
            status_code=400,
            detail=f"{len(problemas)} producto(s) no se pueden pedir — {listados}{extra}",
        )

    return line_items, order_items_data, subtotal


def _crear_orden(user: UserInfo, data: CheckoutRequest, order_items_data: list,
                 subtotal: float, total: float, estado: str) -> int:
    """Inserta la orden y sus renglones en pedidos.db. Devuelve el order_id."""
    with get_pedidos_db() as pconn:
        pcursor = pconn.cursor()
        pcursor.execute(
            """INSERT INTO orders (username, tipo_entrega, sucursal_pickup, subtotal, total, estado)
               VALUES (?, 'pickup', ?, ?, ?, ?)""",
            (user.username, data.sucursal_pickup, subtotal, total, estado),
        )
        order_id = pcursor.lastrowid
        for it in order_items_data:
            pcursor.execute(
                """INSERT INTO order_items (order_id, producto_id, sku, nombre, cantidad, precio_unitario)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (order_id, it["producto_id"], it["sku"], it["nombre"], it["cantidad"], it["precio_unitario"]),
            )
    return order_id


# --- Endpoints --------------------------------------------------------------
@router.post("/pedido", response_model=PedidoResponse)
def crear_pedido(data: CheckoutRequest, user: UserInfo = Depends(get_current_user)):
    """Registra un pedido SIN pago en línea (el proveedor lo 'envía' y RELUVSA
    lo cotiza/cobra por fuera). Queda en estado 'pendiente' y aparece de
    inmediato en el portal de pedidos del admin.

    No toca Stripe ni descuenta inventario: eso solo pasa cuando un pago se
    confirma. Existe para poder recibir pedidos mientras el cobro en línea
    todavía no está configurado."""
    _, order_items_data, subtotal = _validar_carrito(data)
    order_id = _crear_orden(user, data, order_items_data, subtotal, subtotal, "pendiente")
    return PedidoResponse(
        order_id=order_id,
        total=subtotal,
        num_productos=len(order_items_data),
    )


@router.post("/checkout", response_model=CheckoutResponse)
def crear_checkout(data: CheckoutRequest, user: UserInfo = Depends(get_current_user)):
    """Crea una Checkout Session de Stripe tras revalidar precio e inventario."""
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Pagos no configurados (falta STRIPE_SECRET_KEY)")

    line_items, order_items_data, subtotal = _validar_carrito(data)
    total = subtotal  # sin costo de envío por ahora (pickup)

    # Crear la orden en la BD de PEDIDOS (separada del catálogo), estado 'pendiente'
    # ANTES de Stripe, para tener order_id.
    order_id = _crear_orden(user, data, order_items_data, subtotal, total, "pendiente")

    # Referencia Stripe ↔ proveedor: Customer persistente + empresa en metadata.
    stripe_customer_id, nombre_empresa = _get_or_create_stripe_customer(user)

    # Crear la Checkout Session. NO pasar payment_method_types (dynamic methods).
    try:
        session_params = dict(
            mode="payment",
            line_items=line_items,
            success_url=f"{FRONTEND_URL}/success?order={order_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/cancel?order={order_id}",
            client_reference_id=str(order_id),
            metadata={
                "order_id": str(order_id),
                "username": user.username,
                "empresa": nombre_empresa or "",
            },
        )
        if stripe_customer_id:
            session_params["customer"] = stripe_customer_id
        session = stripe.checkout.Session.create(**session_params)
    except stripe.StripeError as e:
        # Marcar la orden como fallida y devolver error.
        with get_pedidos_db() as pconn:
            pconn.execute("UPDATE orders SET estado = 'fallido' WHERE id = ?", (order_id,))
        raise HTTPException(status_code=502, detail=f"Error creando sesión de pago: {str(e)}")

    # Guardar el session_id en la orden.
    with get_pedidos_db() as pconn:
        pconn.execute(
            "UPDATE orders SET stripe_session_id = ? WHERE id = ?",
            (session.id, order_id),
        )

    return CheckoutResponse(checkout_url=session.url, order_id=order_id)


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Recibe eventos de Stripe. SIN auth JWT, pero verifica la firma del webhook.
    Marca la orden como pagada y descuenta inventario de forma idempotente."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook no configurado (falta STRIPE_WEBHOOK_SECRET)")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(status_code=400, detail="Firma de webhook inválida")

    tipo = event["type"]

    # Pago completado (síncrono: tarjeta) o pago async confirmado (OXXO/SPEI).
    if tipo in ("checkout.session.completed", "checkout.session.async_payment_succeeded"):
        session = event["data"]["object"]
        # Para tarjeta, 'completed' ya viene con payment_status='paid'. Para OXXO/SPEI,
        # 'completed' puede llegar con payment_status='unpaid'; el pago real lo confirma
        # async_payment_succeeded. Solo marcamos pagado si payment_status == 'paid'.
        if session.get("payment_status") == "paid":
            _marcar_orden_pagada(session)
    elif tipo == "checkout.session.async_payment_failed":
        session = event["data"]["object"]
        _actualizar_estado_por_session(session.get("id"), "fallido")
    elif tipo == "checkout.session.expired":
        session = event["data"]["object"]
        _actualizar_estado_por_session(session.get("id"), "cancelado")

    return {"received": True}


def _marcar_orden_pagada(session: dict):
    """Marca la orden como pagada (en pedidos.db) y descuenta inventario (en
    catalogo.db). Idempotente: si la orden ya está pagada, no hace nada.

    Nota sobre inventario: el descuento se aplica sobre catalogo.db para no vender
    de más entre actualizaciones. Cuando el usuario actualiza precios/inventario
    con el Excel, ese valor real de RELUVSA vuelve a mandar (Excel = fuente de verdad)."""
    session_id = session.get("id")
    payment_intent = session.get("payment_intent")

    # 1) Leer la orden y sus items desde la BD de pedidos.
    with get_pedidos_db() as pconn:
        pcursor = pconn.cursor()
        pcursor.execute("SELECT id, estado FROM orders WHERE stripe_session_id = ?", (session_id,))
        order = pcursor.fetchone()
        if order is None:
            return  # orden desconocida (no crear nada desde el webhook)
        if order["estado"] == "pagado":
            return  # idempotencia: ya procesada

        order_id = order["id"]
        pcursor.execute(
            "SELECT producto_id, cantidad FROM order_items WHERE order_id = ?",
            (order_id,),
        )
        items = [(row["producto_id"], row["cantidad"]) for row in pcursor.fetchall()]

    # 2) Descontar inventario_total en el CATÁLOGO (sin bajar de 0).
    with get_db() as conn:
        cursor = conn.cursor()
        for producto_id, cantidad in items:
            if producto_id:
                cursor.execute(
                    """UPDATE productos
                       SET inventario_total = MAX(0, COALESCE(inventario_total, 0) - ?)
                       WHERE id = ?""",
                    (cantidad, producto_id),
                )

    # 3) Marcar la orden como pagada en la BD de pedidos.
    with get_pedidos_db() as pconn:
        pconn.execute(
            """UPDATE orders
               SET estado = 'pagado', paid_at = CURRENT_TIMESTAMP, stripe_payment_intent = ?
               WHERE id = ?""",
            (payment_intent, order_id),
        )


def _actualizar_estado_por_session(session_id: str, estado: str):
    """Actualiza el estado de una orden por session_id, salvo que ya esté pagada."""
    if not session_id:
        return
    with get_pedidos_db() as pconn:
        pconn.execute(
            "UPDATE orders SET estado = ? WHERE stripe_session_id = ? AND estado != 'pagado'",
            (estado, session_id),
        )


@router.get("/orders")
def listar_ordenes(
    username: Optional[str] = None,
    estado: Optional[str] = None,
    limit: int = 100,
    admin: UserInfo = Depends(require_admin),
):
    """Todas las órdenes (solo admin), con la empresa del proveedor. Base del
    módulo de pedidos del portal. Filtrable por username y estado."""
    where = []
    params: list = []
    if username:
        where.append("o.username = ?")
        params.append(username)
    if estado:
        where.append("o.estado = ?")
        params.append(estado)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        # Resumen por pedido (sin traer los items: un pedido puede tener cientos
        # de renglones y la lista solo necesita el conteo). El detalle se pide
        # por separado con GET /api/orders/{id}.
        cursor.execute(
            f"""SELECT o.id, o.username, u.nombre_empresa, o.stripe_session_id,
                       o.stripe_payment_intent, o.tipo_entrega, o.sucursal_pickup,
                       o.subtotal, o.total, o.estado, o.created_at, o.paid_at,
                       (SELECT COUNT(*) FROM order_items oi WHERE oi.order_id = o.id)
                           AS num_renglones,
                       (SELECT COALESCE(SUM(oi.cantidad), 0) FROM order_items oi
                            WHERE oi.order_id = o.id) AS num_piezas
                FROM orders o
                LEFT JOIN usuarios u ON u.username = o.username
                {where_sql}
                ORDER BY o.created_at DESC
                LIMIT ?""",
            (*params, max(1, min(limit, 500))),
        )
        pedidos = [dict(row) for row in cursor.fetchall()]

        # Totales globales del filtro aplicado (para el encabezado del portal).
        cursor.execute(
            f"""SELECT o.estado, COUNT(*) AS n, COALESCE(SUM(o.total), 0) AS monto
                FROM orders o {where_sql} GROUP BY o.estado""",
            tuple(params),
        )
        resumen = {r["estado"]: {"pedidos": r["n"], "monto": r["monto"]} for r in cursor.fetchall()}

    return {"pedidos": pedidos, "resumen": resumen}


@router.get("/orders/mis-pedidos")
def mis_pedidos(user: UserInfo = Depends(get_current_user)):
    """Lista los pedidos del usuario autenticado."""
    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, stripe_session_id, tipo_entrega, sucursal_pickup,
                      subtotal, total, estado, created_at, paid_at
               FROM orders WHERE username = ? ORDER BY created_at DESC""",
            (user.username,),
        )
        pedidos = [dict(row) for row in cursor.fetchall()]
        for p in pedidos:
            cursor.execute(
                "SELECT sku, nombre, cantidad, precio_unitario FROM order_items WHERE order_id = ?",
                (p["id"],),
            )
            p["items"] = [dict(r) for r in cursor.fetchall()]
    return {"pedidos": pedidos}


@router.get("/orders/{order_id}")
def obtener_orden(order_id: int, user: UserInfo = Depends(get_current_user)):
    """Detalle de una orden. El usuario solo puede ver sus propias órdenes
    (admin puede ver cualquiera)."""
    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT o.id, o.username, u.nombre_empresa, u.contacto,
                      o.stripe_session_id, o.stripe_payment_intent, o.tipo_entrega,
                      o.sucursal_pickup, o.subtotal, o.total, o.estado,
                      o.created_at, o.paid_at
               FROM orders o
               LEFT JOIN usuarios u ON u.username = o.username
               WHERE o.id = ?""",
            (order_id,),
        )
        order = cursor.fetchone()
        if order is None:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        if order["username"] != user.username and user.role != "admin":
            raise HTTPException(status_code=403, detail="No autorizado")

        result = dict(order)
        # Datos de contacto solo para el admin (el proveedor ya los conoce y no
        # tiene por qué recibirlos de vuelta en su propio detalle).
        if user.role != "admin":
            result.pop("contacto", None)
        cursor.execute(
            """SELECT sku, nombre, cantidad, precio_unitario,
                      (cantidad * precio_unitario) AS importe
               FROM order_items WHERE order_id = ? ORDER BY id""",
            (order_id,),
        )
        result["items"] = [dict(r) for r in cursor.fetchall()]
    return result
