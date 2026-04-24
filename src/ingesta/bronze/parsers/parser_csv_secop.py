"""
Extractor para SECOP II - Contratos Electrónicos (CSV Local).

Este módulo implementa la ingesta de datos desde un archivo CSV local descargado
de datos.gov.co usando lectura por chunks con PyArrow para manejar archivos
masivos (~9.6 GB) sin saturar la RAM.

Fuente original: https://www.datos.gov.co/Gastos-Públicos/SECOP-II-Contratos-Electrónicos/jbjy-vk9h
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import os


try:
    from src.config.settings import Settings
except ImportError:
    from src.config.settings import Settings

logger = logging.getLogger(__name__)


def parse_secop_csv(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    force_ingestion: bool = False,
    chunk_size: int = 250000,
) -> Dict[str, Any]:
    """
    Procesar archivo CSV de SECOP II (Contratos Electrónicos) hacia la capa Bronze.

    Usa lectura por chunks con PyArrow para manejar archivos masivos (~9.6 GB)
    sin saturar la RAM. Todos los campos se leen como string (capa Bronze = datos crudos).

    Parameters:
    - input_path: Ruta al archivo CSV fuente (default: settings.SECOP_CSV_PATH)
    - output_path: Ruta de salida para archivo Parquet (default: capa Bronze)
    - force_ingestion: Forzar proceso incluso si existe archivo Bronze
    - chunk_size: Número de filas por lote de lectura (default: 250,000)

    Returns:
    - Dict con metadata de extracción y ruta del archivo
    """
    logger.info("Iniciando procesamiento de SECOP II (CSV Local)")

    settings = Settings()

    # Determinar rutas
    if input_path is None:
        input_path = settings.SECOP_CSV_PATH

    if not input_path.exists():
        error_msg = f"Archivo fuente SECOP II no encontrado: {input_path}"
        logger.error(error_msg)
        logger.info(
            "Asegúrate de configurar SECOP_CSV_PATH en tu archivo .env "
            "o de colocar el CSV en la carpeta ../Datos/"
        )
        return {"status": "error", "error": error_msg}

    if output_path is None:
        output_path = settings.BRONZE_PATH / "secop_ii"

    output_path.mkdir(parents=True, exist_ok=True)

    # Verificar si ya existen datos
    if any(output_path.glob("*.parquet")) and not force_ingestion:
        logger.info(f"Ya existen datos en Bronze para SECOP II en {output_path}")
        return {
            "status": "skipped",
            "archivo": str(next(output_path.glob("*.parquet"))),
            "mensaje": "Datos ya presentes. Use force_ingestion=True para re-procesar.",
        }

    parquet_file = output_path / "secop_ii_raw.parquet"
    total_records = 0
    writer = None

    try:
        logger.info(f"Leyendo CSV: {input_path}")
        logger.info(f"Tamaño del archivo: {input_path.stat().st_size / (1024**3):.2f} GB")

        # Lectura por chunks - todos los campos como string (Bronze crudo)
        for i, chunk in enumerate(
            pd.read_csv(
                input_path,
                chunksize=chunk_size,
                sep=",",
                dtype=str,
                keep_default_na=False,
                low_memory=False,
                encoding="utf-8",
                on_bad_lines="warn",
            )
        ):
            if chunk.empty:
                continue

            # Agregar metadatos de ingesta a nivel Bronze
            chunk["_ingestion_timestamp"] = datetime.now().isoformat()
            chunk["_source"] = "secop_ii_csv"
            chunk["_source_version"] = "SECOP_II_LOCAL"
            chunk["_extraction_method"] = "CSV_LOCAL_PARSER"

            # Checksum para integridad
            hash_str = pd.util.hash_pandas_object(chunk).astype(str)
            chunk["_checksum_md5"] = hash_str

            table = pa.Table.from_pandas(chunk)

            if writer is None:
                writer = pq.ParquetWriter(
                    parquet_file, table.schema, compression="snappy"
                )

            writer.write_table(table)
            total_records += len(chunk)

            if (i + 1) % 10 == 0:
                logger.info(
                    f"  Chunk {i + 1}: {total_records:,} registros procesados..."
                )

        if writer:
            writer.close()
            logger.info(
                f"Guardado en Bronze: {parquet_file} ({total_records:,} registros)"
            )
        else:
            logger.warning("No se generó archivo Parquet porque el CSV está vacío")
            return {"status": "warning", "error": "Archivo CSV vacío"}

    except Exception as e:
        error_msg = f"Error procesando SECOP II CSV: {str(e)}"
        logger.error(error_msg)
        if writer:
            writer.close()
        return {"status": "error", "error": error_msg}

    return {
        "status": "success",
        "archivo": str(parquet_file),
        "registros": total_records,
        "fuente": "secop_ii",
        "tipo": "CSV_LOCAL",
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "secop_ii",
            "metodo": "CSV_LOCAL_PARSER",
        },
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    resultado = parse_secop_csv(force_ingestion=True)
    print(resultado)
