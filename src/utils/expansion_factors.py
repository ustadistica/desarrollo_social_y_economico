"""
Factores de expansión del DANE para proyecciones de población.

Basado en las Proyecciones de Población del DANE 2018-2035.
Estos factores permiten expandir muestras censales a nivel poblacional.

Nota: En producción, cargar desde archivo oficial del DANE.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


# Factores de expansión por departamento y año (ejemplo simplificado)
# En producción, usar factores oficiales del DANE por municipio
FACTORES_EXPANSION: Dict[str, Dict[str, float]] = {
    # Estructura: {divipola_departamento: {anio: factor}}
    
    # Bogotá D.C. (11)
    '11': {
        '2024': 1.02,
        '2025': 1.03,
    },
    
    # Antioquia (05)
    '05': {
        '2024': 1.05,
        '2025': 1.06,
    },
    
    # Valle del Cauca (76)
    '76': {
        '2024': 1.04,
        '2025': 1.05,
    },
    
    # Atlántico (08)
    '08': {
        '2024': 1.03,
        '2025': 1.04,
    },
    
    # Bolívar (13)
    '13': {
        '2024': 1.06,
        '2025': 1.07,
    },
    
    # Córdoba (23)
    '23': {
        '2024': 1.08,
        '2025': 1.09,
    },
    
    # Sucre (70)
    '70': {
        '2024': 1.07,
        '2025': 1.08,
    },
    
    # Magdalena (47)
    '47': {
        '2024': 1.06,
        '2025': 1.07,
    },
    
    # Cesar (20)
    '20': {
        '2024': 1.05,
        '2025': 1.06,
    },
    
    # La Guajira (44)
    '44': {
        '2024': 1.09,
        '2025': 1.10,
    },
    
    # Santander (68)
    '68': {
        '2024': 1.03,
        '2025': 1.04,
    },
    
    # Norte de Santander (54)
    '54': {
        '2024': 1.05,
        '2025': 1.06,
    },
    
    # Boyacá (15)
    '15': {
        '2024': 1.04,
        '2025': 1.05,
    },
    
    # Cundinamarca (25)
    '25': {
        '2024': 1.03,
        '2025': 1.04,
    },
    
    # Meta (50)
    '50': {
        '2024': 1.07,
        '2025': 1.08,
    },
    
    # Casanare (85)
    '85': {
        '2024': 1.08,
        '2025': 1.09,
    },
    
    # Arauca (81)
    '81': {
        '2024': 1.06,
        '2025': 1.07,
    },
    
    # Nariño (52)
    '52': {
        '2024': 1.05,
        '2025': 1.06,
    },
    
    # Cauca (19)
    '19': {
        '2024': 1.06,
        '2025': 1.07,
    },
    
    # Chocó (27)
    '27': {
        '2024': 1.10,
        '2025': 1.11,
    },
    
    # Huila (41)
    '41': {
        '2024': 1.04,
        '2025': 1.05,
    },
    
    # Tolima (73)
    '73': {
        '2024': 1.04,
        '2025': 1.05,
    },
    
    # Caldas (17)
    '17': {
        '2024': 1.02,
        '2025': 1.03,
    },
    
    # Risaralda (66)
    '66': {
        '2024': 1.02,
        '2025': 1.03,
    },
    
    # Quindío (63)
    '63': {
        '2024': 1.02,
        '2025': 1.03,
    },
    
    # Amazonas (91)
    '91': {
        '2024': 1.08,
        '2025': 1.09,
    },
    
    # Guainía (94)
    '94': {
        '2024': 1.09,
        '2025': 1.10,
    },
    
    # Guaviare (95)
    '95': {
        '2024': 1.08,
        '2025': 1.09,
    },
    
    # Vaupés (97)
    '97': {
        '2024': 1.09,
        '2025': 1.10,
    },
    
    # Vichada (99)
    '99': {
        '2024': 1.08,
        '2025': 1.09,
    },
    
    # Putumayo (86)
    '86': {
        '2024': 1.07,
        '2025': 1.08,
    },
    
    # Caquetá (18)
    '18': {
        '2024': 1.07,
        '2025': 1.08,
    },
    
    # San Andrés y Providencia (88)
    '88': {
        '2024': 1.03,
        '2025': 1.04,
    },
}

# Factor por defecto para departamentos no listados
FACTOR_POR_DEFECTO = 1.05


def get_factor_expansion(divipola_departamento: str, anio: int) -> float:
    """
    Obtener factor de expansión para un departamento y año.
    
    Parameters:
    - divipola_departamento: Código DIVIPOLA del departamento (2 dígitos)
    - anio: Año de proyección
    
    Returns:
    - Factor de expansión
    """
    divipola = str(divipola_departamento).zfill(2)
    anio_str = str(anio)
    
    if divipola in FACTORES_EXPANSION:
        factores_dep = FACTORES_EXPANSION[divipola]
        
        if anio_str in factores_dep:
            return factores_dep[anio_str]
        
        # Interpolación simple si el año no está disponible
        años_disponibles = sorted([int(a) for a in factores_dep.keys()])
        
        if len(años_disponibles) >= 2:
            # Interpolar entre años disponibles
            if anio < años_disponibles[0]:
                return factores_dep[str(años_disponibles[0])]
            elif anio > años_disponibles[-1]:
                return factores_dep[str(años_disponibles[-1])]
            else:
                # Interpolación lineal
                for i in range(len(años_disponibles) - 1):
                    año_inf = años_disponibles[i]
                    año_sup = años_disponibles[i + 1]
                    
                    if año_inf <= anio <= año_sup:
                        factor_inf = factores_dep[str(año_inf)]
                        factor_sup = factores_dep[str(año_sup)]
                        
                        peso = (anio - año_inf) / (año_sup - año_inf)
                        return factor_inf + peso * (factor_sup - factor_inf)
    
    # Retornar factor por defecto
    logger.warning(f"Factor no encontrado para {divipola}/{anio}, usando default: {FACTOR_POR_DEFECTO}")
    return FACTOR_POR_DEFECTO


def aplicar_factor_expansion(
    muestra_count: int,
    divipola_departamento: str,
    anio: int,
) -> int:
    """
    Aplicar factor de expansión a un conteo muestral.
    
    Parameters:
    - muestra_count: Conteo de la muestra
    - divipola_departamento: Código DIVIPOLA del departamento
    - anio: Año de proyección
    
    Returns:
    - Población expandida (redondeada a entero)
    """
    factor = get_factor_expansion(divipola_departamento, anio)
    return round(muestra_count * factor)


def get_poblacion_proyectada(
    poblacion_base: int,
    divipola_departamento: str,
    anio_base: int,
    anio_proyeccion: int,
) -> int:
    """
    Proyectar población de un año base a un año de proyección.
    
    Parameters:
    - poblacion_base: Población en año base
    - divipola_departamento: Código DIVIPOLA del departamento
    - anio_base: Año base (ej. 2018)
    - anio_proyeccion: Año de proyección (ej. 2025)
    
    Returns:
    - Población proyectada
    """
    factor_base = get_factor_expansion(divipola_departamento, anio_base)
    factor_proyeccion = get_factor_expansion(divipola_departamento, anio_proyeccion)
    
    # Razón de factores
    razon = factor_proyeccion / factor_base
    
    return round(poblacion_base * razon)


def cargar_factores_desde_csv(archivo_csv: str) -> Dict[str, Dict[str, float]]:
    """
    Cargar factores de expansión desde archivo CSV.
    
    Parameters:
    - archivo_csv: Ruta al archivo CSV
    
    Returns:
    - Dict con factores de expansión
    """
    import pandas as pd
    from pathlib import Path
    
    archivo_path = Path(archivo_csv)
    
    if not archivo_path.exists():
        logger.warning(f"Archivo de factores no encontrado: {archivo_path}")
        logger.info("Usando factores embebidos")
        return FACTORES_EXPANSION
    
    try:
        df = pd.read_csv(archivo_path)
        
        factores = {}
        for _, row in df.iterrows():
            divipola = str(row['divipola_departamento']).zfill(2)
            anio = str(row['anio'])
            factor = float(row['factor_expansion'])
            
            if divipola not in factores:
                factores[divipola] = {}
            factores[divipola][anio] = factor
        
        logger.info(f"Factores de expansión cargados: {len(factores)} departamentos")
        
        return factores
        
    except Exception as e:
        logger.error(f"Error cargando factores: {e}")
        logger.info("Usando factores embebidos")
        return FACTORES_EXPANSION


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    print("Factores de Expansión DANE")
    print("=" * 40)
    
    # Obtener factor para Bogotá 2025
    factor = get_factor_expansion('11', 2025)
    print(f"Bogotá 2025: {factor}")
    
    # Aplicar factor a muestra
    muestra = 1000
    expandida = aplicar_factor_expansion(muestra, '11', 2025)
    print(f"Muestra: {muestra} -> Expandida: {expandida}")
    
    # Proyección de población
    poblacion_2018 = 7000000
    poblacion_2025 = get_poblacion_proyectada(poblacion_2018, '11', 2018, 2025)
    print(f"Población Bogotá 2018: {poblacion_2018} -> 2025: {poblacion_2025}")
