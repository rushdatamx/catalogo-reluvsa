"""
Script de actualización de precios e inventario desde Excel (con IVA).

Uso:
    python3 scripts/actualizar_precios_excel.py

Lee data/limpieza-catalogo.xlsx, hoja "TODOS LOS PRODUCTOS ACTUALIZADO".
Actualiza:
- precio_publico y precio_mayoreo con precios CON IVA
- inventario_total y tabla inventario por sucursal
NO modifica nombres, compatibilidades, características ni intercambiables.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import openpyxl

# Rutas
DB_PATH = Path(__file__).parent.parent / "data" / "catalogo.db"
EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "limpieza-catalogo.xlsx"
SHEET_NAME = "TODOS LOS PRODUCTOS ACTUALIZADO"

# Columnas del Excel
COL_SKU = 0               # Clave
COL_PRECIO_PUBLICO = 12   # Precio abierto 3 C/IVA (público)
COL_PRECIO_MAYOREO = 13   # Precio abierto 5 C/IVA (mayoreo)
COL_INVENTARIO_TOTAL = 21 # Total Almacenes

# Mapeo: columna Excel -> nombre de sucursal en BD
SUCURSALES = {
    15: 'Suc. Carrera',
    16: 'Suc. Berriozabal',
    17: 'CEDIS',
    18: 'Suc. 31 Juarez',
    19: 'FULL',
    20: 'Suc. E-commerce',
}


def normalizar_sku(sku: str) -> str:
    """Normaliza SKU quitando ceros iniciales en numéricos y espacios."""
    sku = str(sku).strip()
    if sku.isdigit():
        return sku.lstrip('0') or '0'
    return sku


def limpiar_numero(valor) -> float:
    """Convierte valor de celda a float, manejando None y errores."""
    if valor is None:
        return 0.0
    try:
        return float(valor)
    except (ValueError, TypeError):
        return 0.0


def actualizar_precios(db_path: str = None, excel_path: str = None):
    if db_path is None:
        db_path = str(DB_PATH)
    if excel_path is None:
        excel_path = str(EXCEL_PATH)

    # Verificar archivos
    if not Path(excel_path).exists():
        print(f"ERROR: No se encontró el Excel: {excel_path}")
        return
    if not Path(db_path).exists():
        print(f"ERROR: No se encontró la BD: {db_path}")
        return

    # Backup
    backup_path = str(db_path).replace('.db', f'_backup_precios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    shutil.copy2(db_path, backup_path)
    print(f"Backup creado: {backup_path}")

    # Leer Excel
    print(f"\nLeyendo Excel: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb[SHEET_NAME]

    # Construir diccionario SKU -> datos
    datos_excel = {}
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_SKU]:
            continue
        sku = normalizar_sku(row[COL_SKU])
        precio_pub = round(limpiar_numero(row[COL_PRECIO_PUBLICO]), 2)
        precio_may = round(limpiar_numero(row[COL_PRECIO_MAYOREO]), 2)
        inv_total = int(limpiar_numero(row[COL_INVENTARIO_TOTAL]))

        # Inventario por sucursal
        inv_sucursales = {}
        for col_idx, nombre_suc in SUCURSALES.items():
            cantidad = int(limpiar_numero(row[col_idx]))
            if cantidad > 0:
                inv_sucursales[nombre_suc] = cantidad

        datos_excel[sku] = (precio_pub, precio_may, inv_total, inv_sucursales)

    wb.close()
    print(f"Productos en Excel: {len(datos_excel):,}")

    # Conectar a BD
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Obtener SKUs y IDs de la BD
    cursor.execute("SELECT id, sku FROM productos")
    rows_db = cursor.fetchall()
    sku_to_id = {row[1]: row[0] for row in rows_db}
    sku_norm_to_db = {normalizar_sku(s): s for s in sku_to_id.keys()}
    print(f"Productos en BD: {len(sku_to_id):,}")

    # Contar inventario actual
    cursor.execute("SELECT COUNT(*) FROM inventario")
    inv_antes = cursor.fetchone()[0]

    # Estadísticas
    actualizados = 0
    no_encontrados = 0
    precio_cero = 0
    inv_registros = 0

    print(f"\nActualizando precios e inventario...\n")

    for sku_norm, (precio_pub, precio_may, inv_total, inv_sucursales) in datos_excel.items():
        if sku_norm not in sku_norm_to_db:
            no_encontrados += 1
            continue

        sku_db = sku_norm_to_db[sku_norm]
        producto_id = sku_to_id[sku_db]

        # UPDATE precios e inventario_total
        cursor.execute("""
            UPDATE productos
            SET precio_publico = ?, precio_mayoreo = ?, inventario_total = ?
            WHERE id = ?
        """, (precio_pub, precio_may, inv_total, producto_id))

        actualizados += 1
        if precio_pub == 0.0:
            precio_cero += 1

        # Reemplazar inventario por sucursal
        cursor.execute("DELETE FROM inventario WHERE producto_id = ?", (producto_id,))
        for sucursal, cantidad in inv_sucursales.items():
            cursor.execute("""
                INSERT INTO inventario (producto_id, sucursal, cantidad)
                VALUES (?, ?, ?)
            """, (producto_id, sucursal, cantidad))
            inv_registros += 1

        # Commit cada 2000 productos
        if actualizados % 2000 == 0:
            conn.commit()
            print(f"  Procesados: {actualizados:,}...")

    # Productos en BD que NO están en el Excel → inventario a 0
    skus_en_excel = set(sku_norm_to_db[k] for k in datos_excel.keys() if k in sku_norm_to_db)
    skus_sin_excel = set(sku_to_id.keys()) - skus_en_excel
    inv_a_cero = 0
    for sku_db in skus_sin_excel:
        producto_id = sku_to_id[sku_db]
        cursor.execute("UPDATE productos SET inventario_total = 0 WHERE id = ?", (producto_id,))
        cursor.execute("DELETE FROM inventario WHERE producto_id = ?", (producto_id,))
        inv_a_cero += 1

    conn.commit()

    # Verificaciones finales
    cursor.execute("SELECT COUNT(*) FROM productos WHERE precio_publico = 0 OR precio_publico IS NULL")
    total_cero_final = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventario")
    inv_despues = cursor.fetchone()[0]

    cursor.execute("SELECT precio_publico, precio_mayoreo, inventario_total FROM productos WHERE sku = '125010075'")
    ejemplo = cursor.fetchone()

    cursor.execute("""
        SELECT i.sucursal, i.cantidad FROM inventario i
        JOIN productos p ON p.id = i.producto_id
        WHERE p.sku = '125010075'
        ORDER BY i.sucursal
    """)
    ejemplo_inv = cursor.fetchall()

    conn.close()

    # Reporte
    print(f"\n{'='*60}")
    print("RESUMEN DE ACTUALIZACIÓN")
    print(f"{'='*60}")
    print(f"  Productos actualizados:       {actualizados:,}")
    print(f"  No encontrados en BD:         {no_encontrados:,}")
    print(f"  Productos inv. → 0:           {inv_a_cero:,}")
    print(f"  Quedan con precio $0:         {total_cero_final:,}")
    print(f"{'─'*60}")
    print(f"  Registros inventario antes:   {inv_antes:,}")
    print(f"  Registros inventario ahora:   {inv_despues:,}")
    print(f"{'='*60}")

    if ejemplo:
        print(f"\nVerificación SKU 125010075:")
        print(f"  Precio público:  ${ejemplo[0]:,.2f}")
        print(f"  Precio mayoreo:  ${ejemplo[1]:,.2f}")
        print(f"  Inventario total: {ejemplo[2]}")
        for suc, cant in ejemplo_inv:
            print(f"    {suc}: {cant}")

    print(f"\nBackup disponible en: {backup_path}")
    print("Precios incluyen IVA. Inventario actualizado por sucursal.")


if __name__ == "__main__":
    actualizar_precios()
