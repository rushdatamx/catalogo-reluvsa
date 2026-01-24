"""
Parser específico para productos ACDELCO
Formato típico: SKU1/SKU2/SKU3 PRODUCTO MODELO MOTOR AÑO/AÑO,MODELO2 AÑO/AÑO
Ejemplo: "PF47M/19210284/R1008/GP-46 FILTRO ACEITE CHEVY 94/12,CORSA03/08,AVEO 1.6L 08/18"
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class ACDelcoParser(BaseParser):
    """Parser especializado para productos ACDELCO"""

    # Patrón para separar compatibilidades (separadas por coma)
    PATRON_COMPAT_SEP = re.compile(r',\s*')

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea una descripción de ACDELCO"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades - ACDELCO usa comas para separar múltiples vehículos
        resultado.compatibilidades = self._extraer_compatibilidades_acdelco(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_compatibilidades_acdelco(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades específicas de formato ACDELCO"""
        compatibilidades = []

        # Remover SKUs del inicio
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # Encontrar donde empiezan las compatibilidades (después del nombre del producto)
        # Buscar el primer modelo o marca de vehículo
        inicio_compat = None
        desc_upper = descripcion.upper()

        for modelo in self.MODELOS_CONOCIDOS.keys():
            idx = desc_upper.find(f' {modelo} ')
            if idx > 0:
                if inicio_compat is None or idx < inicio_compat:
                    inicio_compat = idx
            # También buscar sin espacio al final (ej: "CHEVY94/12")
            idx = desc_upper.find(f' {modelo}')
            if idx > 0 and idx + len(modelo) + 1 < len(desc_upper):
                siguiente_char = desc_upper[idx + len(modelo) + 1]
                if siguiente_char.isdigit():
                    if inicio_compat is None or idx < inicio_compat:
                        inicio_compat = idx

        for marca in self.MARCAS_VEHICULO.keys():
            idx = desc_upper.find(f' {marca} ')
            if idx > 0:
                if inicio_compat is None or idx < inicio_compat:
                    inicio_compat = idx

        if inicio_compat is None:
            # Intentar con el primer año encontrado
            match_año = self.PATRON_AÑOS.search(descripcion)
            if match_año:
                inicio_compat = max(0, match_año.start() - 30)
            else:
                return compatibilidades

        # Extraer la parte de compatibilidades
        parte_compat = descripcion[inicio_compat:].strip()

        # Separar por comas (cada segmento puede ser un vehículo diferente)
        segmentos = self.PATRON_COMPAT_SEP.split(parte_compat)

        for segmento in segmentos:
            segmento = segmento.strip()
            if not segmento:
                continue

            # Buscar años en este segmento
            match_año = self.PATRON_AÑOS.search(segmento)
            if not match_año:
                continue

            compat = Compatibilidad()

            # Extraer años
            compat.año_inicio = self._normalizar_año(match_año.group(1))
            compat.año_fin = self._normalizar_año(match_año.group(2))

            # Extraer motor
            motor_match = self.PATRON_MOTOR.search(segmento)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            # Extraer cilindros
            cilindros_match = self.PATRON_CILINDROS.search(segmento)
            if cilindros_match:
                compat.cilindros = cilindros_match.group(1).upper()

            # Extraer especificaciones
            spec_match = self.PATRON_SPEC.search(segmento)
            if spec_match:
                compat.especificacion = spec_match.group(1).upper()

            # Extraer modelo y marca
            self._extraer_modelo_marca(segmento, compat)

            # Si encontramos al menos modelo o marca, agregar
            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades
