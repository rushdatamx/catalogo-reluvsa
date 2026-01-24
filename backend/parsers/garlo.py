"""
Parser específico para productos GARLO

Patrón típico:
HY-XXX/JG-XXX CABLES DE BUJIA MODELO MOTOR AÑO/AÑO

Ejemplos:
- HY-201/JG-201 CABLES DE BUJIA LUV 1.8L-2.2L 72/81,BLAZER 1.9L 82/85
- HY-111/8JG-111 CABLES DE BUJIA D100 318 360 75/92,DAKOTA 5.2L 5.9L 90/92
- HY-153/SHY CABLES DE BUJIA VW SEDAN 1600 E.ELEC

Particularidades:
- HY-XXX = código Garlo
- JG-XXX o 8JG-XXX = código alterno
- Motor puede ser rango (1.8L-2.2L)
- "318 360" son motores en pulgadas cúbicas
- Especializado en cables de bujía

Productos: 545
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class GarloParser(BaseParser):
    """Parser especializado para productos GARLO (cables de bujía)"""

    # Patrón para SKU GARLO
    PATRON_SKU_GARLO = re.compile(r'^(HY-\d+|8?JG-\d+|SHY|SEL|EL)', re.IGNORECASE)

    # Patrón para rango de motores (ej: 1.8L-2.2L)
    PATRON_MOTOR_RANGO = re.compile(r'(\d+\.\d+L)-(\d+\.\d+L)', re.IGNORECASE)

    # Patrón para motores en pulgadas cúbicas (ej: 318, 360, 302)
    PATRON_MOTOR_PULGADAS = re.compile(r'\b(2\d{2}|3\d{2}|4\d{2}|5\d{2})\b')

    # Especificaciones eléctricas
    SPECS_ELECTRICAS = ['E.ELEC', 'E ELEC', 'ELECTRONICA', 'ELECTRONIC']

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto GARLO"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self._extraer_skus_garlo(descripcion)

        # Tipo de producto es casi siempre CABLES DE BUJIA
        resultado.tipo_producto = 'CABLES DE BUJIA'

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_garlo(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_skus_garlo(self, descripcion: str) -> List[str]:
        """Extrae SKUs con formato GARLO"""
        skus = []

        # Buscar patrón inicial de SKUs
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            skus_str = match.group(1)
            skus = [sku.strip() for sku in skus_str.split('/') if sku.strip()]

        return skus

    def _extraer_compatibilidades_garlo(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos GARLO"""
        compatibilidades = []

        # Remover SKUs y tipo de producto
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # Remover "CABLES DE BUJIA" si está presente
        descripcion = re.sub(r'^CABLES?\s*(DE)?\s*BUJIAS?\s*', '', descripcion, flags=re.IGNORECASE)

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

            # Buscar motor en rango (1.8L-2.2L)
            motor_rango = self.PATRON_MOTOR_RANGO.search(contexto)
            if motor_rango:
                compat.motor = f"{motor_rango.group(1)}-{motor_rango.group(2)}"
            else:
                # Buscar motor simple
                motor_match = self.PATRON_MOTOR.search(contexto)
                if motor_match:
                    compat.motor = f"{motor_match.group(1)}L"
                else:
                    # Buscar motor en pulgadas cúbicas
                    motor_pulgadas = self.PATRON_MOTOR_PULGADAS.search(contexto)
                    if motor_pulgadas:
                        compat.motor = f"{motor_pulgadas.group(1)} CID"

            # Buscar especificaciones eléctricas
            for spec in self.SPECS_ELECTRICAS:
                if spec in contexto.upper():
                    compat.especificacion = 'ENCENDIDO ELECTRONICO'
                    break

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
