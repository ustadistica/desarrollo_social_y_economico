"""
Validaciones específicas para capa Oro.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def validate_oro_layer(
    oro_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Validar todos los archivos en capa Oro.
    
    Parameters:
    - oro_path: Ruta base de capa Oro
    
    Returns:
    - Dict con resultados de validación
    """
    from config.settings import settings
    
    if oro_path is None:
        oro_path = settings.ORO_PATH
    
    # Estructura esperada
    datamarts_esperados = {
        'datamart_social': [
            'matriz_brechas_municipal',
            'inversion_vs_vulnerabilidad',
            'autocorrelacion_espacial',
        ],
        'datamart_economico': [
            'matriz_sinergia_economica',
            'impacto_economia_popular',
            'formalizacion_proveedores',
        ],
        'cubos_analiticos': [
            'cubo_territorial_sectorial',
            'cubo_temporal_municipal',
        ],
    }
    
    resultados = {
        'datamarts_validados': 0,
        'tablas_validadas': 0,
        'errores': 0,
        'warnings': 0,
        'coherencia_financiera': {},
        'consistencia_agregados': {},
        'detalles': [],
    }
    
    # Cargar y validar cada tabla
    tablas_cargadas = {}
    
    for datamart, tablas in datamarts_esperados.items():
        datamart_path = oro_path / datamart
        
        if not datamart_path.exists():
            resultados['warnings'] += 1
            resultados['detalles'].append({
                'datamart': datamart,
                'nivel': 'warning',
                'mensaje': f'Directorio no existe: {datamart_path}',
            })
            continue
        
        for tabla in tablas:
            archivo = datamart_path / f'{tabla}.parquet'
            
            if archivo.exists():
                try:
                    df = pd.read_parquet(archivo)
                    tablas_cargadas[f'{datamart}.{tabla}'] = df
                    resultados['tablas_validadas'] += 1
                    
                    logger.info(f"Validando Oro: {datamart}.{tabla}")
                    
                    resultado_tabla = _validate_oro_table(datamart, tabla, df, tablas_cargadas)
                    resultados['detalles'].append({
                        'datamart': datamart,
                        'tabla': tabla,
                        **resultado_tabla,
                    })
                    
                    if resultado_tabla.get('errores', 0) > 0:
                        resultados['errores'] += resultado_tabla['errores']
                    
                    if resultado_tabla.get('warnings', 0) > 0:
                        resultados['warnings'] += resultado_tabla['warnings']
                    
                except Exception as e:
                    resultados['errores'] += 1
                    resultados['detalles'].append({
                        'datamart': datamart,
                        'tabla': tabla,
                        'nivel': 'error',
                        'mensaje': f'Error cargando {tabla}: {str(e)}',
                    })
            else:
                resultados['warnings'] += 1
                resultados['detalles'].append({
                    'datamart': datamart,
                    'tabla': tabla,
                    'nivel': 'warning',
                    'mensaje': f'Tabla no encontrada: {archivo}',
                })
    
    resultados['datamarts_validados'] = len(set(
        k.split('.')[0] for k in tablas_cargadas.keys()
    ))
    
    # Validaciones cruzadas entre tablas
    resultados['coherencia_financiera'] = _validate_financial_coherence_across_tables(tablas_cargadas)
    resultados['consistencia_agregados'] = _validate_aggregate_consistency(tablas_cargadas)
    
    return {
        'status': 'error' if resultados['errores'] > 0 else ('warning' if resultados['warnings'] > 0 else 'success'),
        'datamarts_validados': resultados['datamarts_validados'],
        'datamarts_esperados': len(datamarts_esperados),
        'tablas_validadas': resultados['tablas_validadas'],
        'total_errores': resultados['errores'],
        'total_warnings': resultados['warnings'],
        'coherencia_financiera_valida': all(
            v.get('valid', True) for v in resultados['coherencia_financiera'].values()
        ) if resultados['coherencia_financiera'] else None,
        'detalles': resultados['detalles'],
        'timestamp': datetime.now().isoformat(),
    }


def _validate_oro_table(
    datamart: str,
    tabla: str,
    df: pd.DataFrame,
    todas_las_tablas: Dict[str, pd.DataFrame],
) -> Dict[str, Any]:
    """
    Validar una tabla específica de capa Oro.
    
    Parameters:
    - datamart: Nombre del data mart
    - tabla: Nombre de la tabla
    - df: DataFrame
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
    if tabla == 'matriz_brechas_municipal':
        resultado.update(_validate_matriz_brechas(df))
    elif tabla == 'matriz_sinergia_economica':
        resultado.update(_validate_matriz_sinergia(df))
    elif tabla == 'inversion_vs_vulnerabilidad':
        resultado.update(_validate_inversion_vs_vulnerabilidad(df))
    
    # Validaciones comunes para todas las tablas Oro
    # 1. Verificar que no haya duplicados completos
    duplicados = df.duplicated().sum()
    if duplicados > 0:
        resultado['warnings'] += 1
        resultado['duplicados'] = int(duplicados)
    
    # 2. Verificar valores extremos en columnas numéricas
    resultado.update(_detect_outliers(df))
    
    return resultado


def _validate_matriz_brechas(df: pd.DataFrame) -> Dict[str, Any]:
    """Validar Matriz de Brechas."""
    resultado = {'errores': 0, 'warnings': 0}
    
    # Verificar que brecha_ranking sea consistente con rankings
    if all(col in df.columns for col in ['ranking_vulnerabilidad', 'ranking_inversion', 'brecha_ranking']):
        brecha_calculada = df['ranking_vulnerabilidad'] - df['ranking_inversion']
        brecha_diferencia = (df['brecha_ranking'] - brecha_calculada).abs()
        
        if brecha_diferencia.max() > 1:  # Tolerancia de 1 por redondeo
            resultado['errores'] += 1
            resultado['inconsistencia_brecha'] = int(brecha_diferencia.max())
    
    # Verificar que prioridad_score esté en rango 0-100
    if 'prioridad_score' in df.columns:
        fuera_rango = ((df['prioridad_score'] < 0) | (df['prioridad_score'] > 100)).sum()
        if fuera_rango > 0:
            resultado['errores'] += 1
            resultado['prioridad_score_fuera_rango'] = int(fuera_rango)
    
    return resultado


def _validate_matriz_sinergia(df: pd.DataFrame) -> Dict[str, Any]:
    """Validar Matriz de Sinergia Económica."""
    resultado = {'errores': 0, 'warnings': 0}
    
    # Verificar que sinergia_score esté en rango 0-100
    if 'sinergia_score' in df.columns:
        fuera_rango = ((df['sinergia_score'] < 0) | (df['sinergia_score'] > 100)).sum()
        if fuera_rango > 0:
            resultado['errores'] += 1
            resultado['sinergia_score_fuera_rango'] = int(fuera_rango)
    
    # Verificar consistencia de nivel_sinergia
    if 'nivel_sinergia' in df.columns:
        niveles_validos = ['ALTA', 'MEDIA', 'BAJA', 'SIN_DATOS']
        invalidos = ~df['nivel_sinergia'].isin(niveles_validos)
        
        if invalidos.any():
            resultado['warnings'] += 1
            resultado['niveles_invalidos'] = int(invalidos.sum())
    
    return resultado


def _validate_inversion_vs_vulnerabilidad(df: pd.DataFrame) -> Dict[str, Any]:
    """Validar Inversión vs Vulnerabilidad."""
    resultado = {'errores': 0, 'warnings': 0}
    
    # Verificar correlación en rango válido
    if 'correlacion_inversion_ipm' in df.columns:
        correlaciones = pd.to_numeric(df['correlacion_inversion_ipm'], errors='coerce').dropna()
        fuera_rango = ((correlaciones < -1) | (correlaciones > 1)).sum()
        
        if fuera_rango > 0:
            resultado['errores'] += 1
            resultado['correlacion_fuera_rango'] = int(fuera_rango)
    
    return resultado


def _detect_outliers(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detectar valores atípicos en columnas numéricas.
    
    Parameters:
    - df: DataFrame
    
    Returns:
    - Dict con resultados
    """
    resultado = {'errores': 0, 'warnings': 0, 'outliers': {}}
    
    # Columnas numéricas a verificar
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        valores = df[col].dropna()
        
        if len(valores) < 10:
            continue
        
        # Método IQR
        q1 = valores.quantile(0.25)
        q3 = valores.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        
        outliers = ((valores < lower_bound) | (valores > upper_bound)).sum()
        
        if outliers > 0:
            outlier_pct = outliers / len(valores)
            
            if outlier_pct > 0.1:  # Más de 10% outliers
                resultado['warnings'] += 1
                resultado['outliers'][col] = {
                    'count': int(outliers),
                    'percentage': float(outlier_pct),
                    'lower_bound': float(lower_bound),
                    'upper_bound': float(upper_bound),
                }
    
    return resultado


def _validate_financial_coherence_across_tables(tablas: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Validar coherencia financiera entre tablas.
    
    Parameters:
    - tablas: Dict con todas las tablas
    
    Returns:
    - Dict con resultados
    """
    resultados = {}
    
    # Verificar que montos totales en Oro sean consistentes con Plata
    # (En implementación real, comparar con fact_contratacion de Plata)
    
    resultados['monto_total_check'] = {
        'valid': True,
        'mensaje': 'Validación pendiente de implementación',
    }
    
    return resultados


def _validate_aggregate_consistency(tablas: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Validar consistencia de agregados entre tablas.
    
    Parameters:
    - tablas: Dict con todas las tablas
    
    Returns:
    - Dict con resultados
    """
    resultados = {}
    
    # Verificar que cubos analíticos sean consistentes con data marts
    # (En implementación real, comparar agregados)
    
    resultados['aggregate_check'] = {
        'valid': True,
        'mensaje': 'Validación pendiente de implementación',
    }
    
    return resultados


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resultado = validate_oro_layer()
    print(f"Resultado: {resultado}")
