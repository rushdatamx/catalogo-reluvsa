"""
Parser específico para productos DAYCO

Patrón típico:
APXX/69 AXX BANDA DAYCO (genérica por medida)
95XXX/CODIGO KIT DISTRIBUCION MODELO AÑO/AÑO (con aplicación)

Ejemplos:
- AP75/69 A75 BANDA DAYCO (banda genérica por medida - SIN COMPATIBILIDAD)
- DAY-400 DIAFRAGMA FRENOS DAYCO (producto genérico - SIN COMPATIBILIDAD)
- 95285/PKB285 KIT DISTRIBUCION TSURU III 93/17,SENTRA 92/94

Particularidades:
- AP = Banda tipo A, medida en pulgadas (SIN COMPATIBILIDAD)
- 95XXX = Kit de distribución (CON COMPATIBILIDAD)
- Productos genéricos no tienen aplicación
- DAY-XXX son productos genéricos

Productos: 1257
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class DaycoParser(BaseParser):
    """Parser especializado para productos DAYCO (bandas, kits)"""

    # Patrones para productos genéricos (SIN compatibilidad)
    PATRON_BANDA_GENERICA = re.compile(r'^(AP\d+|A\d+|B\d+|C\d+)', re.IGNORECASE)
    PATRON_PRODUCTO_GENERICO = re.compile(r'^DAY-\d+', re.IGNORECASE)

    # Patrones para productos con aplicación
    PATRON_KIT = re.compile(r'^(95\d+|TKN?\d+|PKB\d+)', re.IGNORECASE)

    # Tipos de producto DAYCO
    TIPOS_DAYCO = [
        'KIT DISTRIBUCION', 'KIT TIEMPO', 'BANDA', 'TENSOR',
        'POLEA', 'DIAFRAGMA', 'MANGUERA'
    ]

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto DAYCO"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto
        resultado.tipo_producto = self._extraer_tipo_dayco(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Verificar si es producto genérico (sin compatibilidad)
        if self._es_producto_generico(descripcion):
            resultado.compatibilidades = []
        else:
            resultado.compatibilidades = self._extraer_compatibilidades_dayco(descripcion)

        resultado.raw_compatibilidades = descripcion

        return resultado

    def _es_producto_generico(self, descripcion: str) -> bool:
        """Determina si es un producto genérico sin compatibilidad vehicular"""
        # Bandas genéricas (AP75, A75, etc.)
        if self.PATRON_BANDA_GENERICA.match(descripcion):
            return True

        # Productos DAY-XXX genéricos
        if self.PATRON_PRODUCTO_GENERICO.match(descripcion):
            return True

        # Si dice "BANDA DAYCO" y no tiene años, es genérico
        desc_upper = descripcion.upper()
        if 'BANDA DAYCO' in desc_upper:
            if not self.PATRON_AÑOS.search(descripcion):
                return True

        return False

    def _extraer_tipo_dayco(self, descripcion: str) -> str:
        """Extrae tipo de producto DAYCO"""
        desc_upper = descripcion.upper()

        for tipo in self.TIPOS_DAYCO:
            if tipo in desc_upper:
                return tipo

        # Si es banda genérica
        if self.PATRON_BANDA_GENERICA.match(descripcion):
            return 'BANDA'

        return self.extraer_tipo_producto(descripcion)

    def _extraer_compatibilidades_dayco(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos DAYCO (solo para kits)"""
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
