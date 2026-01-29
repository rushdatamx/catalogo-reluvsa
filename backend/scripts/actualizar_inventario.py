"""
Script de actualización incremental de inventario.

Uso:
    python3 scripts/actualizar_inventario.py ../data/nuevo_inventario.csv

Funcionalidad:
- Actualiza precios e inventario de productos existentes
- Inserta productos nuevos (quedan marcados por created_at)
- Pone en 0 el inventario de productos que no vienen en el CSV
- NO borra datos existentes (compatibilidades, características, intercambiables)
- Actualiza grupo_producto desde el CSV

Formato CSV (16 columnas):
    0: Clave (SKU)
    1: Grupo -> Nombre (grupo_producto)
    2: Codigo de Barras (IGNORADO)
    3: Departamento -> Nombre
    4: Marcas Prodcuto -> Nombre
    5: Descripcion
    6: Precio Publico
    7: Precio Mayoreo
    8: Variant Scr (imagen_url)
    9-14: Sucursales (inventario)
    15: Total Almacenes (inventario_total)
"""

import csv
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Configuración
DB_PATH = Path(__file__).parent.parent / "data" / "catalogo.db"

# Mapeo de columnas del CSV a sucursales (nuevo formato)
SUCURSALES = {
    9: 'Suc. Carrera',
    10: 'Suc. Berriozabal',
    11: 'CEDIS',
    12: 'Suc. 31 Juarez',
    13: 'FULL',
    14: 'Suc. E-commerce'
}


def limpiar_numero(valor: str) -> float:
    """Limpia un valor numérico del CSV (quita comas, maneja vacíos)."""
    if not valor or valor.strip() == '':
        return 0.0
    return float(valor.replace(',', '').strip())


def normalizar_sku(sku: str) -> str:
    """
    Normaliza un SKU quitando ceros iniciales en SKUs numéricos.
    Esto permite hacer match entre '001000001' (CSV) y '1000001' (DB).
    """
    sku = sku.strip()
    if sku.isdigit():
        return sku.lstrip('0') or '0'
    return sku


def actualizar_inventario(csv_path: str, db_path: str = None):
    """
    Actualiza inventario de forma incremental desde un CSV.

    Args:
        csv_path: Ruta al archivo CSV con el nuevo inventario
        db_path: Ruta a la base de datos (opcional, usa default)

    Returns:
        dict con estadísticas de la actualización
    """
    if db_path is None:
        db_path = str(DB_PATH)

    # Verificar que el CSV existe
    if not Path(csv_path).exists():
        print(f"ERROR: No se encontró el archivo CSV: {csv_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Estadísticas
    stats = {
        'actualizados': 0,
        'nuevos': 0,
        'inventario_cero': 0,
        'errores': [],
        'skus_nuevos': []
    }

    print(f"\n{'='*60}")
    print("ACTUALIZACIÓN INCREMENTAL DE INVENTARIO")
    print(f"{'='*60}")
    print(f"CSV: {csv_path}")
    print(f"DB:  {db_path}")
    print(f"{'='*60}\n")

    # Obtener todos los SKUs existentes (normalizados para comparación)
    cursor.execute("SELECT sku FROM productos")
    skus_db_raw = [row[0] for row in cursor.fetchall()]
    # Mapeo: SKU normalizado -> SKU original en DB
    sku_norm_to_db = {normalizar_sku(s): s for s in skus_db_raw}
    skus_existentes_norm = set(sku_norm_to_db.keys())
    print(f"Productos existentes en DB: {len(skus_db_raw):,}")

    skus_en_csv_norm = set()

    # Leer y procesar CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header

        print(f"Columnas detectadas: {len(header)}")
        print(f"Procesando CSV...\n")

        for row_num, row in enumerate(reader, start=2):
            try:
                if len(row) < 16:
                    stats['errores'].append(f"Fila {row_num}: menos de 16 columnas")
                    continue

                sku_csv = row[0].strip()
                if not sku_csv:
                    continue

                sku_norm = normalizar_sku(sku_csv)
                skus_en_csv_norm.add(sku_norm)

                # Parsear datos (nuevo formato 16 columnas)
                grupo_producto = row[1].strip() or None  # Grupo -> Nombre
                # row[2] = Codigo de Barras (IGNORADO)
                departamento = row[3].strip()
                marca = row[4].strip()
                descripcion = row[5].strip()
                precio_publico = limpiar_numero(row[6])
                precio_mayoreo = limpiar_numero(row[7])
                imagen_url = row[8].strip()
                inventario_total = int(limpiar_numero(row[15]))

                if sku_norm in skus_existentes_norm:
                    # Usar el SKU original de la DB para el UPDATE
                    sku = sku_norm_to_db[sku_norm]
                    # UPDATE producto existente
                    cursor.execute("""
                        UPDATE productos SET
                            departamento = ?,
                            marca = ?,
                            descripcion_original = ?,
                            precio_publico = ?,
                            precio_mayoreo = ?,
                            imagen_url = ?,
                            inventario_total = ?,
                            grupo_producto = COALESCE(?, grupo_producto)
                        WHERE sku = ?
                    """, (departamento, marca, descripcion, precio_publico,
                          precio_mayoreo, imagen_url, inventario_total, grupo_producto, sku))
                    stats['actualizados'] += 1
                else:
                    # INSERT nuevo producto (usar SKU normalizado para consistencia)
                    sku = sku_norm
                    cursor.execute("""
                        INSERT INTO productos
                        (sku, departamento, marca, descripcion_original,
                         precio_publico, precio_mayoreo, imagen_url, inventario_total,
                         grupo_producto, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                    """, (sku, departamento, marca, descripcion,
                          precio_publico, precio_mayoreo, imagen_url, inventario_total,
                          grupo_producto))
                    stats['nuevos'] += 1
                    stats['skus_nuevos'].append(sku)

                # Obtener ID del producto
                cursor.execute("SELECT id FROM productos WHERE sku = ?", (sku,))
                producto_id = cursor.fetchone()[0]

                # Eliminar inventario anterior de este producto
                cursor.execute("DELETE FROM inventario WHERE producto_id = ?", (producto_id,))

                # Insertar nuevo inventario por sucursal
                for col_idx, sucursal in SUCURSALES.items():
                    cantidad = limpiar_numero(row[col_idx])
                    if cantidad > 0:
                        cursor.execute("""
                            INSERT INTO inventario (producto_id, sucursal, cantidad)
                            VALUES (?, ?, ?)
                        """, (producto_id, sucursal, cantidad))

                # Commit cada 1000 productos para no perder todo si falla
                if (stats['actualizados'] + stats['nuevos']) % 1000 == 0:
                    conn.commit()
                    print(f"  Procesados: {stats['actualizados'] + stats['nuevos']:,}...")

            except Exception as e:
                stats['errores'].append(f"Fila {row_num} (SKU: {row[0] if row else '?'}): {str(e)}")

    print(f"\nProductos en CSV: {len(skus_en_csv_norm):,}")

    # Poner en 0 inventario de productos que no vienen en CSV
    skus_no_en_csv_norm = skus_existentes_norm - skus_en_csv_norm
    if skus_no_en_csv_norm:
        print(f"\nProductos NO en CSV (inventario → 0): {len(skus_no_en_csv_norm):,}")
        for sku_norm in skus_no_en_csv_norm:
            sku = sku_norm_to_db[sku_norm]  # Usar SKU original de DB
            cursor.execute("""
                UPDATE productos SET inventario_total = 0 WHERE sku = ?
            """, (sku,))
            cursor.execute("""
                DELETE FROM inventario WHERE producto_id = (
                    SELECT id FROM productos WHERE sku = ?
                )
            """, (sku,))
            stats['inventario_cero'] += 1

    conn.commit()
    conn.close()

    # Imprimir resumen
    print(f"\n{'='*60}")
    print("RESUMEN DE ACTUALIZACIÓN")
    print(f"{'='*60}")
    print(f"✓ Productos actualizados:    {stats['actualizados']:,}")
    print(f"✓ Productos NUEVOS:          {stats['nuevos']:,}")
    print(f"✓ Productos con inv. → 0:    {stats['inventario_cero']:,}")
    print(f"✗ Errores:                   {len(stats['errores'])}")

    if stats['nuevos'] > 0:
        print(f"\n{'─'*60}")
        print("PRODUCTOS NUEVOS (primeros 20):")
        for sku in stats['skus_nuevos'][:20]:
            print(f"  • {sku}")
        if stats['nuevos'] > 20:
            print(f"  ... y {stats['nuevos'] - 20} más")
        print(f"\n⚠️  IMPORTANTE: Ejecutar extractores para productos nuevos:")
        print("    python3 scripts/extraer_compatibilidades.py")
        print("    python3 scripts/extraer_caracteristicas.py")
        print("    python3 scripts/calcular_intercambiables.py")

    if stats['errores']:
        print(f"\n{'─'*60}")
        print("ERRORES:")
        for error in stats['errores'][:10]:
            print(f"  • {error}")
        if len(stats['errores']) > 10:
            print(f"  ... y {len(stats['errores']) - 10} errores más")

    print(f"\n{'='*60}\n")

    return stats


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 actualizar_inventario.py <ruta_al_csv>")
        print("Ejemplo: python3 scripts/actualizar_inventario.py ../data/nuevo_inventario.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    actualizar_inventario(csv_path)
