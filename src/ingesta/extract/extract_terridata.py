"""
Extracción de indicadores territoriales de TerriData - DNP.

Fuentes:
- Indicadores de pobreza, empleo, inversión por municipio
- Descarga vía datos.gov.co (SODA API) y TerriData (descarga directa)

Método: SODA API (Socrata) y descarga HTTP
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
# DATASETS SOCRATA EN datos.gov.co PARA TERRIDATA / DNP
# ================================================================
TERRIDATA_DATASETS = {
    'indicadores_municipales': {
        'dataset_id': 'i386-tpjk',  # Indicadores municipales DNP
        'description': 'Indicadores socioeconómicos por municipio (DNP)',
        'base_url': 'https://www.datos.gov.co/resource/i386-tpjk.json',
    },
    'pobreza_multidimensional': {
        'dataset_id': 'cg8c-dckd',  # Pobreza multidimensional DANE/DNP
        'description': 'Medida de pobreza multidimensional municipal',
        'base_url': 'https://www.datos.gov.co/resource/cg8c-dckd.json',
    },
    'ejecucion_presupuestal': {
        'dataset_id': 'dkgx-igp6',  # Ejecución presupuestal territorial
        'description': 'Ejecución presupuestal de entidades territoriales',
        'base_url': 'https://www.datos.gov.co/resource/dkgx-igp6.json',
    },
}

# Indicadores clave a extraer
INDICADORES_CLAVE = [
    'pobreza_multidimensional',
    'pobreza_monetaria',
    'nbi',
    'cobertura_educacion',
    'cobertura_salud',
    'gasto_inversion_per_capita',
    'desempleo',
    'informalidad',
]


def extract_terridata(
    vigencia: str = 'latest',
    indicadores: Optional[List[str]] = None,
    output_path: Optional[Path] = None,
    app_token: Optional[str] = None,
    batch_size: int = 5000,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Extraer indicadores territoriales desde datos.gov.co/TerriData.

    Parameters:
    - vigencia: Vigencia de datos ('2023', '2024', 'latest')
    - indicadores: Lista de indicadores a extraer (default: todos)
    - output_path: Ruta de salida
    - app_token: Token Socrata
    - batch_size: Registros por solicitud
    - max_retries: Reintentos máximos

    Returns:
    - Dict con metadata de extracción
    """
    logger.info(f"Iniciando extracción TerriData, vigencia={vigencia}")
    start_time = datetime.now()

    if indicadores is None:
        indicadores = INDICADORES_CLAVE

    if app_token is None:
        import os
        app_token = os.environ.get('SODA_APP_TOKEN', '')

    all_dataframes = {}

    # ---- 1. Descargar indicadores municipales ----
    logger.info("Descargando indicadores municipales desde datos.gov.co...")
    for dataset_key, dataset_info in TERRIDATA_DATASETS.items():
        logger.info(f"  Descargando {dataset_key}: {dataset_info['description']}...")
        df = _fetch_socrata_dataset(
            base_url=dataset_info['base_url'],
            app_token=app_token,
            batch_size=batch_size,
            max_retries=max_retries,
        )
        if not df.empty:
            all_dataframes[dataset_key] = df
            logger.info(f"  {dataset_key}: {len(df)} registros descargados")
        else:
            logger.warning(f"  {dataset_key}: sin datos")

    # ---- 2. Consolidar datasets ----
    df = _consolidar_terridata(all_dataframes, vigencia)

    # ---- 3. Agregar metadatos de ingesta ----
    df = _add_ingestion_metadata(df, vigencia)

    # ---- 4. Guardar en Parquet ----
    if output_path is None:
        from src.config.settings import settings
        ingestion_date = datetime.now().strftime('%Y-%m-%d')
        output_path = Path(settings.get('paths', {}).get('bronze', 'data/bronze'))
        output_path = output_path / 'terridata' / f'ingestion_date={ingestion_date}'

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_file = output_path / 'terridata_data.parquet'
    df.to_parquet(parquet_file, index=False, compression='snappy')

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"TerriData extracción completada: {len(df)} registros en {elapsed:.1f}s")

    return {
        'status': 'success',
        'registros': len(df),
        'archivo': str(parquet_file),
        'vigencia': vigencia,
        'datasets_descargados': list(all_dataframes.keys()),
        'columnas': list(df.columns),
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
                    logger.warning(f"Rate limit. Esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                batch = response.json()

                if not batch:
                    return pd.DataFrame(all_records)

                all_records.extend(batch)
                offset += len(batch)

                if len(batch) < batch_size:
                    return pd.DataFrame(all_records)

                logger.debug(f"  Página: offset={offset}, acumulado={len(all_records)}")
                break

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"Error (intento {attempt+1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Fallo definitivo: {e}")
                    return pd.DataFrame(all_records) if all_records else pd.DataFrame()

    return pd.DataFrame(all_records)


def _consolidar_terridata(
    dataframes: Dict[str, pd.DataFrame],
    vigencia: str,
) -> pd.DataFrame:
    """Consolidar múltiples datasets TerriData en uno solo."""
    if not dataframes:
        logger.warning("No se obtuvieron datos de TerriData. Retornando esquema vacío.")
        return _create_empty_terridata_schema()

    consolidated = None

    for key, df in dataframes.items():
        df = _normalize_terridata_columns(df, key)

        if consolidated is None:
            consolidated = df
        else:
            # Merge por DIVIPOLA
            merge_cols = ['divipola_municipio']
            if 'vigencia' in consolidated.columns and 'vigencia' in df.columns:
                merge_cols.append('vigencia')

            available_merge = [c for c in merge_cols if c in consolidated.columns and c in df.columns]

            if available_merge:
                consolidated = consolidated.merge(
                    df,
                    on=available_merge,
                    how='outer',
                    suffixes=('', f'_{key}'),
                )

    # Filtrar por vigencia si se especificó
    if consolidated is not None and 'vigencia' in consolidated.columns and vigencia != 'latest':
        consolidated = consolidated[consolidated['vigencia'].astype(str) == str(vigencia)]

    return consolidated if consolidated is not None else _create_empty_terridata_schema()


def _normalize_terridata_columns(df: pd.DataFrame, dataset_key: str) -> pd.DataFrame:
    """Normalizar columnas de un dataset TerriData."""
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'divipola' in col_lower or 'c_digo_dane' in col_lower or 'cod_mun' in col_lower or 'codigo_entidad' in col_lower:
            column_mapping[col] = 'divipola_municipio'
        elif 'municipio' in col_lower and ('nombre' in col_lower or col_lower == 'municipio'):
            column_mapping[col] = 'nombre_municipio'
        elif 'departamento' in col_lower and ('nombre' in col_lower or col_lower == 'departamento'):
            column_mapping[col] = 'nombre_departamento'
        elif col_lower in ['a_o', 'año', 'anio', 'ano', 'year', 'vigencia']:
            column_mapping[col] = 'vigencia'
        elif 'pobreza' in col_lower and 'multi' in col_lower:
            column_mapping[col] = 'ipm_terridata'
        elif 'nbi' in col_lower:
            column_mapping[col] = 'nbi_terridata'
        elif 'cobertura' in col_lower and 'educ' in col_lower:
            column_mapping[col] = 'cobertura_educacion'
        elif 'cobertura' in col_lower and 'salud' in col_lower:
            column_mapping[col] = 'cobertura_salud'
        elif 'gasto' in col_lower and ('inversion' in col_lower or 'per_capita' in col_lower):
            column_mapping[col] = 'gasto_inversion_per_capita'
        elif 'desempleo' in col_lower:
            column_mapping[col] = 'tasa_desempleo'
        elif 'informal' in col_lower:
            column_mapping[col] = 'tasa_informalidad'

    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)

    return df


def _create_empty_terridata_schema() -> pd.DataFrame:
    """Crear DataFrame vacío con esquema esperado."""
    columns = [
        'divipola_municipio', 'nombre_municipio', 'nombre_departamento',
        'vigencia',
        'ipm_terridata', 'nbi_terridata',
        'cobertura_educacion', 'cobertura_salud',
        'gasto_inversion_per_capita',
        'tasa_desempleo', 'tasa_informalidad',
    ]
    return pd.DataFrame(columns=columns)


def _add_ingestion_metadata(df: pd.DataFrame, vigencia: str) -> pd.DataFrame:
    """Agregar metadatos de ingesta."""
    df = df.copy()
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = 'terridata_dnp'
    df['_source_version'] = vigencia

    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values)
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = extract_terridata(vigencia='latest')
    print(f"Resultado: {resultado}")
