"""
Parsers para marcas SIN compatibilidades vehiculares

Estas marcas son:
- Llantas (TORNEL, NEREUS, GOODRIDE, etc.)
- Aceites (RELUVSA, AKRON, CASTROL, etc.)
- Acumuladores (CHECKER, EXTREMA, LTH)
- Herramientas/Genéricos (APS, CDC, ERKCO, etc.)
"""
from .base import BaseParser, ResultadoParseo


class ParserSinCompatibilidad(BaseParser):
    """Parser base para productos sin compatibilidad vehicular"""

    def parse(self, descripcion: str, marca_producto: str = '', departamento: str = '') -> ResultadoParseo:
        """Parsea sin extraer compatibilidades"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)
        resultado.tipo_producto = self.extraer_tipo_producto(descripcion)
        resultado.nombre_producto = self.limpiar_nombre_producto(descripcion, marca_producto, departamento)
        resultado.compatibilidades = []  # Sin compatibilidades
        resultado.raw_compatibilidades = descripcion

        return resultado


# ============================================================
# LLANTAS - Sin compatibilidad vehicular
# ============================================================

class TornelParser(ParserSinCompatibilidad):
    """Parser para TORNEL (llantas) - SIN COMPATIBILIDAD"""
    pass


class NereusParser(ParserSinCompatibilidad):
    """Parser para NEREUS (llantas) - SIN COMPATIBILIDAD"""
    pass


class GoodrideParser(ParserSinCompatibilidad):
    """Parser para GOODRIDE (llantas) - SIN COMPATIBILIDAD"""
    pass


class HankookParser(ParserSinCompatibilidad):
    """Parser para HANKOOK (llantas) - SIN COMPATIBILIDAD"""
    pass


class BktParser(ParserSinCompatibilidad):
    """Parser para BKT (llantas agrícolas) - SIN COMPATIBILIDAD"""
    pass


class CarlisleParser(ParserSinCompatibilidad):
    """Parser para CARLISLE (llantas) - SIN COMPATIBILIDAD"""
    pass


class ChaoyangParser(ParserSinCompatibilidad):
    """Parser para CHAOYANG (llantas moto) - SIN COMPATIBILIDAD"""
    pass


class EpsilonParser(ParserSinCompatibilidad):
    """Parser para EPSILON (llantas) - SIN COMPATIBILIDAD"""
    pass


class HiflyParser(ParserSinCompatibilidad):
    """Parser para HIFLY (llantas) - SIN COMPATIBILIDAD"""
    pass


class MastertrackParser(ParserSinCompatibilidad):
    """Parser para MASTERTRACK (llantas) - SIN COMPATIBILIDAD"""
    pass


class MilestarParser(ParserSinCompatibilidad):
    """Parser para MILESTAR (llantas) - SIN COMPATIBILIDAD"""
    pass


class TriangleParser(ParserSinCompatibilidad):
    """Parser para TRIANGLE (llantas) - SIN COMPATIBILIDAD"""
    pass


class WestlakeParser(ParserSinCompatibilidad):
    """Parser para WESTLAKE (llantas) - SIN COMPATIBILIDAD"""
    pass


class BfgoodrichParser(ParserSinCompatibilidad):
    """Parser para BFGOODRICH (llantas) - SIN COMPATIBILIDAD"""
    pass


# ============================================================
# ACEITES/QUÍMICOS - Sin compatibilidad vehicular
# ============================================================

class ReluvsaParser(ParserSinCompatibilidad):
    """Parser para RELUVSA (aceites propios) - SIN COMPATIBILIDAD"""
    pass


class AkronParser(ParserSinCompatibilidad):
    """Parser para AKRON (aceites) - SIN COMPATIBILIDAD"""
    pass


class CastrolParser(ParserSinCompatibilidad):
    """Parser para CASTROL (aceites) - SIN COMPATIBILIDAD"""
    pass


class ChevronParser(ParserSinCompatibilidad):
    """Parser para CHEVRON (aceites) - SIN COMPATIBILIDAD"""
    pass


class BardahlParser(ParserSinCompatibilidad):
    """Parser para BARDAHL (aditivos) - SIN COMPATIBILIDAD"""
    pass


class MobilParser(ParserSinCompatibilidad):
    """Parser para MOBIL (aceites) - SIN COMPATIBILIDAD"""
    pass


class PennzoilParser(ParserSinCompatibilidad):
    """Parser para PENNZOIL (aceites) - SIN COMPATIBILIDAD"""
    pass


class QuakerStateParser(ParserSinCompatibilidad):
    """Parser para QUAKER STATE (aceites) - SIN COMPATIBILIDAD"""
    pass


class ValvolineParser(ParserSinCompatibilidad):
    """Parser para VALVOLINE (aceites) - SIN COMPATIBILIDAD"""
    pass


class EverestAceiteParser(ParserSinCompatibilidad):
    """Parser para EVEREST ACEITE - SIN COMPATIBILIDAD"""
    pass


class FlexQuimParser(ParserSinCompatibilidad):
    """Parser para FLEX QUIM - SIN COMPATIBILIDAD"""
    pass


class GenetronParser(ParserSinCompatibilidad):
    """Parser para GENETRON (refrigerantes) - SIN COMPATIBILIDAD"""
    pass


# ============================================================
# ACUMULADORES - Sin compatibilidad vehicular
# ============================================================

class CheckerParser(ParserSinCompatibilidad):
    """Parser para CHECKER (acumuladores) - SIN COMPATIBILIDAD"""
    pass


class ExtremaParser(ParserSinCompatibilidad):
    """Parser para EXTREMA (acumuladores) - SIN COMPATIBILIDAD"""
    pass


class CamelParser(ParserSinCompatibilidad):
    """Parser para CAMEL (acumuladores) - SIN COMPATIBILIDAD"""
    pass


# ============================================================
# HERRAMIENTAS/GENÉRICOS - Sin compatibilidad vehicular
# ============================================================

class AbroParser(ParserSinCompatibilidad):
    """Parser para ABRO (silicones) - SIN COMPATIBILIDAD"""
    pass


class ApsParser(ParserSinCompatibilidad):
    """Parser para APS (herramientas) - SIN COMPATIBILIDAD"""
    pass


class AycParser(ParserSinCompatibilidad):
    """Parser para AYC (cables) - SIN COMPATIBILIDAD"""
    pass


class CdcParser(ParserSinCompatibilidad):
    """Parser para CDC (cables) - SIN COMPATIBILIDAD"""
    pass


class ErkcoParser(ParserSinCompatibilidad):
    """Parser para ERKCO (herramientas) - SIN COMPATIBILIDAD"""
    pass


class FandeliParser(ParserSinCompatibilidad):
    """Parser para FANDELI (lijas) - SIN COMPATIBILIDAD"""
    pass


class FiammParser(ParserSinCompatibilidad):
    """Parser para FIAMM (bocinas) - SIN COMPATIBILIDAD"""
    pass


class GenericoParser(ParserSinCompatibilidad):
    """Parser para GENERICO - SIN COMPATIBILIDAD"""
    pass
