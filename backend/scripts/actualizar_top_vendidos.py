"""
Script de actualización del TOP de más vendidos desde Excel.

Uso:
    cd backend
    python3 scripts/actualizar_top_vendidos.py

Lee data/top-mas-vendidos.xlsx (análisis 80-20 mensual del cliente).
Formato esperado (3 columnas, con encabezado en la fila 1):
    | Top (rank) | SKU (= Clave del catálogo) | Descripcion |

Qué hace:
- Limpia el ranking anterior (ranking_ventas = NULL en todos los productos).
- Hace match por sku (Clave) exacto contra la BD.
- Escribe ranking_ventas = posición del Top (1 = el más vendido).
- Los SKUs que no existen en el catálogo (mano de obra, servicios, paquetes)
  simplemente se omiten y se listan en el reporte.

El SKU del archivo hace match directo con productos.sku (la "Clave" interna),
NO con sku_real. Se probó y ~97% de las filas hacen match exacto; el resto son
conceptos de servicio (prefijos 300..., 1982...) que no son productos físicos.

Después de correr: copiar la BD y hacer deploy (igual que actualizar_precios_excel.py):
    cp data/catalogo.db ../data/catalogo.db
    git add backend/data/catalogo.db data/catalogo.db
    git commit -m "Update top más vendidos"
    git push
"""

import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

import openpyxl

# Rutas
DB_PATH = Path(__file__).parent.parent / "data" / "catalogo.db"
EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "top-mas-vendidos.xlsx"

# Columnas del Excel (0-indexed)
COL_TOP = 0          # Ranking (1, 2, 3, ...)
COL_SKU = 1          # SKU = Clave del catálogo
COL_DESCRIPCION = 2  # Descripción (solo informativa)


def limpiar_sku(valor) -> str:
    """Normaliza el SKU del Excel: string, sin espacios sobrantes.

    El Excel a veces trae el SKU como número (openpyxl lo lee como int) y a
    veces como texto con espacios finales ('300OTR037           ').
    """
    if valor is None:
        return ""
    # Si openpyxl lo leyó como número, evitar notación tipo 2.5e+13
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return str(valor).strip()


def main():
    print("=" * 70)
    print("ACTUALIZACIÓN DE TOP MÁS VENDIDOS")
    print("=" * 70)

    if not EXCEL_PATH.exists():
        print(f"\n❌ No se encontró el archivo: {EXCEL_PATH}")
        print("   Coloca el archivo mensual en data/top-mas-vendidos.xlsx")
        sys.exit(1)

    if not DB_PATH.exists():
        print(f"\n❌ No se encontró la base de datos: {DB_PATH}")
        sys.exit(1)

    # Backup automático de la BD
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.parent / f"catalogo_backup_topventas_{ts}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"\n📦 Backup creado: {backup_path.name}")

    # Leer el Excel
    print(f"\n📖 Leyendo {EXCEL_PATH.name}...")
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb.active
    print(f"   Hoja: '{ws.title}'")

    filas = list(ws.iter_rows(values_only=True))
    # Saltar encabezado
    filas = filas[1:]

    # Parsear (rank, sku) — el rank del archivo es la fuente de verdad
    entradas = []
    fila_num = 1  # cuenta desde la primera fila de datos
    for row in filas:
        fila_num += 1
        if not row or row[COL_SKU] is None:
            continue
        sku = limpiar_sku(row[COL_SKU])
        if not sku:
            continue
        # Usar el rank del archivo; si viene vacío, usar el orden de aparición
        rank_raw = row[COL_TOP]
        try:
            rank = int(rank_raw)
        except (TypeError, ValueError):
            rank = len(entradas) + 1
        desc = row[COL_DESCRIPCION] if len(row) > COL_DESCRIPCION else ""
        entradas.append((rank, sku, desc))

    print(f"   Filas con SKU: {len(entradas)}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Asegurar que la columna exista (idempotente)
    try:
        cursor.execute("ALTER TABLE productos ADD COLUMN ranking_ventas INTEGER")
        print("   Columna ranking_ventas creada.")
    except sqlite3.OperationalError:
        pass  # ya existe
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_productos_ranking ON productos(ranking_ventas)"
    )

    # Limpiar ranking anterior (reset completo)
    cursor.execute("UPDATE productos SET ranking_ventas = NULL")
    print("\n🧹 Ranking anterior limpiado.")

    # Aplicar nuevo ranking por match de SKU exacto
    matched = 0
    sin_match = []
    duplicados = 0
    ranks_aplicados = set()

    for rank, sku, desc in entradas:
        # Si un mismo SKU aparece dos veces, conservar la mejor posición (menor rank)
        if sku in ranks_aplicados:
            duplicados += 1
        cursor.execute(
            """
            UPDATE productos
            SET ranking_ventas = ?
            WHERE sku = ?
              AND (ranking_ventas IS NULL OR ranking_ventas > ?)
            """,
            (rank, sku, rank),
        )
        if cursor.rowcount > 0:
            matched += 1
            ranks_aplicados.add(sku)
        else:
            # Verificar si el SKU existe pero ya tenía mejor rank, o no existe
            cursor.execute("SELECT 1 FROM productos WHERE sku = ?", (sku,))
            if cursor.fetchone() is None:
                desc_corta = (str(desc)[:55] + "…") if desc and len(str(desc)) > 55 else (desc or "")
                sin_match.append((rank, sku, desc_corta))

    conn.commit()

    # Verificación final
    cursor.execute(
        "SELECT COUNT(*) AS n FROM productos WHERE ranking_ventas IS NOT NULL"
    )
    total_con_ranking = cursor.fetchone()["n"]

    # Reporte
    print("\n" + "=" * 70)
    print("REPORTE")
    print("=" * 70)
    print(f"Filas en el archivo:         {len(entradas)}")
    print(f"Productos con ranking (BD):  {total_con_ranking}")
    print(f"Sin match (no en catálogo):  {len(sin_match)}")
    if duplicados:
        print(f"SKUs duplicados en archivo:  {duplicados}")

    if sin_match:
        print("\n--- SKUs sin match (servicios / paquetes / no en catálogo) ---")
        for rank, sku, desc in sin_match:
            print(f"   #{rank:<4} {sku:<20} {desc}")

    # Top 10 para verificación visual
    cursor.execute(
        """
        SELECT ranking_ventas, sku, nombre_producto, marca
        FROM productos
        WHERE ranking_ventas IS NOT NULL
        ORDER BY ranking_ventas
        LIMIT 10
        """
    )
    print("\n--- Top 10 (verificación) ---")
    for r in cursor.fetchall():
        nombre = r["nombre_producto"] or "(sin nombre)"
        print(f"   #{r['ranking_ventas']:<4} {r['sku']:<20} [{r['marca']}] {nombre[:45]}")

    conn.close()

    print("\n✅ Listo. Recuerda copiar la BD y hacer deploy:")
    print("   cp data/catalogo.db ../data/catalogo.db")
    print('   git add backend/data/catalogo.db data/catalogo.db')
    print('   git commit -m "Update top más vendidos"')
    print("   git push")


if __name__ == "__main__":
    main()
