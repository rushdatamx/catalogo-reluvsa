"""
Parser específico para productos GONHER
Formato típico: SKU/SKUS FILTRO TIPO MODELO MOTOR AÑO/AÑO
Ejemplo: "GP-13/PH5/OF-13/PF35M FILTRO ACEITE CHEVROLET LARGO SUBURBAN V8 350 69/85"
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class GonherParser(BaseParser):
    """Parser especializado para productos GONHER (principalmente filtros)"""

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea una descripción de GONHER"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos (GONHER tiene muchas referencias cruzadas)
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # El tipo casi siempre es FILTRO para GONHER
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        if not resultado.tipo_producto:
            resultado.tipo_producto = "FILTRO"

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_gonher(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_compatibilidades_gonher(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades específicas de formato GONHER"""
        compatibilidades = []

        # Remover "FILTRO DE ACEITE/COMBUSTIBLE/AIRE GONHER S.P." si está presente
        desc_limpia = descripcion
        for patron in ['FILTRO DE ACEITE GONHER S.P.', 'FILTRO DE COMBUSTIBLE GONHER S.P.',
                       'FILTRO ACEITE GONHER S.P.', 'FILTRO COMBUSTIBLE GONHER S.P.',
                       'GONHER S.P.', 'GONHER S.P', 'S.P.', 'S.P']:
            desc_limpia = desc_limpia.replace(patron, '')

        # GONHER puede tener múltiples vehículos separados por coma
        segmentos = re.split(r',\s*', desc_limpia)

        for segmento in segmentos:
            segmento = segmento.strip()
            if not segmento:
                continue

            # Buscar años
            match_año = self.PATRON_AÑOS.search(segmento)
            if not match_año:
                continue

            compat = Compatibilidad()

            # Extraer años
            compat.año_inicio = self._normalizar_año(match_año.group(1))
            compat.año_fin = self._normalizar_año(match_año.group(2))

            # GONHER incluye a veces cilindrada como número (ej: 350, 302)
            cilindrada_match = self.PATRON_CILINDRADA.search(segmento)
            if cilindrada_match:
                compat.motor = cilindrada_match.group(1)

            # Extraer motor en litros
            motor_match = self.PATRON_MOTOR.search(segmento)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            # Extraer cilindros (V8, V6, L6, etc.)
            cilindros_match = self.PATRON_CILINDROS.search(segmento)
            if cilindros_match:
                compat.cilindros = cilindros_match.group(1).upper()

            # Extraer especificaciones
            spec_match = self.PATRON_SPEC.search(segmento)
            if spec_match:
                compat.especificacion = spec_match.group(1).upper()

            # Extraer modelo y marca
            self._extraer_modelo_marca(segmento, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades
