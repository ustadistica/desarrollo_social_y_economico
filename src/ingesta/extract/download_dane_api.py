"""
Descarga de datos del DANE desde datos.gov.co usando API SODA 2.0

Este script descarga las 5 bases de datos restantes usando la API SODA.
No requiere descarga manual si los endpoints están disponibles.

Endpoints verificados (datos.gov.co):
- IPM: 84mh-x7u2
- NBI: 678p-4r8w  
- EMICRON: r2bh-bfag (u 8x5u-6y4w)
- CENU: jwfy-yjz8 (u 7k8s-9r2p)
- CNPV: vgth-gqwi (combina IPM + NBI)
- Población: csb4-y4hq
"""

import logging
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

from src.config.settings import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ================================================================
# CONFIGURACIÓN DE DATASETS - datos.gov.co
# Endpoints SODA API verificados
# ================================================================

DATASETS_CONFIG = {
    # =========================================================================
    # CNPV - Censo Nacional de Población y Vivienda (combina IPM + NBI)
    # =========================================================================
    'cnpv': {
        'nombre': 'CNPV 2018 - Indicadores Municipales',
        'dataset_id': 'vgth-gqwi',
        'base_url': 'https://www.datos.gov.co/resource/vgth-gqwi.json',
        'descripcion': 'Índice de Pobreza Multidimensional y NBI por municipio',
        'output_folder': 'dane_cnpv',
        'output_file': 'cnpv_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'ipm', 'nbi', 'poblacion', 'pobreza_monetaria'
        ],
        'prioridad': 1,  # Alta prioridad
    },

    # =========================================================================
    # IPM - Índice de Pobreza Multidimensional (base independiente)
    # =========================================================================
    'ipm': {
        'nombre': 'IPM Municipal - Pobreza Multidimensional',
        'dataset_id': '84mh-x7u2',
        'base_url': 'https://www.datos.gov.co/resource/84mh-x7u2.json',
        'descripcion': 'Índice de Pobreza Multidimensional por municipio',
        'output_folder': 'dane_ipm',
        'output_file': 'ipm_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 'ipm_salud'
        ],
        'prioridad': 2,
    },

    # =========================================================================
    # NBI - Necesidades Básicas Insatisfechas
    # =========================================================================
    'nbi': {
        'nombre': 'NBI Municipal - Necesidades Básicas Insatisfechas',
        'dataset_id': '678p-4r8w',
        'base_url': 'https://www.datos.gov.co/resource/678p-4r8w.json',
        'descripcion': 'Necesidades Básicas Insatisfechas por municipio',
        'output_folder': 'dane_nbi',
        'output_file': 'nbi_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'nbi_total', 'nbi_vivienda', 'nbi_servicios'
        ],
        'prioridad': 2,
    },

    # =========================================================================
    # EMICRON - Encuesta de Micronegocios
    # =========================================================================
    'emicron': {
        'nombre': 'EMICRON - Encuesta de Micronegocios',
        'dataset_id': 'r2bh-bfag',
        'base_url': 'https://www.datos.gov.co/resource/r2bh-bfag.json',
        'descripcion': 'Encuesta de Micronegocios por municipio y sector',
        'output_folder': 'dane_emicron',
        'output_file': 'emicron_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'codigo_ciiu', 'total_micronegocios', 'economia_popular'
        ],
        'alternativas': [
            {'dataset_id': '8x5u-6y4w', 'base_url': 'https://www.datos.gov.co/resource/8x5u-6y4w.json'}
        ],
        'prioridad': 2,
    },

    # =========================================================================
    # CENU - Censo Económico Nacional Único
    # =========================================================================
    'cenu': {
        'nombre': 'CENU - Censo Económico Nacional',
        'dataset_id': 'jwfy-yjz8',
        'base_url': 'https://www.datos.gov.co/resource/jwfy-yjz8.json',
        'descripcion': 'Unidades económicas del Censo Económico',
        'output_folder': 'dane_cenu',
        'output_file': 'cenu_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'codigo_ciiu', 'unidades_economicas'
        ],
        'alternativas': [
            {'dataset_id': '7k8s-9r2p', 'base_url': 'https://www.datos.gov.co/resource/7k8s-9r2p.json'}
        ],
        'prioridad': 2,
    },

    # =========================================================================
    # Proyecciones de Población DANE
    # =========================================================================
    'poblacion': {
        'nombre': 'Proyecciones de Población DANE',
        'dataset_id': 'csb4-y4hq',
        'base_url': 'https://www.datos.gov.co/resource/csb4-y4hq.json',
        'descripcion': 'Proyecciones de población por municipio',
        'output_folder': 'dane_poblacion',
        'output_file': 'poblacion_data.parquet',
        'columnas_clave': [
            'divipola', 'municipio', 'departamento',
            'poblacion_total', 'vigencia'
        ],
        'prioridad': 3,
    },
}


def test_api_access(dataset_id: str, base_url: str, app_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Probar acceso a un dataset específico.

    Parameters:
    - dataset_id: ID del dataset
    - base_url: URL del endpoint
    - app_token: Token de la API

    Returns:
    - Dict con resultado del test
    """
    logger.info(f"  Probando acceso a {dataset_id}...")

    headers = {}
    if app_token:
        headers['X-App-Token'] = app_token

    # Probar con una consulta pequeña
    test_params = {
        '$limit': 1,
        '$format': 'json'
    }

    try:
        response = requests.get(
            base_url,
            params=test_params,
            headers=headers,
            timeout=30
        )

        result = {
            'dataset_id': dataset_id,
            'status_code': response.status_code,
            'url_probada': response.url,
        }

        if response.status_code == 200:
            data = response.json()
            result['accesible'] = True
            result['columnas_disponibles'] = list(data[0].keys()) if data else []
            logger.info(f"    ✅ ACCESIBLE - {len(result['columnas_disponibles'])} columnas disponibles")
        elif response.status_code == 403:
            result['accesible'] = False
            result['error'] = 'Forbidden - El dataset puede requerir autenticación especial o no es público'
            logger.warning(f"    ❌ FORBIDDEN (403) - {result['error']}")
        elif response.status_code == 404:
            result['accesible'] = False
            result['error'] = 'Not Found - El dataset ID no existe o cambió'
            logger.warning(f"    ❌ NOT FOUND (404) - {result['error']}")
        else:
            result['accesible'] = False
            result['error'] = f'Error HTTP {response.status_code}'
            logger.warning(f"    ❌ ERROR {response.status_code} - {result['error']}")

        return result

    except Exception as e:
        return {
            'dataset_id': dataset_id,
            'accesible': False,
            'error': str(e),
        }


def download_with_alternatives(
    config: Dict[str, Any],
    app_token: Optional[str],
    batch_size: int,
    max_retries: int,
) -> Dict[str, Any]:
    """
    Intentar descargar usando el endpoint principal y alternativos.

    Parameters:
    - config: Configuración del dataset
    - app_token: Token de la API
    - batch_size: Tamaño de lote
    - max_retries: Reintentos máximos

    Returns:
    - Dict con resultado de descarga
    """
    logger.info(f"\n  Dataset: {config['nombre']}")
    logger.info(f"  ID Principal: {config['dataset_id']}")

    # Lista de endpoints a intentar (principal + alternativos)
    endpoints_a_probar = [
        {
            'dataset_id': config['dataset_id'],
            'base_url': config['base_url'],
            'es_principal': True
        }
    ]

    # Agregar alternativos si existen
    if 'alternativas' in config:
        for alt in config['alternativas']:
            endpoints_a_probar.append({
                'dataset_id': alt['dataset_id'],
                'base_url': alt['base_url'],
                'es_principal': False
            })

    # Probar cada endpoint
    for endpoint in endpoints_a_probar:
        logger.info(f"  Probando endpoint: {endpoint['dataset_id']}...")

        # Test de acceso
        test_result = test_api_access(
            endpoint['dataset_id'],
            endpoint['base_url'],
            app_token
        )

        if test_result.get('accesible'):
            logger.info(f"    ✅ Endpoint accesible, procediendo con descarga...")

            # Intentar descarga completa
            resultado = download_socrata_dataset(
                base_url=endpoint['base_url'],
                dataset_id=endpoint['dataset_id'],
                output_folder=config['output_folder'],
                output_file=config['output_file'],
                batch_size=batch_size,
                max_retries=max_retries,
                app_token=app_token,
            )

            if resultado['status'] == 'success':
                return resultado
            else:
                logger.warning(f"    ⚠️  Descarga falló: {resultado.get('mensaje', '')}")
        else:
            logger.warning(f"    ❌ Endpoint no accesible: {test_result.get('error', '')}")

    # Si llegamos aquí, todos los endpoints fallaron
    return {
        'status': 'error',
        'mensaje': f"Ningún endpoint disponible para {config['nombre']}",
        'endpoints_probados': [e['dataset_id'] for e in endpoints_a_probar],
    }


def download_all_datasets(
    force_download: bool = False,
    batch_size: int = 10000,
    max_retries: int = 3,
    solo_prueba: bool = False,
) -> Dict[str, Any]:
    """
    Descargar todos los datasets del DANE.

    Parameters:
    - force_download: Forzar descarga incluso si existe
    - batch_size: Tamaño de lote para paginación
    - max_retries: Número máximo de reintentos
    - solo_prueba: Solo probar acceso, no descargar

    Returns:
    - Dict con resultados
    """
    logger.info("=" * 80)
    logger.info("DESCARGA DE DATOS DEL DANE - API SODA 2.0")
    logger.info("=" * 80)
    logger.info(f"API Token configurado: {'Sí' if settings.SODA_APP_TOKEN else 'No'}")
    if settings.SODA_APP_TOKEN:
        logger.info(f"Token (primeros 10 chars): {settings.SODA_APP_TOKEN[:10]}...")
    logger.info(f"Fecha: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # Primero, probar acceso a todos los endpoints
    logger.info("\n" + "=" * 80)
    logger.info("FASE 1: PROBANDO ACCESO A ENDPOINTS")
    logger.info("=" * 80)

    resultados_test = {}

    for dataset_key, config in DATASETS_CONFIG.items():
        logger.info(f"\n{config['nombre']} ({dataset_key}):")
        test_result = test_api_access(
            config['dataset_id'],
            config['base_url'],
            settings.SODA_APP_TOKEN
        )
        resultados_test[dataset_key] = test_result

        # Si tiene alternativos, probarlos también
        if 'alternativas' in config:
            for alt in config['alternativas']:
                logger.info(f"  Alternativa: {alt['dataset_id']}")
                alt_test = test_api_access(
                    alt['dataset_id'],
                    alt['base_url'],
                    settings.SODA_APP_TOKEN
                )
                if alt_test.get('accesible'):
                    resultados_test[dataset_key]['alternativa_accesible'] = alt_test
                    break

    # Resumen de tests
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN DE ACCESIBILIDAD")
    logger.info("=" * 80)

    accesibles = []
    no_accesibles = []

    for dataset_key, test_result in resultados_test.items():
        config = DATASETS_CONFIG[dataset_key]
        if test_result.get('accesible'):
            accesibles.append(dataset_key)
            logger.info(f"  ✅ {config['nombre']}: ACCESIBLE")
        elif test_result.get('alternativa_accesible'):
            accesibles.append(dataset_key)
            logger.info(f"  ✅ {config['nombre']}: ACCESIBLE (vía alternativa)")
        else:
            no_accesibles.append(dataset_key)
            logger.info(f"  ❌ {config['nombre']}: NO ACCESIBLE")
            logger.info(f"      Error: {test_result.get('error', 'Desconocido')}")

    if solo_prueba:
        logger.info("\n" + "=" * 80)
        logger.info("MODO PRUEBA - No se realizó descarga")
        logger.info("=" * 80)
        return {
            'modo_prueba': True,
            'accesibles': accesibles,
            'no_accesibles': no_accesibles,
            'detalles': resultados_test,
        }

    # Si no hay datasets accesibles, detener
    if not accesibles:
        logger.error("\n❌ Ningún dataset es accesible. Verificar:")
        logger.error("   1. Conexión a internet")
        logger.error("   2. API Token válido en settings.py")
        logger.error("   3. Endpoints correctos en datos.gov.co")
        return {
            'status': 'error',
            'mensaje': 'Ningún dataset accesible',
            'detalles': resultados_test,
        }

    # FASE 2: Descargar datasets accesibles
    logger.info("\n" + "=" * 80)
    logger.info("FASE 2: DESCARGANDO DATASETS ACCESIBLES")
    logger.info("=" * 80)

    resultados = {}
    exitosos = 0
    fallidos = 0

    for dataset_key in accesibles:
        config = DATASETS_CONFIG[dataset_key]

        # Verificar si ya existe
        output_path = (
            settings.BRONZE_PATH / config['output_folder'] /
            f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}" /
            config['output_file']
        )

        if output_path.exists() and not force_download:
            logger.info(f"\n⚠️  {config['nombre']} YA EXISTE")
            logger.info(f"   Saltando. Use --force para re-descargar.")
            resultados[dataset_key] = {
                'status': 'skipped',
                'archivo': str(output_path),
            }
            continue

        # Descargar
        resultado = download_with_alternatives(
            config=config,
            app_token=settings.SODA_APP_TOKEN,
            batch_size=batch_size,
            max_retries=max_retries,
        )

        if resultado['status'] == 'success':
            logger.info(f"\n  ✅ {config['nombre']} DESCARGADO EXITOSAMENTE")
            logger.info(f"     Registros: {resultado.get('registros', 0):,}")
            logger.info(f"     Archivo: {resultado['archivo']}")
            exitosos += 1
        else:
            logger.warning(f"\n  ❌ {config['nombre']} FALLÓ")
            logger.warning(f"     Error: {resultado.get('mensaje', '')}")
            fallidos += 1

        resultados[dataset_key] = resultado
        time.sleep(1)  # Rate limiting

    # Resumen final
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN FINAL")
    logger.info("=" * 80)
    logger.info(f"Datasets accesibles: {len(accesibles)}")
    logger.info(f"Descargados exitosamente: {exitosos}")
    logger.info(f"Fallidos: {fallidos}")
    logger.info(f"No accesibles (requieren descarga manual): {len(no_accesibles)}")

    if no_accesibles:
        logger.info("\n" + "=" * 80)
        logger.info("DATASETS NO ACCESIBLES - REQUIEREN DESCARGA MANUAL")
        logger.info("=" * 80)
        for key in no_accesibles:
            config = DATASETS_CONFIG[key]
            logger.info(f"\n  ❌ {config['nombre']}")
            logger.info(f"     Dataset ID: {config['dataset_id']}")
            logger.info(f"     Error: {resultados_test[key].get('error', 'Desconocido')}")
            logger.info(f"     URL para descarga manual:")
            logger.info(f"     https://www.datos.gov.co/d/{config['dataset_id']}")

    logger.info("\n" + "=" * 80)

    return {
        'status': 'partial_success' if exitosos > 0 else 'error',
        'exitosos': exitosos,
        'fallidos': fallidos,
        'no_accesibles': no_accesibles,
        'resultados': resultados,
        'detalles': resultados_test,
    }


def download_socrata_dataset(
    base_url: str,
    dataset_id: str,
    output_folder: str,
    output_file: str,
    batch_size: int = 10000,
    max_retries: int = 3,
    app_token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Descargar dataset de Socrata con paginación.
    """
    logger.info(f"  Iniciando descarga: {dataset_id}")

    start_time = datetime.now()

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

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    base_url,
                    params=query_params,
                    headers=headers,
                    timeout=120,
                )

                if response.status_code == 403:
                    logger.error(f"    Error 403: Acceso denegado. El dataset puede ser privado.")
                    return {
                        'status': 'error',
                        'mensaje': 'Acceso denegado (403 Forbidden)',
                    }

                if response.status_code == 404:
                    logger.error(f"    Error 404: Dataset no encontrado.")
                    return {
                        'status': 'error',
                        'mensaje': 'Dataset no encontrado (404 Not Found)',
                    }

                response.raise_for_status()
                batch = response.json()

                if not batch:
                    break

                all_records.extend(batch)
                offset += len(batch)

                logger.info(f"    Progreso: {len(all_records):,} registros...")

                if len(batch) < batch_size:
                    break

                break

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** (attempt + 1)
                    logger.warning(f"    Error (intento {attempt+1}/{max_retries}): {e}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"    Error definitivo: {e}")
                    if all_records:
                        logger.warning(f"    Procediendo con {len(all_records)} registros")
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
        return {
            'status': 'warning',
            'mensaje': 'Dataset vacío o sin datos',
        }

    # Convertir a DataFrame
    df = pd.DataFrame(all_records)
    logger.info(f"    DataFrame: {len(df):,} registros × {len(df.columns)} columnas")

    # Normalizar columnas
    df = normalize_dane_columns(df, dataset_id)

    # Agregar metadatos
    df = add_ingestion_metadata(df, dataset_id)

    # Guardar
    output_path = (
        settings.BRONZE_PATH / output_folder /
        f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}" /
        output_file
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, compression='snappy')
    logger.info(f"    Guardado: {output_path}")

    elapsed = (datetime.now() - start_time).total_seconds()

    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(df),
        'columnas': list(df.columns),
        'tiempo_segundos': elapsed,
    }


def normalize_dane_columns(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """Normalizar columnas del DANE."""
    logger.info("    Normalizando columnas...")

    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower().strip()

        # DIVIPOLA
        if any(x in col_lower for x in ['divipola', 'código_dane', 'codigo_dane', 'dpmp']):
            column_mapping[col] = 'divipola_municipio'
        # Municipio
        elif 'municipio' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_municipio'
        elif 'municipio' in col_lower:
            column_mapping[col] = 'nombre_municipio'
        # Departamento
        elif 'departamento' in col_lower and 'nombre' in col_lower:
            column_mapping[col] = 'nombre_departamento'
        elif 'departamento' in col_lower:
            column_mapping[col] = 'nombre_departamento'
        # IPM
        elif 'ipm' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'ipm_total'
        elif 'ipm' in col_lower:
            column_mapping[col] = 'ipm_total'
        # NBI
        elif 'nbi' in col_lower and 'total' in col_lower:
            column_mapping[col] = 'nbi_total'
        elif 'nbi' in col_lower:
            column_mapping[col] = 'nbi_total'
        # Población
        elif 'poblacion' in col_lower or 'poblac' in col_lower:
            column_mapping[col] = 'poblacion_total'
        # Vigencia
        elif col_lower in ['a_o', 'año', 'anio', 'ano', 'year', 'vigencia']:
            column_mapping[col] = 'vigencia'

    if column_mapping:
        df = df.rename(columns=column_mapping)

    # Asegurar DIVIPOLA
    if 'divipola_municipio' in df.columns:
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)

    return df


def add_ingestion_metadata(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """Agregar metadatos de ingesta."""
    df = df.copy()
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = f'datos_gov_co_{dataset_id}'

    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values[:-2])
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Descarga de datos del DANE vía API SODA'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Forzar descarga incluso si existe'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=10000,
        help='Tamaño de lote (default: 10000)'
    )

    parser.add_argument(
        '--solo-prueba',
        action='store_true',
        help='Solo probar acceso, no descargar'
    )

    args = parser.parse_args()

    logger.info("Iniciando descarga de datos del DANE...")

    resultados = download_all_datasets(
        force_download=args.force,
        batch_size=args.batch_size,
        solo_prueba=args.solo_prueba,
    )

    if resultados.get('exitosos', 0) > 0:
        logger.info(f"\n✅ Descarga completada: {resultados['exitosos']} datasets")
        return 0
    elif resultados.get('no_accesibles'):
        logger.warning("\n⚠️  Algunos datasets requieren descarga manual")
        logger.warning("   Ver GUÍA_DESCARGA_DATOS_DANE.txt para instrucciones")
        return 1
    else:
        logger.error("\n❌ Error en la descarga")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
