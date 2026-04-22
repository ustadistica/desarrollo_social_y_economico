"""
Extractor de datos de SECOP II - Contratación Pública.

Fuente: datos.gov.co (Socrata)
URL: https://www.datos.gov.co/resource/287p-52ht.json
API: SODA 2.0

Nota: Este extractor usa paginación para manejar grandes volúmenes de datos.
      Requiere App Token para rate limits más altos (opcional).
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import hashlib
import time
import json

logger = logging.getLogger(__name__)

# Configuración de API SODA
SODA_BASE_URL = "https://www.datos.gov.co/resource/287p-52ht.json"
DEFAULT_BATCH_SIZE = 50000
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30


def extract_secop_ii(
    output_path: Optional[Path] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = DEFAULT_MAX_RETRIES,
    app_token: Optional[str] = None,
    force_download: bool = False,
) -> Dict[str, Any]:
    """
    Extraer datos de SECOP II usando API SODA 2.0.
    
    Parameters:
    - output_path: Ruta de salida para archivo Parquet (default: capa Bronce)
    - date_from: Fecha inicial (YYYY-MM-DD). Default: primer día del mes actual
    - date_to: Fecha final (YYYY-MM-DD). Default: hoy
    - batch_size: Tamaño de lote para paginación
    - max_retries: Número máximo de reintentos
    - app_token: App Token de Socrata (aumenta rate limit)
    - force_download: Forzar descarga incluso si existe archivo local
    
    Returns:
    - Dict con metadata de extracción y ruta del archivo
    
    Raises:
    - ConnectionError: Si falla la conexión con la API
    - TimeoutError: Si se excede el tiempo de espera
    """
    logger.info("Iniciando extracción de SECOP II")
    
    # Determinar fechas de corte
    if date_from is None:
        date_from = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    if date_to is None:
        date_to = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Rango de fechas: {date_from} a {date_to}")
    
    # Obtener App Token de variables de entorno si no se proporciona
    if app_token is None:
        import os
        app_token = os.getenv("SODA_APP_TOKEN")
    
    # Verificar si ya existe archivo descargado
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_bronze_path("secop_ii")
    
    output_path.mkdir(parents=True, exist_ok=True)
    archivo_salida = output_path / f"secop_ii_{date_from}_to_{date_to}_raw.parquet"
    
    if archivo_salida.exists() and not force_download:
        logger.info(f"Archivo ya existe: {archivo_salida}")
        return {
            "status": "skipped",
            "archivo": str(archivo_salida),
            "mensaje": "Archivo ya existe. Use force_download=True para re-descargar.",
        }
    
    # Extracción de datos
    try:
        # Obtener todos los registros con paginación
        df = _fetch_all_data(
            date_from=date_from,
            date_to=date_to,
            batch_size=batch_size,
            max_retries=max_retries,
            app_token=app_token,
        )
        
        if df.empty:
            logger.warning("No se obtuvieron datos de SECOP II")
            return {
                "status": "warning",
                "archivo": None,
                "mensaje": "Dataset vacío para el rango de fechas especificado",
            }
        
        # Agregar metadatos de ingesta
        df = _add_ingestion_metadata(df)
        
        # Guardar en Parquet
        df.to_parquet(
            archivo_salida,
            index=False,
            compression="snappy",
        )
        
        logger.info(f"Extracción completada: {len(df)} registros guardados en {archivo_salida}")
        
        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(df),
            "columnas": list(df.columns),
            "date_from": date_from,
            "date_to": date_to,
            "fecha_extraccion": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error en extracción de SECOP II: {str(e)}")
        return {
            "status": "error",
            "archivo": None,
            "error": str(e),
        }


def _fetch_all_data(
    date_from: str,
    date_to: str,
    batch_size: int,
    max_retries: int,
    app_token: Optional[str],
) -> pd.DataFrame:
    """
    Obtener todos los datos con paginación.
    
    Parameters:
    - date_from: Fecha inicial
    - date_to: Fecha final
    - batch_size: Tamaño de lote
    - max_retries: Máximo de reintentos
    - app_token: App Token
    
    Returns:
    - DataFrame combinado de todos los lotes
    """
    all_records = []
    offset = 0
    
    logger.info(f"Iniciando descarga con batch_size={batch_size}")
    
    while True:
        # Construir query SODA
        where_clause = f"fecha_publicacion >= '{date_from}' AND fecha_publicacion <= '{date_to}'"
        
        params = {
            "$where": where_clause,
            "$limit": batch_size,
            "$offset": offset,
            "$order": "fecha_publicacion ASC",
        }
        
        # Agregar App Token si está disponible
        headers = {}
        if app_token:
            headers["X-App-Token"] = app_token
        
        # Hacer request con reintentos
        batch_df = _fetch_batch(params, headers, max_retries)
        
        if batch_df.empty:
            logger.info(f"No más registros disponibles (offset={offset})")
            break
        
        all_records.append(batch_df)
        offset += batch_size
        
        logger.info(f"Descargados {offset} registros...")
        
        # Rate limiting: esperar entre lotes
        time.sleep(0.5)
    
    if not all_records:
        return pd.DataFrame()
    
    # Combinar todos los lotes
    df = pd.concat(all_records, ignore_index=True)
    
    logger.info(f"Total de registros descargados: {len(df)}")
    
    return df


def _fetch_batch(
    params: Dict,
    headers: Dict,
    max_retries: int,
) -> pd.DataFrame:
    """
    Obtener un lote de datos con reintentos.
    
    Parameters:
    - params: Parámetros de query SODA
    - headers: Headers HTTP (incluye App Token)
    - max_retries: Máximo de reintentos
    
    Returns:
    - DataFrame del lote
    """
    import requests
    
    for intento in range(max_retries):
        try:
            response = requests.get(
                SODA_BASE_URL,
                params=params,
                headers=headers,
                timeout=DEFAULT_TIMEOUT,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if not data:
                return pd.DataFrame()
            
            return pd.DataFrame(data)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Intento {intento + 1}/{max_retries} fallido: {str(e)}")
            if intento < max_retries - 1:
                time.sleep(2 ** intento)  # Backoff exponencial
            else:
                raise ConnectionError(f"Falló después de {max_retries} intentos: {str(e)}")
    
    return pd.DataFrame()


def _add_ingestion_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta al DataFrame.
    """
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_source"] = "secop_ii"
    df["_source_version"] = "SECOP_II_LATEST"
    df["_extraction_method"] = "SODA_API"
    
    checksum = hashlib.md5(df.to_json().encode()).hexdigest()
    df["_checksum_md5"] = checksum
    
    return df


def get_latest_publication_date(app_token: Optional[str] = None) -> Optional[str]:
    """
    Obtener la fecha de publicación más reciente en SECOP II.
    
    Parameters:
    - app_token: App Token de Socrata
    
    Returns:
    - Fecha en formato YYYY-MM-DD o None si falla
    """
    import requests
    
    query = {
        "$select": "MAX(fecha_publicacion) as latest_date",
        "$order": "fecha_publicacion DESC",
        "$limit": 1,
    }
    
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token
    
    try:
        response = requests.get(
            SODA_BASE_URL,
            params=query,
            headers=headers,
            timeout=DEFAULT_TIMEOUT,
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            latest_date = data[0].get("latest_date")
            if latest_date:
                # Parsear fecha SODA (formato ISO)
                return latest_date.split("T")[0]
        
        return None
        
    except Exception as e:
        logger.error(f"Error obteniendo fecha más reciente: {str(e)}")
        return None


def check_secop_vigencia() -> Dict[str, Any]:
    """
    Verificar vigencia disponible de SECOP II.
    
    Returns:
    - Dict con información de la última fecha de publicación
    """
    latest_date = get_latest_publication_date()
    
    return {
        "ultima_publicacion": latest_date,
        "corte_recomendado": datetime.now().strftime("%Y-%m-%d"),
        "frecuencia": "mensual",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo: extraer datos del mes actual
    resultado = extract_secop_ii(force_download=False)
    print(f"Resultado: {resultado}")
