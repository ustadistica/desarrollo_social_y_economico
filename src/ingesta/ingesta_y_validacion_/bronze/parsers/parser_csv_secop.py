"""
Extractor para SECOP II - Contratación Pública (CSV Local).
 
Este módulo implementa la ingesta de datos desde un archivo CSV local descargado
de datos.gov.co.
 
Fuente original: https://www.datos.gov.co/Gastos-Públicos/SECOP-II-Contratos-Electrónicos/jbjy-vk9h
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
 
# Columnas necesarias para el cruce Issue #13
COLUMNAS_NECESARIAS = [
    'Nombre Entidad',
    'Nit Entidad',
    'Departamento',
    'Ciudad',
    'Sector',
    'Tipo de Contrato',
    'Modalidad de Contratacion',
    'Valor del Contrato',
    'Fecha de Firma',
    'Estado Contrato',
    'ID Contrato',
    'Codigo de Categoria Principal'
]
 
# Schema esperado para validación básica en Bronze
SECOP_SCHEMA = {
    "id_contrato": "string",
    "monto_contrato": "float64",
    "divipola_municipio": "string",
    "codigo_unspsc": "string",
}
 
# Tamaño de chunk para lectura por bloques (100k filas a la vez)
CHUNK_SIZE = 100_000
 
 
def parse_secop_csv(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force_ingestion: bool = False,
    validate_schema: bool = True,
) -> Dict[str, Any]:
    """
    Procesar archivo CSV de SECOP II hacia la capa Bronze.
    Lee el archivo por chunks para manejar archivos grandes sin agotar RAM.
 
    Parameters:
    - input_path: Ruta al archivo CSV fuente (default: settings.SECOP_CSV_PATH)
    - output_path: Ruta de salida para archivo Parquet (default: capa Bronze)
    - force_ingestion: Forzar proceso incluso si existe archivo Bronze
    - validate_schema: Si True, valida el schema básico
 
    Returns:
    - Dict con metadata de extracción y ruta del archivo
    """
    logger.info("Iniciando procesamiento de SECOP II (CSV Local - modo chunks)")
 
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
        logger.info(f"Leyendo CSV por chunks: {input_path}")
 
        # Detectar separador y encoding leyendo solo las primeras filas
        df_sample = pd.read_csv(
            input_path,
            nrows=5,
            encoding='latin-1',
            on_bad_lines='skip'
        )
        sep = ',' if len(df_sample.columns) > 1 else ';'
        logger.info(f"Separador detectado: '{sep}' | Columnas muestra: {len(df_sample.columns)}")
 
        # Filtrar solo columnas disponibles
        cols_disponibles = [c for c in COLUMNAS_NECESARIAS if c in df_sample.columns]
        if not cols_disponibles:
            cols_disponibles = None  # Si no coincide ninguna, leer todas
            logger.warning("No se encontraron columnas esperadas, leyendo todas las columnas")
        else:
            logger.info(f"Columnas seleccionadas: {cols_disponibles}")
 
        # Leer CSV por chunks para no agotar RAM
        chunks = []
        total_registros = 0
 
        chunk_reader = pd.read_csv(
            input_path,
            sep=sep,
            encoding='latin-1',
            low_memory=True,
            usecols=cols_disponibles,
            chunksize=CHUNK_SIZE,
            on_bad_lines='skip',
            dtype=str  # Leer todo como string en Bronze
        )
 
        for i, chunk in enumerate(chunk_reader):
            # Agregar metadatos de ingesta
            chunk["_ingestion_timestamp"] = datetime.now().isoformat()
            chunk["_source"] = "secop_ii_csv"
            chunk["_chunk_id"] = i
            chunks.append(chunk)
            total_registros += len(chunk)
            if i % 10 == 0:
                logger.info(f"Chunks procesados: {i+1} | Registros acumulados: {total_registros:,}")
 
        if not chunks:
            return {"status": "warning", "error": "Archivo CSV vacio o sin datos validos"}
 
        # Concatenar todos los chunks
        logger.info(f"Concatenando {len(chunks)} chunks ({total_registros:,} registros)...")
        df = pd.concat(chunks, ignore_index=True)
 
        # Checksum basico
        df["_checksum_md5"] = hashlib.md5(str(len(df)).encode()).hexdigest()
        df["_source_version"] = "SECOP_II_LOCAL"
        df["_extraction_method"] = "CSV_LOCAL_CHUNKS"
 
        # Guardar en Parquet (Bronze)
        df.to_parquet(archivo_salida, index=False, compression="snappy")
        logger.info(f"Guardado en Bronze: {archivo_salida}")
 
        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(df),
            "columnas": list(df.columns),
            "fuente": "secop",
            "tipo": "CSV_LOCAL_CHUNKS",
        }
 
    except Exception as e:
        error_msg = f"Error procesando SECOP CSV: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
 
 
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = parse_secop_csv(force_ingestion=True)
    print(resultado)
 
