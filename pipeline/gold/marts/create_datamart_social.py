"""
Data Mart de Dimensión Social.

Tablas:
- matriz_brechas_municipal: Brechas entre vulnerabilidad e inversión
- inversion_vs_vulnerabilidad: Correlación inversión-vulnerabilidad
- autocorrelacion_espacial: Índice de Moran
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def create_datamart_social(
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear Data Mart completo de dimensión social.
    
    Parameters:
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta base de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Data Mart Social...")
    
    resultados = {}
    
    # Crear Matriz de Brechas
    resultados['matriz_brechas'] = create_matriz_brechas(
        fact_vulnerabilidad_df,
        fact_contratacion_df,
        dim_municipio_df,
    )
    
    # Crear Inversión vs Vulnerabilidad
    resultados['inversion_vs_vulnerabilidad'] = create_inversion_vs_vulnerabilidad(
        fact_vulnerabilidad_df,
        fact_contratacion_df,
        dim_municipio_df,
    )
    
    # Crear Autocorrelación Espacial
    resultados['autocorrelacion_espacial'] = create_autocorrelacion_espacial(
        fact_vulnerabilidad_df,
        fact_contratacion_df,
        dim_municipio_df,
    )
    
    logger.info(f"Data Mart Social creado: {len(resultados)} tablas")
    
    return {
        'status': 'success',
        'tablas': resultados,
        'output_path': str(output_path) if output_path else None,
    }


def create_matriz_brechas(
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear Matriz de Brechas Socioeconómicas.
    
    Identifica municipios con mayor discrepancia entre vulnerabilidad
    e inversión pública recibida.
    
    Parameters:
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Matriz de Brechas...")
    
    # Agregar inversión por municipio
    inversion_por_municipio = _aggregate_inversion_municipal(fact_contratacion_df)
    
    # Unir con vulnerabilidad
    matriz = fact_vulnerabilidad_df.merge(
        inversion_por_municipio,
        on='divipola_municipio',
        how='left',
    )
    
    # Unir con información de municipio
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        matriz = matriz.merge(
            dim_municipio_df[['divipola_municipio', 'nombre_municipio', 'divipola_departamento', 'nombre_departamento', 'region']],
            on='divipola_municipio',
            how='left',
        )
    
    # Calcular rankings
    matriz['ranking_vulnerabilidad'] = matriz['ipm_total'].rank(ascending=False, method='min').astype(int)
    
    matriz['monto_per_capita'] = (
        matriz['monto_total_contratos'] / 
        matriz['poblacion_total'].replace(0, np.nan)
    ).fillna(0)
    
    matriz['ranking_inversion'] = matriz['monto_per_capita'].rank(ascending=False, method='min').astype(int)
    
    # Calcular brecha (ranking_vuln - ranking_inv)
    # Brecha positiva: alta vulnerabilidad, baja inversión (CRÍTICO)
    # Brecha negativa: baja vulnerabilidad, alta inversión
    matriz['brecha_ranking'] = matriz['ranking_vulnerabilidad'] - matriz['ranking_inversion']
    
    # Categorizar brecha
    matriz['categoria_brecha'] = pd.cut(
        matriz['brecha_ranking'],
        bins=[-np.inf, -50, -20, 20, 50, np.inf],
        labels=[
            'PRIORITARIO: Inversión > Vulnerabilidad',
            'ATENCION: Inversión moderadamente > Vulnerabilidad',
            'BALANCEADO',
            'ATENCION: Vulnerabilidad > Inversión',
            'CRITICO: Alta vulnerabilidad, baja inversión',
        ],
    )
    
    # Calcular percentiles
    matriz['ipm_percentil'] = matriz['ipm_total'].rank(pct=True) * 100
    matriz['inversion_percentil'] = matriz['monto_per_capita'].rank(pct=True) * 100
    
    # Brecha absoluta de percentiles
    matriz['brecha_percentil'] = matriz['ipm_percentil'] - matriz['inversion_percentil']
    
    # Score de prioridad (0-100)
    matriz['prioridad_score'] = (
        (matriz['ipm_percentil'] + (100 - matriz['inversion_percentil'])) / 2
    ).clip(0, 100)
    
    # Seleccionar columnas finales
    columnas_finales = [
        'divipola_municipio', 'nombre_municipio', 'divipola_departamento', 
        'nombre_departamento', 'region',
        'ipm_total', 'ipm_zscore', 'ipm_percentil', 'ranking_vulnerabilidad',
        'pobreza_monetaria', 'pobreza_zscore',
        'monto_total_contratos', 'monto_per_capita', 'inversion_percentil', 
        'ranking_inversion',
        'brecha_ranking', 'brecha_percentil', 'categoria_brecha', 
        'prioridad_score',
        'poblacion_total',
    ]
    
    columnas_existentes = [c for c in columnas_finales if c in matriz.columns]
    matriz = matriz[columnas_existentes]
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.MODELO_ESTRELLA_PATH / 'datamart_social' / 'matriz_brechas_municipal'
    
    output_path = Path(output_path)
    if output_path.suffix == '.parquet':
        output_path = output_path.with_suffix('')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from pipeline.utils.spark_session import write_parquet
    write_parquet(matriz, output_path)
    
    logger.info(f"Matriz de Brechas creada: {len(matriz)} municipios")
    
    # Estadísticas resumen
    criticos = (matriz['categoria_brecha'].astype(str) == 'CRITICO: Alta vulnerabilidad, baja inversión').sum()
    prioritarios = (matriz['categoria_brecha'].astype(str) == 'PRIORITARIO: Inversión > Vulnerabilidad').sum()
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(matriz),
        'municipios_criticos': int(criticos),
        'municipios_prioritarios': int(prioritarios),
    }


def create_inversion_vs_vulnerabilidad(
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear tabla de Inversión vs Vulnerabilidad por departamento.
    
    Parameters:
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando Inversión vs Vulnerabilidad...")
    
    # 1. Extraer año y agregar INVERSIÓN por municipio y año
    cont = fact_contratacion_df[['divipola_municipio', 'monto_contrato', 'fecha_publicacion_key']].copy()
    cont['fecha_publicacion_key'] = cont['fecha_publicacion_key'].fillna(19000101)
    cont['anio'] = (cont['fecha_publicacion_key'] // 10000).astype(int)
    
    cont_agg = cont.groupby(['divipola_municipio', 'anio']).agg({
        'monto_contrato': ['sum', 'mean', 'count']
    }).reset_index()
    
    # Aplanar columnas de jerarquía
    cont_agg.columns = ['divipola_municipio', 'anio', 'inversion_total', 'inversion_promedio', 'num_contratos']
    
    # 2. Unir datos pre-agregados con vulnerabilidad
    datos = fact_vulnerabilidad_df.merge(
        cont_agg,
        on='divipola_municipio',
        how='left',
    )
    
    # Llenar nulos para municipios sin contratos (o datos base)
    datos['anio'] = datos['anio'].fillna(datetime.now().year).astype(int)
    for col in ['inversion_total', 'inversion_promedio', 'num_contratos']:
        datos[col] = datos[col].fillna(0)
    
    # Unir con departamento
    if dim_municipio_df is not None and not dim_municipio_df.empty:
        datos = datos.merge(
            dim_municipio_df[['divipola_municipio', 'divipola_departamento', 'nombre_departamento', 'region']],
            on='divipola_municipio',
            how='left',
        )
    
    # Definir agregaciones a nivel DEPARTAMENTAL
    agg_dict = {
        'inversion_total': 'sum',
        'inversion_promedio': 'mean',
        'num_contratos': 'sum',
        'ipm_total': 'mean',
    }
    
    # Agregar opcionales si existen
    if 'pobreza_monetaria' in datos.columns:
        agg_dict['pobreza_monetaria'] = 'mean'
    if 'monto_per_capita' in datos.columns:
        agg_dict['monto_per_capita'] = 'mean'
    if 'poblacion_total' in datos.columns:
        agg_dict['poblacion_total'] = 'sum'
        
    agregado = datos.groupby(['anio', 'divipola_departamento', 'nombre_departamento', 'region']).agg(agg_dict).reset_index()
    
    # Nombrar las columnas resultantes dinámicamente
    new_cols = ['anio', 'divipola_departamento', 'nombre_departamento', 'region', 'inversion_total', 'inversion_promedio', 'num_contratos', 'ipm_promedio']
    if 'pobreza_monetaria' in datos.columns: new_cols.append('pobreza_promedio')
    if 'monto_per_capita' in datos.columns: new_cols.append('inversion_promedio_per_capita')
    if 'poblacion_total' in datos.columns: new_cols.append('poblacion_total')
    
    agregado.columns = new_cols
    
    # Calcular correlación por año
    correlaciones = []
    for anio in agregado['anio'].unique():
        datos_anio = agregado[agregado['anio'] == anio]
        
        if len(datos_anio) > 2:
            # Seleccionar columna para correlación
            col_inversion = 'inversion_promedio_per_capita' if 'inversion_promedio_per_capita' in datos_anio.columns else 'inversion_promedio'
            corr = datos_anio[col_inversion].corr(datos_anio['ipm_promedio'])
        else:
            corr = np.nan
        
        correlaciones.append({
            'anio': anio,
            'correlacion_inversion_ipm': corr,
        })
    
    df_corr = pd.DataFrame(correlaciones)
    agregado = agregado.merge(df_corr, on='anio', how='left')
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.MODELO_ESTRELLA_PATH / 'datamart_social' / 'inversion_vs_vulnerabilidad'
    
    output_path = Path(output_path)
    if output_path.suffix == '.parquet':
        output_path = output_path.with_suffix('')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from pipeline.utils.spark_session import write_parquet
    write_parquet(agregado, output_path)
    
    logger.info(f"Inversión vs Vulnerabilidad creada: {len(agregado)} registros")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(agregado),
        'anios_cubiertos': list(agregado['anio'].unique()),
    }


def create_autocorrelacion_espacial(
    fact_vulnerabilidad_df: pd.DataFrame,
    fact_contratacion_df: pd.DataFrame,
    dim_municipio_df: pd.DataFrame,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Calcular Índice de Moran para autocorrelación espacial.
    
    Parameters:
    - fact_vulnerabilidad_df: Tabla de hechos de vulnerabilidad
    - fact_contratacion_df: Tabla de hechos de contratación
    - dim_municipio_df: Dimensión de municipios
    - output_path: Ruta de salida
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Calculando Autocorrelación Espacial...")
    
    # Preparar datos
    datos = fact_vulnerabilidad_df.copy()
    
    # Agregar inversión
    inversion = _aggregate_inversion_municipal(fact_contratacion_df)
    datos = datos.merge(inversion, on='divipola_municipio', how='left')
    
    # Agregar coordenadas (en producción usar geoportal)
    datos['latitud'] = np.nan
    datos['longitud'] = np.nan
    
    # Calcular Moran's I (simplificado - en producción usar libpysal/esda)
    resultados = _calcular_morans_i_simplificado(datos)
    
    # Crear DataFrame de resultados
    resultado_df = pd.DataFrame([resultados])
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.MODELO_ESTRELLA_PATH / 'datamart_social' / 'autocorrelacion_espacial'
    
    output_path = Path(output_path)
    if output_path.suffix == '.parquet':
        output_path = output_path.with_suffix('')
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    from pipeline.utils.spark_session import write_parquet
    write_parquet(resultado_df, output_path)
    
    logger.info(f"Autocorrelación Espacial calculada")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'moran_i_inversion': resultados.get('moran_i_inversion'),
        'moran_i_vulnerabilidad': resultados.get('moran_i_vulnerabilidad'),
        'significativo': resultados.get('significativo', False),
    }


def _aggregate_inversion_municipal(fact_contratacion_df: pd.DataFrame) -> pd.DataFrame:
    """Agregar inversión por municipio."""
    if fact_contratacion_df is None or fact_contratacion_df.empty:
        return pd.DataFrame(columns=['divipola_municipio', 'monto_total_contratos', 'num_contratos'])
    
    return fact_contratacion_df.groupby('divipola_municipio').agg({
        'monto_contrato': 'sum',
        'id_contrato': 'count',
    }).reset_index().rename(columns={
        'monto_contrato': 'monto_total_contratos',
        'id_contrato': 'num_contratos',
    })


def _calcular_morans_i_simplificado(datos: pd.DataFrame) -> Dict[str, Any]:
    """
    Calcular Índice de Moran's I para autocorrelación espacial.
    
    Usa libpysal (Queen weights) y esda (Moran) para cálculo real.
    Requiere que el DataFrame tenga geometría (GeoDataFrame) o 
    coordenadas para construir la matriz de pesos espaciales.
    """
    try:
        from libpysal.weights import Queen, KNN
        from esda.moran import Moran
        import geopandas as gpd
    except ImportError:
        logger.warning(
            "libpysal y/o esda no están instalados. "
            "Instalar con: pip install libpysal esda geopandas. "
            "Retornando None en lugar de valores simulados."
        )
        return {
            'moran_i_inversion': None,
            'p_value_inversion': None,
            'z_score_inversion': None,
            'moran_i_vulnerabilidad': None,
            'p_value_vulnerabilidad': None,
            'z_score_vulnerabilidad': None,
            'significativo': None,
            'metodo': 'no_disponible',
            'nota': 'libpysal/esda no instalados',
        }
    
    resultados = {}
    
    # Verificar si tenemos geometría
    if not isinstance(datos, gpd.GeoDataFrame):
        # Intentar cargar geometría desde el geoportal
        try:
            from pathlib import Path
            geo_path = Path('datos/bronze/dane_geoportal')
            shapefiles = list(geo_path.rglob('*.shp'))
            if shapefiles:
                gdf = gpd.read_file(shapefiles[0])
                if 'MPIO_CDPMP' in gdf.columns:
                    gdf = gdf.rename(columns={'MPIO_CDPMP': 'divipola_municipio'})
                datos = datos.merge(
                    gdf[['divipola_municipio', 'geometry']],
                    on='divipola_municipio',
                    how='inner',
                )
                datos = gpd.GeoDataFrame(datos, geometry='geometry')
            else:
                logger.warning("No se encontraron shapefiles para Moran's I. Usando KNN con coordenadas centrales.")
                return _fallback_no_geometry(datos)
        except Exception as e:
            logger.warning(f"Error cargando geometría: {e}")
            return _fallback_no_geometry(datos)
    
    if len(datos) < 3:
        logger.warning("Insuficientes observaciones para Moran's I (mínimo 3)")
        return {
            'moran_i_inversion': None, 'p_value_inversion': None, 'z_score_inversion': None,
            'moran_i_vulnerabilidad': None, 'p_value_vulnerabilidad': None, 'z_score_vulnerabilidad': None,
            'significativo': None, 'metodo': 'insuficientes_datos', 'nota': f'Solo {len(datos)} observaciones',
        }
    
    try:
        # Construir matriz de pesos Queen (contigüidad)
        w = Queen.from_dataframe(datos, silence_warnings=True)
        w.transform = 'r'  # Row-standardize
        
        # Moran's I para inversión
        if 'monto_total_contratos' in datos.columns:
            y_inv = datos['monto_total_contratos'].fillna(0).values
            moran_inv = Moran(y_inv, w)
            resultados['moran_i_inversion'] = round(float(moran_inv.I), 4)
            resultados['p_value_inversion'] = round(float(moran_inv.p_sim), 4)
            resultados['z_score_inversion'] = round(float(moran_inv.z_sim), 4)
        
        # Moran's I para vulnerabilidad
        vuln_col = None
        for col in ['ipm_total', 'nbi_total', 'indice_vulnerabilidad']:
            if col in datos.columns:
                vuln_col = col
                break
        
        if vuln_col:
            y_vuln = datos[vuln_col].fillna(0).values
            moran_vuln = Moran(y_vuln, w)
            resultados['moran_i_vulnerabilidad'] = round(float(moran_vuln.I), 4)
            resultados['p_value_vulnerabilidad'] = round(float(moran_vuln.p_sim), 4)
            resultados['z_score_vulnerabilidad'] = round(float(moran_vuln.z_sim), 4)
        
        # Determinar significancia
        p_inv = resultados.get('p_value_inversion', 1)
        p_vuln = resultados.get('p_value_vulnerabilidad', 1)
        resultados['significativo'] = (p_inv is not None and p_inv < 0.05) or \
                                       (p_vuln is not None and p_vuln < 0.05)
        resultados['metodo'] = 'queen'
        resultados['nota'] = 'Cálculo real con libpysal/esda'
        
        logger.info(f"Moran's I calculado: inv={resultados.get('moran_i_inversion')}, "
                     f"vuln={resultados.get('moran_i_vulnerabilidad')}")
        
    except Exception as e:
        logger.error(f"Error calculando Moran's I: {e}")
        resultados = {
            'moran_i_inversion': None, 'p_value_inversion': None, 'z_score_inversion': None,
            'moran_i_vulnerabilidad': None, 'p_value_vulnerabilidad': None, 'z_score_vulnerabilidad': None,
            'significativo': None, 'metodo': 'error', 'nota': str(e),
        }
    
    return resultados


def _fallback_no_geometry(datos: pd.DataFrame) -> Dict[str, Any]:
    """Fallback cuando no hay geometría disponible."""
    logger.warning("Sin geometría disponible para Moran's I. Retornando None.")
    return {
        'moran_i_inversion': None,
        'p_value_inversion': None,
        'z_score_inversion': None,
        'moran_i_vulnerabilidad': None,
        'p_value_vulnerabilidad': None,
        'z_score_vulnerabilidad': None,
        'significativo': None,
        'metodo': 'sin_geometria',
        'nota': 'No se encontraron datos geoespaciales para construir la matriz de pesos',
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo con datos vacíos
    print("Creando Data Mart Social...")
    
    fact_vuln = pd.DataFrame()
    fact_cont = pd.DataFrame()
    dim_mun = pd.DataFrame()
    
    resultado = create_datamart_social(fact_vuln, fact_cont, dim_mun)
    print(f"Resultado: {resultado}")
