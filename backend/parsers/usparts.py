"""
Parser específico para productos USPARTS

Patrón típico:
XXX-XXX/RXXXXXXX/OEM TIPO MODELO MOTOR AÑO/AÑO

Ejemplos:
- 100-001/R9046588 TOMA AGUA CON TERMOSTATO AVEO NG 1.5L 18/23
- 100-008/KGT-6819A TOMA CON TERMOSTATO RAM PROMASTER RAPID 1.4L 18/22
- 120-016/13251435 CONECTOR MANGUERA RADIADOR INFERIOR CRUZE 1.4L 11/16

Particularidades:
- Código XXX-XXX (grupo-secuencia)
- 100 = Tomas de agua
- 120 = Conectores
- "NG" = Nueva Generación
- Enfoque en GM moderno

Productos: 310
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class UspartsParser(BaseParser):
    """Parser especializado para productos USPARTS (enfriamiento GM)"""

    # Mapeo de grupos de código a tipo de producto
    GRUPOS_PRODUCTO = {
        '100': 'TOMA AGUA',
        '120': 'CONECTOR',
        '130': 'MANGUERA',
        '140': 'TUBO',
        '150': 'TAPON',
        '160': 'SENSOR',
        '200': 'BOMBA'
    }

    # Patrón para SKU USPARTS
    PATRON_SKU_USPARTS = re.compile(r'^(\d{3})-(\d{3})', re.IGNORECASE)

    # Patrón para "NG" (Nueva Generación)
    PATRON_NG = re.compile(r'\bNG\b', re.IGNORECASE)

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto USPARTS"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto desde el código
        resultado.tipo_producto = self._extraer_tipo_usparts(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_usparts(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_tipo_usparts(self, descripcion: str) -> str:
        """Extrae tipo de producto desde el código USPARTS"""
        match = self.PATRON_SKU_USPARTS.match(descripcion)
        if match:
            grupo = match.group(1)
            if grupo in self.GRUPOS_PRODUCTO:
                return self.GRUPOS_PRODUCTO[grupo]

        # Si no se encuentra en el código, buscar en la descripción
        return self.extraer_tipo_producto(descripcion)

    def _extraer_compatibilidades_usparts(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos USPARTS"""
        compatibilidades = []

        # Remover SKUs
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # Detectar si hay "NG" (Nueva Generación)
        es_nueva_gen = bool(self.PATRON_NG.search(descripcion))

        # Buscar todos los años
        años = list(self.PATRON_AÑOS.finditer(descripcion))

        for match_año in años:
            año_inicio_str = match_año.group(1)
            año_fin_str = match_año.group(2)

            compat = Compatibilidad()
            compat.año_inicio = self._normalizar_año(año_inicio_str)
            compat.año_fin = self._normalizar_año(año_fin_str)

            # Validar años
            if not self._años_validos(compat.año_inicio, compat.año_fin):
                continue

            # Buscar contexto antes del año
            contexto = descripcion[:match_año.start()]

            # Extraer motor
            motor_match = self.PATRON_MOTOR.search(contexto)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            # Agregar especificación NG si aplica
            if es_nueva_gen:
                compat.especificacion = 'NUEVA GENERACION'

            # Extraer modelo y marca
            self._extraer_modelo_marca(contexto, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades

    def _años_validos(self, año_inicio: int, año_fin: int) -> bool:
        """Valida que los años sean razonables"""
        if año_inicio is None or año_fin is None:
            return False
        if año_inicio < 1950 or año_inicio > 2030:
            return False
        if año_fin < 1950 or año_fin > 2030:
            return False
        if abs(año_fin - año_inicio) > 50:
            return False
        return True
