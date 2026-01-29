"""
Módulo de Búsqueda Inteligente para Catálogo RELUVSA

Detecta automáticamente cuando una búsqueda contiene:
- Tipo de producto (aceite, filtro, balatas, etc.)
- Vehículo (modelo o marca)
- Año (opcional)

Y ejecuta una búsqueda combinada inteligente usando JOINs.

Ejemplos:
- "aceite aveo" → productos de aceite compatibles con Aveo
- "filtro cruze 2015" → filtros para Cruze año 2015
- "aveo" → todos los productos compatibles con Aveo
"""

import sqlite3
from typing import Optional, Set, Dict, Any

# Vocabulario de vehículos (se carga al iniciar la app)
MODELOS_VEHICULO: Set[str] = set()
MARCAS_VEHICULO: Set[str] = set()

# Flag para saber si ya se cargó el vocabulario
_vocabulario_cargado = False


def cargar_vocabulario_vehiculos(db_path: str) -> None:
    """
    Carga los modelos y marcas de vehículos desde la base de datos.
    Debe llamarse una vez al iniciar la aplicación.
    """
    global MODELOS_VEHICULO, MARCAS_VEHICULO, _vocabulario_cargado

    if _vocabulario_cargado:
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Cargar modelos de vehículo
        cursor.execute("""
            SELECT DISTINCT LOWER(modelo_vehiculo)
            FROM compatibilidades
            WHERE modelo_vehiculo IS NOT NULL
              AND modelo_vehiculo != ''
        """)
        MODELOS_VEHICULO = {row[0] for row in cursor.fetchall() if row[0]}

        # Cargar marcas de vehículo
        cursor.execute("""
            SELECT DISTINCT LOWER(marca_vehiculo)
            FROM compatibilidades
            WHERE marca_vehiculo IS NOT NULL
              AND marca_vehiculo != ''
        """)
        MARCAS_VEHICULO = {row[0] for row in cursor.fetchall() if row[0]}

        conn.close()
        _vocabulario_cargado = True

        print(f"[Búsqueda Inteligente] Vocabulario cargado: {len(MODELOS_VEHICULO)} modelos, {len(MARCAS_VEHICULO)} marcas")

    except Exception as e:
        print(f"[Búsqueda Inteligente] Error cargando vocabulario: {e}")


def analizar_busqueda(query: str) -> Dict[str, Any]:
    """
    Analiza si la búsqueda contiene producto + vehículo + año.

    Args:
        query: Texto de búsqueda del usuario

    Returns:
        Diccionario con el análisis:
        - tipo: "combinada" | "solo_vehiculo" | "simple"
        - producto: término de producto (si aplica)
        - vehiculo: modelo o marca detectado (si aplica)
        - tipo_vehiculo: "modelo" | "marca" (si aplica)
        - año: año detectado (si aplica)
        - query: búsqueda original (para tipo simple)

    Ejemplos:
        "aceite aveo" → {tipo: "combinada", producto: "aceite", vehiculo: "aveo", tipo_vehiculo: "modelo"}
        "filtro chevrolet" → {tipo: "combinada", producto: "filtro", vehiculo: "chevrolet", tipo_vehiculo: "marca"}
        "aceite cruze 2015" → {tipo: "combinada", producto: "aceite", vehiculo: "cruze", tipo_vehiculo: "modelo", año: 2015}
        "aveo" → {tipo: "solo_vehiculo", vehiculo: "aveo", tipo_vehiculo: "modelo"}
        "aveo 2015" → {tipo: "solo_vehiculo", vehiculo: "aveo", tipo_vehiculo: "modelo", año: 2015}
        "monroe" → {tipo: "simple", query: "monroe"}
    """
    if not query or not query.strip():
        return {"tipo": "simple", "query": query}

    # Normalizar y separar términos
    terminos = query.lower().strip().split()

    termino_vehiculo: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    año: Optional[int] = None
    terminos_producto: list = []

    for t in terminos:
        # Detectar año (número de 4 dígitos entre 1990-2030)
        if t.isdigit() and len(t) == 4:
            año_int = int(t)
            if 1990 <= año_int <= 2030:
                año = año_int
                continue

        # Prioridad: modelo sobre marca (si existe en ambos, es modelo)
        if t in MODELOS_VEHICULO:
            termino_vehiculo = t
            tipo_vehiculo = "modelo"
        elif t in MARCAS_VEHICULO and termino_vehiculo is None:
            # Solo asignar marca si no se encontró modelo
            termino_vehiculo = t
            tipo_vehiculo = "marca"
        else:
            terminos_producto.append(t)

    # Caso 1: Solo vehículo (ej: "aveo", "aveo 2015")
    if termino_vehiculo and not terminos_producto:
        return {
            "tipo": "solo_vehiculo",
            "vehiculo": termino_vehiculo,
            "tipo_vehiculo": tipo_vehiculo,
            "año": año
        }

    # Caso 2: Producto + vehículo (ej: "aceite aveo", "aceite cruze 2015")
    if termino_vehiculo and terminos_producto:
        return {
            "tipo": "combinada",
            "producto": " ".join(terminos_producto),
            "vehiculo": termino_vehiculo,
            "tipo_vehiculo": tipo_vehiculo,
            "año": año
        }

    # Caso 3: Búsqueda simple (sin vehículo detectado)
    return {"tipo": "simple", "query": query}


def get_estadisticas_vocabulario() -> Dict[str, int]:
    """Retorna estadísticas del vocabulario cargado."""
    return {
        "modelos": len(MODELOS_VEHICULO),
        "marcas": len(MARCAS_VEHICULO),
        "cargado": _vocabulario_cargado
    }
