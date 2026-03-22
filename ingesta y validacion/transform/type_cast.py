"""
Tipificación y conversión de tipos de datos para capa Plata.

Funciones:
- Conversión a tipos PyArrow optimizados
- Validación de esquemas
- Manejo de valores nulos y conversiones fallidas
"""

import logging
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


# Esquema estándar para capa Plata
PLATA_SCHEMA: Dict[str, str] = {
    # Identificadores geográficos
    'divipola_municipio': 'string[pyarrow]',
    'divipola_departamento': 'string[pyarrow]',
    'nombre_municipio': 'string[pyarrow]',
    'nombre_departamento': 'string[pyarrow]',
    
    # Identificadores de tiempo
    'fecha_key': 'int32[pyarrow]',
    'anio': 'int32[pyarrow]',
    'mes': 'int32[pyarrow]',
    'trimestre': 'int32[pyarrow]',
    
    # Identificadores económicos
    'codigo_ciiu': 'string[pyarrow]',
    'codigo_unspsc': 'string[pyarrow]',
    'nit_proveedor': 'string[pyarrow]',  # Enmascarado para secreto estadístico
    
    # Identificadores de contrato
    'id_contrato': 'string[pyarrow]',
    'id_entidad': 'int32[pyarrow]',
    'id_proveedor': 'int32[pyarrow]',  # Hash del NIT
    
    # Montos (decimales de alta precisión)
    'monto_contrato': 'float64[pyarrow]',
    'monto_ejecutado': 'float64[pyarrow]',
    'monto_pagado': 'float64[pyarrow]',
    
    # Indicadores de vulnerabilidad (0-1 range)
    'ipm_total': 'float32[pyarrow]',
    'ipm_educacion': 'float32[pyarrow]',
    'ipm_ninez': 'float32[pyarrow]',
    'ipm_trabajo': 'float32[pyarrow]',
    'ipm_salud': 'float32[pyarrow]',
    'deficit_habitacional_cuantitativo': 'float32[pyarrow]',
    'deficit_habitacional_cualitativo': 'float32[pyarrow]',
    'nbi_total': 'float32[pyarrow]',
    'pobreza_monetaria': 'float32[pyarrow]',
    'pobreza_extrema': 'float32[pyarrow]',
    
    # Indicadores de tejido productivo
    'total_micronegocios': 'int32[pyarrow]',
    'micronegocios_formales': 'int32[pyarrow]',
    'micronegocios_informales': 'int32[pyarrow]',
    'economia_popular_unidades': 'int32[pyarrow]',
    'economia_popular_empleo': 'int32[pyarrow]',
    'empleo_total': 'int32[pyarrow]',
    'empleo_formal': 'int32[pyarrow]',
    'empleo_informal': 'int32[pyarrow]',
    'tasa_formalizacion': 'float32[pyarrow]',
    
    # Población
    'poblacion_total': 'int32[pyarrow]',
    'poblacion_vulnerable': 'int32[pyarrow]',
    'factor_expansion': 'float32[pyarrow]',
    
    # Banderas
    'es_economia_popular': 'bool[pyarrow]',
    'es_formalizacion': 'bool[pyarrow]',
    'es_fin_mes': 'bool[pyarrow]',
    'es_fin_trimestre': 'bool[pyarrow]',
    'es_fin_anio': 'bool[pyarrow]',
    
    # Estados y categorías
    'estado_contrato': 'string[pyarrow]',
    'modalidad_seleccion': 'string[pyarrow]',
    'sector_predominante': 'string[pyarrow]',
    'categoria_municipal': 'string[pyarrow]',
    
    # Metadatos de ingesta
    '_ingestion_timestamp': 'string[pyarrow]',
    '_source': 'string[pyarrow]',
    '_source_version': 'string[pyarrow]',
    '_checksum_md5': 'string[pyarrow]',
}


def cast_to_schema(
    df: pd.DataFrame,
    schema: Optional[Dict[str, str]] = None,
    errors: str = 'coerce',
) -> pd.DataFrame:
    """
    Convertir DataFrame a esquema de tipos especificado.
    
    Parameters:
    - df: DataFrame original
    - schema: Diccionario {columna: tipo} (default: PLATA_SCHEMA)
    - errors: Cómo manejar errores ('raise', 'coerce', 'ignore')
    
    Returns:
    - DataFrame con tipos convertidos
    """
    if schema is None:
        schema = PLATA_SCHEMA
    
    df = df.copy()
    
    for column, target_type in schema.items():
        if column not in df.columns:
            continue
        
        try:
            df[column] = _cast_column(df[column], target_type)
        except Exception as e:
            if errors == 'raise':
                raise
            elif errors == 'coerce':
                logger.warning(f"Error convirtiendo {column} a {target_type}: {e}")
                df[column] = pd.NA
            # 'ignore' no hace nada
    
    return df


def _cast_column(series: pd.Series, target_type: str) -> pd.Series:
    """
    Convertir una columna a tipo específico.
    
    Parameters:
    - series: Serie original
    - target_type: Tipo objetivo (formato PyArrow)
    
    Returns:
    - Serie convertida
    """
    # Manejar valores nulos primero
    is_null = series.isna()
    
    # Parsear tipo
    base_type = target_type.split('[')[0]
    
    if base_type == 'string':
        return _cast_to_string(series)
    
    elif base_type == 'int32':
        return _cast_to_int32(series)
    
    elif base_type == 'int64':
        return _cast_to_int64(series)
    
    elif base_type == 'float32':
        return _cast_to_float32(series)
    
    elif base_type == 'float64':
        return _cast_to_float64(series)
    
    elif base_type == 'bool':
        return _cast_to_bool(series)
    
    elif base_type == 'date32':
        return _cast_to_date(series)
    
    else:
        # Mantener tipo original
        return series


def _cast_to_string(series: pd.Series) -> pd.Series:
    """Convertir a string PyArrow."""
    # Convertir a string, manteniendo nulos
    series = series.astype('string')
    return series


def _cast_to_int32(series: pd.Series) -> pd.Series:
    """Convertir a int32 PyArrow."""
    # Convertir valores no nulos a numérico
    numeric = pd.to_numeric(series, errors='coerce')
    
    # Redondear y convertir a Int32 (nullable)
    numeric = numeric.round().astype('Int32')
    
    return numeric


def _cast_to_int64(series: pd.Series) -> pd.Series:
    """Convertir a int64 PyArrow."""
    numeric = pd.to_numeric(series, errors='coerce')
    numeric = numeric.round().astype('Int64')
    return numeric


def _cast_to_float32(series: pd.Series) -> pd.Series:
    """Convertir a float32 PyArrow."""
    numeric = pd.to_numeric(series, errors='coerce')
    numeric = numeric.astype('float32')
    return numeric


def _cast_to_float64(series: pd.Series) -> pd.Series:
    """Convertir a float64 PyArrow."""
    numeric = pd.to_numeric(series, errors='coerce')
    numeric = numeric.astype('float64')
    return numeric


def _cast_to_bool(series: pd.Series) -> pd.Series:
    """Convertir a bool PyArrow."""
    def to_bool(val):
        if pd.isna(val):
            return False
        
        if isinstance(val, bool):
            return val
        
        if isinstance(val, (int, float)):
            return bool(val)
        
        if isinstance(val, str):
            val = val.lower().strip()
            if val in ['true', 'yes', '1', 'si']:
                return True
            elif val in ['false', 'no', '0']:
                return False
        
        return False
    
    return series.apply(to_bool).astype('boolean')


def _cast_to_date(series: pd.Series) -> pd.Series:
    """Convertir a fecha PyArrow."""
    return pd.to_datetime(series, errors='coerce').dt.date


def apply_plata_schema(df: pd.DataFrame, contexto: str = 'general') -> pd.DataFrame:
    """
    Aplicar esquema de capa Plata según contexto.
    
    Parameters:
    - df: DataFrame original
    - contexto: Contexto del DataFrame ('vulnerabilidad', 'tejido_productivo', 'contratacion')
    
    Returns:
    - DataFrame con esquema aplicado
    """
    # Esquemas específicos por contexto
    CONTEXT_SCHEMAS = {
        'vulnerabilidad': {
            'divipola_municipio': 'string[pyarrow]',
            'fecha_key': 'int32[pyarrow]',
            'ipm_total': 'float32[pyarrow]',
            'ipm_educacion': 'float32[pyarrow]',
            'ipm_ninez': 'float32[pyarrow]',
            'ipm_trabajo': 'float32[pyarrow]',
            'ipm_salud': 'float32[pyarrow]',
            'deficit_habitacional_cuantitativo': 'float32[pyarrow]',
            'deficit_habitacional_cualitativo': 'float32[pyarrow]',
            'nbi_total': 'float32[pyarrow]',
            'nbi_vivienda': 'float32[pyarrow]',
            'nbi_servicios': 'float32[pyarrow]',
            'nbi_educacion': 'float32[pyarrow]',
            'nbi_dependencia': 'float32[pyarrow]',
            'pobreza_monetaria': 'float32[pyarrow]',
            'pobreza_extrema': 'float32[pyarrow]',
            'poblacion_total': 'int32[pyarrow]',
            'poblacion_vulnerable': 'int32[pyarrow]',
        },
        'tejido_productivo': {
            'divipola_municipio': 'string[pyarrow]',
            'fecha_key': 'int32[pyarrow]',
            'codigo_ciiu': 'string[pyarrow]',
            'total_micronegocios': 'int32[pyarrow]',
            'micronegocios_formales': 'int32[pyarrow]',
            'micronegocios_informales': 'int32[pyarrow]',
            'economia_popular_unidades': 'int32[pyarrow]',
            'economia_popular_empleo': 'int32[pyarrow]',
            'empleo_total': 'int32[pyarrow]',
            'empleo_formal': 'int32[pyarrow]',
            'empleo_informal': 'int32[pyarrow]',
            'tasa_formalizacion': 'float32[pyarrow]',
        },
        'contratacion': {
            'id_contrato': 'string[pyarrow]',
            'divipola_municipio': 'string[pyarrow]',
            'divipola_departamento': 'string[pyarrow]',
            'fecha_publicacion_key': 'int32[pyarrow]',
            'fecha_inicio_key': 'int32[pyarrow]',
            'codigo_unspsc': 'string[pyarrow]',
            'codigo_ciiu_proveedor': 'string[pyarrow]',
            'id_entidad': 'int32[pyarrow]',
            'id_proveedor': 'int32[pyarrow]',
            'monto_contrato': 'float64[pyarrow]',
            'monto_ejecutado': 'float64[pyarrow]',
            'monto_pagado': 'float64[pyarrow]',
            'estado_contrato': 'string[pyarrow]',
            'modalidad_seleccion': 'string[pyarrow]',
            'es_economia_popular': 'bool[pyarrow]',
            'es_formalizacion': 'bool[pyarrow]',
        },
    }
    
    schema = CONTEXT_SCHEMAS.get(contexto, PLATA_SCHEMA)
    
    return cast_to_schema(df, schema=schema)


def validate_schema_compliance(
    df: pd.DataFrame,
    expected_schema: Dict[str, str],
) -> Dict[str, Any]:
    """
    Validar que un DataFrame cumple con el esquema esperado.
    
    Parameters:
    - df: DataFrame a validar
    - expected_schema: Esquema esperado
    
    Returns:
    - Dict con resultados de validación
    """
    results = {
        'valid': True,
        'missing_columns': [],
        'extra_columns': [],
        'type_mismatches': [],
        'null_counts': {},
    }
    
    # Verificar columnas faltantes
    for col in expected_schema.keys():
        if col not in df.columns:
            results['missing_columns'].append(col)
            results['valid'] = False
    
    # Verificar columnas extra
    for col in df.columns:
        if col not in expected_schema:
            results['extra_columns'].append(col)
    
    # Verificar tipos de datos
    for col, expected_type in expected_schema.items():
        if col not in df.columns:
            continue
        
        actual_type = str(df[col].dtype)
        
        # Verificación básica de tipo
        if not _type_matches(actual_type, expected_type):
            results['type_mismatches'].append({
                'column': col,
                'expected': expected_type,
                'actual': actual_type,
            })
    
    # Contar nulos por columna
    for col in df.columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            results['null_counts'][col] = int(null_count)
    
    return results


def _type_matches(actual: str, expected: str) -> bool:
    """
    Verificar si un tipo actual coincide con el esperado (básicamente).
    
    Parameters:
    - actual: Tipo actual
    - expected: Tipo esperado
    
    Returns:
    - True si coinciden básicamente
    """
    # Mapeo básico de tipos
    type_mapping = {
        'string': ['string', 'object', 'str'],
        'int32': ['Int32', 'int32', 'int'],
        'int64': ['Int64', 'int64', 'int'],
        'float32': ['float32', 'float'],
        'float64': ['float64', 'float'],
        'bool': ['boolean', 'bool', 'boolean'],
    }
    
    expected_base = expected.split('[')[0].lower()
    actual_base = actual.lower()
    
    valid_types = type_mapping.get(expected_base, [expected_base])
    
    return any(valid in actual_base for valid in valid_types)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    df = pd.DataFrame({
        'divipola_municipio': ['11001', '05001', '76001'],
        'monto_contrato': ['1000000', '2000000.50', '3000000'],
        'ipm_total': ['0.25', '0.35', '0.15'],
        'es_economia_popular': [True, False, True],
    })
    
    print("Original:")
    print(df.dtypes)
    
    df = apply_plata_schema(df, contexto='contratacion')
    
    print("\nConvertido:")
    print(df.dtypes)
