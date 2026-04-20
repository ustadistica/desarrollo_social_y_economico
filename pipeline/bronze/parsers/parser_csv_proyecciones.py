"""
Parser para Proyecciones Censales DANE (Microdatos CSV Locales).

Este módulo implementa la lectura de archivo CSV de proyecciones censales
directamente a un archivo Parquet en la capa Bronze usando PyArrow.

Fuente: C:\\Users\\user\\Documents\\001 Uni\\Octavo\\CONSULTORIA\\Datos\\PPED-AreaDep-2018-2050_VP.csv
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Importar configuración
import sys
import os

# Asegurar que se puede importar config (agregamos ROOT al path)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import Settings

logger = logging.getLogger(__name__)

def parse_proyecciones_csv(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    chunk_size: int = 250000,
) -> Dict[str, Any]:
    """
    Parsear archivo CSV de Proyecciones Censales 2018-2050 y convertir a Parquet en Bronze.

    Parameters:
    - input_path: Ruta al archivo CSV con las proyecciones (default: Settings.PROYECCIONES_CENSO_PATH)
    - output_path: Ruta de salida base para los archivos en capa Bronze (default: capa Bronze / proyecciones_censo)
    - chunk_size: Tamaño de lote para lectura en memoria eficiente
    
    Returns:
    - Dict con resultados de ejecución y estadísticas
    """
    settings = Settings()
    file_path = input_path or settings.PROYECCIONES_CENSO_PATH
    
    # Resolver ruta de salida final
    if output_path is None:
        output_path = settings.BRONZE_PATH / "proyecciones_censo"
        
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Iniciando ingesta de Proyecciones Censales desde: {file_path}")
    
    if not file_path.exists() or not file_path.is_file():
        logger.error(f"El archivo no existe o no es válido: {file_path}")
        return {
            "status": "error",
            "error": f"Archivo no encontrado: {file_path}"
        }

    total_records = 0
    parquet_file = output_path / "proyecciones_censo_raw.parquet"
    writer = None

    try:
        # Se asume delimitador coma por converción de Excel standard a CSV, y todo a string para mantener esquema rígido de capa Bronze
        for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size, sep=';', dtype=str, keep_default_na=False, low_memory=False)):
            if chunk.empty:
                continue

            # Añadir metadatos de ingesta a nivel Bronze
            chunk["_ingestion_timestamp"] = datetime.now().isoformat()
            chunk["_source"] = "dane_proyecciones"
            chunk["_source_version"] = "2018-2050"
            chunk["_extraction_method"] = "CSV_LOCAL_PARSER"

            # Generar checksum para integridad
            hash_str = pd.util.hash_pandas_object(chunk).astype(str)
            chunk["_checksum_md5"] = hash_str
            
            table = pa.Table.from_pandas(chunk)
            
            if writer is None:
                writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
                
            writer.write_table(table)
            total_records += len(chunk)
            
        if writer:
            writer.close()
            logger.info(f"Guardado exitosamente en: {parquet_file} ({total_records} registros)")
        else:
            logger.warning("No se generó archivo Parquet porque el CSV parece estar vacío")
            
    except Exception as e:
        logger.error(f"Error procesando el archivo {file_path.name}: {str(e)}")
        if writer:
            writer.close()
        return {
            "status": "error",
            "error": str(e)
        }
        
    return {
        "status": "success",
        "archivo": str(file_path),
        "registros": total_records,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "dane_proyecciones",
            "metodo": "CSV_LOCAL_PARSER"
        }
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    res = parse_proyecciones_csv()
    print(res)
