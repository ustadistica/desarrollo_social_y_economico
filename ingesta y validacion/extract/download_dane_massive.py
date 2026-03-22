"""
Descarga masiva de datos del DANE desde datos.gov.co

Este script descarga todas las bases de datos requeridas que faltan:
- CNPV (con IPM y NBI integrados)
- IPM (Índice de Pobreza Multidimensional) - base independiente
- NBI (Necesidades Básicas Insatisfechas) - base independiente  
- CENU (Censo Económico Nacional Urbano)
- EMICRON (Encuesta de Micronegocios)

Usa la API SODA de datos.gov.co con autenticación completa.
"""

import logging
import os
import sys
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import requests
import json

# Agregar el path del pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================================================================
# CONFIGURACIÓN DE DATASETS - datos.gov.co
# ================================================================

DATASETS_CONFIG = {
    # =========================================================================
    # CNPV - Censo Nacional de Población y Vivienda
    # Contiene: IPM, NBI, Población, Pobreza Monetaria, Déficit Habitacional
    # =========================================================================
    'cnpv_completo': {
        'nombre': 'CNPV 2018 - Indicadores Municipales',
        'dataset_id': 'vgth-gqwi',  # IPM y NBI por municipio
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
        'descripcion': 'Índice de Pobreza Multidimensional y NBI por municipio',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 'ipm_salud',
            'nbi_total', 'pobreza_monetaria_total', 'deficit_habitacional',
            'poblacion_total'
        ],
        'output_folder': 'dane_cnpv',
        'output_file': 'cnpv_data.parquet',
    },

    # =========================================================================
    # IPM Independiente - Para mayor detalle
    # =========================================================================
    'ipm_detalle': {
        'nombre': 'IPM Municipal Detallado',
        'dataset_id': 'vgth-gqwi',
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
        'descripcion': 'Índice de Pobreza Multidimensional con todas las dimensiones',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 
            'ipm_salud', 'ipm_acceso_servicios'
        ],
        'output_folder': 'dane_ipm',
        'output_file': 'ipm_data.parquet',
    },

    # =========================================================================
    # NBI Independiente - Para mayor detalle
    # =========================================================================
    'nbi_detalle': {
        'nombre': 'NBI Municipal Detallado',
        'dataset_id': 'vgth-gqwi',
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
        'descripcion': 'Necesidades Básicas Insatisfechas por municipio',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'nbi_total', 'nbi_vivienda', 'nbi_servicios', 'nbi_educacion',
            'nbi_nutricion', 'nbi_trabajo'
        ],
        'output_folder': 'dane_nbi',
        'output_file': 'nbi_data.parquet',
    },

    # =========================================================================
    # CENU / EMICRON - Micronegocios
    # =========================================================================
    'emicron': {
        'nombre': 'EMICRON - Encuesta de Micronegocios',
        'dataset_id': 'r2bh-bfag',
        'base_url': 'https://www.datos.gov.co/resource/r2bh-bfag.json',
        'descripcion': 'Encuesta de Micronegocios por municipio y sector CIIU',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'codigo_ciiu', 'descripcion_ciiu',
            'total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
            'economia_popular_unidades', 'economia_popular_empleo',
            'personal_ocupado', 'vigencia'
        ],
        'output_folder': 'dane_emicron',
        'output_file': 'emicron_data.parquet',
    },

    # =========================================================================
    # CENU - Censo Económico (unidades económicas)
    # =========================================================================
    'cenu_unidades': {
        'nombre': 'CENU - Unidades Económicas',
        'dataset_id': 'jwfy-yjz8',
        'base_url': 'https://www.datos.gov.co/resource/jwfy-yjz8.json',
        'descripcion': 'Unidades económicas del Censo Económico Nacional',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'codigo_ciiu', 'descripcion_ciiu',
            'total_unidades', 'unidades_formales', 'unidades_informales'
        ],
        'output_folder': 'dane_cenu',
        'output_file': 'cenu_data.parquet',
    },

    # =========================================================================
    # Proyecciones de Población DANE
    # =========================================================================
    'poblacion_proyecciones': {
        'nombre': 'Proyecciones de Población DANE',
        'dataset_id': 'csb4-y4hq',
        'base_url': 'https://www.datos.gov.co/resource/csb4-y4hq.json',
        'descripcion': 'Proyecciones de población por municipio 2018-2035',
        'columnas_clave': [
            'divipola', 'nombre_municipio', 'nombre_departamento',
            'poblacion_total', 'poblacion_hombres', 'poblacion_mujeres',
            'vigencia'
        ],
        'output_folder': 'dane_poblacion',
        'output_file': 'poblacion_data.parquet',
    },
}


def download_all_datasets(
    force_download: bool = False,
    batch_size: int = 10000,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    Descargar todos los datasets del DANE.

    Parameters:
    - force_download: Forzar descarga incluso si existe
    - batch_size: Tamaño de lote para paginación
    - max_retries: Número máximo de reintentos

    Returns:
    - Dict con resultados de la descarga
    """
    logger.info("=" * 80)
    logger.info("DESCARGA MASIVA DE DATOS DEL DANE")
    logger.info("=" * 80)
    logger.info(f"API Token: {settings.SODA_APP_TOKEN[:10]}...")
    logger.info(f"Fecha: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    resultados = {}
    exitosos = 0
    fallidos = 0
    saltados = 0

    for dataset_key, config in DATASETS_CONFIG.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"DATASET: {config['nombre']} ({dataset_key})")
        logger.info(f"{'='*80}")

        # Verificar si ya existe
        output_path = (
            settings.BRONZE_PATH / config['output_folder'] / 
            f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}" /
            config['output_file']
        )

        if output_path.exists() and not force_download:
            logger.info(f"⚠️  YA EXISTE: {output_path}")
            logger.info(f"   Saltando. Use --force para re-descargar.")
            resultados[dataset_key] = {
                'status': 'skipped',
                'archivo': str(output_path),
            }
            saltados += 1
            continue

        # Descargar dataset
        try:
            resultado = download_socrata_dataset(
                base_url=config['base_url'],
                dataset_id=config['dataset_id'],
                output_path=output_path,
                batch_size=batch_size,
                max_retries=max_retries,
                app_token=settings.SODA_APP_TOKEN,
            )

            if resultado['status'] == 'success':
                logger.info(f"✅ EXITO: {config['nombre']}")
                logger.info(f"   Registros: {resultado.get('registros', 0):,}")
                logger.info(f"   Archivo: {resultado['archivo']}")
                exitosos += 1
            else:
                logger.warning(f"⚠️  WARNING: {config['nombre']} - {resultado.get('mensaje', '')}")
                fallidos += 1

            resultados[dataset_key] = resultado

        except Exception as e:
            logger.error(f"❌ ERROR: {config['nombre']} - {str(e)}")
            resultados[dataset_key] = {
                'status': 'error',
                'error': str(e),
            }
            fallidos += 1

        # Esperar entre descargas para evitar rate limiting
        time.sleep(1)

    # Resumen final
    logger.info(f"\n{'='*80}")
    logger.info("RESUMEN DE DESCARGA")
    logger.info(f"{'='*80}")
    logger.info(f"Total datasets: {len(DATASETS_CONFIG)}")
    logger.info(f"Exitosos: {exitosos}")
    logger.info(f"Fallidos: {fallidos}")
    logger.info(f"Saltados: {saltados}")
    logger.info(f"{'='*80}")

    return resultados


def download_socrata_dataset(
    base_url: str,
    dataset_id: str,
    output_path: Path,
    batch_size: int = 10000,
    max_retries: int = 3,
    app_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Descargar dataset de Socrata (datos.gov.co) con paginación.

    Parameters:
    - base_url: URL del endpoint .json
    - dataset_id: ID del dataset en datos.gov.co
    - output_path: Ruta de salida del archivo Parquet
    - batch_size: Tamaño de lote para paginación
    - max_retries: Número máximo de reintentos
    - app_token: Token de la API

    Returns:
    - Dict con metadata de descarga
    """
    logger.info(f"Iniciando descarga: {dataset_id}")
    logger.info(f"  URL: {base_url}")
    logger.info(f"  Output: {output_path}")

    start_time = datetime.now()

    # Headers con autenticación
    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token
        logger.info(f"  Usando App Token: {app_token[:10]}...")

    all_records = []
    offset = 0

    while True:
        query_params = {
            '$limit': batch_size,
            '$offset': offset,
            '$order': ':id',
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    base_url,
                    params=query_params,
                    headers=headers,
                    timeout=120,
                )

                # Manejar rate limiting (429)
                if response.status_code == 429:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"  Rate limit (429). Esperando {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                batch = response.json()

                if not batch:
                    logger.info(f"  Descarga completada: {len(all_records)} registros totales")
                    break_outer = True
                    break

                all_records.extend(batch)
                offset += len(batch)

                logger.info(f"  Página descargada: offset={offset:,}, acumulado={len(all_records):,}")

                if len(batch) < batch_size:
                    logger.info(f"  Última página recibida. Total: {len(all_records):,} registros")
                    break_outer = True
                    break

                break

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"  Error (intento {attempt+1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"  Error definitivo tras {max_retries} intentos: {e}")
                    if all_records:
                        logger.warning(f"  Procediendo con {len(all_records)} registros descargados")
                        break_outer = True
                        break
                    else:
                        return {
                            'status': 'error',
                            'mensaje': f'Error de conexión: {str(e)}',
                        }
        else:
            continue
        break

    if not all_records:
        logger.warning(f"  No se obtuvieron datos para {dataset_id}")
        return {
            'status': 'warning',
            'mensaje': 'Dataset vacío o no disponible',
        }

    # Convertir a DataFrame
    df = pd.DataFrame(all_records)
    logger.info(f"  DataFrame creado: {len(df):,} registros × {len(df.columns)} columnas")

    # Normalizar columnas
    df = normalize_dane_columns(df, dataset_id)

    # Agregar metadatos
    df = add_ingestion_metadata(df, dataset_id)

    # Guardar en Parquet
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, compression='snappy')
    logger.info(f"  Archivo guardado: {output_path}")

    elapsed = (datetime.now() - start_time).total_seconds()

    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(df),
        'columnas': list(df.columns),
        'tiempo_segundos': elapsed,
    }


def normalize_dane_columns(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """
    Normalizar nombres de columnas según dataset.

    Parameters:
    - df: DataFrame crudo
    - dataset_id: ID del dataset

    Returns:
    - DataFrame con columnas normalizadas
    """
    logger.info("  Normalizando columnas...")

    # Mapeo general de columnas
    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower().strip()

        # DIVIPOLA
        if any(x in col_lower for x in ['divipola', 'código_dane', 'codigo_dane', 'dpmp']):
            column_mapping[col] = 'divipola_municipio'

        # Nombres geográficos
        elif 'municipio' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_municipio'
        elif 'departamento' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_departamento'

        # IPM
        elif 'ipm' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'ipm_total'
        elif 'ipm' in col_lower and 'educ' in col_lower:
            column_mapping[col] = 'ipm_educacion'
        elif 'ipm' in col_lower and ('niñ' in col_lower or 'ninez' in col_lower or 'nino' in col_lower):
            column_mapping[col] = 'ipm_ninez'
        elif 'ipm' in col_lower and 'trab' in col_lower:
            column_mapping[col] = 'ipm_trabajo'
        elif 'ipm' in col_lower and 'salud' in col_lower:
            column_mapping[col] = 'ipm_salud'

        # NBI
        elif 'nbi' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'nbi_total'
        elif 'nbi' in col_lower and 'vivienda' in col_lower:
            column_mapping[col] = 'nbi_vivienda'
        elif 'nbi' in col_lower and 'servicios' in col_lower:
            column_mapping[col] = 'nbi_servicios'
        elif 'nbi' in col_lower and 'educ' in col_lower:
            column_mapping[col] = 'nbi_educacion'

        # Población
        elif 'poblacion' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'poblacion_total'
        elif 'poblacion' in col_lower and 'hombre' in col_lower:
            column_mapping[col] = 'poblacion_hombres'
        elif 'poblacion' in col_lower and 'mujer' in col_lower:
            column_mapping[col] = 'poblacion_mujeres'

        # Pobreza monetaria
        elif 'pobreza' in col_lower and 'monetaria' in col_lower:
            column_mapping[col] = 'pobreza_monetaria'
        elif 'pobreza' in col_lower and 'extrema' in col_lower:
            column_mapping[col] = 'pobreza_extrema'

        # Micronegocios
        elif 'micronegocios' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'total_micronegocios'
        elif 'micronegocios' in col_lower and 'formal' in col_lower:
            column_mapping[col] = 'micronegocios_formales'
        elif 'micronegocios' in col_lower and 'informal' in col_lower:
            column_mapping[col] = 'micronegocios_informales'
        elif 'economia_popular' in col_lower and 'unidad' in col_lower:
            column_mapping[col] = 'economia_popular_unidades'
        elif 'economia_popular' in col_lower and 'empleo' in col_lower:
            column_mapping[col] = 'economia_popular_empleo'

        # CIIU
        elif 'ciiu' in col_lower and 'código' in col_lower:
            column_mapping[col] = 'codigo_ciiu'
        elif 'ciiu' in col_lower and 'descrip' in col_lower:
            column_mapping[col] = 'descripcion_ciiu'

        # Vigencia/año
        elif col_lower in ['a_o', 'año', 'anio', 'ano', 'year', 'vigencia']:
            column_mapping[col] = 'vigencia'

    if column_mapping:
        df = df.rename(columns=column_mapping)
        logger.info(f"  {len(column_mapping)} columnas renombradas")

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)
        logger.info("  DIVIPOLA estandarizada a 5 dígitos")

    # Convertir columnas numéricas
    numeric_cols = [
        'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 'ipm_salud',
        'nbi_total', 'poblacion_total', 'pobreza_monetaria',
        'total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
        'economia_popular_unidades', 'economia_popular_empleo',
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    logger.info("  Columnas numéricas convertidas")

    return df


def add_ingestion_metadata(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta al DataFrame.

    Parameters:
    - df: DataFrame
    - dataset_id: ID del dataset

    Returns:
    - DataFrame con metadatos
    """
    df = df.copy()

    # Timestamp de ingesta
    df['_ingestion_timestamp'] = datetime.now().isoformat()

    # Fuente
    df['_source'] = f'datos_gov_co_{dataset_id}'

    # Checksum por fila
    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values[:-2])  # Excluir metadatos previos
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Descarga masiva de datos del DANE desde datos.gov.co'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar descarga incluso si existe archivo'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='Tamaño de lote para paginación (default: 10000)'
    )

    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Número máximo de reintentos (default: 3)'
    )

    args = parser.parse_args()

    logger.info("Iniciando descarga masiva de datos del DANE...")
    logger.info(f"Argumentos: force={args.force}, batch_size={args.batch_size}, max_retries={args.max_retries}")

    resultados = download_all_datasets(
        force_download=args.force,
        batch_size=args.batch_size,
        max_retries=args.max_retries,
    )

    # Contar éxitos
    exitosos = sum(1 for r in resultados.values() if r.get('status') == 'success')

    if exitosos > 0:
        logger.info(f"\n✅ Descarga completada con éxito: {exitosos} datasets descargados")
        return 0
    else:
        logger.error("\n❌ Error en la descarga masiva")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
