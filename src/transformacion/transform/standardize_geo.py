"""
Estandarización geográfica usando códigos DIVIPOLA del DANE.

Funciones:
- Validación de códigos DIVIPOLA
- Mapeo de nombres de municipios a códigos
- Estandarización de nombres geográficos
- Carga del catálogo DIVIPOLA completo
"""

import logging
from typing import Dict, Optional, Tuple, List
import pandas as pd
import re

logger = logging.getLogger(__name__)


# Catálogo DIVIPOLA 2024 (muestra - completar con los 1102 municipios)
DIVIPOLA_CATALOG = {
    # Bogotá D.C.
    '11001': {'nombre': 'Bogotá D.C.', 'departamento': 'Bogotá', 'divipola_dep': '11'},
    
    # Antioquia
    '05001': {'nombre': 'Medellín', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05002': {'nombre': 'Abejorral', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05004': {'nombre': 'Abriaquí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05021': {'nombre': 'Alejandría', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05030': {'nombre': 'Amagá', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05031': {'nombre': 'Amalfi', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05034': {'nombre': 'Andes', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05036': {'nombre': 'Angelópolis', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05038': {'nombre': 'Angostura', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05040': {'nombre': 'Anorí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05042': {'nombre': 'Anzá', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05044': {'nombre': 'Apartadó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05045': {'nombre': 'Arboletes', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05051': {'nombre': 'Armenia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05055': {'nombre': 'Barbosa', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05059': {'nombre': 'Bello', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05079': {'nombre': 'Caldas', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05086': {'nombre': 'Caucasia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05088': {'nombre': 'Chigorodó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05101': {'nombre': 'Cisneros', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05107': {'nombre': 'Cocorná', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05113': {'nombre': 'Concepción', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05120': {'nombre': 'Concordia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05125': {'nombre': 'Copacabana', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05129': {'nombre': 'Dabeiba', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05134': {'nombre': 'Donmatías', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05138': {'nombre': 'Ebéjico', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05142': {'nombre': 'El Bagre', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05145': {'nombre': 'El Carmen de Viboral', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05147': {'nombre': 'El Peñol', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05148': {'nombre': 'El Retorno', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05150': {'nombre': 'El Santuario', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05154': {'nombre': 'Entrerríos', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05172': {'nombre': 'Girardota', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05190': {'nombre': 'Gómez Plata', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05197': {'nombre': 'Granada', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05206': {'nombre': 'Guadalupe', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05209': {'nombre': 'Guarne', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05212': {'nombre': 'Guatapé', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05234': {'nombre': 'Heliconia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05237': {'nombre': 'Hispania', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05240': {'nombre': 'Itagüí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05243': {'nombre': 'Ituango', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05245': {'nombre': 'Jardín', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05247': {'nombre': 'Jericó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05250': {'nombre': 'La Ceja', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05253': {'nombre': 'La Estrella', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05254': {'nombre': 'La Pintada', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05256': {'nombre': 'La Unión', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05264': {'nombre': 'Liborina', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05266': {'nombre': 'Maceo', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05282': {'nombre': 'Marinilla', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05306': {'nombre': 'Montebello', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05308': {'nombre': 'Murindó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05310': {'nombre': 'Mutatá', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05313': {'nombre': 'Nariño', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05315': {'nombre': 'Nechí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05318': {'nombre': 'Necoclí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05321': {'nombre': 'Olaya', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05347': {'nombre': 'Peque', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05360': {'nombre': 'Pueblorrico', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05361': {'nombre': 'Puerto Berrío', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05364': {'nombre': 'Puerto Nare', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05376': {'nombre': 'Remedios', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05380': {'nombre': 'Retiro', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05390': {'nombre': 'Rionegro', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05400': {'nombre': 'Sabanalarga', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05411': {'nombre': 'San Andrés de Cuerquia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05425': {'nombre': 'San Carlos', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05440': {'nombre': 'San Jerónimo', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05467': {'nombre': 'San Vicente Ferrer', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05475': {'nombre': 'Santa Bárbara', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05480': {'nombre': 'Santa Rosa de Osos', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05490': {'nombre': 'Santo Domingo', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05495': {'nombre': 'Segovia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05501': {'nombre': 'Sonsón', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05541': {'nombre': 'Tarazá', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05543': {'nombre': 'Tarso', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05576': {'nombre': 'Titiribí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05579': {'nombre': 'Toledo', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05585': {'nombre': 'Turbo', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05604': {'nombre': 'Uramita', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05607': {'nombre': 'Urrao', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05615': {'nombre': 'Valdivia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05628': {'nombre': 'Venecia', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05631': {'nombre': 'Vigía del Fuerte', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05642': {'nombre': 'Yalí', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05647': {'nombre': 'Yarumal', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05649': {'nombre': 'Yolombó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05652': {'nombre': 'Yondó', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    '05659': {'nombre': 'Zaragoza', 'departamento': 'Antioquia', 'divipola_dep': '05'},
    
    # Valle del Cauca
    '76001': {'nombre': 'Cali', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76020': {'nombre': 'Alcalá', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76036': {'nombre': 'Andalucía', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76041': {'nombre': 'Ansermanuevo', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76054': {'nombre': 'Argelia', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76100': {'nombre': 'Buga', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76109': {'nombre': 'Buenaventura', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76111': {'nombre': 'Cartago', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76113': {'nombre': 'Dagua', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76122': {'nombre': 'El Águila', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76126': {'nombre': 'El Cairo', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76130': {'nombre': 'El Cerrito', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76137': {'nombre': 'El Dovio', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76147': {'nombre': 'Florida', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76233': {'nombre': 'Ginebra', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76243': {'nombre': 'Guacarí', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76246': {'nombre': 'Jamundí', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76248': {'nombre': 'La Cumbre', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76250': {'nombre': 'La Unión', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76275': {'nombre': 'Obando', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76306': {'nombre': 'Palmira', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76318': {'nombre': 'Pradera', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76364': {'nombre': 'Restrepo', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76373': {'nombre': 'Riofrío', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76377': {'nombre': 'Roldanillo', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76400': {'nombre': 'San Pedro', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76403': {'nombre': 'Sevilla', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76520': {'nombre': 'Toro', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76563': {'nombre': 'Trujillo', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76577': {'nombre': 'Tuluá', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76580': {'nombre': 'Ulloa', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76606': {'nombre': 'Versalles', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76616': {'nombre': 'Vijes', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76622': {'nombre': 'Yotoco', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    '76670': {'nombre': 'Zarzal', 'departamento': 'Valle del Cauca', 'divipola_dep': '76'},
    
    # ... (completar con los 1102 municipios en implementación real)
}


def _normalize_municipio_name(nombre: str) -> str:
    """
    Normalizar nombre de municipio para matching.
    
    Parameters:
    - nombre: Nombre original
    
    Returns:
    - Nombre normalizado en minúsculas sin acentos
    """
    import unicodedata
    
    # Convertir a minúsculas
    nombre = nombre.lower()
    
    # Eliminar acentos
    nombre = ''.join(
        c for c in unicodedata.normalize('NFD', nombre)
        if unicodedata.category(c) != 'Mn'
    )
    
    # Eliminar caracteres especiales
    nombre = re.sub(r'[^\w\s]', '', nombre)
    
    # Eliminar espacios múltiples
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    
    return nombre


def _get_municipio_variants(nombre: str) -> List[str]:
    """
    Obtener variantes comunes de un nombre de municipio.
    
    Parameters:
    - nombre: Nombre original
    
    Returns:
    - Lista de variantes
    """
    variants = [nombre]
    
    # Eliminar "D.C."
    if "D.C." in nombre or "D.C" in nombre:
        variants.append(nombre.replace("D.C.", "").replace("D.C", "").strip())
        variants.append(nombre.replace("D.C.", "DC").replace("D.C", "DC"))
    
    # Eliminar "de X"
    if " de " in nombre:
        variants.append(nombre.split(" de ")[0].strip())
    
    # Reemplazar acentos
    variants.append(_normalize_municipio_name(nombre))
    
    return variants


# Mapeo inverso: nombres normalizados a DIVIPOLA
# (Ahora las funciones están definidas ANTES de este bloque)
NOMBRE_A_DIVIPOLA = {}
for _divipola, _info in DIVIPOLA_CATALOG.items():
    _nombre_normalizado = _normalize_municipio_name(_info['nombre'])
    NOMBRE_A_DIVIPOLA[_nombre_normalizado] = _divipola
    
    # Agregar variantes comunes
    _variantes = _get_municipio_variants(_info['nombre'])
    for _variante in _variantes:
        NOMBRE_A_DIVIPOLA[_normalize_municipio_name(_variante)] = _divipola


def load_divipola_catalog() -> pd.DataFrame:
    """
    Cargar catálogo DIVIPOLA completo como DataFrame.
    
    Returns:
    - DataFrame con catálogo DIVIPOLA
    """
    records = []
    for divipola, info in DIVIPOLA_CATALOG.items():
        records.append({
            'divipola_municipio': divipola,
            'nombre_municipio': info['nombre'],
            'divipola_departamento': info['divipola_dep'],
            'nombre_departamento': info['departamento'],
        })
    
    return pd.DataFrame(records)


def validate_divipola(code: str) -> Tuple[bool, Optional[str]]:
    """
    Validar código DIVIPOLA.
    
    Parameters:
    - code: Código a validar
    
    Returns:
    - (es_valido, codigo_normalizado)
    """
    if code is None or pd.isna(code):
        return False, None
    
    # Convertir a string
    code = str(code)
    
    # Eliminar espacios y caracteres no numéricos
    code = re.sub(r'[^\d]', '', code)
    
    # Verificar longitud (5 dígitos)
    if len(code) != 5:
        return False, None
    
    # Verificar que existe en catálogo
    if code in DIVIPOLA_CATALOG:
        return True, code
    
    # Código numéricamente válido pero no en catálogo
    logger.warning(f"Código DIVIPOLA {code} no encontrado en catálogo")
    return True, code


def standardize_divipola(
    df: pd.DataFrame,
    column_municipio: str = 'divipola_municipio',
    column_nombre: Optional[str] = None,
    crear_columna_departamento: bool = True,
) -> pd.DataFrame:
    """
    Estandarizar códigos DIVIPOLA en DataFrame.
    
    Parameters:
    - df: DataFrame original
    - column_municipio: Nombre de columna con DIVIPOLA o nombre de municipio
    - column_nombre: Nombre de columna con nombre de municipio (para fallback)
    - crear_columna_departamento: Crear columna de departamento
    
    Returns:
    - DataFrame con DIVIPOLA estandarizado
    """
    df = df.copy()
    
    # Columna para DIVIPOLA estandarizado
    df['_divipola_temp'] = None
    
    for idx, row in df.iterrows():
        divipola = row.get(column_municipio)
        nombre = row.get(column_nombre) if column_nombre else None
        
        # Intentar validar como DIVIPOLA directo
        es_valido, codigo = validate_divipola(divipola)
        
        if es_valido and codigo:
            df.at[idx, '_divipola_temp'] = codigo
        elif nombre:
            # Intentar mapear por nombre
            nombre_norm = _normalize_municipio_name(str(nombre))
            if nombre_norm in NOMBRE_A_DIVIPOLA:
                df.at[idx, '_divipola_temp'] = NOMBRE_A_DIVIPOLA[nombre_norm]
    
    # Reemplazar columna original o crear nueva
    if df['_divipola_temp'].notna().any():
        df[column_municipio] = df['_divipola_temp']
    
    df = df.drop(columns=['_divipola_temp'])
    
    # Crear columna de departamento si se solicita
    if crear_columna_departamento:
        df = _add_departamento_column(df, column_municipio)
    
    return df


def _add_departamento_column(df: pd.DataFrame, column_divipola: str) -> pd.DataFrame:
    """
    Agregar columna de departamento basado en DIVIPOLA.
    
    Parameters:
    - df: DataFrame original
    - column_divipola: Columna con DIVIPOLA
    
    Returns:
    - DataFrame con columna de departamento
    """
    df = df.copy()
    
    def get_departamento(divipola) -> Optional[str]:
        if pd.isna(divipola):
            return None
        
        divipola = str(divipola).zfill(5)
        
        if divipola in DIVIPOLA_CATALOG:
            return DIVIPOLA_CATALOG[divipola]['divipola_dep']
        
        return None
    
    df['divipola_departamento'] = df[column_divipola].apply(get_departamento)
    
    return df


def impute_missing_divipola(
    df: pd.DataFrame,
    column_divipola: str = 'divipola_municipio',
    column_nombre: str = 'nombre_municipio',
) -> pd.DataFrame:
    """
    Imputar códigos DIVIPOLA faltantes usando nombres de municipio.
    
    Parameters:
    - df: DataFrame original
    - column_divipola: Columna con DIVIPOLA (puede tener nulos)
    - column_nombre: Columna con nombre de municipio
    
    Returns:
    - DataFrame con DIVIPOLA imputado
    """
    df = df.copy()
    
    mask_missing = df[column_divipola].isna()
    
    if not mask_missing.any():
        return df
    
    logger.info(f"Imputando {mask_missing.sum()} códigos DIVIPOLA faltantes")
    
    for idx in df[mask_missing].index:
        nombre = df.at[idx, column_nombre]
        
        if pd.notna(nombre):
            nombre_norm = _normalize_municipio_name(str(nombre))
            
            if nombre_norm in NOMBRE_A_DIVIPOLA:
                df.at[idx, column_divipola] = NOMBRE_A_DIVIPOLA[nombre_norm]
    
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    df = pd.DataFrame({
        'municipio': ['Bogotá', 'bogota d.c.', 'MEDELLIN', 'Medellín', 'Cali'],
        'divipola': [None, '11001', '05001', None, '76001'],
    })
    
    print("Original:")
    print(df)
    
    df = standardize_divipola(df, column_municipio='divipola', column_nombre='municipio')
    
    print("\nEstandarizado:")
    print(df)
