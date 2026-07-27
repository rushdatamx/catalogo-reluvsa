"""
Base de datos SEPARADA para datos VIVOS de producción: pedidos/órdenes de
Stripe y usuarios de proveedores.

¿Por qué una BD aparte de catalogo.db?
  El catálogo (productos, precios, inventario) se regenera desde el Excel y se
  SOBRESCRIBE completo en cada deploy (database.ensure_database copia el archivo
  del repo). Si las órdenes o los usuarios vivieran ahí, cada actualización de
  precios los borraría.

  Por eso las órdenes y los usuarios viven en `pedidos.db`, ubicada por defecto
  en un VOLUMEN PERSISTENTE de Railway (env var PEDIDOS_DB_PATH). Ese archivo NO
  está en el repo y NO se sobrescribe en los deploys, así que sobreviven a
  cualquier actualización de catálogo.

  Los usuarios viven JUNTO a las órdenes (misma BD) porque las órdenes
  referencian `username` — así el JOIN usuarios↔orders es directo.

Configuración:
  - PEDIDOS_DB_PATH: ruta al archivo de la BD de pedidos.
      * Producción (Railway): apuntar a un volumen persistente, ej.
        /data/pedidos.db  (con un Volume montado en /data).
      * Desarrollo local: si no se define, usa backend/data/pedidos.db (git-ignored).
"""
import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Ruta de la BD de pedidos. En producción se define PEDIDOS_DB_PATH apuntando
# al volumen persistente de Railway. En local usa un archivo junto al catálogo.
PEDIDOS_DB_PATH = os.getenv(
    "PEDIDOS_DB_PATH",
    str(Path(__file__).parent / "data" / "pedidos.db"),
)


def get_pedidos_connection():
    """Conexión a la BD de pedidos."""
    # Asegurar que el directorio exista (importante para volúmenes recién montados).
    Path(PEDIDOS_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(PEDIDOS_DB_PATH, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


@contextmanager
def get_pedidos_db():
    """Context manager para la BD de pedidos (commit/rollback automático)."""
    conn = get_pedidos_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_pedidos_db():
    """Crea las tablas de pedidos si no existen. Idempotente. Se llama al arrancar."""
    with get_pedidos_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stripe_session_id TEXT UNIQUE,
                stripe_payment_intent TEXT,
                username TEXT NOT NULL,
                tipo_entrega TEXT NOT NULL DEFAULT 'pickup',   -- 'pickup' | 'envio' (futuro)
                sucursal_pickup TEXT,
                direccion_envio TEXT,                          -- JSON, reservado para envío futuro
                costo_envio REAL DEFAULT 0,                    -- reservado para envío futuro
                subtotal REAL NOT NULL DEFAULT 0,
                total REAL NOT NULL DEFAULT 0,
                estado TEXT NOT NULL DEFAULT 'pendiente',      -- 'pendiente' | 'pagado' | 'cancelado' | 'fallido'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                producto_id INTEGER,          -- id del producto en catalogo.db (referencia lógica, sin FK)
                sku TEXT NOT NULL,
                nombre TEXT,
                cantidad INTEGER NOT NULL,
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,               -- bcrypt, nunca texto plano
                nombre_empresa TEXT,
                contacto TEXT,                             -- nombre/tel/email de contacto (texto libre)
                role TEXT NOT NULL DEFAULT 'proveedor',
                activo INTEGER NOT NULL DEFAULT 1,         -- 0 = desactivado (soft delete)
                stripe_customer_id TEXT,                   -- Customer de Stripe (creado en su 1er checkout)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        # Carrito ANTES de enviarse como pedido. Vive en el servidor (no solo en el
        # localStorage del navegador) para que el proveedor lo recupere desde
        # cualquier dispositivo y para que el admin pueda ver carritos armados que
        # nunca se enviaron. Un carrito por usuario (se sobrescribe al guardar).
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS carritos (
                username TEXT PRIMARY KEY,
                items TEXT NOT NULL DEFAULT '[]',   -- JSON: [{sku, cantidad}]
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_username ON orders(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_session ON orders(stripe_session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_carritos_updated ON carritos(updated_at)")
