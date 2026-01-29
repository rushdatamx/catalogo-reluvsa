"""
Módulo de base de datos SQLite para el catálogo de RELUVSA
"""
import os
import shutil
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Usar variable de entorno para producción o path local para desarrollo
DATABASE_PATH = os.getenv("DATABASE_PATH", str(Path(__file__).parent.parent / "data" / "catalogo.db"))

# En producción, copiar la DB del repo al volume si no existe o está vacía
def ensure_database():
    """Asegura que la base de datos exista en el path configurado"""
    global DATABASE_PATH

    db_path = Path(DATABASE_PATH)
    print(f"DATABASE_PATH configurado: {DATABASE_PATH}")
    print(f"DB existe en destino: {db_path.exists()}")

    # Verificar si la DB existe Y tiene contenido (más de 10KB significa que tiene datos)
    db_exists_with_data = db_path.exists() and db_path.stat().st_size > 10000

    if db_exists_with_data:
        print(f"Base de datos ya existe con datos ({db_path.stat().st_size} bytes)")
        return

    # Buscar la DB de origen en el repo
    source_db = Path(__file__).parent / "data" / "catalogo.db"
    print(f"Buscando DB origen en: {source_db}")
    print(f"DB origen existe: {source_db.exists()}")

    if source_db.exists():
        try:
            # Crear directorio destino si no existe
            db_path.parent.mkdir(parents=True, exist_ok=True)
            # Copiar la base de datos (sobrescribir si existe vacía)
            shutil.copy2(source_db, db_path)
            print(f"Base de datos copiada exitosamente de {source_db} a {db_path} ({source_db.stat().st_size} bytes)")
        except Exception as e:
            print(f"Error al copiar base de datos: {e}")
            # Si no se puede copiar al volume, usar la del repo directamente
            DATABASE_PATH = str(source_db)
            print(f"Usando base de datos del repo: {DATABASE_PATH}")
    else:
        print("ADVERTENCIA: No se encontró la base de datos origen")

# Ejecutar al importar el módulo
ensure_database()


def get_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager para conexiones a la base de datos"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Inicializa la base de datos con las tablas necesarias"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Tabla principal de productos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT UNIQUE NOT NULL,
                departamento TEXT,
                marca TEXT,
                descripcion_original TEXT,
                nombre_producto TEXT,
                tipo_producto TEXT,
                skus_alternos TEXT,
                precio_publico REAL,
                precio_mayoreo REAL,
                imagen_url TEXT,
                inventario_total INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de compatibilidades (relación muchos a muchos)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compatibilidades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                marca_vehiculo TEXT,
                modelo_vehiculo TEXT,
                año_inicio INTEGER,
                año_fin INTEGER,
                motor TEXT,
                cilindros TEXT,
                especificacion TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
            )
        """)

        # Tabla de inventario por sucursal
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                sucursal TEXT NOT NULL,
                cantidad REAL DEFAULT 0,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
                UNIQUE(producto_id, sucursal)
            )
        """)

        # Tabla de características específicas de producto (llantas, aceites, acumuladores)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS caracteristicas_producto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                categoria TEXT NOT NULL,
                clave TEXT NOT NULL,
                valor TEXT NOT NULL,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
            )
        """)

        # Índices para búsquedas rápidas
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_departamento ON productos(departamento)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_marca ON productos(marca)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_sku ON productos(sku)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compatibilidades_marca ON compatibilidades(marca_vehiculo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compatibilidades_modelo ON compatibilidades(modelo_vehiculo)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compatibilidades_años ON compatibilidades(año_inicio, año_fin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_compatibilidades_producto ON compatibilidades(producto_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_inventario_producto ON inventario(producto_id)")

        # Índices para características de producto
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_caracteristicas_producto ON caracteristicas_producto(producto_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_caracteristicas_categoria ON caracteristicas_producto(categoria)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_caracteristicas_clave_valor ON caracteristicas_producto(clave, valor)")

        # Tabla de especificaciones manuales (editables por usuario)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS especificaciones_manuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                valor TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
                UNIQUE(producto_id, tipo)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_especs_manuales_producto ON especificaciones_manuales(producto_id)")

        # Tabla de productos intercambiables (precalculada)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS productos_intercambiables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                producto_id INTEGER NOT NULL,
                producto_intercambiable_id INTEGER NOT NULL,
                sku_comun TEXT,
                FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_intercambiable_id) REFERENCES productos(id) ON DELETE CASCADE,
                UNIQUE(producto_id, producto_intercambiable_id)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intercambiables_producto ON productos_intercambiables(producto_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_intercambiables_inverso ON productos_intercambiables(producto_intercambiable_id)")

        # Columna grupo_producto (ALTER TABLE idempotente)
        try:
            cursor.execute("ALTER TABLE productos ADD COLUMN grupo_producto TEXT")
        except Exception:
            pass  # columna ya existe
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_grupo ON productos(grupo_producto)")

        print("Base de datos inicializada correctamente")


if __name__ == "__main__":
    init_database()
