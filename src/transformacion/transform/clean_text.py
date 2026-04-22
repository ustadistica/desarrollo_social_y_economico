"""
Limpieza y normalización de texto para datos socioeconómicos.

Funciones:
- Normalización Unicode (NFKC)
- Eliminación de caracteres especiales
- Estandarización de mayúsculas/minúsculas
- Limpieza de espacios en blanco
"""

import re
import unicodedata
import logging
from typing import Union, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def normalize_unicode(text: str, form: str = "NFKC") -> str:
    """
    Normalizar texto usando Unicode NFKC.
    
    Parameters:
    - text: Texto a normalizar
    - form: Forma de normalización ('NFC', 'NFD', 'NFKC', 'NFKD')
    
    Returns:
    - Texto normalizado
    """
    if not isinstance(text, str):
        return text
    
    # Normalizar Unicode
    text = unicodedata.normalize(form, text)
    
    # Eliminar caracteres de control (excepto newline, tab)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)
    
    # Estandarizar espacios en blanco múltiples
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_text_column(
    df: pd.DataFrame,
    column: str,
    case: str = "title",
    remove_special: bool = True,
    strip_whitespace: bool = True,
) -> pd.DataFrame:
    """
    Limpiar columna de texto en DataFrame.
    
    Parameters:
    - df: DataFrame original
    - column: Nombre de la columna a limpiar
    - case: Transformación de caso ('upper', 'lower', 'title', 'sentence', None)
    - remove_special: Eliminar caracteres especiales
    - strip_whitespace: Eliminar espacios en blanco al inicio/final
    
    Returns:
    - DataFrame con columna limpia
    """
    if column not in df.columns:
        logger.warning(f"Columna {column} no existe en el DataFrame")
        return df
    
    def clean_value(value) -> str:
        if pd.isna(value) or value is None:
            return value
        
        if not isinstance(value, str):
            return str(value)
        
        # Normalizar Unicode
        value = normalize_unicode(value)
        
        # Eliminar caracteres especiales
        if remove_special:
            # Mantener letras, números, espacios y caracteres españoles básicos
            value = re.sub(r'[^\w\sáéíóúÁÉÍÓÚñÑüÜ¿?¡!,.\-:;()\'"]', '', value)
        
        # Aplicar transformación de caso
        if case == "upper":
            value = value.upper()
        elif case == "lower":
            value = value.lower()
        elif case == "title":
            value = value.title()
        elif case == "sentence":
            value = _sentence_case(value)
        
        # Eliminar espacios en blanco
        if strip_whitespace:
            value = value.strip()
        
        return value
    
    df[column] = df[column].apply(clean_value)
    
    return df


def _sentence_case(text: str) -> str:
    """
    Convertir texto a tipo oración (primera letra mayúscula).
    
    Parameters:
    - text: Texto original
    
    Returns:
    - Texto en sentence case
    """
    if not text:
        return text
    
    # Primera letra mayúscula, resto minúscula
    return text[0].upper() + text[1:].lower() if len(text) > 1 else text.upper()


def clean_multiple_columns(
    df: pd.DataFrame,
    columns_config: dict,
) -> pd.DataFrame:
    """
    Limpiar múltiples columnas con configuraciones diferentes.
    
    Parameters:
    - df: DataFrame original
    - columns_config: Dict {columna: config}
    
    Returns:
    - DataFrame con columnas limpias
    
    Example:
    ```python
    config = {
        'nombre_municipio': {'case': 'title', 'remove_special': True},
        'codigo_ciiu': {'case': 'upper', 'remove_special': True},
        'objeto_contrato': {'case': 'sentence', 'remove_special': False},
    }
    df = clean_multiple_columns(df, config)
    ```
    """
    for column, config in columns_config.items():
        df = clean_text_column(
            df,
            column,
            case=config.get('case', 'title'),
            remove_special=config.get('remove_special', True),
            strip_whitespace=config.get('strip_whitespace', True),
        )
    
    return df


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estandarizar nombres de columnas a snake_case.
    
    Parameters:
    - df: DataFrame original
    
    Returns:
    - DataFrame con columnas en snake_case
    """
    def to_snake_case(name: str) -> str:
        # Reemplazar espacios con guiones bajos
        name = name.replace(' ', '_')
        
        # Reemplazar caracteres especiales
        name = re.sub(r'[^\w]', '_', name)
        
        # Convertir CamelCase a snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name)
        
        # Convertir a minúsculas
        name = name.lower()
        
        # Eliminar guiones bajos múltiples
        name = re.sub(r'_+', '_', name)
        
        # Eliminar guiones bajos al inicio/final
        name = name.strip('_')
        
        return name
    
    # Renombrar columnas
    new_columns = {col: to_snake_case(col) for col in df.columns}
    df = df.rename(columns=new_columns)
    
    return df


def remove_duplicate_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Eliminar columnas duplicadas en el DataFrame.
    
    Parameters:
    - df: DataFrame original
    
    Returns:
    - DataFrame sin columnas duplicadas
    """
    # Identificar columnas duplicadas
    seen = set()
    duplicate_cols = []
    
    for col in df.columns:
        if col in seen:
            duplicate_cols.append(col)
        else:
            seen.add(col)
    
    if duplicate_cols:
        logger.info(f"Eliminando columnas duplicadas: {duplicate_cols}")
        df = df.drop(columns=duplicate_cols)
    
    return df


if __name__ == "__main__":
    # Ejemplo de uso
    logging.basicConfig(level=logging.INFO)
    
    df = pd.DataFrame({
        'nombre': ['  MARÍA  ', 'JUAN  pérez', '  josé  '],
        'ciudad': ['bogotá d.c.', 'MEDELLÍN', '  cali  '],
    })
    
    print("Original:")
    print(df)
    
    df = clean_text_column(df, 'nombre', case='title')
    df = clean_text_column(df, 'ciudad', case='title')
    
    print("\nLimpio:")
    print(df)
