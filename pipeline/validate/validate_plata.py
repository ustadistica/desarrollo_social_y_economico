"""
Validaciones específicas para capa Plata.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def validate_plata_layer(
    plata_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Validar todos los archivos en capa Plata.
    
    Parameters:
    - plata_path: Ruta base de capa Plata
    
    Returns:
    - Dict con resultados de validación
    """
    from config.settings import settings
    
    if plata_path is None:
        plata_path = settings.PLATA_PATH
    
    tablas_esperadas = [
        'dim_municipio',
        'dim_tiempo',
        'dim_sector_ciiu',
        'dim_sector_unspsc',
        'fact_vulnerabilidad',
        'fact_tejido_productivo',
        'fact_contratacion',
    ]
    
    resultados = {
        'tablas_validadas': 0,
        'errores': 0,
        'warnings': 0,
        'integridad_referencial': {},
        'detalles': [],
    }
    
    # Cargar tablas
    tablas_cargadas = {}
    
    for tabla in tablas_esperadas:
        archivo = plata_path / f'{tabla}.parquet'
        
        if archivo.exists():
            try:
                tablas_cargadas[tabla] = pd.read_parquet(archivo)
                resultados['tablas_validadas'] += 1
            except Exception as e:
                resultados['errores'] += 1
                resultados['detalles'].append({
                    'tabla': tabla,
                    'nivel': 'error',
                    'mensaje': f'Error cargando {tabla}: {str(e)}',
                })
        else:
            resultados['warnings'] += 1
            resultados['detalles'].append({
                'tabla': tabla,
                'nivel': 'warning',
                'mensaje': f'Tabla no encontrada: {archivo}',
            })
    
    # Validar cada tabla
    for tabla, df in tablas_cargadas.items():
        logger.info(f"Validando Plata: {tabla}")
        
        resultado_tabla = _validate_plata_table(tabla, df, tablas_cargadas)
        resultados['detalles'].append({
            'tabla': tabla,
            **resultado_tabla,
        })
        
        if resultado_tabla.get('errores', 0) > 0:
            resultados['errores'] += resultado_tabla['errores']
        
        if resultado_tabla.get('warnings', 0) > 0:
            resultados['warnings'] += resultado_tabla['warnings']
    
    # Validar integridad referencial
    resultados['integridad_referencial'] = _validate_referential_integrity(tablas_cargadas)
    
    # Resumen
    return {
        'status': 'error' if resultados['errores'] > 0 else ('warning' if resultados['warnings'] > 0 else 'success'),
        'tablas_validadas': resultados['tablas_validadas'],
        'tablas_esperadas': len(tablas_esperadas),
        'total_errores': resultados['errores'],
        'total_warnings': resultados['warnings'],
        'integridad_referencial_valida': all(
            v.get('valid', False) for v in resultados['integridad_referencial'].values()
        ) if resultados['integridad_referencial'] else None,
        'detalles': resultados['detalles'],
        'timestamp': datetime.now().isoformat(),
    }


def _validate_plata_table(
    tabla: str,
    df: pd.DataFrame,
    todas_las_tablas: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """
    Validar una tabla específica de capa Plata.
    
    Parameters:
    - tabla: Nombre de la tabla
    - df: DataFrame de la tabla
    - todas_las_tablas: Dict con todas las tablas cargadas
    
    Returns:
    - Dict con resultados
    """
    resultado = {
        'registros': len(df),
        'columnas': list(df.columns),
        'errores': 0,
        'warnings': 0,
    }
    
    # Validaciones específicas por tabla
    if tabla.startswith('dim_'):
        resultado.update(_validate_dimension(tabla, df))
    elif tabla.startswith('fact_'):
        resultado.update(_validate_fact(tabla, df, todas_las_tablas))
    
    return resultado


def _validate_dimension(tabla: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validar tabla de dimensión.
    
    Parameters:
    - tabla: Nombre de la dimensión
    - df: DataFrame
    
    Returns:
    - Dict con resultados
    """
    resultado = {'errores': 0, 'warnings': 0}
    
    # Todas las dimensiones deben tener PK única
    pk_columns = {
        'dim_municipio': 'divipola_municipio',
        'dim_tiempo': 'fecha_key',
        'dim_sector_ciiu': 'codigo_ciiu',
        'dim_sector_unspsc': 'codigo_unspsc',
    }
    
    pk = pk_columns.get(tabla)
    
    if pk and pk in df.columns:
        # Verificar unicidad
        duplicados = df.duplicated(subset=[pk], keep=False)
        num_duplicados = duplicados.sum()
        
        if num_duplicados > 0:
            resultado['errores'] += 1
            resultado['duplicados_pk'] = num_duplicados
        
        # Verificar nulos en PK
        nulos_pk = df[pk].isna().sum()
        if nulos_pk > 0:
            resultado['errores'] += 1
            resultado['nulos_pk'] = nulos_pk
    
    # Validaciones específicas
    if tabla == 'dim_municipio':
        resultado.update(_validate_dim_municipio(df))
    elif tabla == 'dim_tiempo':
        resultado.update(_validate_dim_tiempo(df))
    
    return resultado


def _validate_dim_municipio(df: pd.DataFrame) -> Dict[str, Any]:
    """Validar dim_municipio específicamente."""
    resultado = {'errores': 0, 'warnings': 0}
    
    # Verificar formato DIVIPOLA (5 dígitos)
    if 'divipola_municipio' in df.columns:
        divipolas = df['divipola_municipio'].dropna().astype(str)
        invalidos = ~divipolas.str.match(r'^\d{5}$')
        
        if invalidos.any():
            resultado['warnings'] += 1
            resultado['divipolas_invalidos'] = int(invalidos.sum())
    
    return resultado


def _validate_dim_tiempo(df: pd.DataFrame) -> Dict[str, Any]:
    """Validar dim_tiempo específicamente."""
    resultado = {'errores': 0, 'warnings': 0}
    
    # Verificar continuidad de fechas
    if 'fecha_key' in df.columns:
        fechas = sorted(df['fecha_key'].unique())
        
        if len(fechas) > 1:
            # Verificar saltos grandes (> 2 días)
            for i in range(1, len(fechas)):
                diff = fechas[i] - fechas[i-1]
                if diff > 200:  # ~2 días en formato YYYYMMDD
                    resultado['warnings'] += 1
                    resultado['saltos_fecha'] = resultado.get('saltos_fecha', 0) + 1
    
    return resultado


def _validate_fact(
    tabla: str,
    df: pd.DataFrame,
    todas_las_tablas: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """
    Validar tabla de hechos.
    
    Parameters:
    - tabla: Nombre de la tabla de hechos
    - df: DataFrame
    - todas_las_tablas: Dict con todas las tablas cargadas
    
    Returns:
    - Dict con resultados
    """
    resultado = {'errores': 0, 'warnings': 0}
    
    # Validar montos no negativos
    monto_cols = [c for c in df.columns if 'monto' in c.lower()]
    for col in monto_cols:
        if col in df.columns:
            negativos = (pd.to_numeric(df[col], errors='coerce') < 0).sum()
            if negativos > 0:
                resultado['warnings'] += 1
                resultado[f'montos_negativos_{col}'] = int(negativos)
    
    # Validar indicadores en rango 0-1
    indicador_cols = [c for c in df.columns if any(x in c for x in ['ipm', 'tasa', 'pobreza', 'deficit'])]
    for col in indicador_cols:
        if col in df.columns:
            valores = pd.to_numeric(df[col], errors='coerce').dropna()
            fuera_rango = ((valores < 0) | (valores > 1)).sum()
            
            if fuera_rango > 0:
                # Algunos indicadores pueden ser > 1 (ej. pobreza monetaria como %)
                resultado['warnings'] += 1
    
    return resultado


def _validate_referential_integrity(tablas: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Validar integridad referencial entre tablas.
    
    Parameters:
    - tablas: Dict con todas las tablas
    
    Returns:
    - Dict con resultados de integridad referencial
    """
    resultados = {}
    
    # Definir relaciones FK -> PK
    relaciones = [
        ('fact_vulnerabilidad', 'dim_municipio', 'divipola_municipio', 'divipola_municipio'),
        ('fact_tejido_productivo', 'dim_municipio', 'divipola_municipio', 'divipola_municipio'),
        ('fact_contratacion', 'dim_municipio', 'divipola_municipio', 'divipola_municipio'),
        ('fact_contratacion', 'dim_sector_unspsc', 'codigo_unspsc', 'codigo_unspsc'),
    ]
    
    for hecho, dim, fk, pk in relaciones:
        key = f'{hecho}.{fk} -> {dim}.{pk}'
        
        if hecho not in tablas or dim not in tablas:
            resultados[key] = {
                'valid': None,
                'mensaje': 'Tablas no disponibles',
            }
            continue
        
        df_hecho = tablas[hecho]
        df_dim = tablas[dim]
        
        if fk not in df_hecho.columns or pk not in df_dim.columns:
            resultados[key] = {
                'valid': None,
                'mensaje': 'Columnas no disponibles',
            }
            continue
        
        # Verificar integridad
        fk_values = set(df_hecho[fk].dropna().unique())
        pk_values = set(df_dim[pk].unique())
        
        huerfanos = fk_values - pk_values
        
        resultados[key] = {
            'valid': len(huerfanos) == 0,
            'fk_count': len(fk_values),
            'pk_count': len(pk_values),
            'huerfanos': len(huerfanos),
            'huerfanos_muestra': list(huerfanos)[:5],
        }
    
    return resultados


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resultado = validate_plata_layer()
    print(f"Resultado: {resultado}")
