"""
Mapeo entre clasificaciones CIIU (DANE) y UNSPSC (SECOP II).

Este mapeo permite cruzar datos de tejido productivo (CIIU)
con datos de contratación pública (UNSPSC) para análisis de
sinergia económica.
"""

from typing import Dict, List, Optional, Set

# Mapeo CIIU -> UNSPSC
# Basado en similitud semántica de descripciones
CIIU_A_UNSPSC: Dict[str, List[str]] = {
    # Sección A - Agricultura, ganadería, caza y silvicultura
    'A01': ['12000000', '94000000'],  # Agricultura
    'A011': ['12000000'],  # Cultivo de plantas no perennes
    'A0111': ['12000000', '50000000'],  # Cereales
    'A0112': ['12000000', '50000000'],  # Arroz
    'A0113': ['12000000', '50000000'],  # Hortalizas
    'A0114': ['12000000', '50000000'],  # Frutas y nueces
    'A0115': ['12000000', '50000000'],  # Frutas tropicales
    'A0116': ['12000000'],  # Oleaginosas
    'A0119': ['12000000'],  # Otros cultivos
    'A012': ['12000000'],  # Cultivo de plantas perennes
    'A013': ['12000000'],  # Propagación de plantas
    'A014': ['12000000'],  # Ganadería
    'A015': ['12000000'],  # Agricultura y ganadería combinadas
    'A016': ['12000000'],  # Actividades de apoyo a la agricultura
    'A017': ['12000000'],  # Caza
    'A02': ['12000000', '94000000'],  # Silvicultura
    'A03': ['13000000', '95000000'],  # Pesca y acuicultura
    
    # Sección B - Explotación de minas y canteras
    'B05': ['20000000', '32000000'],  # Carbón
    'B06': ['30000000', '92000000'],  # Petróleo y gas
    'B07': ['11000000', '32000000'],  # Minerales metálicos
    'B08': ['11000000', '32000000'],  # Otros minerales
    'B09': ['31000000', '93000000'],  # Servicios de minería
    
    # Sección C - Industrias manufactureras
    'C10': ['50000000'],  # Productos alimenticios
    'C101': ['50000000'],  # Carne y pescado
    'C1010': ['50000000'],
    'C102': ['50000000'],  # Frutas y vegetales
    'C103': ['50000000'],  # Aceites y grasas
    'C104': ['50000000'],  # Lácteos
    'C105': ['50000000'],  # Molinería
    'C106': ['50000000'],  # Panadería
    'C107': ['50000000'],  # Otros alimentos
    'C108': ['50000000'],  # Alimentos preparados
    'C11': ['50000000'],  # Bebidas
    'C12': ['50000000'],  # Tabaco
    'C13': ['15000000'],  # Textiles
    'C14': ['15000000'],  # Prendas de vestir
    'C15': ['15000000'],  # Cuero y calzado
    'C16': ['16000000'],  # Madera y corcho
    'C17': ['16000000'],  # Papel y cartón
    'C18': ['16000000'],  # Impresión y reproducción
    'C19': ['60000000'],  # Coque y refinación
    'C20': ['60000000'],  # Productos químicos
    'C21': ['60000000', '90000000'],  # Farmacéuticos
    'C22': ['60000000'],  # Caucho y plástico
    'C23': ['70000000'],  # Minerales no metálicos
    'C24': ['14000000'],  # Metales comunes
    'C25': ['14000000', '45000000'],  # Productos de metal
    'C26': ['42000000'],  # Informática y electrónica
    'C27': ['41000000'],  # Maquinaria eléctrica
    'C28': ['14000000', '45000000'],  # Maquinaria y equipo
    'C29': ['22000000'],  # Vehículos automotores
    'C30': ['22000000'],  # Otro transporte
    'C31': ['25000000'],  # Muebles
    'C32': ['24000000'],  # Otras manufacturas
    'C33': ['63000000'],  # Instalación y mantenimiento
    
    # Sección D - Electricidad, gas y agua
    'D35': ['40000000', '44000000'],  # Electricidad y gas
    'E36': ['44000000'],  # Agua
    'E37': ['67000000'],  # Alcantarillado
    'E38': ['67000000', '66000000'],  # Gestión de desechos
    'E39': ['66000000'],  # Saneamiento ambiental
    
    # Sección F - Construcción (CRÍTICO para SECOP II)
    'F41': ['70000000', '72000000'],  # Construcción de edificios
    'F410': ['72000000', '72100000'],
    'F4101': ['72000000', '72100000'],  # Edificios residenciales
    'F4102': ['72000000', '72100000'],  # Edificios no residenciales
    'F42': ['70000000', '72000000', '72200000'],  # Infraestructura
    'F421': ['72000000', '72200000'],  # Carreteras
    'F4210': ['72000000', '72200000'],
    'F422': ['72000000', '72200000'],  # Proyectos de servicio público
    'F4220': ['72000000', '72200000'],
    'F429': ['72000000'],  # Otras construcciones
    'F43': ['70000000', '72000000'],  # Construcción especializada
    'F431': ['72000000'],  # Demolición
    'F432': ['70000000'],  # Instalaciones eléctricas
    'F433': ['70000000'],  # Acabados
    'F439': ['72000000'],  # Otras actividades
    
    # Sección G - Comercio
    'G45': ['22000000'],  # Venta de vehículos
    'G46': ['50000000'],  # Comercio al por mayor
    'G47': ['50000000'],  # Comercio al por menor
    
    # Sección H - Transporte
    'H49': ['52000000', '22000000'],  # Transporte terrestre
    'H50': ['52000000'],  # Transporte acuático
    'H51': ['52000000'],  # Transporte aéreo
    'H52': ['52000000'],  # Almacenamiento
    'H53': ['52000000'],  # Correos y mensajería
    
    # Sección I - Alojamiento y comida
    'I55': ['28000000', '58000000'],  # Alojamiento
    'I56': ['28000000', '58000000'],  # Comida
    
    # Sección J - Información y comunicaciones
    'J58': ['54000000'],  # Editoriales
    'J59': ['57000000'],  # Cine y video
    'J60': ['57000000'],  # Radio y TV
    'J61': ['53000000', '43000000'],  # Telecomunicaciones
    'J62': ['54000000', '10000000'],  # Desarrollo de software
    'J63': ['54000000'],  # Servicios de información
    
    # Sección K - Actividades financieras
    'K64': ['75000000', '48000000'],  # Servicios financieros
    'K65': ['75000000'],  # Seguros
    'K66': ['75000000'],  # Actividades auxiliares
    
    # Sección L - Inmobiliarias
    'L68': ['71000000'],  # Actividades inmobiliarias
    
    # Sección M - Profesionales, científicas y técnicas
    'M69': ['76000000', '51000000'],  # Jurídicas y contabilidad
    'M70': ['78000000'],  # Oficinas principales
    'M71': ['79000000', '51000000'],  # Arquitectura e ingeniería
    'M72': ['55000000'],  # Investigación y desarrollo
    'M73': ['57000000'],  # Publicidad
    'M74': ['51000000'],  # Otras actividades profesionales
    'M75': ['61000000'],  # Veterinarias
    
    # Sección N - Administrativas y de apoyo
    'N77': ['71000000'],  # Alquiler y arrendamiento
    'N78': ['73000000'],  # Empleo
    'N79': ['74000000'],  # Agencias de viajes
    'N80': ['65000000', '85000000'],  # Seguridad
    'N81': ['67000000', '68000000'],  # Edificios y jardines
    'N82': ['51000000'],  # Actividades de oficina
    
    # Sección O - Administración pública
    'O84': ['64000000', '91000000'],  # Administración pública
    
    # Sección P - Educación
    'P85': ['56000000', '17000000', '49000000'],  # Educación
    
    # Sección Q - Salud humana
    'Q86': ['61000000', '90000000', '47000000'],  # Salud
    'Q87': ['61000000'],  # Atención residencial
    'Q88': ['61000000'],  # Apoyo social
    
    # Sección R - Artes, entretenimiento y recreación
    'R90': ['59000000', '24000000'],  # Artes y entretenimiento
    'R91': ['59000000'],  # Bibliotecas y museos
    'R92': ['59000000'],  # Juegos de azar
    'R93': ['59000000', '24000000'],  # Deportes y recreación
    
    # Sección S - Otras actividades de servicios
    'S94': ['62000000'],  # Asociativas
    'S95': ['63000000'],  # Reparación
    'S96': ['89000000'],  # Servicios personales
    
    # Sección T - Hogares
    'T97': ['89000000'],  # Personal doméstico
    'T98': ['89000000'],  # Producción para uso propio
    
    # Sección U - Extraterritoriales
    'U99': ['64000000'],  # Organizaciones extraterritoriales
}

# Mapeo inverso: UNSPSC -> CIIU (muchos-a-muchos)
UNSPSC_A_CIIU: Dict[str, List[str]] = {}

for ciiu, unspscs in CIIU_A_UNSPSC.items():
    for unspsc in unspscs:
        if unspsc not in UNSPSC_A_CIIU:
            UNSPSC_A_CIIU[unspsc] = []
        UNSPSC_A_CIIU[unspsc].append(ciiu)


def mapear_ciiu_a_unspsc(codigo_ciiu: str) -> List[str]:
    """
    Mapear código CIIU a códigos UNSPSC relacionados.
    
    Parameters:
    - codigo_ciiu: Código CIIU (ej. 'F4101')
    
    Returns:
    - Lista de códigos UNSPSC relacionados
    """
    # Normalizar código (quitar ceros a la derecha para matching jerárquico)
    ciiu = str(codigo_ciiu).upper().rstrip('0')
    
    # Intentar matching exacto primero
    if ciiu in CIIU_A_UNSPSC:
        return CIIU_A_UNSPSC[ciiu]
    
    # Intentar matching por nivel superior (división)
    if len(ciiu) >= 2:
        division = ciiu[:2]
        for key, values in CIIU_A_UNSPSC.items():
            if key.startswith(division):
                return values
    
    # Default: retornar códigos genéricos de servicios
    return ['51000000']  # Servicios profesionales


def mapear_unspsc_a_ciiu(codigo_unspsc: str) -> List[str]:
    """
    Mapear código UNSPSC a códigos CIIU relacionados.
    
    Parameters:
    - codigo_unspsc: Código UNSPSC (ej. '72100000')
    
    Returns:
    - Lista de códigos CIIU relacionados
    """
    unspsc = str(codigo_unspsc)
    
    # Intentar matching exacto
    if unspsc in UNSPSC_A_CIIU:
        return UNSPSC_A_CIIU[unspsc]
    
    # Intentar matching por segmento (primeros 2 dígitos)
    if len(unspsc) >= 2:
        segmento = unspsc[:2]
        for key, values in UNSPSC_A_CIIU.items():
            if key.startswith(segmento):
                return values
    
    # Default: retornar CIIU genérico
    return ['M74']  # Otras actividades profesionales


def calcular_sinergia_sectorial(
    ciiu_municipios: Dict[str, str],
    unspsc_contratos: Dict[str, str],
) -> Dict[str, float]:
    """
    Calcular score de sinergia sectorial por municipio.
    
    Parameters:
    - ciiu_municipios: Dict {divipola: codigo_ciiu_predominante}
    - unspsc_contratos: Dict {divipola: codigo_unspsc_predominante}
    
    Returns:
    - Dict {divipola: score_sinergia (0-1)}
    """
    resultados = {}
    
    divipolas = set(ciiu_municipios.keys()) | set(unspsc_contratos.keys())
    
    for divipola in divipolas:
        ciiu = ciiu_municipios.get(divipola)
        unspsc = unspsc_contratos.get(divipola)
        
        if not ciiu or not unspsc:
            resultados[divipola] = 0.0
            continue
        
        # Obtener UNSPSC relacionados con el CIIU
        unspscs_relacionados = set(mapear_ciiu_a_unspsc(ciiu))
        
        # Verificar si el UNSPSC del contrato está relacionado
        if unspsc in unspscs_relacionados:
            resultados[divipola] = 1.0  # Sinergia alta
        else:
            # Verificar si hay relación parcial (mismo segmento)
            ciiu_unspsc = mapear_ciiu_a_unspsc(ciiu)
            if any(u[:2] == unspsc[:2] for u in ciiu_unspsc):
                resultados[divipola] = 0.5  # Sinergia media
            else:
                resultados[divipola] = 0.0  # Sinergia baja
    
    return resultados


def get_seccion_ciiu(codigo_ciiu: str) -> Optional[str]:
    """
    Obtener sección CIIU a partir del código.
    
    Parameters:
    - codigo_ciiu: Código CIIU
    
    Returns:
    - Letra de sección o None
    """
    if codigo_ciiu and len(codigo_ciiu) >= 1:
        return codigo_ciiu[0].upper()
    return None


def get_sector_descripcion(codigo_ciiu: str) -> str:
    """
    Obtener descripción del sector CIIU.
    
    Parameters:
    - codigo_ciiu: Código CIIU
    
    Returns:
    - Descripción del sector
    """
    descripciones_seccion = {
        'A': 'Agricultura, ganadería, caza y silvicultura',
        'B': 'Explotación de minas y canteras',
        'C': 'Industrias manufactureras',
        'D': 'Suministro de electricidad, gas y agua',
        'E': 'Suministro de agua y saneamiento',
        'F': 'Construcción',
        'G': 'Comercio',
        'H': 'Transporte y almacenamiento',
        'I': 'Alojamiento y servicios de comida',
        'J': 'Información y comunicaciones',
        'K': 'Actividades financieras y de seguros',
        'L': 'Actividades inmobiliarias',
        'M': 'Actividades profesionales, científicas y técnicas',
        'N': 'Actividades administrativas y de apoyo',
        'O': 'Administración pública y defensa',
        'P': 'Educación',
        'Q': 'Salud humana y de apoyo social',
        'R': 'Artes, entretenimiento y recreación',
        'S': 'Otras actividades de servicios',
        'T': 'Actividades de hogares',
        'U': 'Actividades extraterritoriales',
    }
    
    seccion = get_seccion_ciiu(codigo_ciiu)
    return descripciones_seccion.get(seccion, 'Sector no clasificado')


if __name__ == "__main__":
    # Ejemplo de uso
    print("Mapeo CIIU -> UNSPSC")
    print(f"F4101 (Construcción residencial) -> {mapear_ciiu_a_unspsc('F4101')}")
    print(f"A0111 (Cultivo de cereales) -> {mapear_ciiu_a_unspsc('A0111')}")
    
    print("\nMapeo UNSPSC -> CIIU")
    print(f"72100000 (Construcción edificios) -> {mapear_unspsc_a_ciiu('72100000')}")
    print(f"50000000 (Alimentos) -> {mapear_unspsc_a_ciiu('50000000')}")
    
    print("\nDescripciones de sector")
    print(f"F4101 -> {get_sector_descripcion('F4101')}")
    print(f"A0111 -> {get_sector_descripcion('A0111')}")
