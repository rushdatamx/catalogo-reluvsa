"""
Script para precalcular productos intercambiables.

Analiza skus_alternos de todos los productos y detecta cuales comparten
SKUs (principal o alterno). Guarda relaciones bidireccionales en la tabla
productos_intercambiables.

Ejecutar desde /backend:
    python3 scripts/calcular_intercambiables.py
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3


def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "catalogo.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def normalizar_sku(sku):
    """Normaliza un SKU para comparacion: uppercase, sin espacios, sin guiones"""
    if not sku:
        return ''
    return sku.strip().upper().replace(' ', '').replace('-', '')


def main():
    print("=" * 70)
    print("CALCULO DE PRODUCTOS INTERCAMBIABLES")
    print("=" * 70)

    conn = get_db()
    cursor = conn.cursor()

    # Crear tabla si no existe
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

    # Limpiar tabla existente
    cursor.execute("DELETE FROM productos_intercambiables")
    conn.commit()
    print("\nTabla limpiada.")

    # Paso 1: Leer todos los productos con skus_alternos
    cursor.execute("""
        SELECT id, sku, skus_alternos
        FROM productos
        WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
    """)
    productos = cursor.fetchall()
    print(f"Productos con skus_alternos: {len(productos)}")

    # Paso 2: Construir indices
    # sku_principal_norm -> producto_id
    sku_principal_a_id = {}
    # sku_alterno_norm -> set de producto_ids que lo tienen
    sku_alterno_a_ids = defaultdict(set)
    # producto_id -> set de skus_alternos normalizados
    producto_alternos = {}
    # producto_id -> sku principal original
    producto_sku = {}

    # Primero indexar TODOS los SKUs principales (incluidos los sin alternos)
    cursor.execute("SELECT id, sku FROM productos")
    for row in cursor.fetchall():
        norm = normalizar_sku(row['sku'])
        if norm:
            sku_principal_a_id[norm] = row['id']
            producto_sku[row['id']] = row['sku']

    # Ahora indexar los alternos
    for prod in productos:
        prod_id = prod['id']
        try:
            alternos = json.loads(prod['skus_alternos'])
            if not isinstance(alternos, list):
                continue
        except (json.JSONDecodeError, TypeError):
            continue

        alternos_norm = set()
        for alt in alternos:
            if alt and isinstance(alt, str):
                norm = normalizar_sku(alt)
                if norm and len(norm) >= 3:  # Ignorar SKUs muy cortos
                    alternos_norm.add(norm)
                    sku_alterno_a_ids[norm].add(prod_id)

        if alternos_norm:
            producto_alternos[prod_id] = alternos_norm

    print(f"SKUs principales indexados: {len(sku_principal_a_id)}")
    print(f"SKUs alternos unicos: {len(sku_alterno_a_ids)}")
    print(f"Productos con alternos validos: {len(producto_alternos)}")

    # Paso 3: Encontrar intercambiables
    # Usar set de pares para evitar duplicados
    pares = set()  # (min_id, max_id, sku_comun)

    for prod_id, alternos in producto_alternos.items():
        for alt_norm in alternos:
            # Caso 1: El SKU alterno es el SKU principal de otro producto
            if alt_norm in sku_principal_a_id:
                otro_id = sku_principal_a_id[alt_norm]
                if otro_id != prod_id:
                    par = (min(prod_id, otro_id), max(prod_id, otro_id), alt_norm)
                    pares.add(par)

            # Caso 2: El SKU alterno tambien aparece en alternos de otro producto
            if alt_norm in sku_alterno_a_ids:
                for otro_id in sku_alterno_a_ids[alt_norm]:
                    if otro_id != prod_id:
                        par = (min(prod_id, otro_id), max(prod_id, otro_id), alt_norm)
                        pares.add(par)

    print(f"\nPares unicos encontrados: {len(pares)}")

    # Paso 4: Insertar relaciones bidireccionales
    inserts = 0
    batch = []
    for id_a, id_b, sku_comun in pares:
        # Insertar A -> B y B -> A
        batch.append((id_a, id_b, sku_comun))
        batch.append((id_b, id_a, sku_comun))

        if len(batch) >= 1000:
            cursor.executemany("""
                INSERT OR IGNORE INTO productos_intercambiables
                (producto_id, producto_intercambiable_id, sku_comun)
                VALUES (?, ?, ?)
            """, batch)
            inserts += len(batch)
            batch = []

    if batch:
        cursor.executemany("""
            INSERT OR IGNORE INTO productos_intercambiables
            (producto_id, producto_intercambiable_id, sku_comun)
            VALUES (?, ?, ?)
        """, batch)
        inserts += len(batch)

    conn.commit()

    # Paso 5: Estadisticas
    cursor.execute("SELECT COUNT(*) as total FROM productos_intercambiables")
    total_relaciones = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(DISTINCT producto_id) as productos_con_intercambiables
        FROM productos_intercambiables
    """)
    productos_con = cursor.fetchone()['productos_con_intercambiables']

    cursor.execute("""
        SELECT producto_id, COUNT(*) as n
        FROM productos_intercambiables
        GROUP BY producto_id
        ORDER BY n DESC
        LIMIT 10
    """)
    top_productos = cursor.fetchall()

    # Crear indices
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_intercambiables_producto ON productos_intercambiables(producto_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_intercambiables_inverso ON productos_intercambiables(producto_intercambiable_id)")
    conn.commit()

    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")
    print(f"Total relaciones insertadas: {total_relaciones}")
    print(f"Productos con intercambiables: {productos_con}")
    print(f"Promedio intercambiables por producto: {total_relaciones / productos_con:.1f}" if productos_con else "N/A")

    print(f"\nTOP 10 PRODUCTOS CON MAS INTERCAMBIABLES:")
    for row in top_productos:
        prod_sku = producto_sku.get(row['producto_id'], '?')
        cursor.execute("SELECT marca, nombre_producto FROM productos WHERE id = ?", (row['producto_id'],))
        prod_info = cursor.fetchone()
        marca = prod_info['marca'] if prod_info else '?'
        nombre = (prod_info['nombre_producto'] or '')[:50] if prod_info else '?'
        print(f"  [{marca}] {prod_sku}: {row['n']} intercambiables - {nombre}")

    # Ejemplo: mostrar intercambiables del producto ACDELCO bujia
    cursor.execute("""
        SELECT p.sku, p.marca, p.nombre_producto
        FROM productos p WHERE p.sku LIKE '%254224105241%'
    """)
    ejemplo = cursor.fetchone()
    if ejemplo:
        print(f"\nEJEMPLO: {ejemplo['sku']} ({ejemplo['marca']}) - {ejemplo['nombre_producto']}")
        cursor.execute("""
            SELECT p.sku, p.marca, p.nombre_producto, pi.sku_comun
            FROM productos_intercambiables pi
            INNER JOIN productos p ON p.id = pi.producto_intercambiable_id
            WHERE pi.producto_id = (SELECT id FROM productos WHERE sku = ?)
            ORDER BY p.marca
        """, (ejemplo['sku'],))
        for row in cursor.fetchall():
            print(f"  -> [{row['marca']}] {row['sku']}: {row['nombre_producto']}")

    conn.close()
    print(f"\n{'='*70}")
    print("CALCULO COMPLETADO")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
