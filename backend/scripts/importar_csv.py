"""
Script para importar el CSV del catálogo a la base de datos SQLite
"""
import csv
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db, init_database

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "catalogo-reluvsa-oficial.csv"

# Mapeo de columnas del CSV
COLUMNAS = {
    'sku': 0,                    # Clave
    'departamento': 1,           # Departamento -> Nombre
    'marca': 2,                  # Marcas Prodcuto -> Nombre
    'descripcion': 3,            # Descripcion
    'precio_publico': 4,         # Precio público con IVA 2
    'precio_mayoreo': 5,         # Precio mayoreo con IVA 2
    'imagen_url': 6,             # Variant Scr
    'inv_carrera': 7,            # Suc. Carrera
    'inv_berriozabal': 8,        # Suc. Berriozabal
    'inv_cedis': 9,              # CEDIS
    'inv_juarez': 10,            # Suc. 31 Juarez
    'inv_full': 11,              # FULL
    'inv_ecommerce': 12,         # Suc. E-commerce
    'inv_total': 13,             # Total Almacenes
}

SUCURSALES = [
    ('Suc. Carrera', 7),
    ('Suc. Berriozabal', 8),
    ('CEDIS', 9),
    ('Suc. 31 Juarez', 10),
    ('FULL', 11),
    ('Suc. E-commerce', 12),
]


def limpiar_precio(valor: str) -> float:
    """Convierte un string de precio a float"""
    if not valor or valor.strip() == '':
        return 0.0
    try:
        return float(valor.replace(',', ''))
    except ValueError:
        return 0.0


def limpiar_inventario(valor: str) -> float:
    """Convierte un string de inventario a float"""
    if not valor or valor.strip() == '':
        return 0.0
    try:
        return float(valor.replace(',', ''))
    except ValueError:
        return 0.0


def importar_csv():
    """Importa el CSV a la base de datos"""
    print(f"Leyendo archivo: {CSV_PATH}")

    if not CSV_PATH.exists():
        print(f"ERROR: No se encontró el archivo {CSV_PATH}")
        return

    # Inicializar la base de datos
    init_database()

    productos_insertados = 0
    productos_error = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Limpiar tablas existentes
        print("Limpiando tablas existentes...")
        cursor.execute("DELETE FROM inventario")
        cursor.execute("DELETE FROM compatibilidades")
        cursor.execute("DELETE FROM productos")

        with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)

            # Saltar encabezado
            next(reader)

            for row_num, row in enumerate(reader, start=2):
                if len(row) < 14:
                    print(f"Fila {row_num}: Columnas insuficientes ({len(row)})")
                    productos_error += 1
                    continue

                sku = row[COLUMNAS['sku']].strip()
                if not sku:
                    productos_error += 1
                    continue

                departamento = row[COLUMNAS['departamento']].strip()
                marca = row[COLUMNAS['marca']].strip()
                descripcion = row[COLUMNAS['descripcion']].strip()
                precio_publico = limpiar_precio(row[COLUMNAS['precio_publico']])
                precio_mayoreo = limpiar_precio(row[COLUMNAS['precio_mayoreo']])
                imagen_url = row[COLUMNAS['imagen_url']].strip()
                inventario_total = limpiar_inventario(row[COLUMNAS['inv_total']])

                try:
                    # Insertar producto
                    cursor.execute("""
                        INSERT INTO productos (
                            sku, departamento, marca, descripcion_original,
                            precio_publico, precio_mayoreo, imagen_url, inventario_total
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sku, departamento, marca, descripcion,
                        precio_publico, precio_mayoreo, imagen_url, inventario_total
                    ))

                    producto_id = cursor.lastrowid

                    # Insertar inventario por sucursal
                    for sucursal_nombre, col_idx in SUCURSALES:
                        cantidad = limpiar_inventario(row[col_idx])
                        if cantidad > 0:
                            cursor.execute("""
                                INSERT INTO inventario (producto_id, sucursal, cantidad)
                                VALUES (?, ?, ?)
                            """, (producto_id, sucursal_nombre, cantidad))

                    productos_insertados += 1

                    if productos_insertados % 5000 == 0:
                        print(f"  Procesados: {productos_insertados} productos...")
                        conn.commit()

                except Exception as e:
                    print(f"Error en fila {row_num} (SKU: {sku}): {e}")
                    productos_error += 1

    print(f"\nImportación completada:")
    print(f"  - Productos insertados: {productos_insertados}")
    print(f"  - Errores: {productos_error}")

    # Mostrar estadísticas
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM productos")
        total = cursor.fetchone()[0]
        print(f"\nTotal productos en BD: {total}")

        cursor.execute("SELECT departamento, COUNT(*) as cnt FROM productos GROUP BY departamento ORDER BY cnt DESC LIMIT 10")
        print("\nTop 10 departamentos:")
        for row in cursor.fetchall():
            print(f"  - {row['departamento']}: {row['cnt']}")

        cursor.execute("SELECT marca, COUNT(*) as cnt FROM productos GROUP BY marca ORDER BY cnt DESC LIMIT 10")
        print("\nTop 10 marcas:")
        for row in cursor.fetchall():
            print(f"  - {row['marca']}: {row['cnt']}")


if __name__ == "__main__":
    importar_csv()
