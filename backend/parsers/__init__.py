"""
Módulo de parsers para extraer información de las descripciones de productos.

Este módulo contiene parsers específicos para cada marca del catálogo.
Cada parser conoce el patrón de descripción de su marca y extrae:
- SKUs alternos
- Tipo de producto
- Compatibilidades vehiculares (marca, modelo, años, motor)

Documentación detallada: ver PATRONES_POR_MARCA.md
"""
from .base import BaseParser
from .generic import GenericParser

# Parsers principales
from .acdelco import ACDelcoParser
from .gonher import GonherParser
from .syd import SYDParser
from .injetech import InjetechParser
from .cauplas import CauplasParser
from .esaever import EsaeverParser
from .optimo import OptimoParser
from .usparts import UspartsParser
from .garlo import GarloParser
from .dayco import DaycoParser

# Parsers para marcas con compatibilidades
from .marcas_adicionales import (
    BogeParser, DaiParser, DynamikParser, FritecParser, FricraftParser,
    DiamondParser, DCEmpaquesParser, FracoParser, CleviteParser,
    DolzParser, BrumerParser, ContinentalParser,
    CooltechParser, DynamicParser,
    BorgWarnerParser, DynagearParser, GarantiParser,
    ChromiteParser, FagParser, GmbParser,
    DormanParser, GoldenFrictionParser,
    ChampionParser, AutoliteParser,
    ExedyParser,
    KarParser, AgParser, CarfanParser, DepoParser, FlexControlParser,
    TotalpartsParser, AutotalParser, BokarParser, GatesParser, BoschParser
)

# Parsers para marcas SIN compatibilidades
from .sin_compatibilidad import (
    # Llantas
    TornelParser, NereusParser, GoodrideParser, HankookParser, BktParser,
    CarlisleParser, ChaoyangParser, EpsilonParser, HiflyParser,
    MastertrackParser, MilestarParser, TriangleParser, WestlakeParser, BfgoodrichParser,
    # Aceites
    ReluvsaParser, AkronParser, CastrolParser, ChevronParser, BardahlParser,
    MobilParser, PennzoilParser, QuakerStateParser, ValvolineParser,
    EverestAceiteParser, FlexQuimParser, GenetronParser,
    # Acumuladores
    CheckerParser, ExtremaParser, CamelParser,
    # Genéricos
    AbroParser, ApsParser, AycParser, CdcParser, ErkcoParser,
    FandeliParser, FiammParser, GenericoParser
)

# Mapeo de marcas a sus parsers específicos
PARSERS = {
    # === MARCAS PRIORITARIAS CON PARSER ESPECÍFICO ===
    'ACDELCO': ACDelcoParser,
    'GONHER': GonherParser,
    'SYD': SYDParser,
    'INJETECH': InjetechParser,
    'CAUPLAS': CauplasParser,
    'ESAEVER': EsaeverParser,
    'OPTIMO': OptimoParser,
    'USPARTS': UspartsParser,
    'GARLO': GarloParser,
    'DAYCO': DaycoParser,

    # === MARCAS DE SUSPENSIÓN ===
    'BOGE': BogeParser,
    'DAI': DaiParser,
    'DYNAMIK': DynamikParser,
    'FRITEC': FritecParser,
    'FRICRAFT': FricraftParser,
    'AG': AgParser,

    # === MARCAS DE MOTOR/EMPAQUES ===
    'DIAMOND': DiamondParser,
    'DC EMPAQUES': DCEmpaquesParser,
    'FRACO': FracoParser,
    'CLEVITE': CleviteParser,

    # === MARCAS DE BOMBAS/ENFRIAMIENTO ===
    'DOLZ': DolzParser,
    'BRUMER': BrumerParser,
    'CONTINENTAL': ContinentalParser,

    # === MARCAS DE ELÉCTRICOS ===
    'COOLTECH': CooltechParser,
    'DYNAMIC': DynamicParser,
    'BOSCH': BoschParser,

    # === MARCAS DE DISTRIBUCIÓN/TIEMPO ===
    'BORG WARNER': BorgWarnerParser,
    'DYNAGEAR': DynagearParser,
    'GARANTI AUTOPARTES': GarantiParser,

    # === MARCAS DE BALEROS/MAZAS ===
    'CHROMITE': ChromiteParser,
    'FAG': FagParser,
    'GMB': GmbParser,

    # === MARCAS DE FRENOS ===
    'DORMAN': DormanParser,
    'GOLDEN FRICTION': GoldenFrictionParser,

    # === MARCAS DE BUJÍAS ===
    'CHAMPION': ChampionParser,
    'AUTOLITE': AutoliteParser,

    # === MARCAS DE CLUTCH ===
    'EXEDY': ExedyParser,

    # === OTRAS MARCAS CON COMPATIBILIDADES ===
    '4KAR': KarParser,
    'CARFAN': CarfanParser,
    'DEPO': DepoParser,
    'FLEX CONTROL': FlexControlParser,
    'TOTALPARTS': TotalpartsParser,
    'AUTOTAL': AutotalParser,
    'BOKAR': BokarParser,
    'GATES': GatesParser,

    # === LLANTAS (SIN COMPATIBILIDADES) ===
    'TORNEL': TornelParser,
    'NEREUS': NereusParser,
    'GOODRIDE': GoodrideParser,
    'HANKOOK': HankookParser,
    'BKT': BktParser,
    'CARLISLE': CarlisleParser,
    'CHAOYANG': ChaoyangParser,
    'EPSILON': EpsilonParser,
    'HIFLY': HiflyParser,
    'MASTERTRACK': MastertrackParser,
    'MILESTAR': MilestarParser,
    'TRIANGLE': TriangleParser,
    'WESTLAKE': WestlakeParser,
    'BFGOODRICH': BfgoodrichParser,

    # === ACEITES/QUÍMICOS (SIN COMPATIBILIDADES) ===
    'RELUVSA': ReluvsaParser,
    'AKRON': AkronParser,
    'CASTROL': CastrolParser,
    'CHEVRON': ChevronParser,
    'BARDAHL': BardahlParser,
    'MOBIL': MobilParser,
    'PENNZOIL': PennzoilParser,
    'QUAKER STATE': QuakerStateParser,
    'VALVOLINE': ValvolineParser,
    'EVEREST ACEITE': EverestAceiteParser,
    'FLEX QUIM': FlexQuimParser,
    'GENETRON': GenetronParser,

    # === ACUMULADORES (SIN COMPATIBILIDADES) ===
    'CHECKER': CheckerParser,
    'EXTREMA': ExtremaParser,
    'CAMEL': CamelParser,

    # === GENÉRICOS (SIN COMPATIBILIDADES) ===
    'ABRO': AbroParser,
    'APS': ApsParser,
    'AYC': AycParser,
    'CDC': CdcParser,
    'ERKCO': ErkcoParser,
    'FANDELI': FandeliParser,
    'FIAMM': FiammParser,
    'GENERICO': GenericoParser,
}


def get_parser(marca: str) -> BaseParser:
    """
    Obtiene el parser apropiado para una marca.

    Si no hay un parser específico para la marca, se usa GenericParser
    que intentará extraer información usando patrones comunes.

    Args:
        marca: Nombre de la marca del producto

    Returns:
        Instancia del parser apropiado
    """
    parser_class = PARSERS.get(marca, GenericParser)
    return parser_class()


def listar_marcas_con_parser() -> list:
    """Retorna la lista de marcas que tienen parser específico"""
    return list(PARSERS.keys())


def listar_marcas_sin_compatibilidad() -> list:
    """Retorna la lista de marcas que no generan compatibilidades"""
    from .sin_compatibilidad import ParserSinCompatibilidad
    return [
        marca for marca, parser_class in PARSERS.items()
        if issubclass(parser_class, ParserSinCompatibilidad)
    ]
