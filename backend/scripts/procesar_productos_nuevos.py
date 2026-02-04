"""
Script para procesar productos nuevos (recién importados).

Extrae nombres limpios, compatibilidades vehiculares, tipos de producto,
SKUs alternos e intercambiables para productos con created_at reciente.

Uso:
    python3 scripts/procesar_productos_nuevos.py [--days N]

Por defecto procesa productos de los últimos 60 días.
"""
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from parsers import get_parser


def procesar_productos_nuevos(days: int = 60, verbose: bool = True):
    """
    Procesa productos nuevos: extrae nombres, compatibilidades, intercambiables.

    Args:
        days: Procesar productos de los últimos N días
        verbose: Mostrar progreso detallado

    Returns:
        dict con estadísticas del procesamiento
    """
    stats = {
        'total': 0,
        'nombres_actualizados': 0,
        'compatibilidades_nuevas': 0,
        'productos_con_compat': 0,
        'intercambiables_nuevos': 0,
        'errores': []
    }

    if verbose:
        print(f"\n{'='*60}")
        print("PROCESAMIENTO DE PRODUCTOS NUEVOS")
        print(f"{'='*60}")
        print(f"Procesando productos de los últimos {days} días...")

    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener productos nuevos
        cursor.execute(f"""
            SELECT id, sku, marca, departamento, descripcion_original, nombre_producto
            FROM productos
            WHERE created_at >= datetime('now', '-{days} days')
              AND descripcion_original IS NOT NULL
              AND descripcion_original != ''
        """)

        productos = cursor.fetchall()
        stats['total'] = len(productos)

        if stats['total'] == 0:
            if verbose:
                print("No hay productos nuevos para procesar.")
            return stats

        if verbose:
            print(f"Encontrados: {stats['total']} productos nuevos\n")

        for idx, producto in enumerate(productos, 1):
            try:
                producto_id = producto['id']
                sku = producto['sku']
                marca = producto['marca'] or ''
                departamento = producto['departamento'] or ''
                descripcion = producto['descripcion_original'] or ''
                nombre_actual = producto['nombre_producto'] or ''

                # Obtener parser apropiado para la marca
                parser = get_parser(marca)

                # Parsear descripción completa
                resultado = parser.parse(descripcion)

                # Limpiar nombre usando el método más robusto
                nombre_limpio = parser.limpiar_nombre_producto(
                    descripcion,
                    marca,
                    departamento
                )

                # Si no obtuvo un buen nombre, usar el del resultado del parse
                if not nombre_limpio or len(nombre_limpio) < 5:
                    nombre_limpio = resultado.nombre_producto

                # Solo actualizar si el nombre cambió o si no tenía nombre
                if nombre_limpio and nombre_limpio != nombre_actual:
                    cursor.execute("""
                        UPDATE productos
                        SET nombre_producto = ?,
                            tipo_producto = ?,
                            skus_alternos = ?
                        WHERE id = ?
                    """, (
                        nombre_limpio,
                        resultado.tipo_producto or None,
                        json.dumps(resultado.skus_alternos) if resultado.skus_alternos else None,
                        producto_id
                    ))
                    stats['nombres_actualizados'] += 1

                # Eliminar compatibilidades existentes para este producto
                cursor.execute("DELETE FROM compatibilidades WHERE producto_id = ?", (producto_id,))

                # Insertar nuevas compatibilidades
                if resultado.compatibilidades:
                    stats['productos_con_compat'] += 1
                    for compat in resultado.compatibilidades:
                        cursor.execute("""
                            INSERT INTO compatibilidades (
                                producto_id, marca_vehiculo, modelo_vehiculo,
                                año_inicio, año_fin, motor, cilindros, especificacion
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            producto_id,
                            compat.marca_vehiculo or None,
                            compat.modelo_vehiculo or None,
                            compat.año_inicio,
                            compat.año_fin,
                            compat.motor or None,
                            compat.cilindros or None,
                            compat.especificacion or None
                        ))
                        stats['compatibilidades_nuevas'] += 1

                # Mostrar progreso
                if verbose and idx % 50 == 0:
                    print(f"  Procesados: {idx}/{stats['total']}...")
                    conn.commit()

            except Exception as e:
                stats['errores'].append(f"SKU {sku}: {str(e)}")

        conn.commit()

    # Calcular intercambiables para productos nuevos
    if verbose:
        print("\nCalculando productos intercambiables...")
    stats['intercambiables_nuevos'] = calcular_intercambiables_nuevos(days)

    # Mostrar resumen
    if verbose:
        print(f"\n{'='*60}")
        print("RESUMEN DE PROCESAMIENTO")
        print(f"{'='*60}")
        print(f"Productos procesados:      {stats['total']}")
        print(f"Nombres actualizados:      {stats['nombres_actualizados']}")
        print(f"Productos con compat.:     {stats['productos_con_compat']}")
        print(f"Compatibilidades creadas:  {stats['compatibilidades_nuevas']}")
        print(f"Intercambiables nuevos:    {stats['intercambiables_nuevos']}")

        if stats['errores']:
            print(f"\nErrores ({len(stats['errores'])}):")
            for error in stats['errores'][:10]:
                print(f"  - {error}")
            if len(stats['errores']) > 10:
                print(f"  ... y {len(stats['errores']) - 10} más")

        print(f"{'='*60}\n")

    return stats


def calcular_intercambiables_nuevos(days: int = 60):
    """
    Calcula productos intercambiables solo para productos nuevos.

    Busca si los SKUs alternos de productos nuevos coinciden con
    SKUs principales o alternos de productos existentes.

    Returns:
        int: Número de relaciones de intercambiables creadas
    """
    from database import get_db

    relaciones_creadas = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener IDs de productos nuevos
        cursor.execute(f"""
            SELECT id FROM productos
            WHERE created_at >= datetime('now', '-{days} days')
        """)
        nuevos_ids = set(row['id'] for row in cursor.fetchall())

        if not nuevos_ids:
            return 0

        # Construir índice de todos los SKUs principales
        cursor.execute("SELECT id, sku FROM productos")
        sku_principal_a_id = {}
        for row in cursor.fetchall():
            norm = normalizar_sku(row['sku'])
            if norm:
                sku_principal_a_id[norm] = row['id']

        # Construir índice de SKUs alternos -> producto_ids
        cursor.execute("""
            SELECT id, skus_alternos FROM productos
            WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
        """)
        sku_alterno_a_ids = defaultdict(set)
        for row in cursor.fetchall():
            try:
                alternos = json.loads(row['skus_alternos'])
                if isinstance(alternos, list):
                    for alt in alternos:
                        if alt and isinstance(alt, str):
                            norm = normalizar_sku(alt)
                            if norm:
                                sku_alterno_a_ids[norm].add(row['id'])
            except (json.JSONDecodeError, TypeError):
                pass

        # Para cada producto nuevo con SKUs alternos, buscar coincidencias
        cursor.execute(f"""
            SELECT id, sku, skus_alternos FROM productos
            WHERE created_at >= datetime('now', '-{days} days')
              AND skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
        """)

        for prod in cursor.fetchall():
            prod_id = prod['id']
            try:
                alternos = json.loads(prod['skus_alternos'])
                if not isinstance(alternos, list):
                    continue
            except (json.JSONDecodeError, TypeError):
                continue

            for alt in alternos:
                if not alt or not isinstance(alt, str):
                    continue

                norm = normalizar_sku(alt)
                if not norm:
                    continue

                # Buscar coincidencia con SKU principal de otro producto
                if norm in sku_principal_a_id:
                    otro_id = sku_principal_a_id[norm]
                    if otro_id != prod_id:
                        # Crear relación bidireccional
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO productos_intercambiables
                                (producto_id, producto_intercambiable_id, sku_comun)
                                VALUES (?, ?, ?)
                            """, (prod_id, otro_id, alt))
                            cursor.execute("""
                                INSERT OR IGNORE INTO productos_intercambiables
                                (producto_id, producto_intercambiable_id, sku_comun)
                                VALUES (?, ?, ?)
                            """, (otro_id, prod_id, alt))
                            relaciones_creadas += 2
                        except:
                            pass

                # Buscar coincidencia con SKU alterno de otro producto
                if norm in sku_alterno_a_ids:
                    for otro_id in sku_alterno_a_ids[norm]:
                        if otro_id != prod_id:
                            try:
                                cursor.execute("""
                                    INSERT OR IGNORE INTO productos_intercambiables
                                    (producto_id, producto_intercambiable_id, sku_comun)
                                    VALUES (?, ?, ?)
                                """, (prod_id, otro_id, alt))
                                cursor.execute("""
                                    INSERT OR IGNORE INTO productos_intercambiables
                                    (producto_id, producto_intercambiable_id, sku_comun)
                                    VALUES (?, ?, ?)
                                """, (otro_id, prod_id, alt))
                                relaciones_creadas += 2
                            except:
                                pass

        conn.commit()

    return relaciones_creadas


def normalizar_sku(sku):
    """Normaliza un SKU para comparación: uppercase, sin espacios, sin guiones"""
    if not sku:
        return ''
    return sku.strip().upper().replace(' ', '').replace('-', '')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Procesa productos nuevos: extrae nombres, compatibilidades, intercambiables.'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=60,
        help='Procesar productos de los últimos N días (default: 60)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modo silencioso (sin output)'
    )

    args = parser.parse_args()
    procesar_productos_nuevos(days=args.days, verbose=not args.quiet)
