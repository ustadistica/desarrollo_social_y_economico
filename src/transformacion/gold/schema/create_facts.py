"""
Creación de tablas de hechos para capa Plata.

Tablas:
- fact_vulnerabilidad: Indicadores de vulnerabilidad social
- fact_tejido_productivo: Indicadores de tejido productivo
- fact_contratacion: Contratos de SECOP II
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from src.transformacion.transform.standardize_geo import standardize_divipola

logger = logging.getLogger(__name__)


def create_fact_vulnerabilidad(
    cnpv_df: pd.DataFrame,
    terridata_df: Optional[pd.DataFrame] = None,
    dim_municipio_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de hechos de vulnerabilidad social.
    
    Parameters:
    - cnpv_df: DataFrame del CNPV (DANE)
    - terridata_df: DataFrame de TerriData (DNP) - opcional para validación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida para archivo Parquet
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando fact_vulnerabilidad...")
    
    # Validar que exista data
    if cnpv_df is None or cnpv_df.empty:
        logger.warning("No hay datos del CNPV. Creando tabla vacía.")
        fact = _create_empty_vulnerabilidad()
    else:
        # Procesar datos del CNPV
        fact = _process_vulnerabilidad_data(cnpv_df)
        
        # Complementar con TerriData si está disponible
        if terridata_df is not None and not terridata_df.empty:
            fact = _merge_terridata(fact, terridata_df)
    
    # Agregar fecha_key (usar año de vigencia)
    if 'vigencia' in fact.columns:
        fact['fecha_key'] = fact['vigencia'].astype(str) + '0101'  # 1 de enero
        fact['fecha_key'] = fact['fecha_key'].astype(int)
    else:
        fact['fecha_key'] = datetime.now().year * 10000 + 101
    
    # Calcular Z-scores para rankings
    fact = _calculate_zscores(fact)
    
    # Calcular rankings
    fact = _calculate_rankings(fact)
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_plata_path('fact_vulnerabilidad')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'fact_vulnerabilidad.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fact.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"fact_vulnerabilidad creada: {len(fact)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(fact),
        'columnas': list(fact.columns),
    }


def _create_empty_vulnerabilidad() -> pd.DataFrame:
    """Crear DataFrame vacío con schema correcto."""
    columns = [
        'id_registro', 'divipola_municipio', 'fecha_key',
        'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 'ipm_salud',
        'deficit_cuantitativo', 'deficit_cualitativo',
        'nbi_total', 'nbi_vivienda', 'nbi_servicios', 'nbi_educacion', 'nbi_dependencia',
        'pobreza_monetaria', 'pobreza_extrema',
        'poblacion_total', 'poblacion_vulnerable',
        'ipm_zscore', 'pobreza_zscore', 'ranking_vulnerabilidad',
    ]
    return pd.DataFrame(columns=columns)


def _process_vulnerabilidad_data(cnpv_df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesar datos del CNPV para crear tabla de hechos.
    
    Parameters:
    - cnpv_df: DataFrame del CNPV
    
    Returns:
    - DataFrame procesado
    """
    fact = cnpv_df.copy()
    
    # Generar ID único
    fact['id_registro'] = range(1, len(fact) + 1)
    
    # Seleccionar y renombrar columnas
    column_mapping = {
        'ipm': 'ipm_total',
        'nbi': 'nbi_total',
        'poblacion': 'poblacion_total',
        'deficit_habitacional_cuantitativo': 'deficit_cuantitativo',
        'deficit_habitacional_cualitativo': 'deficit_cualitativo',
    }
    
    fact = fact.rename(columns=column_mapping)
    
    # Calcular población vulnerable (estimación basada en IPM)
    if 'ipm_total' in fact.columns and 'poblacion_total' in fact.columns:
        fact['poblacion_vulnerable'] = (fact['ipm_total'] * fact['poblacion_total']).round().astype(int)
    
    return fact


def _merge_terridata(fact: pd.DataFrame, terridata_df: pd.DataFrame) -> pd.DataFrame:
    """
    Complementar con datos de TerriData.
    
    Parameters:
    - fact: DataFrame de vulnerabilidad
    - terridata_df: DataFrame de TerriData
    
    Returns:
    - DataFrame combinado
    """
    # Columnas para merge
    merge_cols = ['divipola_municipio', 'divipola_departamento']
    
    # Validar columnas existentes
    available_cols = [col for col in merge_cols if col in terridata_df.columns]
    
    if available_cols:
        fact = fact.merge(
            terridata_df,
            on=available_cols,
            how='left',
            suffixes=('_cnpv', '_terridata'),
        )
    
    return fact


def _calculate_zscores(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcular Z-scores para indicadores clave."""
    # IPM Z-score
    if 'ipm_total' in fact.columns:
        mean_ipm = fact['ipm_total'].mean()
        std_ipm = fact['ipm_total'].std()
        if std_ipm > 0:
            fact['ipm_zscore'] = (fact['ipm_total'] - mean_ipm) / std_ipm
        else:
            fact['ipm_zscore'] = 0
    
    # Pobreza Z-score
    if 'pobreza_monetaria' in fact.columns:
        mean_pobreza = fact['pobreza_monetaria'].mean()
        std_pobreza = fact['pobreza_monetaria'].std()
        if std_pobreza > 0:
            fact['pobreza_zscore'] = (fact['pobreza_monetaria'] - mean_pobreza) / std_pobreza
        else:
            fact['pobreza_zscore'] = 0
    
    return fact


def _calculate_rankings(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcular rankings de vulnerabilidad."""
    if 'ipm_total' in fact.columns:
        # Ranking de vulnerabilidad (1 = más vulnerable)
        fact['ranking_vulnerabilidad'] = fact['ipm_total'].rank(
            ascending=False, method='min'
        ).astype(int)
    
    return fact


def create_fact_tejido_productivo(
    cenu_df: pd.DataFrame,
    dim_municipio_df: Optional[pd.DataFrame] = None,
    dim_ciiu_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de hechos de tejido productivo.
    
    Parameters:
    - cenu_df: DataFrame del CENU (DANE)
    - dim_municipio_df: Dimensión de municipios
    - dim_ciiu_df: Dimensión de sectores CIIU
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando fact_tejido_productivo...")
    
    if cenu_df is None or cenu_df.empty:
        logger.warning("No hay datos del CENU. Creando tabla vacía.")
        fact = _create_empty_tejido_productivo()
    else:
        fact = _process_tejido_productivo_data(cenu_df)
        
        # Complementar con dimensiones si están disponibles
        if dim_ciiu_df is not None and not dim_ciiu_df.empty:
            fact = fact.merge(
                dim_ciiu_df[['codigo_ciiu', 'economia_popular']],
                on='codigo_ciiu',
                how='left',
            )
    
    # Agregar fecha_key
    fact['fecha_key'] = datetime.now().year * 10000 + 101
    
    # Calcular tasa de formalización
    fact = _calculate_formalizacion_rate(fact)
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_plata_path('fact_tejido_productivo')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'fact_tejido_productivo.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fact.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"fact_tejido_productivo creada: {len(fact)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(fact),
        'columnas': list(fact.columns),
    }


def _create_empty_tejido_productivo() -> pd.DataFrame:
    """Crear DataFrame vacío con schema correcto."""
    columns = [
        'id_registro', 'divipola_municipio', 'fecha_key', 'codigo_ciiu',
        'total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
        'economia_popular_unidades', 'economia_popular_empleo',
        'empleo_total', 'empleo_formal', 'empleo_informal',
        'tasa_formalizacion', 'economia_popular',
    ]
    return pd.DataFrame(columns=columns)


def _process_tejido_productivo_data(cenu_df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesar datos del CENU.
    
    Parameters:
    - cenu_df: DataFrame del CENU
    
    Returns:
    - DataFrame procesado
    """
    fact = cenu_df.copy()
    
    # Generar ID único
    fact['id_registro'] = range(1, len(fact) + 1)
    
    return fact


def _calculate_formalizacion_rate(fact: pd.DataFrame) -> pd.DataFrame:
    """Calcular tasa de formalización."""
    if 'micronegocios_formales' in fact.columns and 'total_micronegocios' in fact.columns:
        fact['tasa_formalizacion'] = (
            fact['micronegocios_formales'] / 
            fact['total_micronegocios'].replace(0, np.nan)
        ).fillna(0)
    
    return fact


def create_fact_contratacion(
    secop_df: pd.DataFrame,
    dim_municipio_df: Optional[pd.DataFrame] = None,
    dim_tiempo_df: Optional[pd.DataFrame] = None,
    dim_unspsc_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de hechos de contratación.
    
    Parameters:
    - secop_df: DataFrame de SECOP II
    - dim_municipio_df: Dimensión de municipios
    - dim_tiempo_df: Dimensión de tiempo
    - dim_unspsc_df: Dimensión de sectores UNSPSC
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando fact_contratacion...")
    
    if secop_df is None or secop_df.empty:
        logger.warning("No hay datos de SECOP II. Creando tabla vacía.")
        fact = _create_empty_contratacion()
    else:
        fact = _process_contratacion_data(secop_df)
        
        # Complementar con dimensiones
        if dim_municipio_df is not None and not dim_municipio_df.empty:
            fact = fact.merge(
                dim_municipio_df[['divipola_municipio', 'divipola_departamento', 'region']],
                on='divipola_municipio',
                how='left',
            )
        
        if dim_unspsc_df is not None and not dim_unspsc_df.empty:
            fact = fact.merge(
                dim_unspsc_df[['codigo_unspsc', 'descripcion']],
                on='codigo_unspsc',
                how='left',
                suffixes=('', '_unspsc'),
            )
    
    # Agregar fecha_key
    if 'fecha_publicacion' in fact.columns:
        fact['fecha_publicacion'] = pd.to_datetime(fact['fecha_publicacion'], errors='coerce')
        # Generar key con fallback para NaT
        fact['fecha_publicacion_key'] = 0
        mask = fact['fecha_publicacion'].notna()
        if mask.any():
            fact.loc[mask, 'fecha_publicacion_key'] = (
                fact.loc[mask, 'fecha_publicacion'].dt.strftime('%Y%m%d').astype(float).astype(int)
            )
        fact.loc[~mask, 'fecha_publicacion_key'] = 19000101 # Fallback fecha mínima
        fact['fecha_publicacion_key'] = fact['fecha_publicacion_key'].astype(int)
    else:
        fact['fecha_publicacion_key'] = 19000101
    
    # Identificar economía popular (simplificado)
    fact = _identify_economia_popular(fact)
    
    # Identificar formalización
    fact = _identify_formalizacion(fact)
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_plata_path('fact_contratacion')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'fact_contratacion.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fact.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"fact_contratacion creada: {len(fact)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(fact),
        'columnas': list(fact.columns),
    }


def _create_empty_contratacion() -> pd.DataFrame:
    """Crear DataFrame vacío con schema correcto."""
    columns = [
        'id_contrato', 'divipola_municipio', 'divipola_departamento',
        'fecha_publicacion_key', 'fecha_inicio_key',
        'codigo_unspsc', 'codigo_ciiu_proveedor',
        'id_entidad', 'id_proveedor',
        'monto_contrato', 'monto_ejecutado', 'monto_pagado',
        'estado_contrato', 'modalidad_seleccion',
        'es_economia_popular', 'es_formalizacion',
        'region',
    ]
    return pd.DataFrame(columns=columns)


def _process_contratacion_data(secop_df: pd.DataFrame) -> pd.DataFrame:
    """
    Procesar datos de SECOP II.
    
    Parameters:
    - secop_df: DataFrame de SECOP II
    
    Returns:
    - DataFrame procesado
    """
    fact = secop_df.copy()
    
    # Estandarizar nombres de columnas
    column_mapping = {
        'objectid': 'id_contrato',
        'id_del_proceso': 'id_contrato',
        'valor_total_adjudicacion': 'monto_contrato',
        'valor_contrato': 'monto_contrato',
        'valor_ejecutado': 'monto_ejecutado',
        'valor_pagado': 'monto_pagado',
        'codigo_divipola': 'divipola_municipio',
        'unspsc_code': 'codigo_unspsc',
        'codigo_principal_de_categoria': 'codigo_unspsc',
        'nit_proveedor': 'nit_proveedor',
        'nit_del_proveedor_adjudicado': 'nit_proveedor',
        'nombre_entidad': 'nombre_entidad',
        'entidad': 'nombre_entidad',
        'modalidad_seleccion': 'modalidad_seleccion',
        'modalidad_de_contratacion': 'modalidad_seleccion',
        'estado': 'estado_contrato',
        'estado_del_procedimiento': 'estado_contrato',
        'fecha_de_publicacion': 'fecha_publicacion',
    }
    
    fact = fact.rename(columns=column_mapping)
    
    # Estandarizar geografía si no hay divipola_municipio
    if 'divipola_municipio' not in fact.columns:
        if 'ciudad_entidad' in fact.columns:
            logger.info("  Estandarizando geografía por ciudad_entidad...")
            fact = standardize_divipola(
                fact, 
                column_municipio='divipola_municipio', 
                column_nombre='ciudad_entidad'
            )
    
    # Convertir montos a numérico
    monto_cols = ['monto_contrato', 'monto_ejecutado', 'monto_pagado']
    for col in monto_cols:
        if col in fact.columns:
            fact[col] = pd.to_numeric(fact[col], errors='coerce').fillna(0)
    
    # Hash del NIT para secreto estadístico
    if 'nit_proveedor' in fact.columns:
        fact['id_proveedor'] = _hash_nit(fact['nit_proveedor'])
    
    # Extraer año para CIIU aproximado (en producción usar cruce real)
    fact['codigo_ciiu_proveedor'] = None  # Pendiente de cruce con CENU
    
    return fact


def _hash_nit(nit_series: pd.Series) -> pd.Series:
    """
    Hashear NIT para preservar secreto estadístico.
    
    Parameters:
    - nit_series: Serie con NITs
    
    Returns:
    - Serie con hashes numéricos
    """
    import hashlib
    
    def hash_value(nit) -> int:
        if pd.isna(nit):
            return 0
        
        hash_obj = hashlib.md5(str(nit).encode())
        return int(hash_obj.hexdigest()[:8], 16)
    
    return nit_series.apply(hash_value)


def _identify_economia_popular(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Identificar contratos de economía popular.
    
    En producción, usar criterios oficiales del DANE:
    - Monto bajo
    - Proveedor persona natural
    - Sector específico (CIIU de economía popular)
    """
    fact['es_economia_popular'] = False
    
    # Criterio simplificado: monto bajo (menor a 10 SMMLV aprox)
    if 'monto_contrato' in fact.columns:
        umbral_economia_popular = 13000000  # ~10 SMMLV 2024
        fact['es_economia_popular'] = fact['monto_contrato'] < umbral_economia_popular
    
    return fact


def _identify_formalizacion(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Identificar contratos que contribuyen a formalización.
    
    Criterio: proveedor que aparece por primera vez en SECOP II
    (en producción, usar histórico completo)
    """
    fact['es_formalizacion'] = False
    
    # Simplificado: marcar como formalización los de economía popular
    if 'es_economia_popular' in fact.columns:
        fact['es_formalizacion'] = fact['es_economia_popular']
    
    return fact


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con datos vacíos
    print("Creando tablas de hechos...")
    
    # fact_vulnerabilidad
    cnpv_empty = pd.DataFrame()
    resultado = create_fact_vulnerabilidad(cnpv_empty)
    print(f"fact_vulnerabilidad: {resultado}")
    
    # fact_tejido_productivo
    cenu_empty = pd.DataFrame()
    resultado = create_fact_tejido_productivo(cenu_empty)
    print(f"fact_tejido_productivo: {resultado}")
    
    # fact_contratacion
    secop_empty = pd.DataFrame()
    resultado = create_fact_contratacion(secop_empty)
    print(f"fact_contratacion: {resultado}")
