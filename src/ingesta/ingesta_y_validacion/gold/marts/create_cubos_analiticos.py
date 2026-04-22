"""
Creación de Cubos Analíticos para capa Oro.

Cubos:
- cubo_territorial_sectorial: Agregación por territorio y sector
- cubo_temporal_municipal: Agregación por tiempo y municipio
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def create_cubo_territorial_sectorial(
    fact_contratacion_df: pd.DataFrame,
    fact_tejido_productivo_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    dim_ciiu_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear cubo analítico territorial-sectorial.
    
    Permite análisis OLAP por dimensiones:
    - Territorio (departamento, municipio, región)
    - Sector (CIIU)
    - Tiempo (año, trimestre)
    
    Parameters:
    - fact_contratacion_df: Tabla de hechos de contratación
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - dim_municipio_df: Dimensión de municipios
    - dim_ciiu_df: Dimensión de sectores CIIU
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Cubo Territorial-Sectorial...")
    
    # Empezar con contratación
    if fact_contratacion_df is None or fact_contratacion_df.empty:
        cubo = _create_empty_cubo_territorial_sectorial()
    else:
        cubo = fact_contratacion_df.copy()
        
        # Extraer año de fecha_key
        if 'fecha_publicacion_key' in cubo.columns:
            cubo['anio'] = (cubo['fecha_publicacion_key'] // 10000).astype(int)
            cubo['trimestre'] = ((cubo['fecha_publicacion_key'] % 10000) // 100).astype(int)
            # Calcular trimestre de forma más precisa
            cubo['trimestre'] = cubo['fecha_publicacion_key'].apply(lambda x: ((x % 10000) - 1) // 300 + 1 if x > 0 else 1)
        else:
            cubo['anio'] = datetime.now().year
            cubo['trimestre'] = 1
        
        # Agregar región de dim_municipio
        if dim_municipio_df is not None and not dim_municipio_df.empty:
            cubo = cubo.merge(
                dim_municipio_df[['divipola_municipio', 'divipola_departamento', 'region']],
                on='divipola_municipio',
                how='left',
            )
        
        # Agregar descripción del sector
        if dim_ciiu_df is not None and not dim_ciiu_df.empty:
            cubo = cubo.merge(
                dim_ciiu_df[['codigo_ciiu', 'descripcion']],
                left_on='codigo_ciiu_proveedor',
                right_on='codigo_ciiu',
                how='left',
                suffixes=('', '_sector'),
            )
            cubo = cubo.rename(columns={'descripcion': 'sector_descripcion'})
        
        # Agregar tejido productivo para cálculo de indicadores
        if fact_tejido_productivo_df is not None and not fact_tejido_productivo_df.empty:
            tp_agg = fact_tejido_productivo_df.groupby('divipola_municipio').agg({
                'total_micronegocios': 'sum',
                'economia_popular_unidades': 'sum',
            }).reset_index()
            cubo = cubo.merge(tp_agg, on='divipola_municipio', how='left')
    
    # Agregar medidas calculadas
    if 'monto_contrato' in cubo.columns:
        # Monto per cápita (requiere población)
        if 'poblacion_total' in cubo.columns:
            cubo['monto_per_capita'] = (
                cubo['monto_contrato'] / 
                cubo['poblacion_total'].replace(0, np.nan)
            ).fillna(0)
        else:
            cubo['monto_per_capita'] = 0
        
        # Proveedores por micronegocio
        if 'total_micronegocios' in cubo.columns:
            cubo['proveedores_por_micronegocio'] = (
                1 / cubo['total_micronegocios'].replace(0, np.nan)
            ).fillna(0)
        else:
            cubo['proveedores_por_micronegocio'] = 0
    
    # Seleccionar columnas de dimensión y medida
    dimension_cols = [
        'divipola_departamento', 'divipola_municipio', 'region',
        'codigo_ciiu_proveedor', 'sector_descripcion',
        'anio', 'trimestre',
    ]
    
    measure_cols = [
        'monto_contrato', 'monto_ejecutado', 'monto_per_capita',
        'id_contrato', 'id_proveedor',
        'proveedores_por_micronegocio',
    ]
    
    # Filtrar columnas existentes
    all_cols = [c for c in dimension_cols + measure_cols if c in cubo.columns]
    cubo = cubo[all_cols]
    
    # Guardar
    if output_path is None:
        from config.settings import settings
        output_path = settings.get_oro_path('cubos_analiticos', 'cubo_territorial_sectorial')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'cubo_territorial_sectorial.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cubo.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"Cubo Territorial-Sectorial creado: {len(cubo)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(cubo),
        'dimensiones': [c for c in dimension_cols if c in cubo.columns],
        'medidas': [c for c in measure_cols if c in cubo.columns],
    }


def _create_empty_cubo_territorial_sectorial() -> pd.DataFrame:
    """Crear DataFrame vacío con schema correcto."""
    columns = [
        'divipola_departamento', 'divipola_municipio', 'region',
        'codigo_ciiu_proveedor', 'sector_descripcion',
        'anio', 'trimestre',
        'monto_contrato', 'monto_ejecutado', 'monto_per_capita',
        'id_contrato', 'id_proveedor',
        'proveedores_por_micronegocio',
    ]
    return pd.DataFrame(columns=columns)


def create_cubo_temporal_municipal(
    fact_contratacion_df: pd.DataFrame,
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_tejido_productivo_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    dim_tiempo_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear cubo analítico temporal-municipal.
    
    Permite análisis de series temporales por municipio.
    
    Parameters:
    - fact_contratacion_df: Tabla de hechos de contratación
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - dim_municipio_df: Dimensión de municipios
    - dim_tiempo_df: Dimensión de tiempo
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Cubo Temporal-Municipal...")
    
    # Crear base de tiempo-municipio (producto cartesiano)
    if dim_tiempo_df is not None and not dim_tiempo_df.empty:
        # Asegurar columnas
        expected_time_cols = ['fecha_key', 'anio', 'mes', 'trimestre']
        available_time_cols = [c for c in expected_time_cols if c in dim_tiempo_df.columns]
        tiempos = dim_tiempo_df[available_time_cols].drop_duplicates()
        
        # Si faltan columnas críticas, intentar extraerlas
        if 'anio' not in tiempos.columns and 'fecha_key' in tiempos.columns:
            tiempos['anio'] = (tiempos['fecha_key'] // 10000).astype(int)
        if 'mes' not in tiempos.columns and 'fecha_key' in tiempos.columns:
            tiempos['mes'] = ((tiempos['fecha_key'] % 10000) // 100).astype(int)
    else:
        # Crear rango de tiempo por defecto (asegurando longitudes iguales)
        anio_actual = datetime.now().year
        meses = list(range(1, 13))
        tiempos = pd.DataFrame({
            'fecha_key': [anio_actual * 10000 + m * 100 + 1 for m in meses],
            'anio': [anio_actual] * 12,
            'mes': meses,
            'trimestre': [1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4],
        })
    
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        municipios = dim_municipio_df[['divipola_municipio', 'nombre_municipio']].drop_duplicates()
    elif fact_contratacion_df is not None and not fact_contratacion_df.empty:
        municipios = fact_contratacion_df[['divipola_municipio']].drop_duplicates()
        municipios['nombre_municipio'] = 'Municipio'
    else:
        return {
            'status': 'error',
            'mensaje': 'No hay datos de municipios disponibles',
        }
    
    # Producto cartesiano
    tiempos['_key'] = 1
    municipios['_key'] = 1
    cubo = tiempos.merge(municipios, on='_key').drop(columns=['_key'])
    
    # Agregar contratación
    if fact_contratacion_df is not None and not fact_contratacion_df.empty:
        cont_agg = _aggregate_contratacion_temporal(fact_contratacion_df)
        cubo = cubo.merge(cont_agg, on=['divipola_municipio', 'anio', 'mes'], how='left')
    
    # Agregar vulnerabilidad
    if fact_vulnerabilidad_df is not None and not fact_vulnerabilidad_df.empty:
        vuln_agg = _aggregate_vulnerabilidad_anual(fact_vulnerabilidad_df)
        cubo = cubo.merge(vuln_agg, on=['divipola_municipio', 'anio'], how='left')
    
    # Agregar tejido productivo
    if fact_tejido_productivo_df is not None and not fact_tejido_productivo_df.empty:
        tp_agg = _aggregate_tejido_productivo_anual(fact_tejido_productivo_df)
        cubo = cubo.merge(tp_agg, on=['divipola_municipio', 'anio'], how='left')
    
    # Llenar valores nulos con 0 para medidas
    measure_cols = [
        'monto_contratado', 'monto_ejecutado', 'num_contratos',
        'ipm', 'pobreza',
        'micronegocios', 'economia_popular',
    ]
    
    for col in measure_cols:
        if col in cubo.columns:
            cubo[col] = cubo[col].fillna(0)
    
    # Guardar
    if output_path is None:
        from config.settings import settings
        output_path = settings.get_oro_path('cubos_analiticos', 'cubo_temporal_municipal')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'cubo_temporal_municipal.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    cubo.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"Cubo Temporal-Municipal creado: {len(cubo)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(cubo),
        'municipios': cubo['divipola_municipio'].nunique(),
        'periodos': cubo['fecha_key'].nunique() if 'fecha_key' in cubo.columns else 0,
    }


def _aggregate_contratacion_temporal(fact_contratacion_df: pd.DataFrame) -> pd.DataFrame:
    """Agregar contratación por municipio y mes."""
    # Extraer año y mes de fecha_key
    df = fact_contratacion_df.copy()
    
    col_fecha = 'fecha_publicacion_key' if 'fecha_publicacion_key' in df.columns else 'fecha_key'
    if col_fecha in df.columns:
        df['anio'] = (df[col_fecha].fillna(0) // 10000).astype(int)
        df['mes'] = ((df[col_fecha].fillna(0) % 10000) // 100).astype(int)
    
    # Solo agrupar por lo que exista
    group_cols = ['divipola_municipio']
    if 'anio' in df.columns: group_cols.append('anio')
    if 'mes' in df.columns: group_cols.append('mes')
    
    agg_dict = {}
    if 'monto_contrato' in df.columns: agg_dict['monto_contrato'] = 'sum'
    if 'monto_ejecutado' in df.columns: agg_dict['monto_ejecutado'] = 'sum'
    if 'id_contrato' in df.columns: agg_dict['id_contrato'] = 'count'
    
    if not agg_dict:
        return pd.DataFrame(columns=group_cols + ['monto_contratado', 'monto_ejecutado', 'num_contratos'])

    return df.groupby(group_cols).agg(agg_dict).reset_index().rename(columns={
        'monto_contrato': 'monto_contratado',
        'monto_ejecutado': 'monto_ejecutado',
        'id_contrato': 'num_contratos',
    })


def _aggregate_vulnerabilidad_anual(fact_vulnerabilidad_df: pd.DataFrame) -> pd.DataFrame:
    """Agregar vulnerabilidad por municipio y año."""
    df = fact_vulnerabilidad_df.copy()
    if 'fecha_key' in df.columns:
        df['anio'] = (df['fecha_key'].fillna(0) // 10000).astype(int)
    
    agg_dict = {}
    if 'ipm_total' in df.columns: agg_dict['ipm_total'] = 'max'
    if 'pobreza_monetaria' in df.columns: agg_dict['pobreza_monetaria'] = 'max'
    
    if not agg_dict:
        return pd.DataFrame(columns=['divipola_municipio', 'anio', 'ipm', 'pobreza'])

    return df.groupby(['divipola_municipio', 'anio']).agg(agg_dict).reset_index().rename(columns={
        'ipm_total': 'ipm',
        'pobreza_monetaria': 'pobreza',
    })


def _aggregate_tejido_productivo_anual(fact_tejido_productivo_df: pd.DataFrame) -> pd.DataFrame:
    """Agregar tejido productivo por municipio y año."""
    df = fact_tejido_productivo_df.copy()
    if 'fecha_key' in df.columns:
        df['anio'] = (df['fecha_key'].fillna(0) // 10000).astype(int)
    
    agg_dict = {}
    if 'total_micronegocios' in df.columns: agg_dict['total_micronegocios'] = 'sum'
    if 'economia_popular_unidades' in df.columns: agg_dict['economia_popular_unidades'] = 'sum'
    
    if not agg_dict:
        return pd.DataFrame(columns=['divipola_municipio', 'anio', 'micronegocios', 'economia_popular'])

    return df.groupby(['divipola_municipio', 'anio']).agg(agg_dict).reset_index().rename(columns={
        'total_micronegocios': 'micronegocios',
        'economia_popular_unidades': 'economia_popular',
    })


def create_cubo_completo(
    fact_contratacion_df: pd.DataFrame,
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_tejido_productivo_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    dim_tiempo_df: Optional[pd.DataFrame] = None,
    dim_ciiu_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear todos los cubos analíticos.
    
    Parameters:
    - fact_contratacion_df: Tabla de hechos de contratación
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - dim_municipio_df: Dimensión de municipios
    - dim_tiempo_df: Dimensión de tiempo
    - dim_ciiu_df: Dimensión de sectores CIIU
    - output_path: Ruta base de salida
    
    Returns:
    - Dict con metadata de creación de todos los cubos
    """
    logger.info("Creando todos los Cubos Analíticos...")
    
    resultados = {}
    
    # Cubo Territorial-Sectorial
    resultados['cubo_territorial_sectorial'] = create_cubo_territorial_sectorial(
        fact_contratacion_df,
        fact_tejido_productivo_df,
        dim_municipio_df,
        dim_ciiu_df,
    )
    
    # Cubo Temporal-Municipal
    resultados['cubo_temporal_municipal'] = create_cubo_temporal_municipal(
        fact_contratacion_df,
        fact_vulnerabilidad_df,
        fact_tejido_productivo_df,
        dim_municipio_df,
        dim_tiempo_df,
    )
    
    logger.info(f"Cubos Analíticos creados: {len(resultados)} cubos")
    
    return {
        'status': 'success',
        'cubos': resultados,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con datos vacíos
    print("Creando Cubos Analíticos...")
    
    fact_cont = pd.DataFrame()
    fact_vuln = pd.DataFrame()
    fact_tp = pd.DataFrame()
    dim_mun = pd.DataFrame()
    dim_tiempo = pd.DataFrame()
    
    resultado = create_cubo_completo(fact_cont, fact_vuln, fact_tp, dim_mun, dim_tiempo)
    print(f"Resultado: {resultado}")
