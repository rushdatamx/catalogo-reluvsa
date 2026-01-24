"""
Parsers adicionales para marcas con compatibilidades vehiculares

Este archivo contiene parsers para marcas que siguen patrones similares
al parser genérico pero con ajustes específicos.
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class ParserConValidacion(BaseParser):
    """Parser base con validación de años mejorada"""

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

    def _extraer_compatibilidades_estandar(self, descripcion: str) -> List[Compatibilidad]:
        """Extracción estándar de compatibilidades con validación"""
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

            # Extraer cilindros
            cilindros_match = self.PATRON_CILINDROS.search(contexto)
            if cilindros_match:
                compat.cilindros = cilindros_match.group(1).upper()

            # Extraer especificaciones
            spec_match = self.PATRON_SPEC.search(contexto)
            if spec_match:
                compat.especificacion = spec_match.group(1).upper()

            # Extraer modelo y marca
            self._extraer_modelo_marca(contexto, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades


# ============================================================
# PARSERS PARA MARCAS DE SUSPENSIÓN
# ============================================================

class BogeParser(ParserConValidacion):
    """Parser para BOGE (amortiguadores)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'AMORTIGUADOR'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DaiParser(ParserConValidacion):
    """Parser para DAI (bases, soportes)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DynamikParser(ParserConValidacion):
    """Parser para DYNAMIK (balatas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BALATA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class FritecParser(ParserConValidacion):
    """Parser para FRITEC (balatas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BALATA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class FricraftParser(ParserConValidacion):
    """Parser para FRICRAFT (balatas zapata)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BALATA ZAPATA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE MOTOR/EMPAQUES
# ============================================================

class DiamondParser(ParserConValidacion):
    """Parser para DIAMOND (anillos, metales, empaques)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DCEmpaquesParser(ParserConValidacion):
    """Parser para DC EMPAQUES"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'EMPAQUE'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class FracoParser(ParserConValidacion):
    """Parser para FRACO (empaques)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'EMPAQUE'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class CleviteParser(ParserConValidacion):
    """Parser para CLEVITE (metales)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'METAL'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE BOMBAS/ENFRIAMIENTO
# ============================================================

class DolzParser(ParserConValidacion):
    """Parser para DOLZ (bombas de agua)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BOMBA AGUA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class BrumerParser(ParserConValidacion):
    """Parser para BRUMER (bombas de agua)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BOMBA AGUA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class ContinentalParser(ParserConValidacion):
    """Parser para CONTINENTAL (mangueras, bandas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE ELÉCTRICOS
# ============================================================

class CooltechParser(ParserConValidacion):
    """Parser para COOLTECH (bulbos, sensores)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'SENSOR'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DynamicParser(ParserConValidacion):
    """Parser para DYNAMIC (interruptores, bulbos)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE DISTRIBUCIÓN/TIEMPO
# ============================================================

class BorgWarnerParser(ParserConValidacion):
    """Parser para BORG WARNER (cadenas de tiempo)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'CADENA TIEMPO'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DynagearParser(ParserConValidacion):
    """Parser para DYNAGEAR (kits distribución)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'KIT DISTRIBUCION'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class GarantiParser(ParserConValidacion):
    """Parser para GARANTI AUTOPARTES (kits, pistones)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE BALEROS/MAZAS
# ============================================================

class ChromiteParser(ParserConValidacion):
    """Parser para CHROMITE (baleros)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BALERO'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class FagParser(ParserConValidacion):
    """Parser para FAG (mazas, baleros)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class GmbParser(ParserConValidacion):
    """Parser para GMB (bombas, mazas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE FRENOS
# ============================================================

class DormanParser(ParserConValidacion):
    """Parser para DORMAN (cilindros de freno)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'CILINDRO FRENO'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class GoldenFrictionParser(ParserConValidacion):
    """Parser para GOLDEN FRICTION (balatas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BALATA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE BUJÍAS
# ============================================================

class ChampionParser(ParserConValidacion):
    """Parser para CHAMPION (bujías)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BUJIA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class AutoliteParser(ParserConValidacion):
    """Parser para AUTOLITE (bujías)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BUJIA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS DE CLUTCH
# ============================================================

class ExedyParser(ParserConValidacion):
    """Parser para EXEDY (clutch)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'CLUTCH'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


# ============================================================
# PARSERS PARA MARCAS VARIAS CON COMPATIBILIDADES
# ============================================================

class KarParser(ParserConValidacion):
    """Parser para 4KAR (poleas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'POLEA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class AgParser(ParserConValidacion):
    """Parser para AG (amortiguadores)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'AMORTIGUADOR'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class CarfanParser(ParserConValidacion):
    """Parser para CARFAN (motoventiladores)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'MOTOVENTILADOR'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class DepoParser(ParserConValidacion):
    """Parser para DEPO (faros, calaveras)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class FlexControlParser(ParserConValidacion):
    """Parser para FLEX CONTROL (cables, chicotes)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'CABLE'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class TotalpartsParser(ParserConValidacion):
    """Parser para TOTALPARTS (varios)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class AutotalParser(ParserConValidacion):
    """Parser para AUTOTAL (kits, bombas)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class BokarParser(ParserConValidacion):
    """Parser para BOKAR (bombas de gasolina)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = 'BOMBA GASOLINA'
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class GatesParser(ParserConValidacion):
    """Parser para GATES (bandas, mangueras)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado


class BoschParser(ParserConValidacion):
    """Parser para BOSCH (eléctricos)"""
    def parse(self, descripcion: str) -> ResultadoParseo:
        resultado = ResultadoParseo()
        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)
        resultado.compatibilidades = self._extraer_compatibilidades_estandar(descripcion)
        resultado.raw_compatibilidades = descripcion
        return resultado
