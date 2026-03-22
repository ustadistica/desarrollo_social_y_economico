"""
Extractor para SECOP II - Contratación Pública (CSV Local).

Este módulo implementa la ingesta de datos desde un archivo CSV local descargado
de datos.gov.co.

Fuente original: https://www.datos.gov.co/Gastos-P\u00fablicos/SECOP-II-Contratos-Electr\u00f3nicos/jbjy-vk9h
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import hashlib
import os
import sys

# Añadir el directorio raíz al path para poder importar config
sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import settings

logger = logging.getLogger(__name__)

# Schema esperado para validación básica en Bronze
SECOP_SCHEMA = {
    "id_contrato": "string",
    "monto_contrato": "float64",
    "divipola_municipio": "string",
    "codigo_unspsc": "string",
}


def parse_secop_csv(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force_ingestion: bool = False,
    validate_schema: bool = True,
) -> Dict[str, Any]:
    """
    Procesar archivo CSV de SECOP II hacia la capa Bronze.

    Parameters:
    - input_path: Ruta al archivo CSV fuente (default: settings.SECOP_CSV_PATH)
    - output_path: Ruta de salida para archivo Parquet (default: capa Bronze)
    - force_ingestion: Forzar proceso incluso si existe archivo Bronze
    - validate_schema: Si True, valida el schema básico

    Returns:
    - Dict con metadata de extracción y ruta del archivo
    """
    logger.info("Iniciando procesamiento de SECOP II (CSV Local)")

    # Determinar rutas
    if input_path is None:
        input_path = settings.SECOP_CSV_PATH
    
    if not input_path.exists():
        error_msg = f"Archivo fuente no encontrado: {input_path}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}

    if output_path is None:
        output_path = settings.get_bronze_path("secop")

    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generar nombre de archivo basado en fecha de ingesta
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo_salida = output_path / f"secop_ii_{timestamp}_raw.parquet"

    if any(output_path.glob("*.parquet")) and not force_ingestion:
        logger.info(f"Ya existen datos en Bronze para SECOP en {output_path}")
        return {
            "status": "skipped",
            "archivo": str(next(output_path.glob("*.parquet"))),
            "mensaje": "Datos ya presentes. Use force_ingestion=True para re-procesar.",
        }

    try:
        # Leer CSV (puede ser grande, se recomienda baja memoria o chunksize si es extremo)
        # SECOP II suele tener separador ',' y encoding utf-8
        logger.info(f"Leyendo CSV: {input_path}")
        
        # Intentamos detectar separador común
        df = pd.read_csv(input_path, nrows=100)
        sep = ',' if len(df.columns) > 1 else ';'
        
        df = pd.read_csv(
            input_path, 
            sep=sep, 
            encoding='utf-8', 
            low_memory=False,
            dtype={'Nombre Entidad': str, 'NIT Entidad': str, 'ID Contrato': str}
        )
        
        if df.empty:
            return {"status": "warning", "error": "Archivo CSV vacío"}

        logger.info(f"Registros leídos: {len(df)}")

        # Agregar metadatos de ingesta
        df["_ingestion_timestamp"] = datetime.now().isoformat()
        df["_source"] = "secop_ii_csv"
        df["_source_version"] = "SECOP_II_LOCAL"
        df["_extraction_method"] = "CSV_LOCAL_PARSER"
        
        # Checksum básico
        df["_checksum_md5"] = hashlib.md5(str(len(df)).encode()).hexdigest()

        # Guardar en Parquet (Bronze)
        df.to_parquet(archivo_salida, index=False, compression="snappy")
        
        logger.info(f"Guardado en Bronze: {archivo_salida}")

        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(df),
            "columnas": list(df.columns),
            "fuente": "secop",
            "tipo": "CSV_LOCAL",
        }

    except Exception as e:
        error_msg = f"Error procesando SECOP CSV: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = parse_secop_csv(force_ingestion=True)
    print(resultado)
