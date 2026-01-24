#!/usr/bin/env python3
"""
Script para extraer características de productos sin compatibilidad vehicular.

Procesa:
- Llantas (departamento = 'LLANTAS')
- Aceites/Lubricantes (departamento = 'LUBRICACIÓN' o 'QUIMICOS/ADITIVOS')
- Acumuladores (marca in ['CHECKER', 'EXTREMA', 'CAMEL'])

Ejecutar desde /backend:
    python scripts/extraer_caracteristicas.py
"""
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from parsers.extractores_caracteristicas import (
    ExtractorLlantas,
    ExtractorAceites,
    ExtractorAcumuladores,
)


def limpiar_caracteristicas_existentes():
    """Limpia las características existentes antes de re-extraer"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM caracteristicas_producto")
        print("Características existentes eliminadas")


def extraer_llantas():
    """Extrae características de productos del departamento LLANTAS"""
    extractor = ExtractorLlantas()
    caracteristicas_insertadas = 0
    productos_procesados = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener todos los productos de llantas
        cursor.execute("""
            SELECT id, descripcion_original
            FROM productos
            WHERE departamento = 'LLANTAS'
        """)
        productos = cursor.fetchall()

        print(f"\n=== LLANTAS: {len(productos)} productos ===")

        for producto in productos:
            producto_id = producto['id']
            descripcion = producto['descripcion_original'] or ''

            caracteristicas = extractor.extraer(descripcion)

            for carac in caracteristicas:
                cursor.execute("""
                    INSERT INTO caracteristicas_producto
                    (producto_id, categoria, clave, valor)
                    VALUES (?, 'llanta', ?, ?)
                """, (producto_id, carac.clave, carac.valor))
                caracteristicas_insertadas += 1

            if caracteristicas:
                productos_procesados += 1

        print(f"  Productos con características: {productos_procesados}")
        print(f"  Características insertadas: {caracteristicas_insertadas}")

    return productos_procesados, caracteristicas_insertadas


def extraer_aceites():
    """Extrae características de productos de lubricación y químicos"""
    extractor = ExtractorAceites()
    caracteristicas_insertadas = 0
    productos_procesados = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener productos de lubricación y químicos
        cursor.execute("""
            SELECT id, descripcion_original
            FROM productos
            WHERE departamento IN ('LUBRICACIÓN', 'QUIMICOS/ADITIVOS')
        """)
        productos = cursor.fetchall()

        print(f"\n=== ACEITES/LUBRICANTES: {len(productos)} productos ===")

        for producto in productos:
            producto_id = producto['id']
            descripcion = producto['descripcion_original'] or ''

            caracteristicas = extractor.extraer(descripcion)

            for carac in caracteristicas:
                cursor.execute("""
                    INSERT INTO caracteristicas_producto
                    (producto_id, categoria, clave, valor)
                    VALUES (?, 'aceite', ?, ?)
                """, (producto_id, carac.clave, carac.valor))
                caracteristicas_insertadas += 1

            if caracteristicas:
                productos_procesados += 1

        print(f"  Productos con características: {productos_procesados}")
        print(f"  Características insertadas: {caracteristicas_insertadas}")

    return productos_procesados, caracteristicas_insertadas


def extraer_acumuladores():
    """Extrae características de acumuladores"""
    extractor = ExtractorAcumuladores()
    caracteristicas_insertadas = 0
    productos_procesados = 0

    with get_db() as conn:
        cursor = conn.cursor()

        # Obtener productos de acumuladores (por marca)
        cursor.execute("""
            SELECT id, descripcion_original
            FROM productos
            WHERE marca IN ('CHECKER', 'EXTREMA', 'CAMEL')
        """)
        productos = cursor.fetchall()

        print(f"\n=== ACUMULADORES: {len(productos)} productos ===")

        for producto in productos:
            producto_id = producto['id']
            descripcion = producto['descripcion_original'] or ''

            caracteristicas = extractor.extraer(descripcion)

            for carac in caracteristicas:
                cursor.execute("""
                    INSERT INTO caracteristicas_producto
                    (producto_id, categoria, clave, valor)
                    VALUES (?, 'acumulador', ?, ?)
                """, (producto_id, carac.clave, carac.valor))
                caracteristicas_insertadas += 1

            if caracteristicas:
                productos_procesados += 1

        print(f"  Productos con características: {productos_procesados}")
        print(f"  Características insertadas: {caracteristicas_insertadas}")

    return productos_procesados, caracteristicas_insertadas


def mostrar_estadisticas():
    """Muestra estadísticas de las características extraídas"""
    with get_db() as conn:
        cursor = conn.cursor()

        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DE CARACTERÍSTICAS EXTRAÍDAS")
        print("=" * 60)

        # Por categoría
        cursor.execute("""
            SELECT categoria, COUNT(DISTINCT producto_id) as productos, COUNT(*) as caracteristicas
            FROM caracteristicas_producto
            GROUP BY categoria
        """)
        print("\nPor categoría:")
        for row in cursor.fetchall():
            print(f"  {row['categoria']}: {row['productos']} productos, {row['caracteristicas']} características")

        # Detalles por clave para llantas
        print("\nLLANTAS - Valores únicos por atributo:")
        cursor.execute("""
            SELECT clave, COUNT(DISTINCT valor) as valores_unicos
            FROM caracteristicas_producto
            WHERE categoria = 'llanta'
            GROUP BY clave
            ORDER BY clave
        """)
        for row in cursor.fetchall():
            print(f"  {row['clave']}: {row['valores_unicos']} valores")

        # Detalles por clave para aceites
        print("\nACEITES - Valores únicos por atributo:")
        cursor.execute("""
            SELECT clave, COUNT(DISTINCT valor) as valores_unicos
            FROM caracteristicas_producto
            WHERE categoria = 'aceite'
            GROUP BY clave
            ORDER BY clave
        """)
        for row in cursor.fetchall():
            print(f"  {row['clave']}: {row['valores_unicos']} valores")

        # Detalles por clave para acumuladores
        print("\nACUMULADORES - Valores únicos por atributo:")
        cursor.execute("""
            SELECT clave, COUNT(DISTINCT valor) as valores_unicos
            FROM caracteristicas_producto
            WHERE categoria = 'acumulador'
            GROUP BY clave
            ORDER BY clave
        """)
        for row in cursor.fetchall():
            print(f"  {row['clave']}: {row['valores_unicos']} valores")

        # Mostrar algunos valores de ejemplo
        print("\n" + "-" * 40)
        print("VALORES DE EJEMPLO:")

        print("\nAnchos de llanta:")
        cursor.execute("""
            SELECT DISTINCT valor FROM caracteristicas_producto
            WHERE categoria = 'llanta' AND clave = 'ancho'
            ORDER BY CAST(valor AS INTEGER)
            LIMIT 15
        """)
        valores = [row['valor'] for row in cursor.fetchall()]
        print(f"  {', '.join(valores)}")

        print("\nDiámetros de llanta:")
        cursor.execute("""
            SELECT DISTINCT valor FROM caracteristicas_producto
            WHERE categoria = 'llanta' AND clave = 'diametro'
            ORDER BY valor
        """)
        valores = [row['valor'] for row in cursor.fetchall()]
        print(f"  {', '.join(valores)}")

        print("\nViscosidades de aceite:")
        cursor.execute("""
            SELECT DISTINCT valor FROM caracteristicas_producto
            WHERE categoria = 'aceite' AND clave = 'viscosidad'
            ORDER BY valor
        """)
        valores = [row['valor'] for row in cursor.fetchall()]
        print(f"  {', '.join(valores)}")

        print("\nGrupos BCI de acumuladores:")
        cursor.execute("""
            SELECT DISTINCT valor FROM caracteristicas_producto
            WHERE categoria = 'acumulador' AND clave = 'grupo_bci'
            ORDER BY valor
        """)
        valores = [row['valor'] for row in cursor.fetchall()]
        print(f"  {', '.join(valores)}")


def main():
    """Función principal"""
    print("=" * 60)
    print("EXTRACCIÓN DE CARACTERÍSTICAS DE PRODUCTOS")
    print("=" * 60)

    # Limpiar características existentes
    limpiar_caracteristicas_existentes()

    # Extraer por categoría
    total_productos = 0
    total_caracteristicas = 0

    prods, caracs = extraer_llantas()
    total_productos += prods
    total_caracteristicas += caracs

    prods, caracs = extraer_aceites()
    total_productos += prods
    total_caracteristicas += caracs

    prods, caracs = extraer_acumuladores()
    total_productos += prods
    total_caracteristicas += caracs

    print("\n" + "=" * 60)
    print(f"TOTAL: {total_productos} productos, {total_caracteristicas} características")
    print("=" * 60)

    # Mostrar estadísticas detalladas
    mostrar_estadisticas()


if __name__ == "__main__":
    main()
