"""
Script para reprocesar skus_alternos de TODOS los productos.
Re-extrae usando la lógica mejorada de PATRON_SKUS + PATRON_SKUS_ESPACIO.

Ejecutar desde /backend:
    python3 scripts/reprocesar_skus_alternos.py
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

import sqlite3
from parsers import get_parser


def get_db():
    db_path = Path(__file__).parent.parent.parent / "data" / "catalogo.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def main():
    print("=" * 70)
    print("REPROCESAMIENTO DE SKUS ALTERNOS")
    print("=" * 70)

    conn = get_db()
    cursor = conn.cursor()

    # Estadisticas antes
    cursor.execute("""
        SELECT COUNT(*) as total FROM productos
        WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
    """)
    antes_con_alternos = cursor.fetchone()['total']
    print(f"\n[ANTES] Productos con skus_alternos: {antes_con_alternos}")

    # Estadisticas antes por marca
    cursor.execute("""
        SELECT marca, COUNT(*) as n FROM productos
        WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
        GROUP BY marca ORDER BY n DESC LIMIT 15
    """)
    print("\n  Top marcas con alternos (antes):")
    for row in cursor.fetchall():
        print(f"    {row['marca']}: {row['n']}")

    # Obtener todos los productos
    cursor.execute("""
        SELECT id, sku, marca, descripcion_original, skus_alternos
        FROM productos
        WHERE descripcion_original IS NOT NULL AND descripcion_original != ''
    """)
    productos = cursor.fetchall()
    total = len(productos)
    print(f"\nProcesando {total} productos...")

    changed = 0
    gained = 0  # No tenia alternos, ahora si
    lost = 0    # Tenia alternos, ahora no (no deberia pasar)
    unchanged = 0
    errors = 0
    cambios_por_marca = defaultdict(int)
    ganados_por_marca = defaultdict(int)
    examples_gained = []

    for idx, prod in enumerate(productos, 1):
        try:
            marca = prod['marca'] or ''
            descripcion = prod['descripcion_original'] or ''

            # Obtener alternos actuales
            old_alternos_str = prod['skus_alternos'] or '[]'
            try:
                old_alternos = json.loads(old_alternos_str)
                if not isinstance(old_alternos, list):
                    old_alternos = []
            except (json.JSONDecodeError, TypeError):
                old_alternos = []

            # Re-extraer con parser mejorado
            parser = get_parser(marca)
            new_alternos = parser.extraer_skus_alternos(descripcion)

            # Comparar
            if sorted(new_alternos) != sorted(old_alternos):
                new_json = json.dumps(new_alternos) if new_alternos else None
                cursor.execute(
                    "UPDATE productos SET skus_alternos = ? WHERE id = ?",
                    (new_json, prod['id'])
                )
                changed += 1
                cambios_por_marca[marca] += 1

                if not old_alternos and new_alternos:
                    gained += 1
                    ganados_por_marca[marca] += 1
                    if len(examples_gained) < 20:
                        examples_gained.append({
                            'sku': prod['sku'],
                            'marca': marca,
                            'desc': descripcion[:80],
                            'alternos': new_alternos,
                        })
                elif old_alternos and not new_alternos:
                    lost += 1
            else:
                unchanged += 1

        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error en {prod['sku']}: {e}")

        if idx % 5000 == 0:
            print(f"  ... procesados {idx}/{total}")
            conn.commit()

    conn.commit()

    # Estadisticas despues
    cursor.execute("""
        SELECT COUNT(*) as total FROM productos
        WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
    """)
    despues_con_alternos = cursor.fetchone()['total']

    print(f"\n{'='*70}")
    print("RESUMEN")
    print(f"{'='*70}")
    print(f"Total procesados: {total}")
    print(f"Cambiados: {changed}")
    print(f"  - Ganaron alternos (no tenian): {gained}")
    print(f"  - Perdieron alternos: {lost}")
    print(f"Sin cambio: {unchanged}")
    print(f"Errores: {errors}")
    print(f"\n[ANTES] Con alternos: {antes_con_alternos}")
    print(f"[DESPUES] Con alternos: {despues_con_alternos}")
    print(f"DIFERENCIA: +{despues_con_alternos - antes_con_alternos}")

    if ganados_por_marca:
        print(f"\nGANARON ALTERNOS POR MARCA (top 20):")
        for marca, n in sorted(ganados_por_marca.items(), key=lambda x: -x[1])[:20]:
            print(f"  {marca}: +{n}")

    if examples_gained:
        print(f"\nEJEMPLOS DE PRODUCTOS QUE GANARON ALTERNOS:")
        for ex in examples_gained:
            print(f"  [{ex['marca']}] {ex['sku']}")
            print(f"    Desc: {ex['desc']}")
            print(f"    Alternos: {ex['alternos']}")
            print()

    conn.close()
    print("Reprocesamiento completado.")


if __name__ == "__main__":
    main()
