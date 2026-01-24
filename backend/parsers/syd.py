"""
Parser específico para productos SYD
Formato típico: SKU/SKU_ALTERNO TIPO_PIEZA MODELO1,MODELO2 AÑO/AÑO
Ejemplo: "1416042/SQNN0900 BUJE INFERIOR CHICO VERSA NOTE 12/18,MARCH 11/18,KICKS 17/18"
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class SYDParser(BaseParser):
    """Parser especializado para productos SYD (suspensión)"""

    # Posiciones que SYD incluye en sus descripciones
    POSICIONES = ['INFERIOR', 'SUPERIOR', 'DELANTERO', 'TRASERO',
                  'DERECHO', 'IZQUIERDO', 'CHICO', 'GRANDE']

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea una descripción de SYD"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)

        # Extraer nombre del producto (incluyendo posición)
        resultado.nombre_producto = self._extraer_nombre_con_posicion(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_syd(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_nombre_con_posicion(self, descripcion: str) -> str:
        """Extrae el nombre del producto incluyendo la posición"""
        # Remover SKUs del inicio
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # Buscar el primer modelo/marca
        desc_upper = descripcion.upper()
        fin_nombre = len(descripcion)

        for modelo in self.MODELOS_CONOCIDOS.keys():
            idx = desc_upper.find(f' {modelo} ')
            if idx > 0 and idx < fin_nombre:
                fin_nombre = idx

        for marca in self.MARCAS_VEHICULO.keys():
            idx = desc_upper.find(f' {marca} ')
            if idx > 0 and idx < fin_nombre:
                fin_nombre = idx

        nombre = descripcion[:fin_nombre].strip()

        # Capitalizar
        return nombre[:80] if len(nombre) > 80 else nombre

    def _extraer_compatibilidades_syd(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades específicas de formato SYD"""
        compatibilidades = []

        # SYD usa comas para separar vehículos
        segmentos = re.split(r',\s*', descripcion)

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

            # Extraer motor
            motor_match = self.PATRON_MOTOR.search(segmento)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            # Extraer cilindros
            cilindros_match = self.PATRON_CILINDROS.search(segmento)
            if cilindros_match:
                compat.cilindros = cilindros_match.group(1).upper()

            # Extraer modelo y marca
            self._extraer_modelo_marca(segmento, compat)

            # SYD a veces tiene "4X2" o "4X4"
            if '4X4' in segmento.upper():
                compat.especificacion = '4X4'
            elif '4X2' in segmento.upper():
                compat.especificacion = '4X2'

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades
