"""
Data Mart de Dimensión Económica.

Tablas:
- matriz_sinergia_economica: Coincidencia gasto-vocación productiva
- impacto_economia_popular: Llegada de contratación a economía popular
- formalizacion_proveedores: Análisis de formalización vía contratación
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def create_datamart_economico(
    fact_tejido_productivo_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    dim_ciiu_df: Optional[pd.DataFrame] = None,
    dim_unspsc_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear Data Mart completo de dimensión económica.
    
    Parameters:
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - dim_ciiu_df: Dimensión de sectores CIIU
    - dim_unspsc_df: Dimensión de sectores UNSPSC
    - output_path: Ruta base de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Data Mart Económico...")
    
    resultados = {}
    
    # Crear Matriz de Sinergia Económica
    resultados['matriz_sinergia'] = create_matriz_sinergia(
        fact_tejido_productivo_df,
        fact_contratacion_df,
        dim_municipio_df,
        dim_ciiu_df,
        dim_unspsc_df,
    )
    
    # Crear Impacto en Economía Popular
    resultados['impacto_economia_popular'] = create_impacto_economia_popular(
        fact_tejido_productivo_df,
        fact_contratacion_df,
        dim_municipio_df,
    )
    
    # Crear Formalización de Proveedores
    resultados['formalizacion_proveedores'] = create_formalizacion_proveedores(
        fact_tejido_productivo_df,
        fact_contratacion_df,
        dim_municipio_df,
    )
    
    logger.info(f"Data Mart Económico creado: {len(resultados)} tablas")
    
    return {
        'status': 'success',
        'tablas': resultados,
        'output_path': str(output_path) if output_path else None,
    }


def create_matriz_sinergia(
    fact_tejido_productivo_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    dim_ciiu_df: Optional[pd.DataFrame] = None,
    dim_unspsc_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear Matriz de Sinergia Económica.
    
    Evalúa coincidencia entre gasto público y vocación productiva territorial.
    
    Parameters:
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - dim_ciiu_df: Dimensión CIIU
    - dim_unspsc_df: Dimensión UNSPSC
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Matriz de Sinergia Económica...")
    
    # 1. Calcular vocación productiva por municipio
    vocacion = _calcular_vocacion_productiva(fact_tejido_productivo_df)
    
    # 2. Calcular gasto público por sector por municipio
    gasto = _calcular_gasto_publico_sector(fact_contratacion_df)
    
    # 3. Unir vocación y gasto
    matriz = vocacion.merge(
        gasto,
        on='divipola_municipio',
        how='outer',
    )
    
    # 4. Unir con información de municipio
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        matriz = matriz.merge(
            dim_municipio_df[['divipola_municipio', 'nombre_municipio', 'divipola_departamento', 'nombre_departamento', 'region']],
            on='divipola_municipio',
            how='left',
        )
    
    # 5. Calcular nivel de sinergia
    matriz = _calcular_nivel_sinergia(matriz)
    
    # 6. Calcular score de sinergia (0-100)
    matriz['sinergia_score'] = _calcular_sinergia_score(matriz)
    
    # 7. Calcular coincidencia de economía popular
    matriz = _calcular_coincidencia_economia_popular(matriz)
    
    # Seleccionar columnas finales
    columnas_finales = [
        'divipola_municipio', 'nombre_municipio', 'divipola_departamento',
        'nombre_departamento', 'region',
        'sector_predominante_tp', 'economia_popular_share', 'formalizacion_rate',
        'sector_predominante_contratacion', 'monto_total_contratos',
        'nivel_sinergia', 'sinergia_score',
        'economia_popular_atendida', 'economia_popular_desatendida',
    ]
    
    columnas_existentes = [c for c in columnas_finales if c in matriz.columns]
    matriz = matriz[columnas_existentes]
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_oro_path('datamart_economico', 'matriz_sinergia_economica')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'matriz_sinergia_economica.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    matriz.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"Matriz de Sinergia creada: {len(matriz)} municipios")
    
    # Estadísticas
    alta_sinergia = (matriz['nivel_sinergia'] == 'ALTA').sum() if 'nivel_sinergia' in matriz.columns else 0
    baja_sinergia = (matriz['nivel_sinergia'] == 'BAJA').sum() if 'nivel_sinergia' in matriz.columns else 0
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(matriz),
        'alta_sinergia': int(alta_sinergia),
        'baja_sinergia': int(baja_sinergia),
        'sinergia_promedio': float(matriz['sinergia_score'].mean()) if 'sinergia_score' in matriz.columns else 0,
    }


def _calcular_vocacion_productiva(fact_tejido_productivo_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcular vocación productiva por municipio usando Factor de Expansión (fex_c).
    
    Parameters:
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo (Microdatos)
    
    Returns:
    - DataFrame con vocación productiva poblacional por municipio
    """
    if fact_tejido_productivo_df is None or fact_tejido_productivo_df.empty:
        return pd.DataFrame(columns=[
            'divipola_municipio', 'sector_predominante_tp', 
            'economia_popular_share', 'formalizacion_rate',
        ])
    
    # Crear copia para evitar modificar el original
    df = fact_tejido_productivo_df.copy()
    
    # Asegurar existencia del FEX. Si no hay, usar 1 (como un censo default, aunque arrojará warning)
    if 'fex_c' in df.columns:
        df['fex_c'] = pd.to_numeric(df['fex_c'], errors='coerce').fillna(1)
    else:
        logger.warning("No se encontró 'fex_c' en EMICRON/CENU. Se usarán pesos muestrales no expandidos (fex_c=1).")
        df['fex_c'] = 1
        
    # Multiplicar conteos base por el FEX
    cols_to_expand = ['economia_popular_unidades', 'total_micronegocios', 'establecimientos_industria', 'total_establecimientos']
    
    for col in cols_to_expand:
        if col in df.columns:
            # Asumimos que la columna puede tener 1/0 o el valor del conteo en microdatos. Multiplicamos por FEX.
            df[f'{col}_exp'] = pd.to_numeric(df[col], errors='coerce').fillna(0) * df['fex_c']
    
    # Agregaciones: Sumar los datos expandidos por municipio
    agg_dict = {}
    for col in cols_to_expand:
        if f'{col}_exp' in df.columns:
            agg_dict[f'{col}_exp'] = 'sum'
            
    if 'tasa_formalizacion' in df.columns:
        # Promedio ponderado real requeriría formalizados_expandido / total_expandido
        # Como fallback usamos promedio simple si no hay cómo discriminar formalizados
        if 'micronegocios_formales' in df.columns:
            df['micronegocios_formales_exp'] = pd.to_numeric(df['micronegocios_formales'], errors='coerce').fillna(0) * df['fex_c']
            agg_dict['micronegocios_formales_exp'] = 'sum'
        else:
            agg_dict['tasa_formalizacion'] = 'mean'
    
    # Manejar CIIU predominante de forma pesada (por FEX)
    if 'codigo_ciiu' in df.columns:
        def weighted_mode(group):
            # Sumar pesos reales fex_c por cada CIIU en el municipio y escoger el mayor
            if group.empty: return None
            return group.groupby('codigo_ciiu')['fex_c'].sum().idxmax()
    
    if not agg_dict and 'codigo_ciiu' not in df.columns:
        return pd.DataFrame(columns=['divipola_municipio', 'sector_predominante_tp', 'economia_popular_share', 'formalizacion_rate'])

    # Calcular CIIU mode ponderado
    if 'codigo_ciiu' in df.columns:
        ciiu_df = df.groupby('divipola_municipio').apply(weighted_mode).reset_index(name='sector_predominante_tp')
    
    # Ejecutar groupby standard
    if agg_dict:
        vocacion = df.groupby('divipola_municipio').agg(agg_dict).reset_index()
    else:
        vocacion = pd.DataFrame(df['divipola_municipio'].unique(), columns=['divipola_municipio'])
        
    # Unir resultados
    if 'codigo_ciiu' in df.columns:
        vocacion = vocacion.merge(ciiu_df, on='divipola_municipio', how='left')

    # Renombrar columnas mapeadas de vuelta a su nombre original y limpiar
    rename_cols = {f'{c}_exp': c for c in cols_to_expand}
    vocacion = vocacion.rename(columns=rename_cols)
    
    # Tasa formalizacion real (formalizados_expandido / micronegocios_expandido)
    if 'micronegocios_formales_exp' in vocacion.columns and 'total_micronegocios' in vocacion.columns:
        vocacion['formalizacion_rate'] = (vocacion['micronegocios_formales_exp'] / vocacion['total_micronegocios'].replace(0, np.nan)).fillna(0)
    elif 'tasa_formalizacion' in vocacion.columns:
        vocacion['formalizacion_rate'] = vocacion['tasa_formalizacion']
        
    if 'sector_predominante_tp' not in vocacion.columns: vocacion['sector_predominante_tp'] = 'SIN DATOS'
    if 'formalizacion_rate' not in vocacion.columns: vocacion['formalizacion_rate'] = 0
    if 'economia_popular_unidades' not in vocacion.columns: vocacion['economia_popular_unidades'] = 0
    if 'total_micronegocios' not in vocacion.columns: vocacion['total_micronegocios'] = 1 
    
    vocacion['economia_popular_share'] = (
        vocacion['economia_popular_unidades'] / 
        vocacion['total_micronegocios'].replace(0, np.nan)
    ).fillna(0)
    
    return vocacion


def _calcular_gasto_publico_sector(fact_contratacion_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcular gasto público por sector por municipio.
    
    Parameters:
    - fact_contratacion_df: Tabla de hechos de contratación
    
    Returns:
    - DataFrame con gasto público por municipio
    """
    if fact_contratacion_df is None or fact_contratacion_df.empty:
        return pd.DataFrame(columns=[
            'divipola_municipio', 'sector_predominante_contratacion',
            'monto_total_contratos',
        ])
    
    # Agrupar por municipio y sector
    gasto = fact_contratacion_df.groupby(['divipola_municipio', 'codigo_ciiu_proveedor']).agg({
        'monto_contrato': 'sum',
    }).reset_index()
    
    # Obtener sector predominante por municipio
    idx = gasto.groupby('divipola_municipio')['monto_contrato'].idxmax()
    gasto_predominante = gasto.loc[idx].rename(columns={
        'codigo_ciiu_proveedor': 'sector_predominante_contratacion',
        'monto_contrato': 'monto_total_contratos',
    })[['divipola_municipio', 'sector_predominante_contratacion', 'monto_total_contratos']]
    
    return gasto_predominante


def _calcular_nivel_sinergia(matriz: pd.DataFrame) -> pd.DataFrame:
    """
    Calcular nivel de sinergia entre vocación y contratación.
    
    Parameters:
    - matriz: DataFrame con vocación y gasto
    
    Returns:
    - DataFrame con nivel de sinergia
    """
    def determinar_sinergia(row):
        sector_tp = row.get('sector_predominante_tp')
        sector_cont = row.get('sector_predominante_contratacion')
        
        if pd.isna(sector_tp) or pd.isna(sector_cont):
            return 'SIN_DATOS'
        
        if sector_tp == sector_cont:
            return 'ALTA'
        
        # Verificar si son sectores relacionados (simplificado)
        seccion_tp = str(sector_tp)[:1] if sector_tp else ''
        seccion_cont = str(sector_cont)[:1] if sector_cont else ''
        
        if seccion_tp == seccion_cont:
            return 'MEDIA'
        
        return 'BAJA'
    
    matriz['nivel_sinergia'] = matriz.apply(determinar_sinergia, axis=1)
    
    return matriz


def _calcular_sinergia_score(matriz: pd.DataFrame) -> pd.Series:
    """
    Calcular score numérico de sinergia (0-100).
    
    Parameters:
    - matriz: DataFrame con datos
    
    Returns:
    - Serie con scores
    """
    # Mapeo de nivel a score base
    nivel_score = {
        'ALTA': 80,
        'MEDIA': 50,
        'BAJA': 20,
        'SIN_DATOS': 0,
    }
    
    score_base = matriz['nivel_sinergia'].map(nivel_score).fillna(0)
    
    # Ajustar por economía popular share (bonificación)
    if 'economia_popular_share' in matriz.columns:
        bonus_ep = matriz['economia_popular_share'] * 20  # Hasta 20 puntos extra
        score_base = score_base + bonus_ep
    
    # Clip a 0-100
    return score_base.clip(0, 100)


def _calcular_coincidencia_economia_popular(matriz: pd.DataFrame) -> pd.DataFrame:
    """
    Calcular coincidencia de economía popular atendida.
    
    Parameters:
    - matriz: DataFrame con datos
    
    Returns:
    - DataFrame con columnas de economía popular
    """
    # En producción, cruzar con datos reales de SECOP II
    # Aquí usamos estimación basada en share de economía popular
    
    if 'economia_popular_share' in matriz.columns and 'monto_total_contratos' in matriz.columns:
        matriz['economia_popular_atendida'] = (
            matriz['monto_total_contratos'] * matriz['economia_popular_share']
        )
        matriz['economia_popular_desatendida'] = (
            matriz['monto_total_contratos'] * (1 - matriz['economia_popular_share'])
        )
    else:
        matriz['economia_popular_atendida'] = 0
        matriz['economia_popular_desatendida'] = 0
    
    return matriz


def create_impacto_economia_popular(
    fact_tejido_productivo_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de Impacto en Economía Popular.
    
    Parameters:
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Impacto en Economía Popular...")
    
    # Unir datos
    datos = fact_tejido_productivo_df.copy()
    
    # Agregar contratación
    if fact_contratacion_df is not None and not fact_contratacion_df.empty:
        cont_agg = fact_contratacion_df.groupby('divipola_municipio').agg({
            'monto_contrato': 'sum',
            'id_contrato': 'count',
            'es_economia_popular': 'sum',
        }).reset_index()
        cont_agg = cont_agg.rename(columns={
            'monto_contrato': 'monto_total_contratos',
            'id_contrato': 'total_contratos',
            'es_economia_popular': 'contratos_economia_popular',
        })
        datos = datos.merge(cont_agg, on='divipola_municipio', how='left')
    
    # Agregar departamento
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        datos = datos.merge(
            dim_municipio_df[['divipola_municipio', 'divipola_departamento', 'nombre_departamento']],
            on='divipola_municipio',
            how='left',
        )
    
    # Calcular indicadores
    # Share de economía popular en contratación
    if 'contratos_economia_popular' in datos.columns and 'total_contratos' in datos.columns:
        datos['share_economia_popular'] = (
            datos['contratos_economia_popular'] / 
            datos['total_contratos'].replace(0, np.nan)
        ).fillna(0)
    else:
        datos['share_economia_popular'] = 0
    
    # Penetración de economía popular
    if 'economia_popular_unidades' in datos.columns and 'total_contratos' in datos.columns:
        datos['penetracion_economia_popular'] = (
            datos['total_contratos'] / 
            datos['economia_popular_unidades'].replace(0, np.nan)
        ).fillna(0)
    
    # Agregar por departamento
    agg_dict = {
        'monto_total_contratos': 'sum',
        'contratos_economia_popular': 'sum',
        'total_contratos': 'sum',
        'share_economia_popular': 'mean',
    }
    if 'economia_popular_unidades' in datos.columns: agg_dict['economia_popular_unidades'] = 'sum'
    if 'economia_popular_empleo' in datos.columns: agg_dict['economia_popular_empleo'] = 'sum'
    if 'penetracion_economia_popular' in datos.columns: agg_dict['penetracion_economia_popular'] = 'mean'
    
    agregado = datos.groupby(['divipola_departamento', 'nombre_departamento']).agg(agg_dict).reset_index()
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_oro_path('datamart_economico', 'impacto_economia_popular')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'impacto_economia_popular.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    agregado.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"Impacto en Economía Popular creado: {len(agregado)} departamentos")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(agregado),
    }


def create_formalizacion_proveedores(
    fact_tejido_productivo_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de Formalización de Proveedores.
    
    Parameters:
    - fact_tejido_productivo_df: Tabla de hechos de tejido productivo
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Formalización de Proveedores...")
    
    # Unir datos
    datos = fact_tejido_productivo_df.copy()
    
    # Agregar contratación
    if fact_contratacion_df is not None and not fact_contratacion_df.empty:
        cont_agg = fact_contratacion_df.groupby('divipola_municipio').agg({
            'id_proveedor': 'nunique',
            'es_formalizacion': 'sum',
        }).reset_index()
        cont_agg = cont_agg.rename(columns={
            'id_proveedor': 'total_proveedores_secop',
            'es_formalizacion': 'proveedores_formalizados',
        })
        datos = datos.merge(cont_agg, on='divipola_municipio', how='left')
    
    # Agregar departamento
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        datos = datos.merge(
            dim_municipio_df[['divipola_municipio', 'divipola_departamento', 'nombre_departamento']],
            on='divipola_municipio',
            how='left',
        )
    
    # Calcular tasa de informalidad (inverso de formalización)
    if 'tasa_formalizacion' in datos.columns:
        datos['tasa_informalidad'] = 1 - datos['tasa_formalizacion']
    else:
        datos['tasa_informalidad'] = 0.5  # Default
    
    # Calcular tasa de formalización vía SECOP
    if 'total_proveedores_secop' in datos.columns and 'proveedores_formalizados' in datos.columns:
        datos['tasa_formalizacion_secop'] = (
            datos['proveedores_formalizados'] / 
            datos['total_proveedores_secop'].replace(0, np.nan)
        ).fillna(0)
    else:
        datos['tasa_formalizacion_secop'] = 0
    
    # Agregar por departamento
    agregado = datos.groupby(['divipola_departamento', 'nombre_departamento']).agg({
        'tasa_informalidad': 'mean',
        'total_proveedores_secop': 'sum',
        'proveedores_formalizados': 'sum',
        'tasa_formalizacion_secop': 'mean',
    }).reset_index()
    
    # Calcular correlación
    if len(agregado) > 2:
        correlacion = agregado['tasa_informalidad'].corr(agregado['tasa_formalizacion_secop'])
    else:
        correlacion = np.nan
    
    agregado['correlacion_informalidad_formalizacion'] = correlacion
    
    # Guardar
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_oro_path('datamart_economico', 'formalizacion_proveedores')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'formalizacion_proveedores.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    agregado.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"Formalización de Proveedores creada: {len(agregado)} departamentos")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(agregado),
        'correlacion': float(correlacion) if not np.isnan(correlacion) else None,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con datos vacíos
    print("Creando Data Mart Económico...")
    
    fact_tp = pd.DataFrame()
    fact_cont = pd.DataFrame()
    dim_mun = pd.DataFrame()
    
    resultado = create_datamart_economico(fact_tp, fact_cont, dim_mun)
    print(f"Resultado: {resultado}")
