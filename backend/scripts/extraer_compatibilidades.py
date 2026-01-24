"""
Script para extraer compatibilidades de las descripciones de productos
y poblar la tabla de compatibilidades
"""
import sys
import json
from pathlib import Path
from collections import defaultdict

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from parsers import get_parser


def extraer_compatibilidades():
    """Extrae compatibilidades de todos los productos"""
    print("Iniciando extracción de compatibilidades...")

    estadisticas = defaultdict(int)
    productos_con_compat = 0
    total_compatibilidades = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Limpiar compatibilidades existentes
        print("Limpiando compatibilidades existentes...")
        cursor.execute("DELETE FROM compatibilidades")

        # Obtener todos los productos
        cursor.execute("""
            SELECT id, sku, marca, descripcion_original
            FROM productos
            WHERE descripcion_original IS NOT NULL AND descripcion_original != ''
        """)

        productos = cursor.fetchall()
        total_productos = len(productos)
        print(f"Procesando {total_productos} productos...")

        for idx, producto in enumerate(productos, 1):
            producto_id = producto['id']
            marca = producto['marca'] or ''
            descripcion = producto['descripcion_original'] or ''

            # Obtener parser apropiado
            parser = get_parser(marca)

            # Parsear descripción
            resultado = parser.parse(descripcion)

            # Actualizar nombre y tipo del producto
            if resultado.nombre_producto or resultado.tipo_producto or resultado.skus_alternos:
                cursor.execute("""
                    UPDATE productos
                    SET nombre_producto = ?,
                        tipo_producto = ?,
                        skus_alternos = ?
                    WHERE id = ?
                """, (
                    resultado.nombre_producto or None,
                    resultado.tipo_producto or None,
                    json.dumps(resultado.skus_alternos) if resultado.skus_alternos else None,
                    producto_id
                ))

            # Insertar compatibilidades
            if resultado.compatibilidades:
                productos_con_compat += 1
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
                    total_compatibilidades += 1
                    estadisticas[f"marca_{marca}"] += 1

            if idx % 5000 == 0:
                print(f"  Procesados: {idx}/{total_productos} productos...")
                conn.commit()

        conn.commit()

    # Mostrar estadísticas
    print(f"\n{'='*60}")
    print("EXTRACCIÓN COMPLETADA")
    print(f"{'='*60}")
    print(f"Total productos procesados: {total_productos}")
    print(f"Productos con compatibilidades: {productos_con_compat} ({100*productos_con_compat/total_productos:.1f}%)")
    print(f"Total compatibilidades extraídas: {total_compatibilidades}")

    # Estadísticas adicionales
    with get_db() as conn:
        cursor = conn.cursor()

        print(f"\n{'='*60}")
        print("ESTADÍSTICAS DE COMPATIBILIDADES")
        print(f"{'='*60}")

        # Marcas de vehículos encontradas
        cursor.execute("""
            SELECT marca_vehiculo, COUNT(*) as cnt
            FROM compatibilidades
            WHERE marca_vehiculo IS NOT NULL
            GROUP BY marca_vehiculo
            ORDER BY cnt DESC
            LIMIT 15
        """)
        print("\nTop 15 marcas de vehículos:")
        for row in cursor.fetchall():
            print(f"  - {row['marca_vehiculo']}: {row['cnt']}")

        # Modelos de vehículos más comunes
        cursor.execute("""
            SELECT modelo_vehiculo, marca_vehiculo, COUNT(*) as cnt
            FROM compatibilidades
            WHERE modelo_vehiculo IS NOT NULL
            GROUP BY modelo_vehiculo, marca_vehiculo
            ORDER BY cnt DESC
            LIMIT 15
        """)
        print("\nTop 15 modelos de vehículos:")
        for row in cursor.fetchall():
            print(f"  - {row['modelo_vehiculo']} ({row['marca_vehiculo']}): {row['cnt']}")

        # Rango de años
        cursor.execute("""
            SELECT MIN(año_inicio) as min_año, MAX(año_fin) as max_año
            FROM compatibilidades
            WHERE año_inicio IS NOT NULL AND año_fin IS NOT NULL
        """)
        row = cursor.fetchone()
        print(f"\nRango de años: {row['min_año']} - {row['max_año']}")

        # Productos por marca con compatibilidades
        cursor.execute("""
            SELECT p.marca, COUNT(DISTINCT p.id) as productos_con_compat,
                   COUNT(c.id) as total_compat
            FROM productos p
            INNER JOIN compatibilidades c ON c.producto_id = p.id
            GROUP BY p.marca
            ORDER BY total_compat DESC
            LIMIT 15
        """)
        print("\nTop 15 marcas de producto por compatibilidades extraídas:")
        for row in cursor.fetchall():
            print(f"  - {row['marca']}: {row['productos_con_compat']} productos, {row['total_compat']} compatibilidades")


if __name__ == "__main__":
    extraer_compatibilidades()
