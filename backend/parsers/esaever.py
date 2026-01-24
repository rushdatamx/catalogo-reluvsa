"""
Parser específico para productos ESAEVER

Patrón típico:
RXXXXXXX/ZXXXXXXX/OEM/CODIGO TIPO_PRODUCTO MODELO MOTOR AÑO/AÑO

Ejemplos:
- R42609220/Z95048411/700061 TANQUE CON TAPON DEPOSITO ANTICONGELANTE SONIC 1.6L DOHC 12/17
- R19314860/19314860/B-6046 BOMBA AGUA AVEO 1.6L 06/17
- R94539597/96420303 TAPON TANQUE DEPOSITO ANTICONGELANTE AVEO,OPTRA 16V 2.0L 03/12

Particularidades:
- Prefijo R = código ESAEVER
- Prefijo Z = código alterno
- DOHC/SOHC = tipo de motor
- 16V = 16 válvulas
- Especializado en sistema de enfriamiento

Productos: 336
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class EsaeverParser(BaseParser):
    """Parser especializado para productos ESAEVER (enfriamiento)"""

    # Patrones específicos de ESAEVER
    PATRON_SKU_ESAEVER = re.compile(r'^(R\d+|Z\d+)(/[A-Z0-9\-]+)*', re.IGNORECASE)

    # Tipos de motor
    TIPOS_MOTOR = ['DOHC', 'SOHC', 'OHV', 'OHC']

    # Válvulas
    PATRON_VALVULAS = re.compile(r'(\d+)V(?:ALVULAS)?', re.IGNORECASE)

    # Tipos de producto ESAEVER
    TIPOS_ESAEVER = [
        'TANQUE', 'DEPOSITO', 'TAPON', 'BOMBA AGUA', 'MANGUERA',
        'TERMOSTATO', 'SENSOR', 'VALVULA', 'TOMA', 'CONECTOR',
        'TUBO', 'FILTRO', 'ENGRANE', 'BANDA', 'TENSOR'
    ]

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto ESAEVER"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos (ESAEVER tiene formato especial R/Z)
        resultado.skus_alternos = self._extraer_skus_esaever(descripcion)

        # Extraer tipo de producto
        resultado.tipo_producto = self._extraer_tipo_esaever(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_esaever(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_skus_esaever(self, descripcion: str) -> List[str]:
        """Extrae SKUs con formato ESAEVER (R/Z prefijos)"""
        # Primero intentar patrón ESAEVER específico
        match = self.PATRON_SKU_ESAEVER.match(descripcion)
        if match:
            skus_str = match.group(0)
            return [sku.strip() for sku in skus_str.split('/') if sku.strip()]

        # Si no, usar método base
        return self.extraer_skus_alternos(descripcion)

    def _extraer_tipo_esaever(self, descripcion: str) -> str:
        """Extrae tipo de producto ESAEVER"""
        desc_upper = descripcion.upper()

        for tipo in self.TIPOS_ESAEVER:
            if tipo in desc_upper:
                return tipo

        return self.extraer_tipo_producto(descripcion)

    def _extraer_compatibilidades_esaever(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos ESAEVER"""
        compatibilidades = []

        # Remover SKUs
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

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

            # Extraer tipo de motor (DOHC, SOHC)
            for tipo_motor in self.TIPOS_MOTOR:
                if tipo_motor in contexto.upper():
                    compat.especificacion = tipo_motor
                    break

            # Extraer válvulas
            valvulas_match = self.PATRON_VALVULAS.search(contexto)
            if valvulas_match:
                valvulas = valvulas_match.group(1)
                if compat.especificacion:
                    compat.especificacion += f' {valvulas}V'
                else:
                    compat.especificacion = f'{valvulas}V'

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
