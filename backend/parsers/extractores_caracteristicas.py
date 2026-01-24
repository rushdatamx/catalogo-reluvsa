"""
Extractores de características específicas para productos sin compatibilidad vehicular.

- Llantas: ancho, relación, diámetro, tipo, capas
- Aceites: viscosidad, tipo, presentación
- Acumuladores: grupo BCI, capacidad CCA, placas
"""
import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CaracteristicaExtraida:
    """Representa una característica extraída"""
    clave: str
    valor: str


class ExtractorLlantas:
    """
    Extractor de características para llantas.

    Patrones soportados:
    - Radial: 205/55 R16, 215/70 R15, 185/60 R14
    - LT (Light Truck): 31X10.5 R15 LT
    - Convencional: 750 16 8C, 1000 20 14C, 700 15 6C
    """

    # Patrón radial estándar: ancho/relación Rdiámetro
    PATRON_RADIAL = re.compile(r'(\d{3})/(\d{2})\s*R\s*(\d{2})', re.IGNORECASE)

    # Patrón LT (Light Truck): 31X10.5 R15 LT
    PATRON_LT = re.compile(r'(\d{2,3})X(\d+\.?\d*)\s*R\s*(\d{2})', re.IGNORECASE)

    # Patrón convencional: 750 16 8C, 1000 20 14C
    PATRON_CONVENCIONAL = re.compile(r'^(\d{3,4})\s+(\d{2})\s+(\d{1,2})C', re.IGNORECASE)

    # Patrón capas: 6C, 8C, 10C, 14C, 16C
    PATRON_CAPAS = re.compile(r'(\d{1,2})C\b')

    # Tipos de llanta
    TIPOS_LLANTA = {
        'DEPORTIVA': 'Deportiva',
        'DIRECCIONAL': 'Direccional',
        'TRACCION': 'Tracción',
        'CONVENCIONAL': 'Convencional',
        'AMAZONAS': 'Todo Terreno',
        'PISO EXTRA': 'Piso Extra',
        'RADIAL': 'Radial',
        'LT': 'Light Truck',
    }

    def extraer(self, descripcion: str) -> List[CaracteristicaExtraida]:
        """Extrae características de una llanta"""
        caracteristicas = []
        desc_upper = descripcion.upper()

        # Intentar patrón radial primero (más común)
        match_radial = self.PATRON_RADIAL.search(descripcion)
        if match_radial:
            caracteristicas.append(CaracteristicaExtraida('ancho', match_radial.group(1)))
            caracteristicas.append(CaracteristicaExtraida('relacion', match_radial.group(2)))
            caracteristicas.append(CaracteristicaExtraida('diametro', f"R{match_radial.group(3)}"))
            caracteristicas.append(CaracteristicaExtraida('formato', 'Radial'))

        # Intentar patrón LT
        elif self.PATRON_LT.search(descripcion):
            match_lt = self.PATRON_LT.search(descripcion)
            # Para LT, el ancho es el primer número, la relación es el segundo
            caracteristicas.append(CaracteristicaExtraida('ancho', match_lt.group(1)))
            caracteristicas.append(CaracteristicaExtraida('relacion', match_lt.group(2)))
            caracteristicas.append(CaracteristicaExtraida('diametro', f"R{match_lt.group(3)}"))
            caracteristicas.append(CaracteristicaExtraida('formato', 'LT'))

        # Intentar patrón convencional
        else:
            match_conv = self.PATRON_CONVENCIONAL.search(descripcion)
            if match_conv:
                caracteristicas.append(CaracteristicaExtraida('ancho', match_conv.group(1)))
                caracteristicas.append(CaracteristicaExtraida('diametro', match_conv.group(2)))
                caracteristicas.append(CaracteristicaExtraida('capas', match_conv.group(3)))
                caracteristicas.append(CaracteristicaExtraida('formato', 'Convencional'))

        # Extraer capas si no se extrajo antes
        if not any(c.clave == 'capas' for c in caracteristicas):
            match_capas = self.PATRON_CAPAS.search(descripcion)
            if match_capas:
                caracteristicas.append(CaracteristicaExtraida('capas', match_capas.group(1)))

        # Extraer tipo de llanta
        for patron, tipo in self.TIPOS_LLANTA.items():
            if patron in desc_upper:
                caracteristicas.append(CaracteristicaExtraida('tipo', tipo))
                break

        return caracteristicas


class ExtractorAceites:
    """
    Extractor de características para aceites y lubricantes.

    Patrones soportados:
    - Viscosidad SAE: 5W30, 10W40, 20W50
    - Viscosidad monograde: SAE 40, SAE 50, SAE 90, SAE 140, SAE 250
    - Presentación: .946L, 1L, 4L, 5L, 19L
    - Tipo: Motor, Transmisión, Hidráulico, ATF, 2 Tiempos
    """

    # Patrón viscosidad multigrade: 5W30, 10W40, 20W50
    PATRON_MULTIGRADE = re.compile(r'(\d{1,2}W\d{2})', re.IGNORECASE)

    # Patrón viscosidad monograde: SAE 40, SAE 50, SAE 90, SAE 140
    PATRON_MONOGRADE = re.compile(r'SAE\s*(\d{2,3})', re.IGNORECASE)

    # Patrón presentación en litros: .946L, 1L, 4L, 5L, 19L, 946ml
    PATRON_LITROS = re.compile(r'\.?(\d+\.?\d*)\s*(L|LT|LTS)\b', re.IGNORECASE)
    PATRON_ML = re.compile(r'(\d{3})\s*ML\b', re.IGNORECASE)

    # Tipos de aceite
    TIPOS_ACEITE = {
        'MOTOR': 'Motor',
        'TRANSMISION': 'Transmisión',
        'TRANSM.': 'Transmisión',
        'HIDRAULICO': 'Hidráulico',
        'ATF': 'ATF (Transmisión Automática)',
        '2 TIEMPOS': '2 Tiempos',
        '2T': '2 Tiempos',
        'DIESEL': 'Diesel',
        'GRASA': 'Grasa',
        'NAUTICO': 'Náutico',
    }

    # Tipos de base
    BASES_ACEITE = {
        'SINTETICO': 'Sintético',
        'SYNTHETIC': 'Sintético',
        'SEMI SINTETICO': 'Semi-Sintético',
        'MINERAL': 'Mineral',
        'HIGH MILEAGE': 'Alto Kilometraje',
    }

    def extraer(self, descripcion: str) -> List[CaracteristicaExtraida]:
        """Extrae características de un aceite/lubricante"""
        caracteristicas = []
        desc_upper = descripcion.upper()

        # Extraer viscosidad multigrade
        match_multi = self.PATRON_MULTIGRADE.search(descripcion)
        if match_multi:
            viscosidad = match_multi.group(1).upper()
            caracteristicas.append(CaracteristicaExtraida('viscosidad', viscosidad))
        else:
            # Intentar monograde
            match_mono = self.PATRON_MONOGRADE.search(descripcion)
            if match_mono:
                viscosidad = f"SAE {match_mono.group(1)}"
                caracteristicas.append(CaracteristicaExtraida('viscosidad', viscosidad))

        # Extraer presentación
        match_litros = self.PATRON_LITROS.search(descripcion)
        if match_litros:
            cantidad = match_litros.group(1)
            if cantidad.startswith('.'):
                cantidad = '0' + cantidad
            caracteristicas.append(CaracteristicaExtraida('presentacion', f"{cantidad}L"))
        else:
            match_ml = self.PATRON_ML.search(descripcion)
            if match_ml:
                ml = match_ml.group(1)
                caracteristicas.append(CaracteristicaExtraida('presentacion', f"{ml}ml"))

        # Extraer tipo de aceite
        for patron, tipo in self.TIPOS_ACEITE.items():
            if patron in desc_upper:
                caracteristicas.append(CaracteristicaExtraida('tipo_aceite', tipo))
                break

        # Extraer base del aceite
        for patron, base in self.BASES_ACEITE.items():
            if patron in desc_upper:
                caracteristicas.append(CaracteristicaExtraida('base', base))
                break

        return caracteristicas


class ExtractorAcumuladores:
    """
    Extractor de características para acumuladores/baterías.

    Patrones soportados:
    - Grupo BCI: G-47, V-65, CH-34, 34-550, 47-600
    - Capacidad CCA: 350A, 550A, 750A (o número después del guión: 34-550)
    - Placas: 14 PLACAS
    - Ciclo profundo: CICLO PROFUNDO
    """

    # Patrón grupo BCI estándar: G-47, V-65, CH-34
    PATRON_GRUPO_PREFIJO = re.compile(r'[GVC]H?-(\d{2,3}R?)', re.IGNORECASE)

    # Patrón grupo alternativo: 34-550, 47-600 (grupo-CCA)
    PATRON_GRUPO_CCA = re.compile(r'\b(\d{2,3}R?)-(\d{3,4})\b')

    # Patrón CCA explícito: 550A, 750A
    PATRON_CCA = re.compile(r'(\d{3,4})\s*A\b')

    # Patrón placas: 14 PLACAS
    PATRON_PLACAS = re.compile(r'(\d{1,2})\s*PLACAS?', re.IGNORECASE)

    # Tamaños de grupo
    TAMANOS_GRUPO = {
        'CHICO': 'Chico',
        'MEDIO CHICO': 'Medio Chico',
        'INTERMEDIO': 'Intermedio',
        'MEDIANO': 'Mediano',
        'GRANDE': 'Grande',
    }

    def extraer(self, descripcion: str) -> List[CaracteristicaExtraida]:
        """Extrae características de un acumulador"""
        caracteristicas = []
        desc_upper = descripcion.upper()

        grupo = None
        cca = None

        # Intentar patrón grupo-CCA primero (ej: 34-550)
        match_grupo_cca = self.PATRON_GRUPO_CCA.search(descripcion)
        if match_grupo_cca:
            grupo = match_grupo_cca.group(1)
            cca = match_grupo_cca.group(2)

        # Intentar patrón de prefijo (G-47, V-65, CH-34)
        if not grupo:
            match_prefijo = self.PATRON_GRUPO_PREFIJO.search(descripcion)
            if match_prefijo:
                grupo = match_prefijo.group(1)

        # Agregar grupo BCI si se encontró
        if grupo:
            caracteristicas.append(CaracteristicaExtraida('grupo_bci', grupo))

        # Buscar CCA si no se encontró antes
        if not cca:
            match_cca = self.PATRON_CCA.search(descripcion)
            if match_cca:
                cca = match_cca.group(1)

        if cca:
            caracteristicas.append(CaracteristicaExtraida('capacidad_cca', f"{cca}A"))

        # Extraer placas
        match_placas = self.PATRON_PLACAS.search(descripcion)
        if match_placas:
            caracteristicas.append(CaracteristicaExtraida('placas', match_placas.group(1)))

        # Extraer tamaño de grupo
        for patron, tamano in self.TAMANOS_GRUPO.items():
            if patron in desc_upper:
                caracteristicas.append(CaracteristicaExtraida('tamano', tamano))
                break

        # Verificar si es ciclo profundo
        if 'CICLO PROFUNDO' in desc_upper:
            caracteristicas.append(CaracteristicaExtraida('tipo_bateria', 'Ciclo Profundo'))

        return caracteristicas


def get_extractor(categoria: str):
    """Obtiene el extractor apropiado según la categoría"""
    extractores = {
        'llanta': ExtractorLlantas(),
        'aceite': ExtractorAceites(),
        'acumulador': ExtractorAcumuladores(),
    }
    return extractores.get(categoria)
