"""
Parser para CNPV 2018 - DANE (Microdatos CSV Locales).

Este módulo implementa la lectura masiva de archivos CSV del Censo
Nacional de Población y Vivienda 2018 organizados en carpetas por departamento.
Lee en lotes (chunks) y consolida por módulo (Viviendas, Hogares, Personas, etc.)
directamente a archivos Parquet en la capa Bronze usando PyArrow.

Fuente configurada vía variables de entorno o archivo de configuración.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import hashlib
import pyarrow as pa
import pyarrow.parquet as pq


try:
    from src.config.settings import Settings
except ImportError:
    from src.config.settings import Settings

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
    - input_dir: Directorio raíz con carpetas por departamento (default: Settings.CNPV_ROOT_DIR)
    - output_path: Ruta de salida para archivos Parquet (default: capa Bronze / cnpv)
    - chunk_size: Tamaño de chunk para procesamiento eficiente
    
    Returns:
    - Dict con resultados de ejecución y conteos
    """
    settings = Settings()
    input_path = input_dir or settings.CNPV_ROOT_DIR
    
    if output_path is None:
        output_path = settings.BRONZE_PATH / "cnpv"
        
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Iniciando ingesta de Microdatos CNPV desde: {input_path}")
    
    if not input_path.exists() or not input_path.is_dir():
        logger.error(f"El directorio raíz del CNPV no existe: {input_path}")
        return {
            "status": "error",
            "error": f"Directorio no encontrado: {input_path}. Configura CNPV_ROOT_DIR en tu .env o verifica la ruta."
        }

    total_records = 0
    module_counts = {}
    departamentos_detectados = set()
    archivos_detectados = 0
    
    # 1. Fase de Descubrimiento (Crawling multicarpeta)
    inventario = {module: [] for module in CNPV_MODULES}
    
    logger.info("Fase 1: Descubrimiento de archivos y carpetas...")
    for dpto_dir in input_path.iterdir():
        if not dpto_dir.is_dir():
            continue
            
        dpto_name = dpto_dir.name
        # Usar set para evitar duplicados en sistemas case-insensitive
        archivos_en_depto = list({f.resolve() for f in dpto_dir.glob("*.[cC][sS][vV]")})
        
        if not archivos_en_depto:
            continue
            
        departamentos_detectados.add(dpto_name)
        
        for file_path in archivos_en_depto:
            archivos_detectados += 1
            matched_module = None
            for module in CNPV_MODULES:
                if module in file_path.name.upper():
                    matched_module = module
                    break
            
            if matched_module:
                inventario[matched_module].append(file_path)
            else:
                logger.debug(f"Archivo ignorado: {file_path.name}")
                
    if not departamentos_detectados:
        logger.error(f"No se detectaron carpetas con archivos CSV en {input_path}")
        return {"status": "error", "error": "No se encontraron subcarpetas departamentales con archivos CSV válidos."}
        
    logger.info(f"Descubrimiento completado: {len(departamentos_detectados)} departamentos, {archivos_detectados} archivos totales.")
    
    # 2. Fase de Ingesta por Módulo
    for module in CNPV_MODULES:
        files_for_module = inventario[module]
        if not files_for_module:
            logger.warning(f"Faltan datos para el módulo {module}.")
            continue
            
        logger.info(f"=== Procesando módulo CNPV: {module} ({len(files_for_module)} archivos) ===")
        parquet_file = output_path / f"cnpv_{module.lower()}_raw.parquet"
        
        writer = None
        module_records = 0
        
        for csv_file in files_for_module:
            logger.info(f"Leyendo: {csv_file.parent.name}/{csv_file.name}")
            try:
                # Detectar el separador leyendo la primera linea
                with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                    first_line = f.readline()
                sep = ';' if ';' in first_line else ','
                
                # Leer en chunks
                for i, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size, dtype=str, keep_default_na=False, on_bad_lines='skip', sep=sep)):
                    if chunk.empty:
                        continue
                        
                    chunk["_ingestion_timestamp"] = datetime.now().isoformat()
                    chunk["_source"] = "dane_cnpv"
                    chunk["_source_version"] = "CNPV_2018"
                    chunk["_extraction_method"] = "CSV_LOCAL_PARSER_MULTI"
                    chunk["_source_file"] = csv_file.name
                    
                    hash_str = pd.util.hash_pandas_object(chunk).astype(str)
                    chunk["_checksum_md5"] = hash_str
                    
                    table = pa.Table.from_pandas(chunk)
                    
                    if writer is None:
                        writer = pq.ParquetWriter(parquet_file, table.schema, compression='snappy')
                        
                    writer.write_table(table)
                    module_records += len(chunk)
                    
            except Exception as e:
                logger.error(f"Error procesando {csv_file.name}: {str(e)}")
                
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
        "departamentos_detectados": len(departamentos_detectados),
        "archivos_detectados": archivos_detectados,
        "registros": total_records,
        "detalles": module_counts,
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "source": "dane_cnpv",
            "metodo": "CSV_LOCAL_PARSER_MULTI"
        }
    }

if __name__ == "__main__":
    # Prueba rápida
    logging.basicConfig(level=logging.INFO)
    res = parse_cnpv_csv()
    print(res)
