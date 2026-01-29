"""
Script para importar grupos de producto desde CSV.

Lee data/grupos_producto.csv y actualiza la columna grupo_producto
en la tabla productos.

Ejecutar desde /backend:
    python3 scripts/importar_grupos.py
"""
import sys
import csv
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3


def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "catalogo.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def main():
    print("=" * 70)
    print("IMPORTACION DE GRUPOS DE PRODUCTO")
    print("=" * 70)

    csv_path = Path(__file__).parent.parent.parent / "data" / "grupos_producto.csv"
    if not csv_path.exists():
        print(f"ERROR: No se encontro {csv_path}")
        return

    conn = get_db()
    cursor = conn.cursor()

    # Agregar columna si no existe
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN grupo_producto TEXT")
        print("Columna grupo_producto creada.")
    except Exception:
        print("Columna grupo_producto ya existe.")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_productos_grupo ON productos(grupo_producto)")

    # Limpiar valores previos
    cursor.execute("UPDATE productos SET grupo_producto = NULL")
    conn.commit()

    # Leer CSV
    actualizados = 0
    sin_grupo = 0
    no_encontrados = 0
    total = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        print(f"Header: {header}")

        batch = []
        for row in reader:
            total += 1
            sku = row[0].strip()
            grupo = row[1].strip() if len(row) > 1 else ''

            # Ignorar sin grupo
            if grupo in ('#N/D', '0', '', 'N/D'):
                sin_grupo += 1
                continue

            batch.append((grupo, sku))

            if len(batch) >= 1000:
                cursor.executemany(
                    "UPDATE productos SET grupo_producto = ? WHERE sku = ?",
                    batch
                )
                actualizados += len(batch)
                batch = []

        if batch:
            cursor.executemany(
                "UPDATE productos SET grupo_producto = ? WHERE sku = ?",
                batch
            )
            actualizados += len(batch)

    conn.commit()

    # Verificar
    cursor.execute("SELECT COUNT(*) as n FROM productos WHERE grupo_producto IS NOT NULL")
    en_db = cursor.fetchone()['n']

    cursor.execute("SELECT COUNT(DISTINCT grupo_producto) as n FROM productos WHERE grupo_producto IS NOT NULL")
    grupos_unicos = cursor.fetchone()['n']

    cursor.execute("SELECT COUNT(*) as n FROM productos WHERE grupo_producto IS NULL")
    sin_grupo_db = cursor.fetchone()['n']

    # Top 10 grupos
    cursor.execute("""
        SELECT grupo_producto, COUNT(*) as n
        FROM productos
        WHERE grupo_producto IS NOT NULL
        GROUP BY grupo_producto
        ORDER BY n DESC
        LIMIT 15
    """)
    top = cursor.fetchall()

    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")
    print(f"Total filas CSV: {total}")
    print(f"Actualizados: {actualizados}")
    print(f"Sin grupo (CSV): {sin_grupo}")
    print(f"Productos con grupo (DB): {en_db}")
    print(f"Productos sin grupo (DB): {sin_grupo_db}")
    print(f"Grupos unicos: {grupos_unicos}")

    print(f"\nTOP 15 GRUPOS:")
    for row in top:
        print(f"  {row['grupo_producto']:40s}: {row['n']} productos")

    conn.close()
    print(f"\n{'='*70}")
    print("IMPORTACION COMPLETADA")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
