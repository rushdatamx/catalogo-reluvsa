"""
Parser específico para productos INJETECH

Patrón típico:
CODIGO/CODIGO TIPO_PRODUCTO MODELO MOTOR AÑO/AÑO

Ejemplos:
- 12903/84991/D95166 VALVULA DE MARCHA MINIMA IAC PLATINA 01/05 RENAULT CLIO 02/04 1.6L
- 11008/AC253 VALVULA BY PASS FORD IKON,KA,COURIER, FOCUS 00/AD
- 04866/12596851 SENSOR DE POCISION DE CIGUEÑAL ESCALADE,BLAZER-S10,SUBURBAN 94-07

Particularidades:
- "AD" = Año actual/Adelante
- Incluye marca de vehículo explícita frecuentemente (FORD, NISSAN, etc.)
- Tipos específicos: IAC, TPS, CKP, MAF, EGR

Productos: 1111
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad
from datetime import datetime


class InjetechParser(BaseParser):
    """Parser especializado para productos INJETECH"""

    # Año actual para "AD"
    AÑO_ACTUAL = datetime.now().year

    # Patrón para separar compatibilidades
    PATRON_COMPAT_SEP = re.compile(r'[,;]\s*')

    # Patrón para años con "AD"
    PATRON_AÑOS_AD = re.compile(r'(\d{2,4})[/-](AD|ADELANTE|ACTUAL)', re.IGNORECASE)

    # Tipos de sensores específicos de INJETECH
    TIPOS_SENSOR = ['IAC', 'TPS', 'CKP', 'CMP', 'MAF', 'MAP', 'EGR', 'O2', 'ABS']

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto INJETECH"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto (incluyendo tipos de sensor)
        resultado.tipo_producto = self._extraer_tipo_injetech(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self.extraer_nombre_producto(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_injetech(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_tipo_injetech(self, descripcion: str) -> str:
        """Extrae tipo de producto incluyendo tipos de sensor específicos"""
        desc_upper = descripcion.upper()

        # Primero buscar tipos de sensor específicos
        for tipo in self.TIPOS_SENSOR:
            if f' {tipo} ' in f' {desc_upper} ' or f' {tipo},' in desc_upper:
                return f'SENSOR {tipo}'

        # Luego tipos generales
        return self.extraer_tipo_producto(descripcion)

    def _extraer_compatibilidades_injetech(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades con lógica específica de INJETECH"""
        compatibilidades = []

        # Remover SKUs del inicio
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # Primero verificar si hay años con "AD"
        match_ad = self.PATRON_AÑOS_AD.search(descripcion)
        if match_ad:
            # Procesar años con AD
            compatibilidades.extend(self._procesar_con_ad(descripcion))

        # Buscar patrones regulares de años
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

            # Extraer marca y modelo
            self._extraer_modelo_marca(contexto, compat)

            # También buscar marca explícita (FORD, NISSAN, etc.)
            self._buscar_marca_explicita(contexto, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades

    def _procesar_con_ad(self, descripcion: str) -> List[Compatibilidad]:
        """Procesa descripciones que usan 'AD' para año actual"""
        compatibilidades = []

        match = self.PATRON_AÑOS_AD.search(descripcion)
        if match:
            compat = Compatibilidad()
            compat.año_inicio = self._normalizar_año(match.group(1))
            compat.año_fin = self.AÑO_ACTUAL

            contexto = descripcion[:match.start()]
            self._extraer_modelo_marca(contexto, compat)
            self._buscar_marca_explicita(contexto, compat)

            if compat.modelo_vehiculo or compat.marca_vehiculo:
                compatibilidades.append(compat)

        return compatibilidades

    def _buscar_marca_explicita(self, contexto: str, compat: Compatibilidad):
        """Busca marca de vehículo explícita en el contexto"""
        contexto_upper = contexto.upper()

        # Buscar marcas explícitas si no hay marca asignada
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
