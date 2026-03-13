"""
Script de actualización de precios e inventario desde Excel (con IVA).

Uso:
    python3 scripts/actualizar_precios_excel.py

Lee data/limpieza-catalogo.xlsx, hoja "TODOS LOS PRODUCTOS ACTUALIZADO".
Actualiza:
- precio_publico y precio_mayoreo con precios CON IVA
- inventario_total y tabla inventario por sucursal
- Inserta productos NUEVOS si: inventario > 0 AND última compra < 5 años
Para productos nuevos, ejecuta procesamiento automático (nombres, compatibilidades, etc.)
"""

import sys
import sqlite3
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import openpyxl

# Rutas
DB_PATH = Path(__file__).parent.parent / "data" / "catalogo.db"
EXCEL_PATH = Path(__file__).parent.parent.parent / "data" / "limpieza-catalogo.xlsx"
SHEET_NAME = "TODOS LOS PRODUCTOS MARZO"

# Columnas del Excel
COL_SKU = 0               # Clave
COL_GRUPO = 1             # Grupo -> Nombre
COL_DEPARTAMENTO = 4      # Departamento -> Nombre
COL_MARCA = 5             # Marcas Prodcuto -> Nombre
COL_ULTIMA_COMPRA = 7     # Última Compra
COL_DESCRIPCION = 9       # Descripcion
COL_PRECIO_PUBLICO = 12   # Precio abierto 3 C/IVA (público)
COL_PRECIO_MAYOREO = 13   # Precio abierto 5 C/IVA (mayoreo)
COL_IMAGEN_URL = 14       # Variant Scr
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

# Condiciones para productos nuevos
AÑOS_LIMITE_COMPRA = 5  # Última compra debe ser < 5 años
MARCAS_ACUMULADORES = ['CHECKER', 'EXTREMA', 'CAMEL']


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


def limpiar_texto(valor) -> str:
    """Convierte valor de celda a string limpio."""
    if valor is None:
        return ''
    return str(valor).strip()


def parsear_fecha(valor) -> Optional[date]:
    """Parsea una fecha del Excel. Puede ser datetime o string."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    # Intentar parsear como string
    texto = str(valor).strip()
    if not texto:
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'):
        try:
            return datetime.strptime(texto, fmt).date()
        except ValueError:
            continue
    return None


def procesar_nuevos_inline(cursor, ids_nuevos: list):
    """
    Procesa productos nuevos directamente sobre el mismo cursor/conexión.
    Extrae nombres, compatibilidades, SKUs alternos y características.
    """
    import json
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from parsers import get_parser
    from parsers.extractores_caracteristicas import (
        ExtractorLlantas,
        ExtractorAceites,
        ExtractorAcumuladores,
    )

    stats = {
        'nombres_actualizados': 0,
        'productos_con_compat': 0,
        'compatibilidades_nuevas': 0,
        'caracteristicas_extraidas': 0,
        'errores': [],
    }

    if not ids_nuevos:
        return stats

    extractor_llantas = ExtractorLlantas()
    extractor_aceites = ExtractorAceites()
    extractor_acumuladores = ExtractorAcumuladores()

    placeholders = ','.join('?' * len(ids_nuevos))
    cursor.execute(f"""
        SELECT id, sku, marca, departamento, descripcion_original
        FROM productos WHERE id IN ({placeholders})
    """, ids_nuevos)
    productos = cursor.fetchall()

    for idx, (producto_id, sku, marca, departamento, descripcion) in enumerate(productos, 1):
        marca = marca or ''
        departamento = departamento or ''
        descripcion = descripcion or ''

        if not descripcion:
            continue

        try:
            # === Nombres, compatibilidades, SKUs alternos ===
            parser = get_parser(marca)
            resultado = parser.parse(descripcion)
            nombre_limpio = parser.limpiar_nombre_producto(descripcion, marca, departamento)

            if not nombre_limpio or len(nombre_limpio) < 5:
                nombre_limpio = resultado.nombre_producto

            if nombre_limpio:
                cursor.execute("""
                    UPDATE productos
                    SET nombre_producto = ?, tipo_producto = ?, skus_alternos = ?
                    WHERE id = ?
                """, (
                    nombre_limpio,
                    resultado.tipo_producto or None,
                    json.dumps(resultado.skus_alternos) if resultado.skus_alternos else None,
                    producto_id
                ))
                stats['nombres_actualizados'] += 1

            # Compatibilidades
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

            # === Características específicas (llantas, aceites, acumuladores) ===
            caracteristicas = []
            categoria = None

            if departamento == 'LLANTAS':
                caracteristicas = extractor_llantas.extraer(descripcion)
                categoria = 'llanta'
            elif departamento in ('LUBRICACIÓN', 'QUIMICOS/ADITIVOS'):
                caracteristicas = extractor_aceites.extraer(descripcion)
                categoria = 'aceite'
            elif marca in MARCAS_ACUMULADORES:
                caracteristicas = extractor_acumuladores.extraer(descripcion)
                categoria = 'acumulador'

            for carac in caracteristicas:
                cursor.execute("""
                    INSERT INTO caracteristicas_producto
                    (producto_id, categoria, clave, valor)
                    VALUES (?, ?, ?, ?)
                """, (producto_id, categoria, carac.clave, carac.valor))
                stats['caracteristicas_extraidas'] += 1

        except Exception as e:
            stats['errores'].append(f"SKU {sku}: {str(e)}")

        if idx % 50 == 0:
            print(f"  Procesados: {idx}/{len(productos)}...")

    # === Intercambiables ===
    print("\n  Calculando intercambiables...")
    stats['intercambiables_nuevos'] = _calcular_intercambiables(cursor, ids_nuevos)

    return stats


def _calcular_intercambiables(cursor, ids_nuevos: list):
    """Calcula intercambiables para productos nuevos usando el mismo cursor."""
    import json
    from collections import defaultdict

    relaciones = 0

    # Índice de SKUs principales
    cursor.execute("SELECT id, sku FROM productos")
    sku_principal = {}
    for row in cursor.fetchall():
        norm = row[1].strip().upper().replace(' ', '').replace('-', '')
        if norm:
            sku_principal[norm] = row[0]

    # Índice de SKUs alternos
    cursor.execute("""
        SELECT id, skus_alternos FROM productos
        WHERE skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
    """)
    sku_alterno = defaultdict(set)
    for row in cursor.fetchall():
        try:
            alternos = json.loads(row[1])
            if isinstance(alternos, list):
                for alt in alternos:
                    if alt and isinstance(alt, str):
                        norm = alt.strip().upper().replace(' ', '').replace('-', '')
                        if norm:
                            sku_alterno[norm].add(row[0])
        except (json.JSONDecodeError, TypeError):
            pass

    # Para cada producto nuevo con alternos, buscar coincidencias
    placeholders = ','.join('?' * len(ids_nuevos))
    cursor.execute(f"""
        SELECT id, skus_alternos FROM productos
        WHERE id IN ({placeholders})
          AND skus_alternos IS NOT NULL AND skus_alternos != '' AND skus_alternos != '[]'
    """, ids_nuevos)

    for row in cursor.fetchall():
        prod_id = row[0]
        try:
            alternos = json.loads(row[1])
            if not isinstance(alternos, list):
                continue
        except (json.JSONDecodeError, TypeError):
            continue

        for alt in alternos:
            if not alt or not isinstance(alt, str):
                continue
            norm = alt.strip().upper().replace(' ', '').replace('-', '')
            if not norm:
                continue

            # Coincidencia con SKU principal
            if norm in sku_principal:
                otro_id = sku_principal[norm]
                if otro_id != prod_id:
                    try:
                        cursor.execute("INSERT OR IGNORE INTO productos_intercambiables (producto_id, producto_intercambiable_id, sku_comun) VALUES (?, ?, ?)", (prod_id, otro_id, alt))
                        cursor.execute("INSERT OR IGNORE INTO productos_intercambiables (producto_id, producto_intercambiable_id, sku_comun) VALUES (?, ?, ?)", (otro_id, prod_id, alt))
                        relaciones += 2
                    except Exception:
                        pass

            # Coincidencia con SKU alterno
            if norm in sku_alterno:
                for otro_id in sku_alterno[norm]:
                    if otro_id != prod_id:
                        try:
                            cursor.execute("INSERT OR IGNORE INTO productos_intercambiables (producto_id, producto_intercambiable_id, sku_comun) VALUES (?, ?, ?)", (prod_id, otro_id, alt))
                            cursor.execute("INSERT OR IGNORE INTO productos_intercambiables (producto_id, producto_intercambiable_id, sku_comun) VALUES (?, ?, ?)", (otro_id, prod_id, alt))
                            relaciones += 2
                        except Exception:
                            pass

    return relaciones


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

    # Fecha límite para productos nuevos (5 años atrás)
    fecha_limite = date(date.today().year - AÑOS_LIMITE_COMPRA, date.today().month, date.today().day)
    print(f"Fecha límite última compra: {fecha_limite}")

    # Leer Excel
    print(f"\nLeyendo Excel: {excel_path}")
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb[SHEET_NAME]

    # Construir diccionario SKU -> datos
    datos_excel = {}
    datos_nuevos = {}  # Datos adicionales para productos nuevos
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[COL_SKU]:
            continue
        sku = normalizar_sku(row[COL_SKU])
        precio_pub = round(limpiar_numero(row[COL_PRECIO_PUBLICO]), 2)
        precio_may = round(limpiar_numero(row[COL_PRECIO_MAYOREO]), 2)
        # Inventario por sucursal (calculamos total sumando sucursales)
        inv_sucursales = {}
        inv_total = 0
        for col_idx, nombre_suc in SUCURSALES.items():
            cantidad = int(limpiar_numero(row[col_idx]))
            if cantidad > 0:
                inv_sucursales[nombre_suc] = cantidad
                inv_total += cantidad

        datos_excel[sku] = (precio_pub, precio_may, inv_total, inv_sucursales)

        # Guardar datos adicionales para posible INSERT de producto nuevo
        datos_nuevos[sku] = {
            'sku_original': str(row[COL_SKU]).strip(),
            'grupo_producto': limpiar_texto(row[COL_GRUPO]),
            'departamento': limpiar_texto(row[COL_DEPARTAMENTO]),
            'marca': limpiar_texto(row[COL_MARCA]),
            'ultima_compra': parsear_fecha(row[COL_ULTIMA_COMPRA]),
            'descripcion_original': limpiar_texto(row[COL_DESCRIPCION]),
            'imagen_url': limpiar_texto(row[COL_IMAGEN_URL]) if str(row[COL_IMAGEN_URL] or '').startswith('http') else '',
        }

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
    nuevos_insertados = 0
    nuevos_sin_inventario = 0
    nuevos_compra_vieja = 0
    ids_nuevos = []

    print(f"\nActualizando precios e inventario...\n")

    for sku_norm, (precio_pub, precio_may, inv_total, inv_sucursales) in datos_excel.items():
        if sku_norm not in sku_norm_to_db:
            # === PRODUCTO NUEVO: verificar condiciones ===
            datos = datos_nuevos[sku_norm]

            # Condición 1: inventario > 0
            if inv_total <= 0:
                nuevos_sin_inventario += 1
                no_encontrados += 1
                continue

            # Condición 2: última compra < 5 años
            ultima_compra = datos['ultima_compra']
            if ultima_compra is None or ultima_compra < fecha_limite:
                nuevos_compra_vieja += 1
                no_encontrados += 1
                continue

            # Insertar producto nuevo
            sku_insert = datos['sku_original']
            # Si el SKU original es numérico, usar normalizado para consistencia con BD
            if sku_insert.isdigit():
                sku_insert = sku_insert.lstrip('0') or '0'

            cursor.execute("""
                INSERT INTO productos (
                    sku, departamento, marca, descripcion_original,
                    precio_publico, precio_mayoreo, imagen_url,
                    inventario_total, grupo_producto, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sku_insert,
                datos['departamento'] or None,
                datos['marca'] or None,
                datos['descripcion_original'] or None,
                precio_pub,
                precio_may,
                datos['imagen_url'] or None,
                inv_total,
                datos['grupo_producto'] or None,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            ))

            producto_id = cursor.lastrowid
            ids_nuevos.append(producto_id)

            # Insertar inventario por sucursal
            for sucursal, cantidad in inv_sucursales.items():
                cursor.execute("""
                    INSERT INTO inventario (producto_id, sucursal, cantidad)
                    VALUES (?, ?, ?)
                """, (producto_id, sucursal, cantidad))
                inv_registros += 1

            nuevos_insertados += 1
            if precio_pub == 0.0:
                precio_cero += 1
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

    # === PROCESAMIENTO DE PRODUCTOS NUEVOS ===
    stats_nuevos = None
    if ids_nuevos:
        print(f"\n{'='*60}")
        print(f"PROCESANDO {len(ids_nuevos)} PRODUCTOS NUEVOS...")
        print(f"{'='*60}")

        stats_nuevos = procesar_nuevos_inline(cursor, ids_nuevos)
        conn.commit()

        print(f"\n  Nombres actualizados:      {stats_nuevos['nombres_actualizados']}")
        print(f"  Con compatibilidades:      {stats_nuevos['productos_con_compat']}")
        print(f"  Compatibilidades creadas:  {stats_nuevos['compatibilidades_nuevas']}")
        print(f"  Intercambiables nuevos:    {stats_nuevos['intercambiables_nuevos']}")
        print(f"  Características extraídas: {stats_nuevos['caracteristicas_extraidas']}")
        if stats_nuevos['errores']:
            print(f"  Errores: {len(stats_nuevos['errores'])}")
            for err in stats_nuevos['errores'][:5]:
                print(f"    - {err}")

    # Verificaciones finales
    cursor.execute("SELECT COUNT(*) FROM productos WHERE precio_publico = 0 OR precio_publico IS NULL")
    total_cero_final = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM inventario")
    inv_despues = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]

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
    print(f"  Productos NUEVOS insertados:  {nuevos_insertados:,}")
    print(f"  No encontrados en BD:         {no_encontrados:,}")
    if nuevos_sin_inventario > 0 or nuevos_compra_vieja > 0:
        print(f"{'─'*60}")
        print(f"  Nuevos descartados:")
        print(f"    Sin inventario:             {nuevos_sin_inventario:,}")
        print(f"    Compra > {AÑOS_LIMITE_COMPRA} años:             {nuevos_compra_vieja:,}")
    print(f"{'─'*60}")
    print(f"  Productos inv. → 0:           {inv_a_cero:,}")
    print(f"  Quedan con precio $0:         {total_cero_final:,}")
    print(f"  Total productos en BD:        {total_productos:,}")
    print(f"{'─'*60}")
    print(f"  Registros inventario antes:   {inv_antes:,}")
    print(f"  Registros inventario ahora:   {inv_despues:,}")

    if stats_nuevos:
        print(f"{'─'*60}")
        print(f"  PROCESAMIENTO PRODUCTOS NUEVOS:")
        print(f"    Nombres actualizados:       {stats_nuevos.get('nombres_actualizados', 0):,}")
        print(f"    Con compatibilidades:       {stats_nuevos.get('productos_con_compat', 0):,}")
        print(f"    Compatibilidades creadas:   {stats_nuevos.get('compatibilidades_nuevas', 0):,}")
        print(f"    Intercambiables nuevos:     {stats_nuevos.get('intercambiables_nuevos', 0):,}")
        print(f"    Características extraídas:  {stats_nuevos.get('caracteristicas_extraidas', 0):,}")

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
