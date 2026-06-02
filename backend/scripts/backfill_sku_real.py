"""
Backfill de la columna sku_real (SKU comercial, col 2 del Excel) para productos
que ya existen en la BD.

Contexto:
- productos.sku  = "Clave" (col 0 del Excel), código interno largo
- productos.sku_real = "SKU" (col 2 del Excel), número de parte comercial
  (solo ~19% de productos lo tienen poblado)

El script lee data/limpieza-catalogo.xlsx, normaliza la Clave igual que
actualizar_precios_excel.py y escribe sku_real donde el Excel lo trae poblado.
No borra ningún sku_real existente con un valor vacío.

Uso:
    python3 scripts/backfill_sku_real.py
"""

import sqlite3
from pathlib import Path

import openpyxl

# Mismas rutas/constantes que actualizar_precios_excel.py
DB_PATH = Path(__file__).parent.parent / "data" / "catalogo.db"
EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "limpieza-catalogo.xlsx"
SHEET_NAME = "TODOS LOS PRODUCTOS MAYO"

COL_SKU = 0       # Clave
COL_SKU_REAL = 2  # SKU comercial


def normalizar_sku(sku: str) -> str:
    """Normaliza SKU quitando ceros iniciales en numéricos y espacios."""
    sku = str(sku).strip()
    if sku.isdigit():
        return sku.lstrip('0') or '0'
    return sku


def main():
    print(f"Leyendo Excel: {EXCEL_PATH}")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb[SHEET_NAME]

    # Clave normalizada -> sku_real (col 2), solo donde col 2 viene poblada
    sku_real_por_clave = {}
    filas_con_sku = 0
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_SKU]:
            continue
        sku_real = (str(row[COL_SKU_REAL]).strip() if row[COL_SKU_REAL] is not None else '')
        if not sku_real:
            continue
        filas_con_sku += 1
        clave_norm = normalizar_sku(row[COL_SKU])
        sku_real_por_clave[clave_norm] = sku_real
    wb.close()
    print(f"Filas con SKU comercial en Excel: {filas_con_sku:,}")
    print(f"Claves únicas con SKU: {len(sku_real_por_clave):,}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, sku, sku_real FROM productos")
    rows_db = cursor.fetchall()
    print(f"Productos en BD: {len(rows_db):,}")

    actualizados = 0
    sin_cambio = 0
    no_en_excel = 0
    for pid, sku, sku_real_actual in rows_db:
        sku_real_excel = sku_real_por_clave.get(normalizar_sku(sku))
        if not sku_real_excel:
            no_en_excel += 1
            continue
        if (sku_real_actual or '') == sku_real_excel:
            sin_cambio += 1
            continue
        cursor.execute(
            "UPDATE productos SET sku_real = ? WHERE id = ?",
            (sku_real_excel, pid),
        )
        actualizados += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM productos WHERE sku_real IS NOT NULL AND sku_real != ''")
    total_con_sku = cursor.fetchone()[0]
    conn.close()

    print("\n=== RESUMEN BACKFILL ===")
    print(f"  Actualizados:           {actualizados:,}")
    print(f"  Ya correctos:           {sin_cambio:,}")
    print(f"  Sin SKU en Excel:       {no_en_excel:,}")
    print(f"  Total con sku_real:     {total_con_sku:,}")


if __name__ == "__main__":
    main()
