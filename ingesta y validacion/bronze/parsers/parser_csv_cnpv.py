"""
Parser para CNPV 2018 - DANE (Microdatos CSV Locales).

Este módulo implementa la lectura masiva de archivos CSV del Censo
Nacional de Población y Vivienda 2018 organizados en carpetas por departamento.
Lee en lotes (chunks) y consolida por módulo (Viviendas, Hogares, Personas, etc.)
directamente a archivos Parquet en la capa Bronze usando PyArrow.

Fuente: C:\\Users\\user\\Documents\\001 Uni\\Octavo\\CONSULTORIA\\Datos\\CENSO 2018 dep\\
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import hashlib
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

# Módulos del CNPV a procesar
CNPV_MODULES = ["1VIV", "2HOG", "3FALL", "5PER", "MGN"]


def parse_cnpv_csv(
    input_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
    chunk_size: int = 250000,
) -> Dict[str, Any]:
    """
    Parsear directorio de archivos CSV del CNPV 2018 y convertir a Parquet por módulo.

    Parameters:
    - input_dir: Directorio raíz con carpetas por departamento (default: Settings.CNPV_CSV_DIR)
    - output_path: Ruta de salida para archivos Parquet (default: capa Bronze / cnpv)
    - chunk_size: Tamaño de chunk para procesamiento eficiente
    
    Returns:
    - Dict con resultados de ejecución y conteos
    """
    # Configurar rutas
    settings = Settings()
    input_path = input_dir or settings.CNPV_CSV_DIR
    
    # Resolver ruta de salida
    if output_path is None:
        output_path = settings.BRONZE_PATH / "cnpv"
        
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Iniciando ingesta de Microdatos CNPV desde: {input_path}")
    
    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"El directorio no existe: {input_path}")
        return {
            "status": "error",
            "error": f"Directorio no encontrado: {input_path}"
        }

    total_records = 0
    module_counts = {}
    
    # Procesar cada módulo por separado para tener un Parquet por módulo
    for module in CNPV_MODULES:
        logger.info(f"=== Procesando módulo CNPV: {module} ===")
        parquet_file = output_path / f"cnpv_{module.lower()}_raw.parquet"
        
        writer = None
        module_records = 0
        
        # Buscar carpetas de departamento
        dpto_dirs = [d for d in input_path.iterdir() if d.is_dir()]
        dpto_dirs.sort() # Procesar en orden
        
        for dpto_dir in dpto_dirs:
            # Buscar archivo CSV correspondiente a este módulo en la carpeta
            csv_files = list(dpto_dir.glob(f"*{module}*.CSV"))
            if not csv_files:
                logger.warning(f"No se encontró archivo para el módulo {module} en {dpto_dir.name}")
                continue
                
            csv_file = csv_files[0]
            logger.info(f"Leyendo: {csv_file.name}")
            
            try:
                # Leer en chunks, forzando todos los tipos a string para Bronze (evitar problemas de inferencia en parquet)
                for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size, dtype=str, keep_default_na=False)):
                    # Validar si el chunk está vacío
                    if chunk.empty:
                        continue
                        
                    # Añadir metadatos de ingesta
                    chunk["_ingestion_timestamp"] = datetime.now().isoformat()
                    chunk["_source"] = "dane_cnpv"
                    chunk["_source_version"] = "CNPV_2018"
                    chunk["_extraction_method"] = "CSV_LOCAL_PARSER"
                    
                    # Generar hash corto de forma vectorizada (muy rpido)
                    hash_str = pd.util.hash_pandas_object(chunk).astype(str)
                    chunk["_checksum_md5"] = hash_str
                    
                    table = pa.Table.from_pandas(chunk)
                    
                    # Inicializar escritor Parquet usando el schema inferido del primer chunk
                    if writer is None:
                        writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
                        
                    writer.write_table(table)
                    module_records += len(chunk)
                    
            except Exception as e:
                logger.error(f"Error procesando {csv_file.name}: {str(e)}")
                # Continuar con el siguiente archivo
                
        if writer:
            writer.close()
            logger.info(f"Guardado {module} en: {parquet_file} ({module_records} registros)")
        else:
            logger.warning(f"No se generó archivo Parquet para el módulo {module}")
            
        module_counts[module] = module_records
        total_records += module_records
        
    logger.info(f"Total registros procesados CNPV: {total_records}")
    
    return {
        "status": "success",
        "archivo": str(input_path),
        "registros": total_records,
        "detalles": module_counts,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "dane_cnpv",
            "metodo": "CSV_LOCAL_PARSER"
        }
    }

if __name__ == "__main__":
    # Prueba rápida
    logging.basicConfig(level=logging.INFO)
    res = parse_cnpv_csv()
    print(res)
