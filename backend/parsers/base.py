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
    PATRON_MOTOR = re.compile(r'(\d+\.?\d*)\s*[Ll](?:T|ITROS?)?', re.IGNORECASE)
    PATRON_CILINDRADA = re.compile(r'(\d{3})\s*(?:CID|CI|C\.I\.)?', re.IGNORECASE)
    PATRON_CILINDROS = re.compile(r'(V\d+|L\d+|\d+\s*CIL(?:INDROS?)?)', re.IGNORECASE)
    PATRON_SPEC = re.compile(r'(DOHC|SOHC|OHV|TBI|VORTEC|MPFI|EFI|16V|8V|12V|24V)', re.IGNORECASE)
    PATRON_SKUS = re.compile(r'^([A-Z0-9\-]+(?:/[A-Z0-9\-]+)+)\s+', re.IGNORECASE)

    # Marcas de vehículos conocidas
    MARCAS_VEHICULO = {
        # GM
        'CHEVROLET': 'CHEVROLET', 'CHEVY': 'CHEVROLET', 'GM': 'CHEVROLET',
        'CHEV': 'CHEVROLET', 'GMC': 'GMC',
        # Ford
        'FORD': 'FORD',
        # Nissan
        'NISSAN': 'NISSAN', 'DATSUN': 'NISSAN',
        # Chrysler
        'DODGE': 'DODGE', 'CHRYSLER': 'CHRYSLER', 'JEEP': 'JEEP', 'RAM': 'DODGE',
        # VW
        'VOLKSWAGEN': 'VOLKSWAGEN', 'VW': 'VOLKSWAGEN',
        # Toyota
        'TOYOTA': 'TOYOTA',
        # Honda
        'HONDA': 'HONDA',
        # Hyundai/Kia
        'HYUNDAI': 'HYUNDAI', 'KIA': 'KIA',
        # Mazda
        'MAZDA': 'MAZDA',
        # Mitsubishi
        'MITSUBISHI': 'MITSUBISHI',
        # Renault
        'RENAULT': 'RENAULT',
        # Fiat
        'FIAT': 'FIAT',
        # BMW
        'BMW': 'BMW',
        # Mercedes
        'MERCEDES': 'MERCEDES', 'MERCEDES-BENZ': 'MERCEDES',
        # Otros
        'ISUZU': 'ISUZU', 'SUZUKI': 'SUZUKI', 'PONTIAC': 'PONTIAC',
        'BUICK': 'BUICK', 'CADILLAC': 'CADILLAC', 'OLDSMOBILE': 'OLDSMOBILE',
        'LINCOLN': 'LINCOLN', 'MERCURY': 'MERCURY',
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
        'SORENTO': 'KIA', 'SOUL': 'KIA',
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

    def extraer_compatibilidades(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae las compatibilidades del producto"""
        compatibilidades = []
        descripcion_upper = descripcion.upper()

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
