"""
Extracción de datos del Censo Económico Nacional Urbano (CENU) / EMICRON - DANE.

Fuentes:
- Encuesta de Micronegocios (EMICRON) - datos.gov.co
- Indicadores de micronegocios por municipio y sector CIIU

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
# DATASETS SOCRATA EN datos.gov.co PARA CENU / EMICRON
# ================================================================
CENU_DATASETS = {
    # Encuesta de Micronegocios (fuente más actualizada para datos de micronegocios)
    'emicron': {
        'dataset_id': 'r2bh-bfag',  # EMICRON DANE en datos.gov.co
        'description': 'Encuesta de Micronegocios por municipio y sector',
        'base_url': 'https://www.datos.gov.co/resource/r2bh-bfag.json',
    },
    # Unidades económicas (CENU 2024 resultados preliminares)
    'unidades_economicas': {
        'dataset_id': 'jwfy-yjz8',
        'description': 'Unidades económicas censo económico',
        'base_url': 'https://www.datos.gov.co/resource/jwfy-yjz8.json',
    },
}


def extract_dane_cenu(
    vigencia: str = 'latest',
    tamano_empresa: str = 'micro',
    sector: Optional[str] = None,
    output_path: Optional[Path] = None,
    app_token: Optional[str] = None,
    batch_size: int = 5000,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Extraer datos del CENU/EMICRON desde datos.gov.co.

    Parameters:
    - vigencia: Vigencia de datos ('2024', 'latest')
    - tamano_empresa: Filtro por tamaño ('micro', 'pequena', 'todas')
    - sector: Filtro por sector CIIU (e.g., 'G47')
    - output_path: Ruta de salida para Parquet
    - app_token: Token de la API Socrata
    - batch_size: Registros por solicitud
    - max_retries: Reintentos máximos

    Returns:
    - Dict con metadata de extracción
    """
    logger.info(f"Iniciando extracción CENU/EMICRON, vigencia={vigencia}, tamano={tamano_empresa}")
    start_time = datetime.now()

    if app_token is None:
        import os
        app_token = os.environ.get('SODA_APP_TOKEN', '')

    # Construir filtros SoQL
    soql_params = _build_soql_filters(vigencia, tamano_empresa, sector)

    # ---- 1. Extraer datos de EMICRON ----
    logger.info("Descargando datos EMICRON desde datos.gov.co...")
    emicron_df = _fetch_socrata_dataset(
        base_url=CENU_DATASETS['emicron']['base_url'],
        app_token=app_token,
        batch_size=batch_size,
        max_retries=max_retries,
        params=soql_params,
    )

    # ---- 2. Si EMICRON falla, intentar con unidades_economicas ----
    if emicron_df.empty:
        logger.info("EMICRON vacío, intentando con unidades económicas...")
        emicron_df = _fetch_socrata_dataset(
            base_url=CENU_DATASETS['unidades_economicas']['base_url'],
            app_token=app_token,
            batch_size=batch_size,
            max_retries=max_retries,
            params={},
        )

    # ---- 3. Normalizar y procesar ----
    df = _normalize_cenu_columns(emicron_df, tamano_empresa)

    # ---- 4. Agregar metadatos de ingesta ----
    df = _add_ingestion_metadata(df, vigencia)

    # ---- 5. Guardar en Parquet ----
    if output_path is None:
        from config.settings import settings
        ingestion_date = datetime.now().strftime('%Y-%m-%d')
        output_path = Path(settings.get('paths', {}).get('bronze', 'datos/bronze'))
        output_path = output_path / 'dane_cenu' / f'ingestion_date={ingestion_date}'

    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    parquet_file = output_path / 'cenu_data.parquet'
    df.to_parquet(parquet_file, index=False, compression='snappy')

    elapsed = (datetime.now() - start_time).total_seconds()

    logger.info(f"CENU/EMICRON extracción completada: {len(df)} registros en {elapsed:.1f}s")

    return {
        'status': 'success',
        'registros': len(df),
        'archivo': str(parquet_file),
        'vigencia': vigencia,
        'tamano_empresa': tamano_empresa,
        'columnas': list(df.columns),
        'tiempo_segundos': elapsed,
    }


def _build_soql_filters(
    vigencia: str,
    tamano_empresa: str,
    sector: Optional[str],
) -> dict:
    """Construir filtros SoQL para la consulta Socrata."""
    params = {}
    where_clauses = []

    # Filtro por vigencia
    if vigencia != 'latest':
        where_clauses.append(f"anio='{vigencia}' OR a_o='{vigencia}' OR año='{vigencia}'")

    # Filtro por tamaño de empresa
    if tamano_empresa == 'micro':
        where_clauses.append("(tamano='Micro' OR tamano_empresa='Microempresa' OR personal_ocupado<10)")

    # Filtro por sector CIIU
    if sector:
        where_clauses.append(f"(ciiu LIKE '{sector}%' OR actividad_economica LIKE '{sector}%')")

    if where_clauses:
        params['$where'] = ' AND '.join(f'({clause})' for clause in where_clauses)

    return params


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
    - base_url: URL del endpoint .json
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


def _normalize_cenu_columns(df: pd.DataFrame, tamano_empresa: str) -> pd.DataFrame:
    """Normalizar columnas del dataset CENU/EMICRON."""
    if df.empty:
        logger.warning("No se obtuvieron datos CENU/EMICRON. Retornando esquema vacío.")
        return _create_empty_cenu_schema()

    # Mapeo flexible de columnas
    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'divipola' in col_lower or 'c_digo_dane' in col_lower or 'cod_mun' in col_lower:
            column_mapping[col] = 'divipola_municipio'
        elif 'ciiu' in col_lower or 'actividad_econ' in col_lower:
            column_mapping[col] = 'codigo_ciiu'
        elif 'micronegocios' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'total_micronegocios'
        elif 'formal' in col_lower and 'micro' in col_lower:
            column_mapping[col] = 'micronegocios_formales'
        elif 'informal' in col_lower and 'micro' in col_lower:
            column_mapping[col] = 'micronegocios_informales'
        elif 'empleo' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'empleo_total'
        elif 'personal_ocupado' in col_lower or 'personas_ocupadas' in col_lower:
            column_mapping[col] = 'empleo_total'
        elif 'economia_popular' in col_lower:
            column_mapping[col] = 'economia_popular_unidades'
        elif 'municipio' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_municipio'
        elif 'departamento' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_departamento'

    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)

    # Convertir columnas numéricas
    numeric_cols = ['total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
                    'empleo_total', 'economia_popular_unidades']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calcular campos derivados
    if 'micronegocios_formales' in df.columns and 'total_micronegocios' in df.columns:
        df['tasa_formalizacion'] = (
            df['micronegocios_formales'] /
            df['total_micronegocios'].replace(0, float('nan'))
        ).fillna(0)

    if 'micronegocios_informales' not in df.columns:
        if 'total_micronegocios' in df.columns and 'micronegocios_formales' in df.columns:
            df['micronegocios_informales'] = df['total_micronegocios'] - df['micronegocios_formales']

    return df


def _create_empty_cenu_schema() -> pd.DataFrame:
    """Crear DataFrame vacío con esquema esperado."""
    columns = [
        'divipola_municipio', 'nombre_municipio', 'nombre_departamento',
        'codigo_ciiu',
        'total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
        'economia_popular_unidades', 'economia_popular_empleo',
        'empleo_total', 'empleo_formal', 'empleo_informal',
        'tasa_formalizacion',
    ]
    return pd.DataFrame(columns=columns)


def _add_ingestion_metadata(df: pd.DataFrame, vigencia: str) -> pd.DataFrame:
    """Agregar metadatos de ingesta."""
    df = df.copy()
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = 'dane_cenu'
    df['_source_version'] = vigencia

    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values)
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = extract_dane_cenu(vigencia='latest', tamano_empresa='micro')
    print(f"Resultado: {resultado}")
