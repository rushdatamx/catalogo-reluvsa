"""
Parser específico para productos CAUPLAS

Patrón típico:
CODIGO/CODIGO/OEM MANGUERA CAUPLAS [TIPO] MODELO MOTOR AÑO/AÑO

Ejemplos:
- 5477 MANGUERA CAUPLAS SALIDA CALEFACCION CAPTIVA 2.4L 08/14
- 4500/93428011/62695 MANGUERA CAUPLAS RADIADOR INFERIOR SIN AC CHEVY 1.4L 1.6L 99/13
- 3922/61105/CH137502 MANGUERA CAUPLAS RADIADOR INFERIOR BRONCO 5.0L 90-92

Particularidades:
- Tipo manguera: RADIADOR, CALEFACCION, REFRIGERACION
- Posición: SUPERIOR, INFERIOR, ENTRADA, SALIDA
- Especificación: CON AC, SIN AC
- Motor casi siempre presente en formato X.XL

Productos: 1469
"""
import re
from typing import List
from .base import BaseParser, ResultadoParseo, Compatibilidad


class CauplasParser(BaseParser):
    """Parser especializado para productos CAUPLAS (mangueras)"""

    # Tipos de manguera
    TIPOS_MANGUERA = ['RADIADOR', 'CALEFACCION', 'REFRIGERACION', 'DEPOSITO', 'MOTOR']

    # Posiciones
    POSICIONES = ['SUPERIOR', 'INFERIOR', 'ENTRADA', 'SALIDA', 'LATERAL']

    # Especificaciones AC
    SPECS_AC = ['CON AC', 'SIN AC', 'C/AC', 'S/AC', 'CON/AC', 'SIN/AC']

    # Patrón para múltiples motores (ej: 1.4L 1.6L)
    PATRON_MOTORES = re.compile(r'(\d+\.\d+L(?:\s+\d+\.\d+L)*)', re.IGNORECASE)

    def parse(self, descripcion: str) -> ResultadoParseo:
        """Parsea descripción de producto CAUPLAS"""
        resultado = ResultadoParseo()

        if not descripcion:
            return resultado

        descripcion = descripcion.strip()

        # Extraer SKUs alternos
        resultado.skus_alternos = self.extraer_skus_alternos(descripcion)

        # Extraer tipo de producto específico
        resultado.tipo_producto = self._extraer_tipo_cauplas(descripcion)

        # Extraer nombre del producto
        resultado.nombre_producto = self._extraer_nombre_cauplas(descripcion)

        # Extraer compatibilidades
        resultado.compatibilidades = self._extraer_compatibilidades_cauplas(descripcion)
        resultado.raw_compatibilidades = descripcion

        return resultado

    def _extraer_tipo_cauplas(self, descripcion: str) -> str:
        """Extrae tipo específico de manguera CAUPLAS"""
        desc_upper = descripcion.upper()

        tipo_base = 'MANGUERA'
        tipo_especifico = ''
        posicion = ''

        # Buscar tipo específico
        for tipo in self.TIPOS_MANGUERA:
            if tipo in desc_upper:
                tipo_especifico = tipo
                break

        # Buscar posición
        for pos in self.POSICIONES:
            if pos in desc_upper:
                posicion = pos
                break

        if tipo_especifico and posicion:
            return f'{tipo_base} {tipo_especifico} {posicion}'
        elif tipo_especifico:
            return f'{tipo_base} {tipo_especifico}'
        else:
            return tipo_base

    def _extraer_nombre_cauplas(self, descripcion: str) -> str:
        """Extrae nombre del producto CAUPLAS"""
        # Remover SKUs
        match = self.PATRON_SKUS.match(descripcion)
        if match:
            descripcion = descripcion[match.end():]

        # Buscar hasta primer modelo conocido
        desc_upper = descripcion.upper()
        posicion_corte = len(descripcion)

        for modelo in self.MODELOS_CONOCIDOS.keys():
            idx = desc_upper.find(f' {modelo} ')
            if idx > 0 and idx < posicion_corte:
                posicion_corte = idx

        nombre = descripcion[:posicion_corte].strip()

        # Limpiar "CAUPLAS" duplicado
        nombre = re.sub(r'CAUPLAS\s+CAUPLAS', 'CAUPLAS', nombre, flags=re.IGNORECASE)

        return nombre[:100] if len(nombre) > 100 else nombre

    def _extraer_compatibilidades_cauplas(self, descripcion: str) -> List[Compatibilidad]:
        """Extrae compatibilidades de productos CAUPLAS"""
        compatibilidades = []

        # Remover SKUs
        match_skus = self.PATRON_SKUS.match(descripcion)
        if match_skus:
            descripcion = descripcion[match_skus.end():]

        # CAUPLAS tiene múltiples formatos de separación
        # 1. Coma: BRONCO 5.0L 90-92, F-150 5.0L 90-95
        # 2. Slash en años: CHEVY 1.4L 1.6L 99/13

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

            # Extraer motor(es) - CAUPLAS a menudo tiene múltiples motores
            motores_match = self.PATRON_MOTORES.search(contexto[-50:] if len(contexto) > 50 else contexto)
            if motores_match:
                compat.motor = motores_match.group(1).replace(' ', '/')

            # Extraer especificación AC
            for spec in self.SPECS_AC:
                if spec in contexto.upper():
                    compat.especificacion = spec.replace('/', ' ')
                    break

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
