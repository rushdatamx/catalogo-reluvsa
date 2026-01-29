"""
Endpoints para productos
"""
import json
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException
import math

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import ProductoLista, ProductoDetalle, PaginatedResponse, Compatibilidad, InventarioSucursal, EspecificacionesManualRequest, EspecificacionesManuales

router = APIRouter(prefix="/api/productos", tags=["productos"])


@router.get("", response_model=PaginatedResponse)
def listar_productos(
    # Filtros básicos
    departamento: Optional[str] = Query(None),
    marca: Optional[str] = Query(None, description="Marca del producto"),
    marca_vehiculo: Optional[str] = Query(None),
    modelo_vehiculo: Optional[str] = Query(None),
    año: Optional[int] = Query(None),
    motor: Optional[str] = Query(None),
    tipo_producto: Optional[str] = Query(None),
    grupo_producto: Optional[str] = Query(None, description="Grupo del producto"),
    con_inventario: Optional[bool] = Query(None, description="Solo productos con inventario"),
    # Filtros para LLANTAS
    ancho_llanta: Optional[str] = Query(None, description="Ancho de llanta (mm)"),
    relacion_llanta: Optional[str] = Query(None, description="Relación/perfil de llanta"),
    diametro_llanta: Optional[str] = Query(None, description="Diámetro de rin"),
    tipo_llanta: Optional[str] = Query(None, description="Tipo de llanta"),
    capas_llanta: Optional[str] = Query(None, description="Número de capas"),
    # Filtros para ACEITES
    viscosidad: Optional[str] = Query(None, description="Viscosidad SAE"),
    tipo_aceite: Optional[str] = Query(None, description="Tipo de aceite"),
    presentacion: Optional[str] = Query(None, description="Presentación del aceite"),
    # Filtros para ACUMULADORES
    grupo_bci: Optional[str] = Query(None, description="Grupo BCI"),
    capacidad_cca: Optional[str] = Query(None, description="Capacidad CCA"),
    tamano_acumulador: Optional[str] = Query(None, description="Tamaño del acumulador"),
    # Búsqueda
    q: Optional[str] = Query(None, description="Búsqueda por texto"),
    # Paginación
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Lista productos con filtros y paginación"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Construir query base
        base_query = """
            FROM productos p
        """
        where_clauses = []
        params = []

        # Si hay filtros de vehículo, hacer JOIN con compatibilidades
        needs_compat_join = any([marca_vehiculo, modelo_vehiculo, año, motor])
        if needs_compat_join:
            base_query += """
                INNER JOIN compatibilidades c ON c.producto_id = p.id
            """

        # Si hay filtros de características (llantas, aceites, acumuladores)
        needs_carac_join = any([
            ancho_llanta, relacion_llanta, diametro_llanta, tipo_llanta, capas_llanta,
            viscosidad, tipo_aceite, presentacion,
            grupo_bci, capacidad_cca, tamano_acumulador
        ])
        if needs_carac_join:
            base_query += """
                INNER JOIN caracteristicas_producto cp ON cp.producto_id = p.id
            """

        # Aplicar filtros
        if departamento:
            where_clauses.append("p.departamento = ?")
            params.append(departamento)

        if marca:
            where_clauses.append("p.marca = ?")
            params.append(marca)

        if tipo_producto:
            where_clauses.append("p.tipo_producto = ?")
            params.append(tipo_producto)

        if grupo_producto:
            where_clauses.append("p.grupo_producto = ?")
            params.append(grupo_producto)

        if con_inventario:
            where_clauses.append("p.inventario_total > 0")

        if marca_vehiculo:
            where_clauses.append("c.marca_vehiculo = ?")
            params.append(marca_vehiculo)

        if modelo_vehiculo:
            where_clauses.append("c.modelo_vehiculo = ?")
            params.append(modelo_vehiculo)

        if año:
            where_clauses.append("c.año_inicio <= ? AND c.año_fin >= ?")
            params.extend([año, año])

        if motor:
            where_clauses.append("c.motor = ?")
            params.append(motor)

        if q:
            # Búsqueda súper flexible - busca en TODOS los campos posibles
            where_clauses.append("""
                (
                    p.descripcion_original LIKE ?
                    OR p.sku LIKE ?
                    OR p.nombre_producto LIKE ?
                    OR p.skus_alternos LIKE ?
                    OR p.marca LIKE ?
                    OR p.departamento LIKE ?
                    OR p.tipo_producto LIKE ?
                    OR p.id IN (
                        SELECT producto_id FROM compatibilidades
                        WHERE marca_vehiculo LIKE ?
                           OR modelo_vehiculo LIKE ?
                           OR motor LIKE ?
                    )
                )
            """)
            search_term = f"%{q}%"
            # 7 campos de productos + 3 de compatibilidades = 10 parámetros
            params.extend([search_term] * 10)

        # Filtros para LLANTAS (usando subqueries para múltiples características)
        if ancho_llanta:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'ancho' AND valor = ?
                )
            """)
            params.append(ancho_llanta)

        if relacion_llanta:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'relacion' AND valor = ?
                )
            """)
            params.append(relacion_llanta)

        if diametro_llanta:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'diametro' AND valor = ?
                )
            """)
            params.append(diametro_llanta)

        if tipo_llanta:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'tipo' AND valor = ?
                )
            """)
            params.append(tipo_llanta)

        if capas_llanta:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'capas' AND valor = ?
                )
            """)
            params.append(capas_llanta)

        # Filtros para ACEITES
        if viscosidad:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'viscosidad' AND valor = ?
                )
            """)
            params.append(viscosidad)

        if tipo_aceite:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'tipo_aceite' AND valor = ?
                )
            """)
            params.append(tipo_aceite)

        if presentacion:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'presentacion' AND valor = ?
                )
            """)
            params.append(presentacion)

        # Filtros para ACUMULADORES
        if grupo_bci:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'acumulador' AND clave = 'grupo_bci' AND valor = ?
                )
            """)
            params.append(grupo_bci)

        if capacidad_cca:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'acumulador' AND clave = 'capacidad_cca' AND valor = ?
                )
            """)
            params.append(capacidad_cca)

        if tamano_acumulador:
            where_clauses.append("""
                p.id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'acumulador' AND clave = 'tamano' AND valor = ?
                )
            """)
            params.append(tamano_acumulador)

        # Construir WHERE
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Contar total
        count_query = f"SELECT COUNT(DISTINCT p.id) as total {base_query} {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']

        # Calcular paginación
        pages = math.ceil(total / limit) if total > 0 else 1
        offset = (page - 1) * limit

        # Obtener productos
        select_query = f"""
            SELECT DISTINCT
                p.id, p.sku, p.departamento, p.marca, p.descripcion_original,
                p.nombre_producto, p.tipo_producto, p.precio_publico, p.precio_mayoreo,
                p.imagen_url, p.inventario_total
            {base_query}
            {where_sql}
            ORDER BY p.inventario_total DESC, p.sku
            LIMIT ? OFFSET ?
        """
        cursor.execute(select_query, params + [limit, offset])

        items = []
        for row in cursor.fetchall():
            items.append(ProductoLista(
                id=row['id'],
                sku=row['sku'],
                departamento=row['departamento'],
                marca=row['marca'],
                descripcion_original=row['descripcion_original'],
                nombre_producto=row['nombre_producto'],
                tipo_producto=row['tipo_producto'],
                precio_publico=row['precio_publico'],
                precio_mayoreo=row['precio_mayoreo'],
                imagen_url=row['imagen_url'],
                inventario_total=row['inventario_total']
            ))

        return PaginatedResponse(
            total=total,
            page=page,
            limit=limit,
            pages=pages,
            items=items
        )


@router.get("/buscar")
def buscar_productos(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=50)
):
    """Búsqueda rápida de productos - busca en TODOS los campos posibles"""
    with get_db() as conn:
        cursor = conn.cursor()

        search_term = f"%{q}%"
        # Búsqueda súper flexible - igual que el endpoint principal
        cursor.execute("""
            SELECT DISTINCT
                p.id, p.sku, p.marca, p.descripcion_original,
                p.nombre_producto, p.precio_publico, p.inventario_total,
                p.departamento, p.tipo_producto
            FROM productos p
            WHERE p.descripcion_original LIKE ?
               OR p.sku LIKE ?
               OR p.nombre_producto LIKE ?
               OR p.skus_alternos LIKE ?
               OR p.marca LIKE ?
               OR p.departamento LIKE ?
               OR p.tipo_producto LIKE ?
               OR p.id IN (
                   SELECT producto_id FROM compatibilidades
                   WHERE marca_vehiculo LIKE ?
                      OR modelo_vehiculo LIKE ?
                      OR motor LIKE ?
               )
            ORDER BY p.inventario_total DESC
            LIMIT ?
        """, [search_term] * 10 + [limit])

        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row['id'],
                'sku': row['sku'],
                'marca': row['marca'],
                'descripcion': row['descripcion_original'],
                'nombre': row['nombre_producto'],
                'precio': row['precio_publico'],
                'inventario': row['inventario_total'],
                'departamento': row['departamento'],
                'tipo': row['tipo_producto']
            })

        return {'results': results, 'total': len(results)}


@router.put("/{sku}/especificaciones-manuales")
def actualizar_especificaciones_manuales(sku: str, datos: EspecificacionesManualRequest):
    """Crea o actualiza especificaciones manuales de un producto"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Buscar producto_id por SKU
        cursor.execute("SELECT id FROM productos WHERE sku = ?", [sku])
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        producto_id = row['id']

        # Procesar cada especificación
        especificaciones = [
            ('garantia', datos.garantia),
            ('material', datos.material),
            ('posicion', datos.posicion)
        ]

        for tipo, valor in especificaciones:
            if valor and valor.strip():
                # INSERT OR REPLACE
                cursor.execute("""
                    INSERT OR REPLACE INTO especificaciones_manuales (producto_id, tipo, valor, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, [producto_id, tipo, valor.strip()])
            else:
                # DELETE si está vacío
                cursor.execute("""
                    DELETE FROM especificaciones_manuales
                    WHERE producto_id = ? AND tipo = ?
                """, [producto_id, tipo])

        # Retornar especificaciones actualizadas
        cursor.execute("""
            SELECT tipo, valor FROM especificaciones_manuales
            WHERE producto_id = ?
        """, [producto_id])

        result = {row['tipo']: row['valor'] for row in cursor.fetchall()}

        return {
            "success": True,
            "especificaciones_manuales": {
                "garantia": result.get('garantia'),
                "material": result.get('material'),
                "posicion": result.get('posicion')
            }
        }


@router.get("/{sku:path}")
def get_producto(sku: str):
    """Obtiene el detalle de un producto por SKU"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener producto
        cursor.execute("""
            SELECT *
            FROM productos
            WHERE sku = ?
        """, [sku])

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Parsear SKUs alternos
        skus_alternos = []
        if row['skus_alternos']:
            try:
                skus_alternos = json.loads(row['skus_alternos'])
            except:
                pass

        # Obtener compatibilidades
        cursor.execute("""
            SELECT marca_vehiculo, modelo_vehiculo, año_inicio, año_fin,
                   motor, cilindros, especificacion
            FROM compatibilidades
            WHERE producto_id = ?
        """, [row['id']])

        compatibilidades = []
        for c_row in cursor.fetchall():
            compatibilidades.append(Compatibilidad(
                marca_vehiculo=c_row['marca_vehiculo'],
                modelo_vehiculo=c_row['modelo_vehiculo'],
                año_inicio=c_row['año_inicio'],
                año_fin=c_row['año_fin'],
                motor=c_row['motor'],
                cilindros=c_row['cilindros'],
                especificacion=c_row['especificacion']
            ))

        # Obtener inventario por sucursal
        cursor.execute("""
            SELECT sucursal, cantidad
            FROM inventario
            WHERE producto_id = ?
            ORDER BY sucursal
        """, [row['id']])

        inventario_sucursales = []
        for i_row in cursor.fetchall():
            inventario_sucursales.append(InventarioSucursal(
                sucursal=i_row['sucursal'],
                cantidad=i_row['cantidad']
            ))

        # Obtener especificaciones manuales
        cursor.execute("""
            SELECT tipo, valor FROM especificaciones_manuales
            WHERE producto_id = ?
        """, [row['id']])

        especs_dict = {e_row['tipo']: e_row['valor'] for e_row in cursor.fetchall()}
        especificaciones_manuales = {
            "garantia": especs_dict.get('garantia'),
            "material": especs_dict.get('material'),
            "posicion": especs_dict.get('posicion')
        }

        # Obtener productos intercambiables
        intercambiables = []
        try:
            cursor.execute("""
                SELECT p.sku, p.nombre_producto, p.marca, p.inventario_total
                FROM productos_intercambiables pi
                INNER JOIN productos p ON p.id = pi.producto_intercambiable_id
                WHERE pi.producto_id = ?
                ORDER BY p.marca, p.nombre_producto
            """, [row['id']])

            for i_row in cursor.fetchall():
                intercambiables.append({
                    'sku': i_row['sku'],
                    'nombre_producto': i_row['nombre_producto'],
                    'marca': i_row['marca'],
                    'inventario_total': i_row['inventario_total']
                })
        except Exception:
            pass  # Tabla puede no existir aun

        return {
            "id": row['id'],
            "sku": row['sku'],
            "departamento": row['departamento'],
            "marca": row['marca'],
            "descripcion_original": row['descripcion_original'],
            "nombre_producto": row['nombre_producto'],
            "tipo_producto": row['tipo_producto'],
            "precio_publico": row['precio_publico'],
            "precio_mayoreo": row['precio_mayoreo'],
            "imagen_url": row['imagen_url'],
            "inventario_total": row['inventario_total'],
            "skus_alternos": skus_alternos,
            "compatibilidades": [c.model_dump() for c in compatibilidades],
            "inventario_sucursales": [i.model_dump() for i in inventario_sucursales],
            "especificaciones_manuales": especificaciones_manuales,
            "intercambiables": intercambiables
        }
