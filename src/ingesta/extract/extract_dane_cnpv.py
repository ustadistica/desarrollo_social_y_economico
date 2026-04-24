"""
Extracción de datos del Censo Nacional de Población y Vivienda (CNPV) - DANE.

Fuentes:
- Indicadores de pobreza multidimensional a nivel municipal (datos.gov.co)
- Proyecciones de población DANE (datos.gov.co)
- Déficit habitacional por municipio

Método: SODA API (Socrata) via datos.gov.co
"""

import logging
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import requests

logger = logging.getLogger(__name__)

# ================================================================
# DATASETS SOCRATA EN datos.gov.co PARA CNPV
# ================================================================
CNPV_DATASETS = {
    # Pobreza multidimensional municipal (CNPV 2018)
    'ipm_municipal': {
        'dataset_id': 'vgth-gqwi',  # IPM por municipio DANE
        'description': 'Índice de Pobreza Multidimensional por municipio',
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
    },
    # NBI municipal
    'nbi_municipal': {
        'dataset_id': 'vgth-gqwi',
        'description': 'Necesidades Básicas Insatisfechas municipal',
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
    },
    # Proyecciones de población DANE
    'poblacion_proyecciones': {
        'dataset_id': 'csb4-y4hq',  # Proyecciones de población DANE
        'description': 'Proyecciones de población por municipio',
        'base_url': 'https://www.datos.gov.co/resource/csb4-y4hq.json',
    },
}


def extract_dane_cnpv(
    vigencia: str = 'latest',
    output_path: Optional[Path] = None,
    app_token: Optional[str] = None,
    batch_size: int = 5000,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Extraer datos del CNPV desde datos.gov.co.

    Parameters:
    - vigencia: Vigencia de datos ('2024', '2025', 'latest')
    - output_path: Ruta de salida para Parquet
    - app_token: Token de la API Socrata (opcional pero recomendado)
    - batch_size: Registros por solicitud
    - max_retries: Número máximo de reintentos

    Returns:
    - Dict con metadata de extracción
    """
    logger.info(f"Iniciando extracción CNPV, vigencia={vigencia}")
    start_time = datetime.now()

    if app_token is None:
        import os
        app_token = os.environ.get('SODA_APP_TOKEN', '')

    all_dataframes = {}

    # ---- 1. Extraer datos de pobreza multidimensional (IPM) ----
    logger.info("Descargando IPM municipal desde datos.gov.co...")
    ipm_df = _fetch_socrata_dataset(
        base_url=CNPV_DATASETS['ipm_municipal']['base_url'],
        app_token=app_token,
        batch_size=batch_size,
        max_retries=max_retries,
        params={},
    )
    all_dataframes['ipm'] = ipm_df

    # ---- 2. Extraer proyecciones de población ----
    logger.info("Descargando proyecciones de población desde datos.gov.co...")
    poblacion_df = _fetch_socrata_dataset(
        base_url=CNPV_DATASETS['poblacion_proyecciones']['base_url'],
        app_token=app_token,
        batch_size=batch_size,
        max_retries=max_retries,
        params={},
    )
    all_dataframes['poblacion'] = poblacion_df

    # ---- 3. Consolidar en un solo DataFrame ----
    df = _consolidar_cnpv(all_dataframes, vigencia)

    # ---- 4. Agregar metadatos de ingesta ----
    df = _add_ingestion_metadata(df, vigencia)

    # ---- 5. Guardar en Parquet ----
    if output_path is None:
        from src.config.settings import settings
        ingestion_date = datetime.now().strftime('%Y-%m-%d')
        output_path = Path(settings.get('paths', {}).get('bronze', 'datos/bronze'))
        output_path = output_path / 'dane_cnpv' / f'ingestion_date={ingestion_date}'

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_file = output_path / 'cnpv_data.parquet'
    df.to_parquet(parquet_file, index=False, compression='snappy')

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"CNPV extracción completada: {len(df)} registros en {elapsed:.1f}s")

    return {
        'status': 'success',
        'registros': len(df),
        'archivo': str(parquet_file),
        'vigencia': vigencia,
        'columnas': list(df.columns),
        'fuentes_descargadas': list(all_dataframes.keys()),
        'tiempo_segundos': elapsed,
    }


def _fetch_socrata_dataset(
    base_url: str,
    app_token: str = '',
    batch_size: int = 5000,
    max_retries: int = 3,
    params: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Descargar dataset completo vía SODA API con paginación.

    Parameters:
    - base_url: URL del endpoint .json del dataset
    - app_token: Token Socrata
    - batch_size: Registros por página
    - max_retries: Reintentos por fallo

    Returns:
    - DataFrame con todos los registros
    """
    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token

    all_records = []
    offset = 0

    while True:
        query_params = {
            '$limit': batch_size,
            '$offset': offset,
            '$order': ':id',
        }
        if params:
            query_params.update(params)

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    base_url,
                    params=query_params,
                    headers=headers,
                    timeout=60,
                )

                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Rate limit alcanzado. Esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                batch = response.json()

                if not batch:
                    logger.info(f"Descarga completa: {len(all_records)} registros totales")
                    return pd.DataFrame(all_records)

                all_records.extend(batch)
                offset += len(batch)

                if len(batch) < batch_size:
                    logger.info(f"Última página recibida. Total: {len(all_records)} registros")
                    return pd.DataFrame(all_records)

                logger.debug(f"  Página descargada: offset={offset}, acumulado={len(all_records)}")
                break

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Error en request (intento {attempt+1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Fallo definitivo tras {max_retries} intentos: {e}")
                    return pd.DataFrame(all_records) if all_records else pd.DataFrame()

    return pd.DataFrame(all_records)


def _consolidar_cnpv(
    dataframes: Dict[str, pd.DataFrame],
    vigencia: str,
) -> pd.DataFrame:
    """
    Consolidar los diferentes datasets CNPV en un solo DataFrame.

    Parameters:
    - dataframes: Dict con DataFrames descargados
    - vigencia: Vigencia solicitada

    Returns:
    - DataFrame consolidado a nivel municipal
    """
    ipm_df = dataframes.get('ipm', pd.DataFrame())
    poblacion_df = dataframes.get('poblacion', pd.DataFrame())

    # Si no hay datos, retornar esquema vacío
    if ipm_df.empty and poblacion_df.empty:
        logger.warning("No se obtuvieron datos del CNPV. Retornando DataFrame vacío con esquema.")
        return _create_empty_cnpv_schema()

    # Normalizar columnas del IPM
    if not ipm_df.empty:
        ipm_df = _normalize_ipm_columns(ipm_df)

    # Normalizar columnas de población
    if not poblacion_df.empty:
        poblacion_df = _normalize_poblacion_columns(poblacion_df, vigencia)

    # Merge por DIVIPOLA
    if not ipm_df.empty and not poblacion_df.empty:
        df = ipm_df.merge(
            poblacion_df,
            on='divipola_municipio',
            how='outer',
            suffixes=('', '_pob'),
        )
    elif not ipm_df.empty:
        df = ipm_df
    else:
        df = poblacion_df

    return df


def _normalize_ipm_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizar nombres de columnas del dataset IPM."""
    # Mapeo flexible de columnas (los nombres pueden variar según el dataset)
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'divipola' in col_lower or 'c_digo_dane' in col_lower or 'codigo_dane' in col_lower or 'cod_mun' in col_lower:
            column_mapping[col] = 'divipola_municipio'
        elif 'ipm' in col_lower and ('total' in col_lower or 'general' in col_lower):
            column_mapping[col] = 'ipm_total'
        elif 'municipio' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_municipio'
        elif 'departamento' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_departamento'
        elif 'nbi' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'nbi_total'
        elif 'deficit' in col_lower and 'cuantitativo' in col_lower:
            column_mapping[col] = 'deficit_cuantitativo'
        elif 'deficit' in col_lower and 'cualitativo' in col_lower:
            column_mapping[col] = 'deficit_cualitativo'
        elif 'pobreza' in col_lower and 'monetaria' in col_lower:
            column_mapping[col] = 'pobreza_monetaria'
        elif 'pobreza' in col_lower and 'extrema' in col_lower:
            column_mapping[col] = 'pobreza_extrema'

    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)

    # Convertir valores numéricos
    numeric_cols = ['ipm_total', 'nbi_total', 'deficit_cuantitativo', 'deficit_cualitativo',
                    'pobreza_monetaria', 'pobreza_extrema']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    return df


def _normalize_poblacion_columns(df: pd.DataFrame, vigencia: str) -> pd.DataFrame:
    """Normalizar columnas del dataset de proyecciones de población."""
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'divipola' in col_lower or 'c_digo' in col_lower or 'dpmp' in col_lower or 'cod_mun' in col_lower:
            column_mapping[col] = 'divipola_municipio'
        elif 'poblaci' in col_lower and ('total' in col_lower or 'proyecc' in col_lower):
            column_mapping[col] = 'poblacion_total'
        elif col_lower in ['a_o', 'año', 'anio', 'ano', 'year']:
            column_mapping[col] = 'vigencia'

    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Filtrar por vigencia
    if 'vigencia' in df.columns and vigencia != 'latest':
        df = df[df['vigencia'].astype(str) == str(vigencia)]

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)

    if 'poblacion_total' in df.columns:
        df['poblacion_total'] = pd.to_numeric(df['poblacion_total'], errors='coerce')

    return df


def _create_empty_cnpv_schema() -> pd.DataFrame:
    """Crear DataFrame vacío con el esquema esperado."""
    columns = [
        'divipola_municipio', 'nombre_municipio', 'nombre_departamento',
        'ipm_total', 'nbi_total',
        'deficit_cuantitativo', 'deficit_cualitativo',
        'pobreza_monetaria', 'pobreza_extrema',
        'poblacion_total', 'vigencia',
    ]
    return pd.DataFrame(columns=columns)


def _add_ingestion_metadata(df: pd.DataFrame, vigencia: str) -> pd.DataFrame:
    """Agregar metadatos de ingesta al DataFrame."""
    df = df.copy()
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = 'dane_cnpv'
    df['_source_version'] = vigencia

    # Checksum MD5 por fila
    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values)
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = extract_dane_cnpv(vigencia='latest')
    print(f"Resultado: {resultado}")
