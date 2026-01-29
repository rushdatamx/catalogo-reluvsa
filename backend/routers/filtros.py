"""
Endpoints para obtener opciones de filtros
"""
from typing import Optional, List
from fastapi import APIRouter, Query

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_db
from models import FiltroOpciones

router = APIRouter(prefix="/api/filtros", tags=["filtros"])


@router.get("/departamentos", response_model=FiltroOpciones)
def get_departamentos():
    """Obtiene la lista de departamentos disponibles"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT departamento
            FROM productos
            WHERE departamento IS NOT NULL AND departamento != ''
            ORDER BY departamento
        """)
        valores = [row['departamento'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/marcas-producto", response_model=FiltroOpciones)
def get_marcas_producto(
    departamento: Optional[str] = Query(None, description="Filtrar por departamento")
):
    """Obtiene la lista de marcas de producto"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT marca
            FROM productos
            WHERE marca IS NOT NULL AND marca != ''
        """
        params = []
        if departamento:
            query += " AND departamento = ?"
            params.append(departamento)

        query += " ORDER BY marca"
        cursor.execute(query, params)
        valores = [row['marca'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/marcas-vehiculo", response_model=FiltroOpciones)
def get_marcas_vehiculo(
    departamento: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene la lista de marcas de vehículo con compatibilidades"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT c.marca_vehiculo
            FROM compatibilidades c
            INNER JOIN productos p ON p.id = c.producto_id
            WHERE c.marca_vehiculo IS NOT NULL AND c.marca_vehiculo != ''
        """
        params = []

        if departamento:
            query += " AND p.departamento = ?"
            params.append(departamento)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY c.marca_vehiculo"
        cursor.execute(query, params)
        valores = [row['marca_vehiculo'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/modelos-vehiculo", response_model=FiltroOpciones)
def get_modelos_vehiculo(
    marca_vehiculo: str = Query(..., description="Marca del vehículo"),
    departamento: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene la lista de modelos para una marca de vehículo"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT c.modelo_vehiculo
            FROM compatibilidades c
            INNER JOIN productos p ON p.id = c.producto_id
            WHERE c.modelo_vehiculo IS NOT NULL AND c.modelo_vehiculo != ''
              AND c.marca_vehiculo = ?
        """
        params = [marca_vehiculo]

        if departamento:
            query += " AND p.departamento = ?"
            params.append(departamento)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY c.modelo_vehiculo"
        cursor.execute(query, params)
        valores = [row['modelo_vehiculo'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/años", response_model=FiltroOpciones)
def get_años(
    marca_vehiculo: Optional[str] = Query(None),
    modelo_vehiculo: Optional[str] = Query(None),
    departamento: Optional[str] = Query(None)
):
    """Obtiene la lista de años disponibles"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT c.año_inicio, c.año_fin
            FROM compatibilidades c
            INNER JOIN productos p ON p.id = c.producto_id
            WHERE c.año_inicio IS NOT NULL
              AND c.año_inicio >= 1950 AND c.año_inicio <= 2030
              AND c.año_fin >= 1950 AND c.año_fin <= 2030
        """
        params = []

        if marca_vehiculo:
            query += " AND c.marca_vehiculo = ?"
            params.append(marca_vehiculo)

        if modelo_vehiculo:
            query += " AND c.modelo_vehiculo = ?"
            params.append(modelo_vehiculo)

        if departamento:
            query += " AND p.departamento = ?"
            params.append(departamento)

        cursor.execute(query, params)

        # Generar lista de años únicos
        años_set = set()
        for row in cursor.fetchall():
            año_inicio = row['año_inicio']
            año_fin = row['año_fin']
            for año in range(año_inicio, año_fin + 1):
                años_set.add(año)

        valores = sorted([str(a) for a in años_set], reverse=True)
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/motores", response_model=FiltroOpciones)
def get_motores(
    marca_vehiculo: Optional[str] = Query(None),
    modelo_vehiculo: Optional[str] = Query(None),
    año: Optional[int] = Query(None)
):
    """Obtiene la lista de motores disponibles"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT c.motor
            FROM compatibilidades c
            WHERE c.motor IS NOT NULL AND c.motor != ''
        """
        params = []

        if marca_vehiculo:
            query += " AND c.marca_vehiculo = ?"
            params.append(marca_vehiculo)

        if modelo_vehiculo:
            query += " AND c.modelo_vehiculo = ?"
            params.append(modelo_vehiculo)

        if año:
            query += " AND c.año_inicio <= ? AND c.año_fin >= ?"
            params.extend([año, año])

        query += " ORDER BY c.motor"
        cursor.execute(query, params)
        valores = [row['motor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/grupos-producto", response_model=FiltroOpciones)
def get_grupos_producto(
    departamento: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None),
    marca_vehiculo: Optional[str] = Query(None),
    modelo_vehiculo: Optional[str] = Query(None),
    año: Optional[int] = Query(None),
    motor: Optional[str] = Query(None)
):
    """Obtiene la lista de grupos de producto con filtros en cascada"""
    with get_db() as conn:
        cursor = conn.cursor()

        needs_compat = any([marca_vehiculo, modelo_vehiculo, año, motor])

        query = """
            SELECT DISTINCT p.grupo_producto
            FROM productos p
        """
        if needs_compat:
            query += " INNER JOIN compatibilidades c ON c.producto_id = p.id"

        query += " WHERE p.grupo_producto IS NOT NULL AND p.grupo_producto != ''"
        params = []

        if departamento:
            query += " AND p.departamento = ?"
            params.append(departamento)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        if marca_vehiculo:
            query += " AND c.marca_vehiculo = ?"
            params.append(marca_vehiculo)

        if modelo_vehiculo:
            query += " AND c.modelo_vehiculo = ?"
            params.append(modelo_vehiculo)

        if año:
            query += " AND c.año_inicio <= ? AND c.año_fin >= ?"
            params.extend([año, año])

        if motor:
            query += " AND c.motor = ?"
            params.append(motor)

        query += " ORDER BY p.grupo_producto"
        cursor.execute(query, params)
        valores = [row['grupo_producto'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/tipos-producto", response_model=FiltroOpciones)
def get_tipos_producto(
    departamento: Optional[str] = Query(None)
):
    """Obtiene la lista de tipos de producto"""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT tipo_producto
            FROM productos
            WHERE tipo_producto IS NOT NULL AND tipo_producto != ''
        """
        params = []

        if departamento:
            query += " AND departamento = ?"
            params.append(departamento)

        query += " ORDER BY tipo_producto"
        cursor.execute(query, params)
        valores = [row['tipo_producto'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


# ============================================================
# FILTROS PARA LLANTAS
# ============================================================

@router.get("/llantas/anchos", response_model=FiltroOpciones)
def get_anchos_llanta(
    marca_producto: Optional[str] = Query(None, description="Filtrar por marca de llanta")
):
    """Obtiene anchos de llantas disponibles: 155, 175, 185, 205..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'llanta' AND cp.clave = 'ancho'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY CAST(cp.valor AS INTEGER)"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/llantas/relaciones", response_model=FiltroOpciones)
def get_relaciones_llanta(
    ancho: Optional[str] = Query(None, description="Filtrar por ancho"),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene relaciones (perfil) de llantas: 50, 55, 60, 65, 70..."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Primero obtenemos los producto_ids que tienen el ancho especificado
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'llanta' AND cp.clave = 'relacion'
        """
        params = []

        if ancho:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'ancho' AND valor = ?
                )
            """
            params.append(ancho)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY CAST(cp.valor AS INTEGER)"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/llantas/diametros", response_model=FiltroOpciones)
def get_diametros_llanta(
    ancho: Optional[str] = Query(None),
    relacion: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene diámetros (rin) de llantas: R13, R14, R15, R16..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'llanta' AND cp.clave = 'diametro'
        """
        params = []

        # Filtrar por productos que tengan el ancho especificado
        if ancho:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'ancho' AND valor = ?
                )
            """
            params.append(ancho)

        # Filtrar por productos que tengan la relación especificada
        if relacion:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'llanta' AND clave = 'relacion' AND valor = ?
                )
            """
            params.append(relacion)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/llantas/tipos", response_model=FiltroOpciones)
def get_tipos_llanta(
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene tipos de llantas: Deportiva, Direccional, Tracción..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'llanta' AND cp.clave = 'tipo'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/llantas/capas", response_model=FiltroOpciones)
def get_capas_llanta(
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene capas de llantas: 6, 8, 10, 14, 16..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'llanta' AND cp.clave = 'capas'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY CAST(cp.valor AS INTEGER)"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


# ============================================================
# FILTROS PARA ACEITES
# ============================================================

@router.get("/aceites/viscosidades", response_model=FiltroOpciones)
def get_viscosidades(
    tipo_aceite: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene viscosidades SAE: 5W30, 10W40, 20W50, SAE 40..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'aceite' AND cp.clave = 'viscosidad'
        """
        params = []

        if tipo_aceite:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'tipo_aceite' AND valor = ?
                )
            """
            params.append(tipo_aceite)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/aceites/tipos", response_model=FiltroOpciones)
def get_tipos_aceite(
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene tipos de aceite: Motor, Transmisión, Hidráulico, ATF..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'aceite' AND cp.clave = 'tipo_aceite'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/aceites/presentaciones", response_model=FiltroOpciones)
def get_presentaciones(
    viscosidad: Optional[str] = Query(None),
    tipo_aceite: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene presentaciones: 946ml, 1L, 4L, 5L, 19L..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'aceite' AND cp.clave = 'presentacion'
        """
        params = []

        if viscosidad:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'viscosidad' AND valor = ?
                )
            """
            params.append(viscosidad)

        if tipo_aceite:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'aceite' AND clave = 'tipo_aceite' AND valor = ?
                )
            """
            params.append(tipo_aceite)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


# ============================================================
# FILTROS PARA ACUMULADORES
# ============================================================

@router.get("/acumuladores/grupos", response_model=FiltroOpciones)
def get_grupos_bci(
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene grupos BCI: 34, 35, 47, 65, 99..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'acumulador' AND cp.clave = 'grupo_bci'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/acumuladores/capacidades", response_model=FiltroOpciones)
def get_capacidades_cca(
    grupo_bci: Optional[str] = Query(None),
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene capacidades CCA: 350A, 550A, 750A..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'acumulador' AND cp.clave = 'capacidad_cca'
        """
        params = []

        if grupo_bci:
            query += """
                AND cp.producto_id IN (
                    SELECT producto_id FROM caracteristicas_producto
                    WHERE categoria = 'acumulador' AND clave = 'grupo_bci' AND valor = ?
                )
            """
            params.append(grupo_bci)

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))


@router.get("/acumuladores/tamanos", response_model=FiltroOpciones)
def get_tamanos_acumulador(
    marca_producto: Optional[str] = Query(None)
):
    """Obtiene tamaños: Chico, Medio Chico, Intermedio, Mediano, Grande..."""
    with get_db() as conn:
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT cp.valor
            FROM caracteristicas_producto cp
            INNER JOIN productos p ON p.id = cp.producto_id
            WHERE cp.categoria = 'acumulador' AND cp.clave = 'tamano'
        """
        params = []

        if marca_producto:
            query += " AND p.marca = ?"
            params.append(marca_producto)

        query += " ORDER BY cp.valor"
        cursor.execute(query, params)
        valores = [row['valor'] for row in cursor.fetchall()]
        return FiltroOpciones(valores=valores, total=len(valores))
