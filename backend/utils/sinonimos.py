"""
Diccionario de sinónimos para búsqueda de autopartes.

Permite que búsquedas como "kit de aceleración" encuentren productos de CLUTCH,
o "pastilla de freno" encuentre BALATAS.

El diccionario se carga en memoria al importar el módulo (O(1) lookup).
"""

from typing import List, Set, Tuple, Dict

from utils.busqueda_inteligente import STOP_WORDS

# ---------------------------------------------------------------------------
# GRUPOS DE SINÓNIMOS
# Cada set agrupa términos equivalentes. Todos en minúsculas.
# ---------------------------------------------------------------------------

GRUPOS_SINONIMOS: List[Set[str]] = [
    # --- CLUTCH / EMBRAGUE ---
    {"clutch", "embrague", "kit clutch", "kit embrague", "kit de embrague",
     "kit aceleracion", "kit de aceleracion", "disco clutch", "disco embrague",
     "disco de clutch", "disco de embrague", "plato clutch", "plato embrague",
     "plato de clutch", "plato de embrague", "cluth", "partes de clutch",
     "partes de cluth"},

    # --- FRENOS: BALATAS ---
    {"balata", "balatas", "pastilla freno", "pastilla de freno",
     "pastillas de freno", "pastillas freno", "brake pad", "brake pads"},

    # --- FRENOS: DISCO ---
    {"disco freno", "disco de freno", "discos de freno", "rotor",
     "rotores", "brake rotor", "brake disc"},

    # --- FRENOS: TAMBOR ---
    {"tambor", "tambor freno", "tambor de freno", "brake drum"},

    # --- FRENOS: BOMBA ---
    {"bomba frenos", "bomba de frenos", "bomba freno", "bomba de freno",
     "cilindro maestro", "master cylinder"},

    # --- SUSPENSION: AMORTIGUADOR ---
    {"amortiguador", "amortiguadores", "shock", "shocks", "shock absorber"},

    # --- SUSPENSION: ROTULA ---
    {"rotula", "rotulas", "ball joint", "rotula inferior", "rotula superior"},

    # --- SUSPENSION: HORQUILLA ---
    {"horquilla", "brazo suspension", "brazo de suspension",
     "brazo control", "control arm"},

    # --- SUSPENSION: BUJE ---
    {"buje", "bujes", "bushing", "bushings", "buje suspension",
     "buje de suspension"},

    # --- SUSPENSION: TERMINAL ---
    {"terminal", "terminal direccion", "terminal de direccion",
     "tie rod", "tie rod end", "barra de direccion"},

    # --- SUSPENSION: CREMALLERA ---
    {"cremallera", "cremallera direccion", "cremallera de direccion",
     "rack", "steering rack"},

    # --- SUSPENSION: MAZA ---
    {"maza", "mazas", "hub", "hub assembly", "maza rueda", "maza de rueda"},

    # --- SUSPENSION: BIELETA ---
    {"bieleta", "bieletas", "vieleta", "vieletas", "biela estabilizador",
     "biela de estabilizador", "stabilizer link", "sway bar link"},

    # --- MOTOR: BUJIA ---
    {"bujia", "bujias", "spark plug", "spark plugs"},

    # --- MOTOR: CABLES BUJIA ---
    {"cables bujia", "cables de bujia", "juego cables", "juego de cables",
     "ignition wires", "plug wires", "cables de ignicion"},

    # --- MOTOR: BOBINA ---
    {"bobina", "bobinas", "bobina ignicion", "bobina de ignicion",
     "coil", "ignition coil"},

    # --- MOTOR: BOMBA AGUA ---
    {"bomba agua", "bomba de agua", "water pump"},

    # --- MOTOR: EMPAQUE / JUNTA ---
    {"empaque", "empaques", "junta", "juntas", "gasket", "gaskets",
     "empaque motor", "junta motor"},

    # --- MOTOR: RETEN / SELLO ---
    {"reten", "retenes", "sello", "sellos", "seal", "oil seal",
     "reten ciguenal", "sello ciguenal"},

    # --- MOTOR: METAL BANCADA ---
    {"metal bancada", "metales bancada", "metales de bancada",
     "main bearing", "main bearings", "cojinete bancada"},

    # --- MOTOR: ANILLO ---
    {"anillo", "anillos", "anillos piston", "anillos de piston",
     "piston ring", "piston rings"},

    # --- MOTOR: SOPORTE MOTOR ---
    {"soporte motor", "soporte de motor", "soportes motor",
     "soportes de motor", "engine mount", "motor mount"},

    # --- MOTOR: TERMOSTATO ---
    {"termostato", "thermostat"},

    # --- MOTOR: TOMA AGUA ---
    {"toma agua", "toma de agua", "water outlet", "salida agua",
     "salida de agua"},

    # --- ENFRIAMIENTO: RADIADOR ---
    {"radiador", "radiadores", "radiator"},

    # --- ENFRIAMIENTO: VENTILADOR ---
    {"motoventilador", "ventilador", "ventilador radiador",
     "ventilador de radiador", "fan", "cooling fan", "electroventilador"},

    # --- ENFRIAMIENTO: FAN CLUTCH ---
    {"fan clutch", "clutch ventilador", "clutch de ventilador",
     "clutch del ventilador"},

    # --- ENFRIAMIENTO: ANTICONGELANTE ---
    {"anticongelante", "coolant", "refrigerante", "liquido refrigerante",
     "liquido enfriamiento"},

    # --- ENFRIAMIENTO: MANGUERA ---
    {"manguera", "mangueras", "manguera radiador", "manguera de radiador",
     "hose", "radiator hose", "coolant hose"},

    # --- DISTRIBUCION: BANDA TIEMPO ---
    {"banda tiempo", "banda de tiempo", "banda de distribucion",
     "timing belt", "correa tiempo", "correa de tiempo",
     "correa distribucion", "correa de distribucion"},

    # --- DISTRIBUCION: CADENA TIEMPO ---
    {"cadena tiempo", "cadena de tiempo", "cadena distribucion",
     "cadena de distribucion", "timing chain"},

    # --- DISTRIBUCION: KIT DISTRIBUCION ---
    {"kit distribucion", "kit de distribucion", "timing kit",
     "kit tiempo", "kit de tiempo"},

    # --- DISTRIBUCION: TENSOR ---
    {"tensor", "tensores", "tensor banda", "tensor de banda",
     "tensioner", "belt tensioner", "tensor distribucion"},

    # --- BANDAS ---
    {"banda", "bandas", "correa", "correas", "belt", "serpentina",
     "banda serpentina", "banda de serpentina", "serpentine belt",
     "banda accesorios", "banda de accesorios", "poly v",
     "banda alternador"},

    # --- POLEA ---
    {"polea", "poleas", "pulley", "pulleys", "polea tensora",
     "polea loca", "idler pulley"},

    # --- FILTRO ACEITE ---
    {"filtro aceite", "filtro de aceite", "oil filter"},

    # --- FILTRO AIRE ---
    {"filtro aire", "filtro de aire", "air filter"},

    # --- FILTRO GASOLINA ---
    {"filtro gasolina", "filtro de gasolina", "filtro combustible",
     "filtro de combustible", "fuel filter"},

    # --- FILTRO CABINA ---
    {"filtro cabina", "filtro de cabina", "filtro ac",
     "filtro aire acondicionado", "cabin filter"},

    # --- ELECTRICO: ACUMULADOR ---
    {"acumulador", "acumuladores", "bateria", "baterias", "battery"},

    # --- ELECTRICO: ALTERNADOR ---
    {"alternador", "alternadores", "alternator"},

    # --- ELECTRICO: MARCHA ---
    {"marcha", "motor arranque", "motor de arranque", "starter",
     "arranque"},

    # --- ELECTRICO: INYECTOR ---
    {"inyector", "inyectores", "fuel injector", "fuel injectors",
     "inyector combustible", "inyector de combustible"},

    # --- TRANSMISION: CRUCETA ---
    {"cruceta", "crucetas", "u-joint", "junta universal",
     "junta cardan", "cardan"},

    # --- TRANSMISION: FLECHA ---
    {"flecha", "flechas", "flecha transmision", "flecha de transmision",
     "drive shaft", "driveshaft"},

    # --- TRANSMISION: JUNTA HOMOCINETICA ---
    {"junta homocinetica", "junta cv", "cv joint", "junta vc",
     "homocinetica", "homocinética"},

    # --- TRANSMISION: COLLARIN ---
    {"collarin", "collarín", "throwout bearing", "clutch bearing",
     "rodamiento clutch"},

    # --- TRANSMISION: CABLE CLUTCH ---
    {"cable clutch", "cable de clutch", "cable embrague",
     "cable de embrague"},

    # --- ACEITES ---
    {"aceite motor", "aceite de motor", "lubricante", "engine oil",
     "aceite lubricante"},

    # --- GRASA ---
    {"grasa", "grasas", "grease"},

    # --- LLANTAS ---
    {"llanta", "llantas", "neumatico", "neumaticos", "neumático",
     "tire", "tires", "cubierta", "cubiertas"},

    # --- LIMPIAPARABRISAS ---
    {"limpiaparabrisas", "pluma", "plumas", "wiper", "wipers",
     "escobilla", "escobillas", "plumas limpiaparabrisas",
     "wiper blade", "wiper blades"},

    # --- BOMBA ACEITE ---
    {"bomba aceite", "bomba de aceite", "oil pump"},

    # --- BOMBA GASOLINA ---
    {"bomba gasolina", "bomba de gasolina", "bomba combustible",
     "bomba de combustible", "fuel pump"},
]


# ---------------------------------------------------------------------------
# ÍNDICES INVERSOS (se construyen una vez al importar)
# ---------------------------------------------------------------------------

# Palabra individual → referencia al set del grupo
_indice_sinonimos: Dict[str, Set[str]] = {}

# Tupla de palabras → referencia al set del grupo (frases multi-palabra)
_frases_multipalabra: Dict[Tuple[str, ...], Set[str]] = {}

# Longitud máxima de frase (para matching greedy)
_max_len_frase: int = 0


def _construir_indices() -> None:
    """Construye los índices inversos a partir de GRUPOS_SINONIMOS."""
    global _indice_sinonimos, _frases_multipalabra, _max_len_frase

    for grupo in GRUPOS_SINONIMOS:
        for termino in grupo:
            palabras = termino.split()
            if len(palabras) == 1:
                _indice_sinonimos[termino] = grupo
            else:
                # Frase multi-palabra: indexar la versión completa
                clave = tuple(palabras)
                _frases_multipalabra[clave] = grupo
                if len(clave) > _max_len_frase:
                    _max_len_frase = len(clave)

                # También indexar versión sin stop words
                sin_stop = tuple(p for p in palabras if p not in STOP_WORDS)
                if sin_stop != clave and len(sin_stop) > 1:
                    _frases_multipalabra[sin_stop] = grupo


# Construir al importar
_construir_indices()


# ---------------------------------------------------------------------------
# FUNCIONES PÚBLICAS
# ---------------------------------------------------------------------------

def _deduplicar_para_like(grupo: Set[str]) -> Set[str]:
    """
    Elimina términos redundantes para consultas LIKE.

    Si "amortiguador" ya está en el grupo, no necesitamos "amortiguadores"
    porque `%amortiguador%` ya lo cubre en un LIKE.

    Retorna un set reducido de términos.
    """
    # Ordenar por longitud (más cortos primero)
    ordenados = sorted(grupo, key=len)
    resultado: Set[str] = set()

    for termino in ordenados:
        # Verificar si algún término ya en resultado es substring de este
        cubierto = False
        for existente in resultado:
            if existente in termino:
                cubierto = True
                break
        if not cubierto:
            resultado.add(termino)

    return resultado


def expandir_sinonimos(palabras: List[str]) -> List[Set[str]]:
    """
    Expande una lista de palabras de búsqueda con sus sinónimos.

    Busca primero frases multi-palabra (greedy, de más larga a más corta),
    luego palabras individuales.

    Args:
        palabras: Lista de palabras de la búsqueda (ya en minúsculas, sin stop words)

    Returns:
        Lista de sets. Cada set contiene los sinónimos de un término encontrado.
        Si un término no tiene sinónimos, se retorna un set con solo ese término.

    Ejemplo:
        expandir_sinonimos(["clutch"]) → [{"clutch", "embrague", "kit clutch", ...}]
        expandir_sinonimos(["filtro", "aceite"]) → [{sinónimos_filtro_aceite}]
    """
    if not palabras:
        return []

    resultado: List[Set[str]] = []
    i = 0
    n = len(palabras)

    while i < n:
        encontrado = False

        # Intentar frases multi-palabra (greedy: de más larga a más corta)
        max_j = min(i + _max_len_frase, n)
        for j in range(max_j, i, -1):
            frase = tuple(palabras[i:j])
            if frase in _frases_multipalabra:
                grupo = _frases_multipalabra[frase]
                resultado.append(_deduplicar_para_like(grupo))
                i = j
                encontrado = True
                break

        if not encontrado:
            # Intentar palabra individual
            palabra = palabras[i]
            if palabra in _indice_sinonimos:
                grupo = _indice_sinonimos[palabra]
                resultado.append(_deduplicar_para_like(grupo))
            else:
                # Sin sinónimos: retornar solo la palabra original
                resultado.append({palabra})
            i += 1

    return resultado
