"""
Parser específico para productos OPTIMO

Patrón típico:
CODIGOXXNNXXXX/OEM TIPO_PRODUCTO MARCA MODELO AÑO/AÑO

Ejemplos:
- BMNN0150/OEM43200-50Y00 MAZA TRASERA 4 BIRLOS NISSAN TSURU-III 92/14
- TKNN0100/OEM30502-53J01 KIT DE CLUTCH NISSAN TSURU III 92/10
- SUNC9900/1003008/19334782 ROTULA INFERIOR AVEO 06/16,PONTIAC G3 06/11

Particularidades:
- Prefijo indica tipo: BM=Maza, TK=Kit, SU=Suspensión, SH=Horquilla, SQ=Buje
- XX indica marca destino: NN=Nissan, NC=Chevrolet, NF=Ford, NK=Chrysler
- Incluye marca de vehículo explícita frecuentemente

Productos: 351
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class OptimoParser(BaseParser):
    """Parser especializado para productos OPTIMO (suspensión)"""

    # Mapeo de prefijos a tipos de producto
    PREFIJOS_TIPO = {
        'BM': 'MAZA',
        'TK': 'KIT CLUTCH',
        'SU': 'ROTULA',
        'SH': 'HORQUILLA',
        'SQ': 'BUJE',
        'ES': 'SENSOR',
        'DO': 'TRIPOIDE',
        'MB': 'BOMBA',
        'MV': 'GUIA VALVULA',
        'RC': 'COLLARIN',
        'DM': 'CREMALLERA'
    }

    # Mapeo de códigos de marca en SKU a marca de vehículo
    CODIGO_MARCA = {
        'NN': 'NISSAN',
        'NC': 'CHEVROLET',
        'NF': 'FORD',
        'NK': 'CHRYSLER',
        'NR': 'RENAULT',
        'NV': 'VOLKSWAGEN',
        'NT': 'TOYOTA'
    }

    # Patrón para SKU OPTIMO
    PATRON_SKU_OPTIMO = re.compile(r'^([A-Z]{2})([A-Z]{2})(\d+)', re.IGNORECASE)

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto OPTIMO"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto desde el código
        resultado.tipo_producto = self._extraer_tipo_optimo(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_optimo(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_tipo_optimo(self, descripcion: str) -> str:
        """Extrae tipo de producto desde el código OPTIMO"""
        match = self.PATRON_SKU_OPTIMO.match(descripcion)
        if match:
            prefijo = match.group(1).upper()
            if prefijo in self.PREFIJOS_TIPO:
                return self.PREFIJOS_TIPO[prefijo]

        # Si no se encuentra en el código, buscar en la descripción
        return self.extraer_tipo_producto(descripcion)

    def _extraer_marca_desde_sku(self, descripcion: str) -> str:
        """Extrae la marca de vehículo desde el código SKU"""
        match = self.PATRON_SKU_OPTIMO.match(descripcion)
        if match:
            codigo_marca = match.group(2).upper()
            if codigo_marca in self.CODIGO_MARCA:
                return self.CODIGO_MARCA[codigo_marca]
        return ""

    def _extraer_compatibilidades_optimo(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos OPTIMO"""
        compatibilidades = []

        # Obtener marca desde SKU (si está disponible)
        marca_desde_sku = self._extraer_marca_desde_sku(descripcion)

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

            # Buscar marca explícita en el contexto
            self._buscar_marca_explicita(contexto, compat)

            # Si no hay marca pero la tenemos del SKU, usarla
            if not compat.marca_vehiculo and marca_desde_sku:
                compat.marca_vehiculo = marca_desde_sku

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades

    def _buscar_marca_explicita(self, contexto: str, compat: Compatibilidad):
        """Busca marca de vehículo explícita en el contexto"""
        contexto_upper = contexto.upper()

        if not compat.marca_vehiculo:
            for marca_text, marca_norm in self.MARCAS_VEHICULO.items():
                if f' {marca_text} ' in f' {contexto_upper} ':
                    compat.marca_vehiculo = marca_norm
                    break

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
