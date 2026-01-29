"""
Parser base con métodos comunes para extraer información de descripciones
"""
import re
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Compatibilidad:
    """Representa una compatibilidad de un producto con un vehículo"""
    marca_vehiculo: str = ""
    modelo_vehiculo: str = ""
    año_inicio: Optional[int] = None
    año_fin: Optional[int] = None
    motor: str = ""
    cilindros: str = ""
    especificacion: str = ""


@dataclass
class ResultadoParseo:
    """Resultado del parseo de una descripción"""
    nombre_producto: str = ""
    tipo_producto: str = ""
    skus_alternos: List[str] = field(default_factory=list)
    compatibilidades: List[Compatibilidad] = field(default_factory=list)
    raw_compatibilidades: str = ""  # Para debugging


class BaseParser:
    """Parser base con métodos comunes"""

    # Patrones regex comunes
    PATRON_AÑOS = re.compile(r'(\d{2,4})[/-](\d{2,4})')
    PATRON_AÑO_INCOMPLETO = re.compile(r'(\d{2})/\s*$')  # Año incompleto al final: "72/"
    PATRON_AÑO_SOLO = re.compile(r'\b(19[5-9]\d|20[0-3]\d)\b')  # Año solo: 1950-2039
    PATRON_MOTOR = re.compile(r'(\d+\.?\d*)\s*[Ll](?:T|ITROS?)?', re.IGNORECASE)
    PATRON_CILINDRADA = re.compile(r'(\d{3})\s*(?:CID|CI|C\.I\.)?', re.IGNORECASE)
    PATRON_CILINDROS = re.compile(r'(V\d+|L\d+|\d+\s*CIL(?:INDROS?)?)', re.IGNORECASE)
    PATRON_SPEC = re.compile(r'(DOHC|SOHC|OHV|TBI|VORTEC|MPFI|EFI|16V|8V|12V|24V)', re.IGNORECASE)
    PATRON_SKUS = re.compile(r'^([A-Z0-9\-]+(?:/[A-Z0-9\-]+)+)\s+', re.IGNORECASE)

    # Falsos positivos - modelos que no son realmente modelos de vehículo
    FALSOS_POSITIVOS_MODELOS = {
        '300': re.compile(r'[A-Z]-300|MH-300|T-300|H-300|F-300', re.IGNORECASE),
        '1600': re.compile(r'1600/\d+|DATSUN.*1600|1600\s*CC', re.IGNORECASE),
        '1800': re.compile(r'1800/\d+|DATSUN.*1800|1800\s*CC', re.IGNORECASE),
        '2000': re.compile(r'2000/\d+|DATSUN.*2000|2000\s*CC', re.IGNORECASE),
        # SEDAN como tipo de carrocería (no como VW Sedan/Vocho)
        'SEDAN': re.compile(r'SEDAN\s+Y\s+HATCHBACK|SEDAN\s+Y\s+VAGONETA|TIPO\s+SEDAN|SEDAN\s+HATCHBACK', re.IGNORECASE),
    }

    # Modelos que NO deben dividirse por guión
    MODELOS_CON_GUION = {'CR-V', 'HR-V', 'BR-V', 'CX-3', 'CX-5', 'CX-7', 'CX-9', 'MX-5',
                         'F-150', 'F-250', 'F-350', 'F-450', 'F-550', 'E-150', 'E-250', 'E-350',
                         'F-100', 'F-200', 'F-300', 'F-400', 'F-500', 'F-600', 'F-700', 'F-800',
                         'B-100', 'B-200', 'B-300', 'D-100', 'D-200', 'D-300', 'D-400',
                         'W-100', 'W-200', 'W-300', 'C-10', 'C-15', 'C-20', 'C-30', 'C-35',
                         'K-10', 'K-15', 'K-20', 'K-30', 'K-35', 'S-10', 'T-100'}

    # Marcas de vehículos conocidas - LISTA EXHAUSTIVA
    MARCAS_VEHICULO = {
        # GM Americanas
        'CHEVROLET': 'CHEVROLET', 'CHEVY': 'CHEVROLET', 'GM': 'CHEVROLET',
        'CHEV': 'CHEVROLET', 'GMC': 'GMC', 'PONTIAC': 'PONTIAC',
        'BUICK': 'BUICK', 'CADILLAC': 'CADILLAC', 'OLDSMOBILE': 'OLDSMOBILE',
        'SATURN': 'SATURN', 'GEO': 'GEO', 'HUMMER': 'HUMMER',

        # Ford Americanas
        'FORD': 'FORD', 'LINCOLN': 'LINCOLN', 'MERCURY': 'MERCURY',

        # Chrysler Americanas
        'DODGE': 'DODGE', 'CHRYSLER': 'CHRYSLER', 'JEEP': 'JEEP', 'RAM': 'DODGE',
        'PLYMOUTH': 'PLYMOUTH', 'EAGLE': 'EAGLE',

        # Japonesas
        'TOYOTA': 'TOYOTA', 'LEXUS': 'LEXUS', 'SCION': 'SCION',
        'HONDA': 'HONDA', 'ACURA': 'ACURA',
        'NISSAN': 'NISSAN', 'DATSUN': 'NISSAN', 'INFINITI': 'INFINITI',
        'MAZDA': 'MAZDA',
        'MITSUBISHI': 'MITSUBISHI',
        'SUBARU': 'SUBARU',
        'SUZUKI': 'SUZUKI',
        'ISUZU': 'ISUZU',

        # Coreanas
        'HYUNDAI': 'HYUNDAI', 'KIA': 'KIA', 'DAEWOO': 'DAEWOO',

        # Alemanas
        'VOLKSWAGEN': 'VOLKSWAGEN', 'VW': 'VOLKSWAGEN',
        'BMW': 'BMW',
        'MERCEDES': 'MERCEDES', 'MERCEDES-BENZ': 'MERCEDES',
        'AUDI': 'AUDI',
        'PORSCHE': 'PORSCHE',
        'OPEL': 'OPEL',

        # Francesas
        'RENAULT': 'RENAULT',
        'PEUGEOT': 'PEUGEOT',
        'CITROEN': 'CITROEN',

        # Italianas
        'FIAT': 'FIAT',
        'ALFA ROMEO': 'ALFA ROMEO', 'ALFA': 'ALFA ROMEO',

        # Británicas
        'MINI': 'MINI',
        'JAGUAR': 'JAGUAR',
        'LAND ROVER': 'LAND ROVER',

        # Suecas
        'VOLVO': 'VOLVO',
        'SAAB': 'SAAB',

        # Españolas
        'SEAT': 'SEAT',

        # Americanas históricas
        'AMC': 'AMC',

        # Camiones y comerciales
        'HINO': 'HINO',
        'INTERNATIONAL': 'INTERNATIONAL', 'NAVISTAR': 'INTERNATIONAL',
        'FREIGHTLINER': 'FREIGHTLINER',
        'KENWORTH': 'KENWORTH',
        'PETERBILT': 'PETERBILT',
        'MACK': 'MACK',
        'STERLING': 'STERLING',
        'WESTERN STAR': 'WESTERN STAR',
        'DINA': 'DINA',
        'UD': 'UD',
    }

    # Modelos conocidos con su marca
    MODELOS_CONOCIDOS = {
        # Chevrolet
        'CHEVY': 'CHEVROLET', 'AVEO': 'CHEVROLET', 'SPARK': 'CHEVROLET',
        'SONIC': 'CHEVROLET', 'CRUZE': 'CHEVROLET', 'MALIBU': 'CHEVROLET',
        'CAMARO': 'CHEVROLET', 'CORVETTE': 'CHEVROLET', 'IMPALA': 'CHEVROLET',
        'SUBURBAN': 'CHEVROLET', 'TAHOE': 'CHEVROLET', 'SILVERADO': 'CHEVROLET',
        'CHEYENNE': 'CHEVROLET', 'COLORADO': 'CHEVROLET', 'S10': 'CHEVROLET',
        'BLAZER': 'CHEVROLET', 'TRAILBLAZER': 'CHEVROLET', 'EQUINOX': 'CHEVROLET',
        'TRAVERSE': 'CHEVROLET', 'TRAX': 'CHEVROLET', 'CAVALIER': 'CHEVROLET',
        'CORSA': 'CHEVROLET', 'TORNADO': 'CHEVROLET', 'MERIVA': 'CHEVROLET',
        'ASTRA': 'CHEVROLET', 'VECTRA': 'CHEVROLET', 'ZAFIRA': 'CHEVROLET',
        'OPTRA': 'CHEVROLET', 'CAPTIVA': 'CHEVROLET', 'MATIZ': 'CHEVROLET',
        'BEAT': 'CHEVROLET', 'ONIX': 'CHEVROLET', 'TRACKER': 'CHEVROLET',
        'EXPRESS': 'CHEVROLET', 'ASTRO': 'CHEVROLET', 'VENTURE': 'CHEVROLET',
        'UPLANDER': 'CHEVROLET', 'HHR': 'CHEVROLET', 'COBALT': 'CHEVROLET',
        'CUTLASS': 'CHEVROLET', 'CELEBRITY': 'CHEVROLET', 'CENTURY': 'CHEVROLET',
        'LUMINA': 'CHEVROLET', 'MONTE CARLO': 'CHEVROLET', 'BERETTA': 'CHEVROLET',
        # Ford
        'FIESTA': 'FORD', 'FOCUS': 'FORD', 'FUSION': 'FORD', 'MUSTANG': 'FORD',
        'TAURUS': 'FORD', 'ESCORT': 'FORD', 'TOPAZ': 'FORD', 'CONTOUR': 'FORD',
        'F-150': 'FORD', 'F-250': 'FORD', 'F-350': 'FORD', 'LOBO': 'FORD',
        'RANGER': 'FORD', 'EXPLORER': 'FORD', 'EXPEDITION': 'FORD',
        'ESCAPE': 'FORD', 'EDGE': 'FORD', 'ECOSPORT': 'FORD', 'BRONCO': 'FORD',
        'WINDSTAR': 'FORD', 'FREESTAR': 'FORD', 'ECONOLINE': 'FORD',
        'COURIER': 'FORD', 'IKON': 'FORD', 'KA': 'FORD', 'MONDEO': 'FORD',
        'SABLE': 'FORD', 'GHIA': 'FORD', 'THUNDERBIRD': 'FORD',
        # Nissan
        'TSURU': 'NISSAN', 'SENTRA': 'NISSAN', 'VERSA': 'NISSAN', 'MARCH': 'NISSAN',
        'ALTIMA': 'NISSAN', 'MAXIMA': 'NISSAN', 'TIIDA': 'NISSAN', 'NOTE': 'NISSAN',
        'V DRIVE': 'NISSAN', 'VDRIVE': 'NISSAN', 'V-DRIVE': 'NISSAN',
        'KICKS': 'NISSAN', 'JUKE': 'NISSAN', 'MURANO': 'NISSAN', 'PATHFINDER': 'NISSAN',
        'XTERRA': 'NISSAN', 'FRONTIER': 'NISSAN', 'NP300': 'NISSAN', 'TITAN': 'NISSAN',
        'PICKUP': 'NISSAN', 'D21': 'NISSAN', 'URVAN': 'NISSAN', 'PLATINA': 'NISSAN',
        'APRIO': 'NISSAN', 'HIKARI': 'NISSAN',
        # Dodge/Chrysler
        'NEON': 'DODGE', 'STRATUS': 'DODGE', 'AVENGER': 'DODGE', 'CHARGER': 'DODGE',
        'CHALLENGER': 'DODGE', 'DART': 'DODGE', 'ATTITUDE': 'DODGE', 'VISION': 'DODGE',
        'JOURNEY': 'DODGE', 'DURANGO': 'DODGE', 'DAKOTA': 'DODGE', 'RAM': 'DODGE',
        'CARAVAN': 'DODGE', 'VOYAGER': 'DODGE', 'TOWN': 'CHRYSLER', 'PT': 'CHRYSLER',
        'CRUISER': 'CHRYSLER', 'SEBRING': 'CHRYSLER', '300': 'CHRYSLER',
        'CALIBER': 'DODGE', 'NITRO': 'DODGE', 'VALIANT': 'DODGE',
        # Volkswagen
        'JETTA': 'VOLKSWAGEN', 'GOLF': 'VOLKSWAGEN', 'BEETLE': 'VOLKSWAGEN',
        'PASSAT': 'VOLKSWAGEN', 'POLO': 'VOLKSWAGEN', 'VENTO': 'VOLKSWAGEN',
        'BORA': 'VOLKSWAGEN', 'TIGUAN': 'VOLKSWAGEN', 'TOUAREG': 'VOLKSWAGEN',
        'POINTER': 'VOLKSWAGEN', 'SEDAN': 'VOLKSWAGEN', 'CARIBE': 'VOLKSWAGEN',
        'ATLANTIC': 'VOLKSWAGEN', 'CORSAR': 'VOLKSWAGEN', 'COMBI': 'VOLKSWAGEN',
        'GOL': 'VOLKSWAGEN', 'LUPO': 'VOLKSWAGEN', 'CROSSFOX': 'VOLKSWAGEN',
        # Toyota
        'COROLLA': 'TOYOTA', 'CAMRY': 'TOYOTA', 'YARIS': 'TOYOTA', 'PRIUS': 'TOYOTA',
        'RAV4': 'TOYOTA', 'HIGHLANDER': 'TOYOTA', '4RUNNER': 'TOYOTA', 'TACOMA': 'TOYOTA',
        'TUNDRA': 'TOYOTA', 'HILUX': 'TOYOTA', 'SIENNA': 'TOYOTA', 'CELICA': 'TOYOTA',
        # Honda
        'CIVIC': 'HONDA', 'ACCORD': 'HONDA', 'FIT': 'HONDA', 'CITY': 'HONDA',
        'CR-V': 'HONDA', 'HR-V': 'HONDA', 'PILOT': 'HONDA', 'ODYSSEY': 'HONDA',
        # Hyundai
        'ACCENT': 'HYUNDAI', 'ELANTRA': 'HYUNDAI', 'SONATA': 'HYUNDAI',
        'TUCSON': 'HYUNDAI', 'SANTA FE': 'HYUNDAI', 'ATOS': 'HYUNDAI',
        'VERNA': 'HYUNDAI', 'I10': 'HYUNDAI', 'I20': 'HYUNDAI', 'IX35': 'HYUNDAI',
        # Kia
        'RIO': 'KIA', 'FORTE': 'KIA', 'OPTIMA': 'KIA', 'SPORTAGE': 'KIA',
        'SORENTO': 'KIA', 'SOUL': 'KIA', 'SELTOS': 'KIA',
        # Renault
        'CLIO': 'RENAULT', 'MEGANE': 'RENAULT', 'FLUENCE': 'RENAULT',
        'DUSTER': 'RENAULT', 'KOLEOS': 'RENAULT', 'KANGOO': 'RENAULT',
        'STEPWAY': 'RENAULT', 'SANDERO': 'RENAULT', 'LOGAN': 'RENAULT',
        # Mazda
        'MAZDA3': 'MAZDA', 'MAZDA6': 'MAZDA', 'CX-3': 'MAZDA', 'CX-5': 'MAZDA',
        'CX-9': 'MAZDA', 'MX-5': 'MAZDA', 'B2200': 'MAZDA', 'B2500': 'MAZDA',
        # Fiat
        'PALIO': 'FIAT', 'UNO': 'FIAT', 'STRADA': 'FIAT', '500': 'FIAT',
        'MOBI': 'FIAT', 'ARGO': 'FIAT', 'DUCATO': 'FIAT',
        # Jeep
        'WRANGLER': 'JEEP', 'CHEROKEE': 'JEEP', 'GRAND CHEROKEE': 'JEEP',
        'LIBERTY': 'JEEP', 'PATRIOT': 'JEEP', 'COMPASS': 'JEEP', 'RENEGADE': 'JEEP',
        'WAGONEER': 'JEEP', 'CJ5': 'JEEP', 'CJ7': 'JEEP',
        # Dodge/Chrysler camiones y vans (modelos históricos)
        'D100': 'DODGE', 'D200': 'DODGE', 'D300': 'DODGE', 'D400': 'DODGE',
        'B100': 'DODGE', 'B200': 'DODGE', 'B300': 'DODGE',
        'W100': 'DODGE', 'W200': 'DODGE', 'W300': 'DODGE',
        'RAM CHARGER': 'DODGE', 'RAMCHARGER': 'DODGE',
        # Chevrolet adicionales
        'LUV': 'CHEVROLET', 'MONZA': 'CHEVROLET', 'NOVA': 'CHEVROLET',
        'CAPRICE': 'CHEVROLET', 'PICKUPS': 'CHEVROLET', 'PICK UP': 'CHEVROLET',
        'C10': 'CHEVROLET', 'C20': 'CHEVROLET', 'C30': 'CHEVROLET',
        'K10': 'CHEVROLET', 'K20': 'CHEVROLET', 'K30': 'CHEVROLET',
        'G10': 'CHEVROLET', 'G20': 'CHEVROLET', 'G30': 'CHEVROLET',
        # Ford adicionales
        'FAIRMONT': 'FORD', 'MAVERICK': 'FORD', 'PINTO': 'FORD',
        'LTD': 'FORD', 'GRAN MARQUIS': 'FORD', 'CROWN VICTORIA': 'FORD',
        'F100': 'FORD', 'F250': 'FORD', 'F350': 'FORD',
        'E150': 'FORD', 'E250': 'FORD', 'E350': 'FORD',
        # Nissan/Datsun históricos
        'TSUBAME': 'NISSAN', 'ICHI VAN': 'NISSAN', 'ICHIVAN': 'NISSAN',
        'ESTACAS': 'NISSAN', 'ESTAQUITAS': 'NISSAN',
        '1600': 'NISSAN', '1800': 'NISSAN', '2000': 'NISSAN',
        # Volkswagen adicionales
        'BRASILIA': 'VOLKSWAGEN', 'SAFARI': 'VOLKSWAGEN',
        'VOCHO': 'VOLKSWAGEN', 'ESCARABAJO': 'VOLKSWAGEN',
        # Suzuki
        'SAMURAI': 'SUZUKI', 'SIDEKICK': 'SUZUKI', 'VITARA': 'SUZUKI',
        'JIMNY': 'SUZUKI', 'SWIFT': 'SUZUKI', 'SX4': 'SUZUKI',
        # AMC/Otros
        'RAMBLER': 'AMC', 'JAVELIN': 'AMC', 'GREMLIN': 'AMC',
        # GMC
        'SIERRA': 'GMC', 'YUKON': 'GMC', 'SAFARI': 'GMC', 'SAVANA': 'GMC',
        # Pontiac
        'FIREBIRD': 'PONTIAC', 'GRAND AM': 'PONTIAC', 'GRAND PRIX': 'PONTIAC',
        'SUNFIRE': 'PONTIAC', 'TRANS AM': 'PONTIAC', 'BONNEVILLE': 'PONTIAC',
        # Buick
        'LESABRE': 'BUICK', 'REGAL': 'BUICK', 'RIVIERA': 'BUICK',
        'SKYLARK': 'BUICK', 'PARK AVENUE': 'BUICK', 'LACROSSE': 'BUICK',
        'ENCORE': 'BUICK', 'ENCLAVE': 'BUICK', 'ENVISION': 'BUICK',
        'VERANO': 'BUICK', 'RENDEZVOUS': 'BUICK', 'TERRAZA': 'BUICK',
        'RAINIER': 'BUICK', 'LUCERNE': 'BUICK', 'CENTURY': 'BUICK',
        # Oldsmobile
        'CUTLASS SUPREME': 'OLDSMOBILE', 'DELTA 88': 'OLDSMOBILE',
        'TORONADO': 'OLDSMOBILE', 'ALERO': 'OLDSMOBILE', 'INTRIGUE': 'OLDSMOBILE',
        # Cadillac
        'DEVILLE': 'CADILLAC', 'ELDORADO': 'CADILLAC', 'SEVILLE': 'CADILLAC',
        'ESCALADE': 'CADILLAC', 'CTS': 'CADILLAC', 'STS': 'CADILLAC',
        # Lincoln
        'TOWN CAR': 'LINCOLN', 'CONTINENTAL': 'LINCOLN', 'NAVIGATOR': 'LINCOLN',
        'MKZ': 'LINCOLN', 'MKX': 'LINCOLN', 'AVIATOR': 'LINCOLN',
        # Mercury
        'GRAND MARQUIS': 'MERCURY', 'COUGAR': 'MERCURY', 'MYSTIQUE': 'MERCURY',
        'MOUNTAINEER': 'MERCURY', 'VILLAGER': 'MERCURY', 'TRACER': 'MERCURY',
        # Isuzu
        'TROOPER': 'ISUZU', 'RODEO': 'ISUZU', 'AMIGO': 'ISUZU',
        'HOMBRE': 'ISUZU', 'AXIOM': 'ISUZU', 'ASCENDER': 'ISUZU',

        # ============ MODELOS AGREGADOS EN CORRECCIÓN EXHAUSTIVA ============

        # AUDI - TODOS los modelos encontrados
        'A1': 'AUDI', 'A3': 'AUDI', 'A4': 'AUDI', 'A5': 'AUDI', 'A6': 'AUDI',
        'A7': 'AUDI', 'A8': 'AUDI', 'Q3': 'AUDI', 'Q5': 'AUDI', 'Q7': 'AUDI',
        'Q8': 'AUDI', 'TT': 'AUDI', 'R8': 'AUDI', 'S3': 'AUDI', 'S4': 'AUDI',
        'RS3': 'AUDI', 'RS4': 'AUDI', 'RS6': 'AUDI',

        # BMW - TODOS los modelos encontrados
        '318I': 'BMW', '320I': 'BMW', '323I': 'BMW', '325I': 'BMW', '328I': 'BMW',
        '330I': 'BMW', '335I': 'BMW', '340I': 'BMW', '328IS': 'BMW', '323TI': 'BMW',
        '330CI': 'BMW', '520I': 'BMW', '525I': 'BMW', '528I': 'BMW', '530I': 'BMW',
        '535I': 'BMW', '540I': 'BMW', '550I': 'BMW', '125I': 'BMW', '128I': 'BMW',
        'X1': 'BMW', 'X3': 'BMW', 'X5': 'BMW', 'X6': 'BMW', 'X7': 'BMW',
        'Z3': 'BMW', 'Z4': 'BMW', 'M3': 'BMW', 'M5': 'BMW', 'M6': 'BMW',
        'SERIE 3': 'BMW', 'SERIE 5': 'BMW', 'SERIE 7': 'BMW',

        # VOLVO - TODOS los modelos encontrados
        'C30': 'VOLVO', 'C70': 'VOLVO', 'S40': 'VOLVO', 'S60': 'VOLVO', 'S80': 'VOLVO',
        'V40': 'VOLVO', 'V50': 'VOLVO', 'V60': 'VOLVO', 'V70': 'VOLVO',
        'XC60': 'VOLVO', 'XC90': 'VOLVO', 'XC40': 'VOLVO',
        '240': 'VOLVO', '740': 'VOLVO', '850': 'VOLVO', '940': 'VOLVO', '960': 'VOLVO',
        'VNL': 'VOLVO', 'VNM': 'VOLVO',  # Camiones Volvo

        # SEAT - TODOS los modelos encontrados
        'IBIZA': 'SEAT', 'LEON': 'SEAT', 'CORDOBA': 'SEAT', 'TOLEDO': 'SEAT',
        'ALTEA': 'SEAT', 'ALHAMBRA': 'SEAT', 'ATECA': 'SEAT', 'ARONA': 'SEAT',

        # PEUGEOT - TODOS los modelos encontrados
        '206': 'PEUGEOT', '207': 'PEUGEOT', '208': 'PEUGEOT', '301': 'PEUGEOT',
        '307': 'PEUGEOT', '308': 'PEUGEOT', '406': 'PEUGEOT', '407': 'PEUGEOT',
        '508': 'PEUGEOT', '2008': 'PEUGEOT', '3008': 'PEUGEOT', '5008': 'PEUGEOT',
        'PARTNER': 'PEUGEOT', 'BOXER': 'PEUGEOT', 'MANAGER': 'PEUGEOT',
        'EXPERT': 'PEUGEOT',

        # ACURA - TODOS los modelos encontrados
        'TL': 'ACURA', 'TSX': 'ACURA', 'MDX': 'ACURA', 'RDX': 'ACURA',
        'ILX': 'ACURA', 'TLX': 'ACURA', 'RSX': 'ACURA', 'INTEGRA': 'ACURA',
        'CL': 'ACURA', 'RL': 'ACURA', 'LEGEND': 'ACURA', 'NSX': 'ACURA',
        'EL': 'ACURA', 'ZDX': 'ACURA',

        # LEXUS - TODOS los modelos encontrados
        'IS250': 'LEXUS', 'IS350': 'LEXUS', 'ES350': 'LEXUS', 'GS350': 'LEXUS',
        'GS400': 'LEXUS', 'LS430': 'LEXUS', 'LS460': 'LEXUS',
        'RX350': 'LEXUS', 'RX400': 'LEXUS', 'NX200': 'LEXUS', 'NX300': 'LEXUS',
        'LX570': 'LEXUS', 'LX-570': 'LEXUS', 'LX': 'LEXUS', 'ES': 'LEXUS', 'GX': 'LEXUS',
        'SC300': 'LEXUS', 'SC400': 'LEXUS',

        # INFINITI - TODOS los modelos encontrados
        'G35': 'INFINITI', 'G37': 'INFINITI', 'G20': 'INFINITI',
        'Q45': 'INFINITI', 'Q50': 'INFINITI', 'Q60': 'INFINITI',
        'QX4': 'INFINITI', 'QX56': 'INFINITI', 'QX60': 'INFINITI', 'QX80': 'INFINITI',
        'FX35': 'INFINITI', 'FX45': 'INFINITI', 'FX30': 'INFINITI',
        'I30': 'INFINITI', 'I35': 'INFINITI', 'J30': 'INFINITI', 'M30': 'INFINITI',

        # SATURN - TODOS los modelos encontrados
        'VUE': 'SATURN', 'ION': 'SATURN', 'AURA': 'SATURN', 'OUTLOOK': 'SATURN',
        'RELAY': 'SATURN', 'SC': 'SATURN', 'SL': 'SATURN', 'SW': 'SATURN',

        # GEO - TODOS los modelos encontrados
        'METRO': 'GEO', 'PRIZM': 'GEO', 'STORM': 'GEO',
        # TRACKER ya está como CHEVROLET

        # PLYMOUTH - TODOS los modelos encontrados
        'DUSTER': 'PLYMOUTH', 'BREEZE': 'PLYMOUTH', 'ACCLAIM': 'PLYMOUTH',
        'SUNDANCE': 'PLYMOUTH', 'HORIZON': 'PLYMOUTH', 'RELIANT': 'PLYMOUTH',
        'NEON': 'PLYMOUTH', 'PROWLER': 'PLYMOUTH',
        # VOYAGER ya está como DODGE

        # FIAT adicionales
        'ALBEA': 'FIAT', 'IDEA': 'FIAT', 'PUNTO': 'FIAT', 'LINEA': 'FIAT',
        '500L': 'FIAT', 'PANDA': 'FIAT',

        # MITSUBISHI - Modelos faltantes importantes
        'MONTERO': 'MITSUBISHI', 'ECLIPSE': 'MITSUBISHI', 'LANCER': 'MITSUBISHI',
        'OUTLANDER': 'MITSUBISHI', 'GALANT': 'MITSUBISHI', 'MIRAGE': 'MITSUBISHI',
        'L200': 'MITSUBISHI', 'ENDEAVOR': 'MITSUBISHI', 'RAIDER': 'MITSUBISHI',
        'DIAMANTE': 'MITSUBISHI', '3000GT': 'MITSUBISHI',

        # MAZDA adicionales
        'B2000': 'MAZDA', 'B2300': 'MAZDA', 'B3000': 'MAZDA', 'B4000': 'MAZDA',
        'TRIBUTE': 'MAZDA', 'NAVAJO': 'MAZDA', 'MPV': 'MAZDA', 'PROTEGE': 'MAZDA',
        '626': 'MAZDA', '929': 'MAZDA', 'RX7': 'MAZDA', 'RX8': 'MAZDA',
        'CX-7': 'MAZDA', 'CX7': 'MAZDA',

        # SUBARU - TODOS los modelos encontrados
        'OUTBACK': 'SUBARU', 'FORESTER': 'SUBARU', 'IMPREZA': 'SUBARU',
        'LEGACY': 'SUBARU', 'WRX': 'SUBARU', 'CROSSTREK': 'SUBARU',
        'B9': 'SUBARU', 'TRIBECA': 'SUBARU', 'BAJA': 'SUBARU',

        # PONTIAC adicionales - Modelos faltantes
        'G3': 'PONTIAC', 'G4': 'PONTIAC', 'G5': 'PONTIAC', 'G6': 'PONTIAC',
        'G8': 'PONTIAC', 'VIBE': 'PONTIAC', 'SOLSTICE': 'PONTIAC',
        'AZTEK': 'PONTIAC', 'MONTANA': 'PONTIAC', 'TORRENT': 'PONTIAC',

        # CHRYSLER adicionales
        'CIRRUS': 'CHRYSLER', 'CONCORDE': 'CHRYSLER', 'LHS': 'CHRYSLER',
        'INTREPID': 'DODGE', 'SHADOW': 'DODGE', 'SPIRIT': 'DODGE',
        '200': 'CHRYSLER', 'ASPEN': 'DODGE',

        # FORD adicionales - Modelos faltantes
        'F150': 'FORD', 'F450': 'FORD', 'F550': 'FORD',  # Sin guión
        'AEROSTAR': 'FORD', 'TRANSIT': 'FORD', 'TRANSIT CONNECT': 'FORD',
        'TRITON': 'FORD', 'GALAXIE': 'FORD', 'FAIRLANE': 'FORD',
        'TORINO': 'FORD', 'GRAN TORINO': 'FORD', 'RANCHERO': 'FORD',
        'FLEX': 'FORD', 'EXCURSION': 'FORD', 'E150': 'FORD', 'E250': 'FORD',

        # CHEVROLET adicionales - Modelos faltantes
        'C1500': 'CHEVROLET', 'C2500': 'CHEVROLET', 'C3500': 'CHEVROLET',
        'K1500': 'CHEVROLET', 'K2500': 'CHEVROLET', 'K3500': 'CHEVROLET',
        'R1500': 'CHEVROLET', 'R2500': 'CHEVROLET', 'R3500': 'CHEVROLET',
        'AVALANCHE': 'CHEVROLET', 'SSR': 'CHEVROLET', 'EL CAMINO': 'CHEVROLET',
        'C2': 'CHEVROLET', 'C3': 'CHEVROLET',  # Chevy C2, C3

        # NISSAN adicionales
        'X-TRAIL': 'NISSAN', 'XTRAIL': 'NISSAN', 'QUEST': 'NISSAN',
        'ARMADA': 'NISSAN', 'ROGUE': 'NISSAN', 'ALMERA': 'NISSAN',
        '350Z': 'NISSAN', '370Z': 'NISSAN', 'Z': 'NISSAN',

        # TOYOTA adicionales
        'HIACE': 'TOYOTA', 'AVANZA': 'TOYOTA', 'LAND CRUISER': 'TOYOTA',
        'SEQUOIA': 'TOYOTA', 'FJ CRUISER': 'TOYOTA', 'MATRIX': 'TOYOTA',
        'SUPRA': 'TOYOTA', 'MR2': 'TOYOTA', 'TERCEL': 'TOYOTA',
        'PREVIA': 'TOYOTA', 'T100': 'TOYOTA',

        # HONDA adicionales
        'CRV': 'HONDA', 'HRV': 'HONDA',  # Sin guión
        'PASSPORT': 'HONDA', 'ELEMENT': 'HONDA', 'RIDGELINE': 'HONDA',
        'INSIGHT': 'HONDA', 'S2000': 'HONDA', 'PRELUDE': 'HONDA',
        'DEL SOL': 'HONDA',

        # HYUNDAI adicionales
        'H100': 'HYUNDAI', 'STAREX': 'HYUNDAI', 'CRETA': 'HYUNDAI', 'CRETAS': 'HYUNDAI',
        'PALISADE': 'HYUNDAI', 'VENUE': 'HYUNDAI', 'KONA': 'HYUNDAI',
        'GENESIS': 'HYUNDAI', 'AZERA': 'HYUNDAI', 'VERACRUZ': 'HYUNDAI',
        'ENTOURAGE': 'HYUNDAI', 'XG350': 'HYUNDAI',

        # DODGE adicionales
        'H100': 'DODGE',  # Algunos H100 son Dodge

        # MINI
        'COOPER': 'MINI', 'COUNTRYMAN': 'MINI', 'CLUBMAN': 'MINI',
        'PACEMAN': 'MINI',

        # MERCURY adicionales
        'MARINER': 'MERCURY', 'MILAN': 'MERCURY', 'MONTEGO': 'MERCURY',

        # LINCOLN adicionales
        'MARK': 'LINCOLN', 'LS': 'LINCOLN', 'ZEPHYR': 'LINCOLN',

        # CADILLAC adicionales
        'SRX': 'CADILLAC', 'XTS': 'CADILLAC', 'ATS': 'CADILLAC',
        'XT5': 'CADILLAC', 'XT4': 'CADILLAC', 'CT6': 'CADILLAC',

        # ============ MODELOS AGREGADOS EN VERIFICACION 100% ============

        # GMC adicionales
        'TERRAIN': 'GMC', 'CANYON': 'GMC', 'ACADIA': 'GMC',
        'JIMMY': 'GMC', 'SONOMA': 'GMC', 'ENVOY': 'GMC',
        'BRAVADA': 'OLDSMOBILE',  # Oldsmobile Bravada
        'SAVEIRO': 'VOLKSWAGEN',  # VW Saveiro (pickup)

        # JEEP adicionales
        'COMMANDER': 'JEEP', 'COMANDER': 'JEEP',  # Typo comun
        'COMANCHE': 'JEEP',

        # CHEVROLET adicionales fase 2
        'CORSICA': 'CHEVROLET', 'MONTECARLO': 'CHEVROLET',
        'KODIAK': 'CHEVROLET', 'P30': 'CHEVROLET',
        'C15': 'CHEVROLET', 'C35': 'CHEVROLET',
        'K15': 'CHEVROLET', 'K35': 'CHEVROLET',

        # FORD adicionales fase 2
        'TEMPO': 'FORD', 'PROBE': 'FORD',
        'FIGO': 'FORD',
        'CROWN VICTORIA': 'FORD',  # Ya existe pero refuerzo

        # DODGE adicionales fase 2
        'LEBARON': 'CHRYSLER', 'LE BARON': 'CHRYSLER',
        'NEW YORKER': 'CHRYSLER', 'CONCORD': 'CHRYSLER',
        'VOLARE': 'CHRYSLER',
        'D150': 'DODGE', 'D250': 'DODGE',
        'B150': 'DODGE', 'B250': 'DODGE',
        'RAM WAGON': 'DODGE',
        'PROMASTER': 'DODGE',  # RAM ProMaster

        # NISSAN adicionales fase 2
        'LUCINO': 'NISSAN', 'DATSUN 1600': 'NISSAN',
        'CUBE': 'NISSAN', 'LEAF': 'NISSAN',
        'SCALA': 'NISSAN',
        'D22': 'NISSAN',

        # TOYOTA adicionales fase 2
        'CORONA': 'TOYOTA', '4 RUNNER': 'TOYOTA', '4RUNNER': 'TOYOTA',
        'AVALON': 'TOYOTA',

        # HONDA adicionales fase 2
        'CRX': 'HONDA',

        # RENAULT adicionales fase 2
        'SCENIC': 'RENAULT', 'LAGUNA': 'RENAULT',
        'CAPTUR': 'RENAULT', 'OROCH': 'RENAULT',
        'KWID': 'RENAULT',

        # VOLKSWAGEN adicionales fase 2
        'DERBY': 'VOLKSWAGEN', 'EUROVAN': 'VOLKSWAGEN',
        'GTI': 'VOLKSWAGEN',  # Golf GTI
        'CLASICO': 'VOLKSWAGEN', 'CLASSIC': 'VOLKSWAGEN',

        # PEUGEOT adicionales fase 2
        'RCZ': 'PEUGEOT',

        # FIAT adicionales fase 2
        'ADVENTURE': 'FIAT',  # Fiat Palio Adventure

        # PONTIAC adicionales fase 2
        'PRIX': 'PONTIAC',  # Grand Prix (cuando "GRAND" ya se consumio)
        'SUNBIRD': 'PONTIAC',

        # HYUNDAI adicionales fase 2
        'SANTA FE': 'HYUNDAI',  # Ya existe pero refuerzo

        # ISUZU adicionales fase 2
        'ELF': 'ISUZU', 'NPR': 'ISUZU', 'NHR': 'ISUZU', 'NQR': 'ISUZU',

        # CHRYSLER adicionales fase 2
        'PACIFICA': 'CHRYSLER',
        'TOWN COUNTRY': 'CHRYSLER',  # Town & Country sin &
        'TOWN AND COUNTRY': 'CHRYSLER',

        # FORD adicionales fase 2 - variantes
        'MARQUIS': 'FORD',  # Grand Marquis
        'T-BIRD': 'FORD',  # Thunderbird abreviado

        # CHEVROLET - typos y variantes comunes
        'SILERADO': 'CHEVROLET',  # Typo Silverado

        # PLYMOUTH - typos comunes
        'BREZZE': 'PLYMOUTH',  # Typo de BREEZE

        # VOLKSWAGEN adicional
        'SHARAN': 'VOLKSWAGEN',

        # HINO (Camiones)
        'SERIE 500': 'HINO', 'SERIE 300': 'HINO', 'DUTRO': 'HINO',

        # INTERNATIONAL (Camiones)
        'PROSTAR': 'INTERNATIONAL', 'DURASTAR': 'INTERNATIONAL',
        'WORKSTAR': 'INTERNATIONAL', 'LONESTAR': 'INTERNATIONAL',
        '4300': 'INTERNATIONAL', '4400': 'INTERNATIONAL', '4700': 'INTERNATIONAL',

        # FREIGHTLINER (Camiones)
        'CASCADIA': 'FREIGHTLINER', 'COLUMBIA': 'FREIGHTLINER',
        'CENTURY': 'FREIGHTLINER', 'M2': 'FREIGHTLINER',
        'FL70': 'FREIGHTLINER', 'FL60': 'FREIGHTLINER', 'FL50': 'FREIGHTLINER',
        'FL360': 'FREIGHTLINER', 'FC70': 'FREIGHTLINER',
        '114SD': 'FREIGHTLINER', '108SD': 'FREIGHTLINER',
        'SPRINTER': 'FREIGHTLINER',

        # KENWORTH (Camiones)
        'T680': 'KENWORTH', 'T880': 'KENWORTH', 'T800': 'KENWORTH',
        'T660': 'KENWORTH', 'T600': 'KENWORTH', 'T2000': 'KENWORTH',
        'T300': 'KENWORTH', 'W900': 'KENWORTH',

        # PETERBILT (Camiones)
        '579': 'PETERBILT', '389': 'PETERBILT', '379': 'PETERBILT',
        '567': 'PETERBILT', '365': 'PETERBILT',

        # MACK (Camiones)
        'GRANITE': 'MACK', 'PINNACLE': 'MACK', 'ANTHEM': 'MACK',
        'CHU': 'MACK', 'CH': 'MACK',
    }

    # Tipos de productos
    TIPOS_PRODUCTO = [
        'FILTRO', 'BUJIA', 'BALATA', 'DISCO', 'BANDA', 'BOMBA', 'SENSOR',
        'BOBINA', 'INYECTOR', 'VALVULA', 'EMPAQUE', 'MANGUERA', 'TERMOSTATO',
        'AMORTIGUADOR', 'ROTULA', 'TERMINAL', 'BUJE', 'HORQUILLA', 'MAZA',
        'BALERO', 'CLUTCH', 'ALTERNADOR', 'MARCHA', 'RADIADOR', 'CONDENSADOR',
        'COMPRESOR', 'CABLE', 'TAPON', 'DEPOSITO', 'TOMA', 'POLEA', 'TENSOR',
        'CADENA', 'ENGRANE', 'ANILLO', 'METAL', 'PISTON', 'BIELA', 'CIGUEÑAL',
        'ARBOL', 'LEVA', 'RETEN', 'JUNTA', 'SELLO', 'BARRA', 'BRAZO', 'TORNILLO',
        'SILVIN', 'FARO', 'CALAVERA', 'ESPEJO', 'DEFENSA', 'COFRE', 'PUERTA',
        # Productos sin compatibilidad (llantas, aceites, acumuladores, etc.)
        'LLANTA', 'NEUMATICO', 'ACEITE', 'ACUMULADOR', 'BATERIA',
        'ANTICONGELANTE', 'REFRIGERANTE', 'LIQUIDO', 'ADITIVO',
        'GRASA', 'SILICON', 'LIJA', 'BOCINA', 'HERRAMIENTA',
        'KIT', 'DIAFRAGMA', 'SOPORTE', 'BASE', 'CUBREPOLVO',
        'CRUCETA', 'FLECHA', 'RESORTE', 'ABRAZADERA', 'FORRO',
        'ROTOR', 'TAMBOR', 'CILINDRO', 'TUBO', 'ESCAPE',
        'DIRECCION', 'CREMALLERA', 'MODULO', 'RELAY', 'RELEVADOR',
        'BULBO', 'SWITCH', 'INTERRUPTOR', 'TAPICERIA', 'MOLDURA',
    ]

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea una descripción y extrae la información estructurada"""
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

        # Extraer compatibilidades
        resultado.compatibilidades = self.extraer_compatibilidades(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def extraer_skus_alternos(self, descripcion: str) -> List[str]:
        """Extrae los SKUs alternos del inicio de la descripción"""
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            skus_str = match.group(1)
            return [sku.strip() for sku in skus_str.split('/') if sku.strip()]
        return []

    def extraer_tipo_producto(self, descripcion: str) -> str:
        """Extrae el tipo de producto"""
        descripcion_upper = descripcion.upper()
        for tipo in self.TIPOS_PRODUCTO:
            if tipo in descripcion_upper:
                return tipo
        return ""

    def extraer_nombre_producto(self, descripcion: str) -> str:
        """Extrae el nombre del producto"""
        # Remover SKUs alternos del inicio
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            descripcion = descripcion[match.end():]

        # Buscar hasta el primer modelo/marca de vehículo o año
        # El nombre suele estar entre los SKUs y las compatibilidades
        for marca in list(self.MARCAS_VEHICULO.keys()) + list(self.MODELOS_CONOCIDOS.keys()):
            idx = descripcion.upper().find(f' {marca} ')
            if idx > 0:
                return descripcion[:idx].strip()

        # Si no encontramos marca, buscar el primer año
        match_año = self.PATRON_AÑOS.search(descripcion)
        if match_año:
            return descripcion[:match_año.start()].strip()

        return descripcion[:50] if len(descripcion) > 50 else descripcion

    # ================================================================
    # PIPELINE DE LIMPIEZA DE NOMBRE DE PRODUCTO
    # ================================================================

    def limpiar_nombre_producto(self, descripcion: str, marca_producto: str = '', departamento: str = '') -> str:
        """Limpia y extrae el nombre del producto de la descripcion.

        Pipeline:
        1. Strip SKUs del inicio (iterativo)
        2. Si es llanta: manejo especial (medidas al final)
        3. Si es autoparte: strip info vehicular (marcas, modelos, anos, motor)
        4. Limpieza final
        """
        if not descripcion:
            return ""

        descripcion = descripcion.strip()
        dept_upper = departamento.upper() if departamento else ''
        es_llanta = dept_upper == 'LLANTAS'
        # Departamentos que NO tienen compatibilidad vehicular
        es_sin_compat = dept_upper in (
            'LLANTAS', 'LUBRICACIÓN', 'LUBRICACION',
            'QUIMICOS,ADITIVOS,AGUA PARA BATERIA,EMBE',
            'HERREMIENTA Y EQUIPOS', 'SERVICIOS TALLER',
        )

        # Fase 1: Strip SKUs del inicio
        nombre = self._limpiar_skus_inicio_nombre(descripcion)

        # Fase 2: Llantas - manejo especial
        if es_llanta:
            return self._limpiar_nombre_llanta(nombre, descripcion)

        # Fase 3: Strip info vehicular (solo para autopartes con compatibilidad)
        if not es_sin_compat:
            nombre = self._strip_vehicle_info(nombre, marca_producto)

        # Fase 4: Limpieza final
        nombre = self._limpieza_final_nombre(nombre)

        return nombre

    def _limpiar_skus_inicio_nombre(self, descripcion: str) -> str:
        """Strip iterativo de SKUs/codigos del inicio de la descripcion.

        Remueve tokens alfanumericos del inicio hasta encontrar una
        palabra de producto (FILTRO, BANDA, MANGUERA, etc.) o una
        palabra comun en espanol (3+ letras consecutivas).
        """
        original = descripcion

        # Paso 1: Strip slash-separated SKUs (BKR5EGP/AP3924/7090 BUJIA...)
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            descripcion = descripcion[match.end():].strip()

        # Paso 2: Iterar removiendo tokens de codigo del inicio
        for _ in range(5):
            if self._starts_with_product_word(descripcion):
                break

            # Intentar remover un token alfanumerico seguido de espacio
            match_token = re.match(r'^[A-Z0-9\.\-/]+\s+', descripcion, re.IGNORECASE)
            if match_token:
                candidate = descripcion[match_token.end():].strip()
                if candidate and len(candidate) > 5:
                    descripcion = candidate
                else:
                    break
            else:
                break

        return descripcion if descripcion else original

    def _starts_with_product_word(self, text: str) -> bool:
        """Retorna True si el texto empieza con un tipo de producto conocido
        o con una palabra en espanol (3+ letras, no un codigo)."""
        text_upper = text.upper().strip()

        # Checar contra tipos de producto conocidos
        for tipo in self.TIPOS_PRODUCTO:
            if text_upper.startswith(tipo):
                return True

        # Checar si empieza con 3+ letras consecutivas (palabra, no codigo)
        match = re.match(r'^[A-ZÁÉÍÓÚÑÜ]{3,}', text_upper)
        if match:
            word = match.group(0)
            # Excluir patrones tipo codigo: letras seguidas de digitos (G1502H, R19, B14)
            full_token = re.match(r'^[A-Z0-9]+', text_upper)
            if full_token:
                token = full_token.group(0)
                # Si el token tiene digitos mezclados, es codigo
                if re.search(r'[A-Z]\d|\d[A-Z]', token):
                    return False
            return True

        return False

    def _strip_vehicle_info(self, nombre: str, marca_producto: str = '') -> str:
        """Elimina marcas de vehiculo, modelos, anos y motores del nombre.

        Preserva la marca del fabricante del producto (ej: CONTINENTAL como
        marca de mangueras no se elimina aunque sea modelo Lincoln).
        """
        nombre_upper = nombre.upper()
        marca_prod_upper = marca_producto.upper().strip() if marca_producto else ''

        earliest_cut = len(nombre)

        # Buscar marcas de vehiculo
        for marca_text in self.MARCAS_VEHICULO.keys():
            if marca_prod_upper and marca_text == marca_prod_upper:
                continue
            # Buscar con espacio antes y despues
            idx = nombre_upper.find(f' {marca_text} ')
            if idx > 0 and idx < earliest_cut:
                earliest_cut = idx
            # Tambien al final del string
            if nombre_upper.endswith(f' {marca_text}'):
                idx = len(nombre) - len(marca_text) - 1
                if idx > 0 and idx < earliest_cut:
                    earliest_cut = idx

        # Buscar modelos de vehiculo
        for modelo in self.MODELOS_CONOCIDOS.keys():
            if len(modelo) <= 2:
                continue
            # Skip si es la marca del producto
            if marca_prod_upper and modelo == marca_prod_upper:
                continue
            idx = nombre_upper.find(f' {modelo} ')
            if idx > 0 and idx < earliest_cut:
                earliest_cut = idx
            if nombre_upper.endswith(f' {modelo}'):
                idx = len(nombre) - len(modelo) - 1
                if idx > 0 and idx < earliest_cut:
                    earliest_cut = idx

        # Buscar patrones de anos (01/06, 2015-2020)
        match_year = re.search(r'\s+\d{2,4}[/-]\d{2,4}', nombre)
        if match_year and match_year.start() < earliest_cut:
            earliest_cut = match_year.start()

        # Buscar patrones de motor (2.0L, 5.3L, 1.6L, 16V)
        match_motor = re.search(r'\s+\d+\.?\d*\s*[Ll](?:T|ITROS?)?\b', nombre)
        if match_motor and match_motor.start() < earliest_cut:
            earliest_cut = match_motor.start()

        result = nombre[:earliest_cut].strip()

        # Safety: resultado debe tener al menos 5 chars
        if len(result) < 5:
            return nombre.strip()

        return result

    def _limpiar_nombre_llanta(self, nombre: str, descripcion_original: str = '') -> str:
        """Manejo especial para nombres de llantas.

        Extrae dimensiones y las coloca al final del nombre.
        Input:  "235/55 R19 105H LLANTA CONTINENTAL CROSSCONTACT LX SPORT"
        Output: "LLANTA CONTINENTAL CROSSCONTACT LX SPORT 235/55 R19"
        """
        # Extraer dimension de la descripcion original (tiene mas info)
        src = descripcion_original or nombre
        dimension_str = ""

        # Patron radial: 235/55 R19
        match_radial = re.search(r'(\d{3})/(\d{2})\s*R\s*(\d{2})', src, re.IGNORECASE)
        if match_radial:
            dimension_str = f"{match_radial.group(1)}/{match_radial.group(2)} R{match_radial.group(3)}"
        else:
            # Patron LT: 31X10.5 R15
            match_lt = re.search(r'(\d{2,3})X(\d+\.?\d*)\s*R\s*(\d{2})', src, re.IGNORECASE)
            if match_lt:
                dimension_str = f"{match_lt.group(1)}X{match_lt.group(2)} R{match_lt.group(3)}"

        # Buscar inicio del nombre real (LLANTA, NEUMATICO o marca)
        nombre_limpio = nombre
        for keyword in ['LLANTA', 'NEUMATICO']:
            idx = nombre.upper().find(keyword)
            if idx >= 0:
                nombre_limpio = nombre[idx:]
                break
        else:
            # Si no encontramos tipo, al menos strip codigos
            nombre_limpio = self._limpiar_skus_inicio_nombre(nombre)

        # Remover codigos de carga/velocidad (105H, 91V, 94W, etc.)
        nombre_limpio = re.sub(r'\b\d{2,3}[A-Z]{1,2}\b', '', nombre_limpio)

        # Remover dimensiones embebidas
        nombre_limpio = re.sub(r'\d{3}/\d{2}\s*R\s*\d{2}', '', nombre_limpio)
        nombre_limpio = re.sub(r'\d{2,3}X\d+\.?\d*\s*R\s*\d{2}', '', nombre_limpio)

        # Remover capas (6C, 8C, 10C)
        nombre_limpio = re.sub(r'\b\d{1,2}C\b', '', nombre_limpio)

        # Limpiar espacios multiples
        nombre_limpio = re.sub(r'\s{2,}', ' ', nombre_limpio).strip()

        # Agregar dimension al final
        if dimension_str and dimension_str not in nombre_limpio:
            nombre_limpio = f"{nombre_limpio} {dimension_str}"

        return nombre_limpio

    def _limpieza_final_nombre(self, nombre: str) -> str:
        """Limpieza final del nombre: trailing basura, longitud, etc."""
        # Strip trailing commas, periods, dashes, slashes
        nombre = nombre.strip(' ,.-/')

        # Remover "S.P." y "TENEMOS EN FRAM/etc" (notas internas de Gonher/etc)
        nombre = re.sub(r'\s*S\.?P\.?\s*TENEMOS\s+EN\s+\w+.*$', '', nombre, flags=re.IGNORECASE)
        nombre = re.sub(r'\s+S\.?P\.?\s*$', '', nombre, flags=re.IGNORECASE)
        nombre = re.sub(r'\s+TENEMOS\s+EN\s+\w+.*$', '', nombre, flags=re.IGNORECASE)

        # Remover medidas de manguera tipo "14X51X609 / 1 3/4 X 2 X 19"
        nombre = re.sub(r'\s+\d+X\d+X\d+.*$', '', nombre)

        # Remover "C/DM" "SIN/AA" "C/AC" "S/AC" al final
        nombre = re.sub(r'\s+[CS]/(?:DM|AA|AC)\s*$', '', nombre, flags=re.IGNORECASE)

        # Remover "TODOS" suelto al final
        nombre = re.sub(r'\s+TODOS\s*$', '', nombre, flags=re.IGNORECASE)

        # Colapsar espacios multiples
        nombre = re.sub(r'\s{2,}', ' ', nombre).strip()

        # Strip trailing commas again after cleanup
        nombre = nombre.strip(' ,.-/')

        # Cap longitud a 120 chars
        if len(nombre) > 120:
            nombre = nombre[:120].rsplit(' ', 1)[0]

        return nombre

    def extraer_compatibilidades(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae las compatibilidades del producto.

        Usa primero el método por segmentos (para descripciones con múltiples
        vehículos separados por coma), y si no encuentra nada, usa el método legacy.
        """
        # Intentar primero con segmentos (nuevo método - más preciso)
        compatibilidades = self._extraer_compatibilidades_por_segmentos(descripcion)

        # Si encontró algo, eliminar duplicados y retornar
        if compatibilidades:
            return self._eliminar_duplicados(compatibilidades)

        # Fallback al método legacy
        compatibilidades = self._extraer_compatibilidades_legacy(descripcion)
        return self._eliminar_duplicados(compatibilidades)

    def _eliminar_duplicados(self, compatibilidades: List[Compatibilidad]) -> List[Compatibilidad]:
        """Elimina compatibilidades duplicadas manteniendo la más completa.

        Una compatibilidad es duplicada si tiene la misma marca+modelo+años.
        Si hay dos con el mismo modelo pero una tiene más información (motor),
        se mantiene la más completa.
        """
        if not compatibilidades:
            return compatibilidades

        # Usar diccionario para agrupar por clave única
        unicos = {}
        for compat in compatibilidades:
            # Clave: marca + modelo + años
            clave = (
                compat.marca_vehiculo or '',
                compat.modelo_vehiculo or '',
                compat.año_inicio,
                compat.año_fin
            )

            if clave in unicos:
                # Ya existe, mantener el que tenga más información
                existente = unicos[clave]
                # Contar campos no vacíos
                info_existente = sum([
                    bool(existente.motor),
                    bool(existente.cilindros),
                    bool(existente.especificacion)
                ])
                info_nueva = sum([
                    bool(compat.motor),
                    bool(compat.cilindros),
                    bool(compat.especificacion)
                ])
                if info_nueva > info_existente:
                    unicos[clave] = compat
            else:
                unicos[clave] = compat

        return list(unicos.values())

    def _extraer_compatibilidades_por_segmentos(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades dividiendo la descripción por comas/separadores.

        Esto resuelve el problema de descripciones como:
        "AVEO 1.6L 05/15,ASTRA 1.8 2.0L 00/04,MERIVA 1.8L 04/06"
        donde el método legacy solo extraía AVEO para todos.

        Separadores reconocidos: coma, punto y coma, " Y ", " y ", " & "
        NO divide comas dentro de paréntesis.

        MEJORAS:
        - FASE 2: Divide modelos separados por guión (DART-VALIANT)
        - FASE 3: Acepta compatibilidades sin años
        - FASE 4: Filtra falsos positivos (300 en MH-300, etc.)
        """
        compatibilidades = []

        # Limpiar SKUs del inicio (antes del tipo de producto)
        descripcion_limpia = self._limpiar_skus_inicio(descripcion)

        # Primero, remover contenido entre paréntesis para evitar dividir por comas ahí
        # Ej: "(VENTA X PIEZA, CAJA CON 4 PIEZAS)" no debería dividirse
        descripcion_sin_parentesis = re.sub(r'\([^)]*\)', '', descripcion_limpia)

        # FASE 2: Expandir modelos separados por guión antes de dividir
        # Ej: "DART-VALIANT 73/82" → "DART,VALIANT 73/82"
        descripcion_expandida = self._expandir_modelos_guion(descripcion_sin_parentesis)

        # Dividir por TODOS los separadores comunes:
        # - Coma y punto y coma
        # - " Y " y " y " (con espacios para evitar cortar palabras)
        # - " & " (con espacios)
        segmentos = re.split(r'[,;]|\s+[Yy]\s+|\s*&\s*', descripcion_expandida)

        # Contexto para heredar marca Y años entre segmentos
        contexto_marca = None
        contexto_años = None  # (año_inicio, año_fin)

        for segmento in segmentos:
            segmento = segmento.strip()
            if not segmento or len(segmento) < 3:
                continue

            # Detectar múltiples modelos consecutivos separados por espacio
            # Patrón: "MODELO [cosa] AÑO/AÑO MODELO AÑO/AÑO"
            # Ej: "AVEO NG 18/23 BEAT 18/22"
            if self.PATRON_AÑOS.search(segmento):
                multi_compat = self._extraer_multiples_modelos_consecutivos(segmento)
                if multi_compat and len(multi_compat) > 1:
                    for mc in multi_compat:
                        if not mc.marca_vehiculo and contexto_marca:
                            mc.marca_vehiculo = contexto_marca
                        if mc.marca_vehiculo:
                            contexto_marca = mc.marca_vehiculo
                        if mc.año_inicio:
                            contexto_años = (mc.año_inicio, mc.año_fin)
                        # FASE 4: Filtrar falsos positivos
                        if not self._es_falso_positivo(mc.modelo_vehiculo, descripcion):
                            compatibilidades.append(mc)
                    continue

            # Extraer compatibilidades de este segmento individual
            # Puede devolver múltiples si hay varios modelos sin años
            compats_segmento = self._extraer_compats_de_segmento(segmento)

            for compat in compats_segmento:
                # Heredar marca del contexto si no se encontró en este segmento
                if not compat.marca_vehiculo and contexto_marca:
                    compat.marca_vehiculo = contexto_marca

                # FASE 3: Heredar años del contexto si no se encontraron
                if not compat.año_inicio and contexto_años:
                    compat.año_inicio, compat.año_fin = contexto_años

                # Guardar contexto para segmentos siguientes
                if compat.marca_vehiculo:
                    contexto_marca = compat.marca_vehiculo
                if compat.año_inicio:
                    contexto_años = (compat.año_inicio, compat.año_fin)

                # FASE 4: Filtrar falsos positivos
                if self._es_falso_positivo(compat.modelo_vehiculo, descripcion):
                    continue

                # Aceptar si tiene modelo O marca (con o sin años - FASE 3)
                if compat.modelo_vehiculo or compat.marca_vehiculo:
                    compatibilidades.append(compat)

        # FASE 3: Si no encontró nada con años, buscar modelos sin años
        if not compatibilidades:
            compatibilidades = self._extraer_compatibilidades_sin_años(descripcion_limpia)

        return compatibilidades

    def _expandir_modelos_guion(self, descripcion: str) -> str:
        """FASE 2: Expande modelos separados por guión.

        Ej: "DART-VALIANT V8 73/82" → "DART 73/82,VALIANT 73/82"
        Ej: "CELICA-CORONA-PICK UP 75/79" → "CELICA 75/79,CORONA 75/79,PICK UP 75/79"

        NO expande modelos que naturalmente tienen guión (CR-V, F-150, etc.)
        """
        resultado = descripcion

        # Buscar patrones MODELO-MODELO con texto intermedio hasta años
        # Patrón: palabra-palabra ... años (permite V8, motor, etc. en medio)
        patron_guion = re.compile(r'([A-Z]+)-([A-Z]+)(?:-([A-Z]+))?\s+.*?(\d{2}/\d{2})', re.IGNORECASE)

        for match in patron_guion.finditer(descripcion):
            modelo1 = match.group(1).upper()
            modelo2 = match.group(2).upper()
            modelo3 = match.group(3).upper() if match.group(3) else None
            años = match.group(4)

            # Verificar si ambos son modelos conocidos
            es_modelo1 = modelo1 in self.MODELOS_CONOCIDOS
            es_modelo2 = modelo2 in self.MODELOS_CONOCIDOS
            es_modelo3 = modelo3 in self.MODELOS_CONOCIDOS if modelo3 else False

            # No expandir si es un modelo conocido con guión
            modelo_completo = f"{modelo1}-{modelo2}"
            if modelo3:
                modelo_completo = f"{modelo1}-{modelo2}-{modelo3}"

            if modelo_completo.upper() in [m.upper() for m in self.MODELOS_CON_GUION]:
                continue

            # Expandir si al menos 2 son modelos conocidos
            if es_modelo1 and es_modelo2:
                # Obtener el contenido entre los modelos y los años
                texto_completo = match.group(0)
                idx_guion = texto_completo.upper().find(f"{modelo1}-{modelo2}")
                idx_años = texto_completo.find(años)
                texto_medio = texto_completo[len(f"{modelo1}-{modelo2}"):idx_años].strip()
                if modelo3:
                    texto_medio = texto_completo[len(f"{modelo1}-{modelo2}-{modelo3}"):idx_años].strip()

                nuevos = [f"{modelo1} {texto_medio} {años}".strip()]
                nuevos.append(f"{modelo2} {texto_medio} {años}".strip())
                if es_modelo3:
                    nuevos.append(f"{modelo3} {texto_medio} {años}".strip())

                reemplazo = ", ".join(nuevos)
                resultado = resultado[:match.start()] + reemplazo + resultado[match.end():]
                # Solo procesar el primero para evitar índices rotos
                break

        return resultado

    def _es_falso_positivo(self, modelo: str, descripcion: str) -> bool:
        """FASE 4: Detecta si un modelo es un falso positivo.

        Ej: "300" en "MH-300" no es Chrysler 300
        Ej: "1600" en "DATSUN 1600/1800/2000" es cilindrada, no modelo
        """
        if not modelo:
            return False

        if modelo in self.FALSOS_POSITIVOS_MODELOS:
            patron = self.FALSOS_POSITIVOS_MODELOS[modelo]
            if patron.search(descripcion):
                return True

        return False

    def _extraer_compatibilidades_sin_años(self, descripcion: str) -> List[Compatibilidad]:
        """FASE 3: Extrae compatibilidades cuando no hay patrón de años.

        Para productos "universales" o que aplican a todos los años del modelo.
        Ej: "CABLES DE BUJIA CARIBE TODOS MODELOS"
        """
        compatibilidades = []
        desc_upper = descripcion.upper()

        # Buscar TODOS los modelos mencionados (no solo uno)
        modelos_encontrados = []
        for modelo, marca in self.MODELOS_CONOCIDOS.items():
            if re.search(rf'\b{re.escape(modelo)}\b', desc_upper):
                # Verificar que no sea falso positivo
                if not self._es_falso_positivo(modelo, descripcion):
                    modelos_encontrados.append((modelo, marca))

        # Buscar TODAS las marcas mencionadas también
        marcas_encontradas = set()
        for marca_text, marca_norm in self.MARCAS_VEHICULO.items():
            if re.search(rf'\b{re.escape(marca_text)}\b', desc_upper):
                marcas_encontradas.add(marca_norm)

        # Crear compatibilidad para cada modelo encontrado (sin años)
        for modelo, marca in modelos_encontrados:
            compat = Compatibilidad()
            compat.modelo_vehiculo = modelo
            compat.marca_vehiculo = marca
            # año_inicio y año_fin quedan como None (todos los años)

            # Buscar motor si está presente
            motor_match = self.PATRON_MOTOR.search(descripcion)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            compatibilidades.append(compat)

        # Si encontramos marcas pero no modelos, crear compat solo con marca
        modelos_marcas = set(marca for _, marca in modelos_encontrados)
        for marca in marcas_encontradas:
            if marca not in modelos_marcas:
                compat = Compatibilidad()
                compat.marca_vehiculo = marca
                compatibilidades.append(compat)

        return compatibilidades

    def _extraer_multiples_modelos_consecutivos(self, segmento: str) -> List[Compatibilidad]:
        """Detecta múltiples modelos separados por espacio con sus años.

        Patrón: "MODELO [opcional] AÑO/AÑO MODELO AÑO/AÑO ..."
        Ejemplo: "AVEO NG 18/23 BEAT 18/22" → [AVEO 2018-2023, BEAT 2018-2022]
        """
        compatibilidades = []
        segmento_upper = segmento.upper()

        # Encontrar todos los rangos de años en el segmento
        años_matches = list(self.PATRON_AÑOS.finditer(segmento))
        if len(años_matches) < 2:
            return []  # Solo usar este método si hay 2+ rangos de años

        # Para cada rango de años, buscar el modelo que lo precede
        for i, match_año in enumerate(años_matches):
            # Validar que sea un año real
            año_str = match_año.group(0)
            if not self._es_año_valido(año_str, segmento):
                continue

            año_inicio = self._normalizar_año(match_año.group(1))
            año_fin = self._normalizar_año(match_año.group(2))

            # Validar rango
            if not (1950 <= año_inicio <= 2030 and 1950 <= año_fin <= 2030):
                continue

            # Corregir si está invertido
            if año_fin < año_inicio:
                año_inicio, año_fin = año_fin, año_inicio

            # Buscar el contexto antes de este rango de años
            # Si es el primer año, desde el inicio; si no, desde el año anterior
            if i == 0:
                inicio_contexto = 0
            else:
                inicio_contexto = años_matches[i-1].end()

            contexto = segmento[inicio_contexto:match_año.start()].strip()
            contexto_upper = contexto.upper()

            # Buscar modelo en este contexto
            modelo_encontrado = None
            marca_encontrada = None

            for modelo, marca in self.MODELOS_CONOCIDOS.items():
                if re.search(rf'\b{re.escape(modelo)}\b', contexto_upper):
                    modelo_encontrado = modelo
                    marca_encontrada = marca
                    break

            if modelo_encontrado:
                compat = Compatibilidad()
                compat.modelo_vehiculo = modelo_encontrado
                compat.marca_vehiculo = marca_encontrada
                compat.año_inicio = año_inicio
                compat.año_fin = año_fin

                # Buscar motor en el contexto
                motor_match = self.PATRON_MOTOR.search(contexto)
                if motor_match:
                    compat.motor = f"{motor_match.group(1)}L"

                compatibilidades.append(compat)

        return compatibilidades

    def _es_año_valido(self, año_str: str, contexto: str) -> bool:
        """Valida que el patrón de año sea realmente un año y no parte de un SKU.

        Ejemplos de falsos positivos a rechazar:
        - "ARE/140" → el "ARE" indica que 140 no es un año
        - "GP-46/PF952" → números de SKU, no años
        - "3924/7090" → números de SKU muy grandes

        FASE 1: Flexibilizado para aceptar más casos válidos.
        """
        # Verificar que los números son razonables como años
        partes = re.split(r'[/-]', año_str)
        for parte in partes:
            try:
                num = int(parte)
                # Si es de 2 dígitos, cualquier valor 00-99 es OK
                if len(parte) == 2:
                    continue
                # Si es de 3+ dígitos, debe estar en rango razonable
                if len(parte) >= 3:
                    if num < 1950 or num > 2030:
                        return False
            except ValueError:
                return False

        # Rechazar si está precedido por letras (indica SKU)
        # PERO permitir si hay un espacio cerca o si es después de motor (L)
        idx = contexto.find(año_str)
        if idx > 0:
            char_antes = contexto[idx - 1]
            # Si hay una letra justo antes, verificar contexto más amplio
            if char_antes.isalpha() and char_antes not in 'LlVv':
                # Permitir si hay un espacio en los 3 caracteres anteriores
                # Ej: "4L 84/90" o "TOPAZ 84/90"
                contexto_previo = contexto[max(0, idx-3):idx]
                if ' ' in contexto_previo:
                    pass  # Permitir
                else:
                    return False

        # Rechazar patrones conocidos de SKUs (solo si están MUY cerca)
        patrones_sku = ['ARE/', 'IT/', 'SHN/', 'HG3', 'ES-', 'PF', 'OF-', 'GP-', 'GC-']
        contexto_upper = contexto.upper()
        for patron in patrones_sku:
            if patron in contexto_upper:
                # Verificar si el año está muy cerca de este patrón de SKU
                patron_idx = contexto_upper.find(patron)
                if abs(patron_idx - idx) < 5:  # Reducido de 10 a 5
                    return False

        return True

    def _extraer_compats_de_segmento(self, segmento: str) -> List[Compatibilidad]:
        """Extrae TODAS las compatibilidades de un segmento individual.

        Si el segmento tiene años, extrae un solo resultado con el modelo encontrado.
        Si NO tiene años, busca TODOS los modelos mencionados (productos universales).
        """
        segmento_upper = segmento.upper()

        # Extraer información común (años, motor, etc.)
        año_inicio = None
        año_fin = None
        motor = ""
        cilindros = ""
        especificacion = ""

        # 1. Buscar años (XX/YY o XXXX-YYYY) con validación
        match_año = self.PATRON_AÑOS.search(segmento)
        if match_año:
            año_str = match_año.group(0)
            if self._es_año_valido(año_str, segmento):
                año_inicio = self._normalizar_año(match_año.group(1))
                año_fin = self._normalizar_año(match_año.group(2))

                # Validar que los años estén en rango razonable
                if not (1950 <= año_inicio <= 2030 and 1950 <= año_fin <= 2030):
                    año_inicio = None
                    año_fin = None
                else:
                    # Corregir si año_fin < año_inicio (swap)
                    if año_fin < año_inicio:
                        año_inicio, año_fin = año_fin, año_inicio

        # 2. Buscar motor (X.XL)
        motor_match = self.PATRON_MOTOR.search(segmento)
        if motor_match:
            motor = f"{motor_match.group(1)}L"

        # 3. Buscar cilindrada americana (350, 302, etc.)
        if not motor:
            cilindrada_match = re.search(r'\b(\d{3})\s*(?:CID|CI|C\.I\.)\b', segmento, re.IGNORECASE)
            if cilindrada_match:
                motor = cilindrada_match.group(1)

        # 4. Buscar cilindros
        cilindros_match = self.PATRON_CILINDROS.search(segmento)
        if cilindros_match:
            cilindros = cilindros_match.group(1).upper()

        # 5. Buscar especificaciones
        spec_match = self.PATRON_SPEC.search(segmento)
        if spec_match:
            especificacion = spec_match.group(1).upper()

        # 6. Buscar modelos - COMPORTAMIENTO DIFERENTE según si hay años
        # IMPORTANTE: Ordenar modelos por longitud (más largos primero)
        # para que "LAND CRUISER" se detecte antes que "CRUISER"
        modelos_ordenados = sorted(self.MODELOS_CONOCIDOS.items(),
                                   key=lambda x: len(x[0]), reverse=True)
        compatibilidades = []

        if año_inicio:
            # CON AÑOS: buscar TODOS los modelos del segmento
            # (antes solo buscaba uno y se detenía con break)
            modelos_encontrados = []
            texto_restante = segmento_upper
            for modelo, marca in modelos_ordenados:
                if re.search(rf'\b{re.escape(modelo)}\b', texto_restante):
                    modelos_encontrados.append((modelo, marca))
                    # Remover del texto para evitar subcoincidencias
                    texto_restante = re.sub(rf'\b{re.escape(modelo)}\b', '', texto_restante)

            if modelos_encontrados:
                for modelo, marca in modelos_encontrados:
                    compat = Compatibilidad()
                    compat.modelo_vehiculo = modelo
                    compat.marca_vehiculo = marca
                    compat.año_inicio = año_inicio
                    compat.año_fin = año_fin
                    compat.motor = motor
                    compat.cilindros = cilindros
                    compat.especificacion = especificacion
                    compatibilidades.append(compat)

            # Si no encontró modelo, buscar solo marca (también ordenados)
            if not compatibilidades:
                marcas_ordenadas = sorted(self.MARCAS_VEHICULO.items(),
                                         key=lambda x: len(x[0]), reverse=True)
                for marca_text, marca_norm in marcas_ordenadas:
                    if re.search(rf'\b{re.escape(marca_text)}\b', segmento_upper):
                        compat = Compatibilidad()
                        compat.marca_vehiculo = marca_norm
                        compat.año_inicio = año_inicio
                        compat.año_fin = año_fin
                        compat.motor = motor
                        compat.cilindros = cilindros
                        compat.especificacion = especificacion
                        compatibilidades.append(compat)
                        break
        else:
            # SIN AÑOS: buscar TODOS los modelos (producto universal)
            modelos_encontrados = []
            texto_restante = segmento_upper
            for modelo, marca in modelos_ordenados:
                if re.search(rf'\b{re.escape(modelo)}\b', texto_restante):
                    modelos_encontrados.append((modelo, marca))
                    # Remover el modelo encontrado para evitar subcoincidencias
                    # Ej: encontrar "LAND CRUISER" evita encontrar "CRUISER" después
                    texto_restante = re.sub(rf'\b{re.escape(modelo)}\b', '', texto_restante)

            # Si encontró modelos, crear compat para cada uno
            if modelos_encontrados:
                for modelo, marca in modelos_encontrados:
                    compat = Compatibilidad()
                    compat.modelo_vehiculo = modelo
                    compat.marca_vehiculo = marca
                    compat.motor = motor
                    compat.cilindros = cilindros
                    compat.especificacion = especificacion
                    compatibilidades.append(compat)
            else:
                # Si no encontró modelos, buscar marcas
                marcas_encontradas = set()
                marcas_ordenadas = sorted(self.MARCAS_VEHICULO.items(),
                                         key=lambda x: len(x[0]), reverse=True)
                for marca_text, marca_norm in marcas_ordenadas:
                    if re.search(rf'\b{re.escape(marca_text)}\b', segmento_upper):
                        marcas_encontradas.add(marca_norm)

                for marca in marcas_encontradas:
                    compat = Compatibilidad()
                    compat.marca_vehiculo = marca
                    compat.motor = motor
                    compat.cilindros = cilindros
                    compat.especificacion = especificacion
                    compatibilidades.append(compat)

        return compatibilidades

    def _extraer_compat_de_segmento(self, segmento: str) -> Optional[Compatibilidad]:
        """Extrae una compatibilidad de un segmento individual (legacy wrapper)."""
        compats = self._extraer_compats_de_segmento(segmento)
        return compats[0] if compats else None

    def _extraer_compatibilidades_legacy(self, descripcion: str) -> List[Compatibilidad]:
        """Método legacy de extracción (para descripciones sin comas)."""
        compatibilidades = []

        # Buscar patrones de año
        años = list(self.PATRON_AÑOS.finditer(descripcion))

        if not años:
            return compatibilidades

        # Para cada rango de años, intentar extraer la información del vehículo
        for match_año in años:
            compat = Compatibilidad()

            año_inicio_str = match_año.group(1)
            año_fin_str = match_año.group(2)

            # Convertir años de 2 dígitos a 4 dígitos
            compat.año_inicio = self._normalizar_año(año_inicio_str)
            compat.año_fin = self._normalizar_año(año_fin_str)

            # Buscar contexto antes del año (modelo, marca, motor)
            contexto = descripcion[:match_año.start()]

            # Extraer motor
            motor_match = self.PATRON_MOTOR.search(contexto)
            if motor_match:
                compat.motor = f"{motor_match.group(1)}L"

            # Extraer cilindrada (ej: 350, 302)
            cilindrada_match = self.PATRON_CILINDRADA.search(contexto)
            if cilindrada_match and not motor_match:
                compat.motor = cilindrada_match.group(1)

            # Extraer cilindros
            cilindros_match = self.PATRON_CILINDROS.search(contexto)
            if cilindros_match:
                compat.cilindros = cilindros_match.group(1).upper()

            # Extraer especificaciones
            spec_match = self.PATRON_SPEC.search(contexto)
            if spec_match:
                compat.especificacion = spec_match.group(1).upper()

            # Buscar modelo y marca
            self._extraer_modelo_marca(contexto, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades

    def _normalizar_año(self, año_str: str) -> int:
        """Convierte un año de 2 o 4 dígitos a 4 dígitos"""
        año = int(año_str)
        if año < 100:
            # Asumimos que años < 30 son 2000s, >= 30 son 1900s
            if año < 30:
                return 2000 + año
            else:
                return 1900 + año
        return año

    def _extraer_modelo_marca(self, contexto: str, compat: Compatibilidad):
        """Extrae el modelo y marca del vehículo del contexto"""
        contexto_upper = contexto.upper()

        # Primero buscar modelos conocidos
        for modelo, marca in self.MODELOS_CONOCIDOS.items():
            if f' {modelo} ' in f' {contexto_upper} ' or f' {modelo},' in f' {contexto_upper},':
                compat.modelo_vehiculo = modelo
                compat.marca_vehiculo = marca
                return

        # Si no encontramos modelo, buscar marca
        for marca_text, marca_norm in self.MARCAS_VEHICULO.items():
            if f' {marca_text} ' in f' {contexto_upper} ':
                compat.marca_vehiculo = marca_norm
                return

    def _limpiar_skus_inicio(self, descripcion: str) -> str:
        """Remueve SKUs alternos del inicio de la descripción.

        Ejemplos que debe manejar:
        - "BKR5EGP/AP3924/7090/BKR5E11 BUJIA NGK PLATINO AVEO..." → "BUJIA NGK..."
        - "HY-201/JG-201 CABLES DE BUJIA LUV..." → "CABLES DE BUJIA LUV..."
        - "G-330/P184/2M3243 FILTRO DE ACEITE..." → "FILTRO DE ACEITE..."
        - "021BKR5EGP BUJIA..." → "BUJIA..."

        Esto evita que números como 3924/7090 se interpreten como años.
        """
        descripcion_original = descripcion

        # Patrón 1: SKUs separados por / al inicio (patrón existente)
        # Ej: "BKR5EGP/AP3924/7090/BKR5E11 BUJIA..."
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            descripcion = descripcion[match.end():].strip()

        # Patrón 2: Códigos con guión al inicio tipo "HY-201/JG-201"
        # Ej: "HY-201/JG-201 CABLES DE BUJIA..."
        patron_hy = re.match(r'^[A-Z]{1,3}-?\d+(?:/[A-Z0-9\-]+)*\s+', descripcion, re.IGNORECASE)
        if patron_hy:
            resto = descripcion[patron_hy.end():]
            for tipo in self.TIPOS_PRODUCTO:
                if resto.upper().startswith(tipo):
                    return resto

        # Patrón 3: Códigos tipo "G-330/P184/2M3243"
        # Ej: "G-330/P184/2M3243/P551278 FILTRO..."
        patron_g = re.match(r'^[A-Z]-\d+(?:/[A-Z0-9\-]+)*\s+', descripcion, re.IGNORECASE)
        if patron_g:
            resto = descripcion[patron_g.end():]
            for tipo in self.TIPOS_PRODUCTO:
                if resto.upper().startswith(tipo):
                    return resto

        # Patrón 4: Códigos tipo "EL-145/SEL" o "GP-22/PH927"
        patron_el = re.match(r'^[A-Z]{2,3}-?\d+(?:/[A-Z0-9\-]+)*\s+', descripcion, re.IGNORECASE)
        if patron_el:
            resto = descripcion[patron_el.end():]
            for tipo in self.TIPOS_PRODUCTO:
                if resto.upper().startswith(tipo):
                    return resto

        # Patrón 5: Código alfanumérico simple seguido de espacio
        # Ej: "021BKR5EGP BUJIA..." → "BUJIA..."
        match2 = re.match(r'^[A-Z0-9\-]+\s+', descripcion, re.IGNORECASE)
        if match2:
            resto = descripcion[match2.end():]
            for tipo in self.TIPOS_PRODUCTO:
                if resto.upper().startswith(tipo):
                    return resto

        return descripcion
