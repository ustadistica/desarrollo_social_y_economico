"""
Limpieza y Agregación de CNPV 2018 (Capa Silver).

Implementa la agregación a nivel de municipio (población total)
a partir de los microdatos crudos de Personas extraídos en Parquet.
Utiliza el motor dual PySpark/PyArrow para realizar agregaciones
out-of-core de manera altamente eficiente sobre Parquet de varios GBs.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def clean_cnpv_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    """
    Agrega los microdatos de CNPV desde Bronze y los guarda en Silver.
    
    Busca el archivo `cnpv_5per_raw.parquet` dentro de bronze_path,
    agrupa por departamento y municipio, y devuelve la tabla:
    | divipola_municipio | poblacion_total | _cleaning_timestamp |
    """
    logger.info(f"Iniciando limpieza/agregación de CNPV desde {bronze_path}")
    
    # 1. Ubicar el archivo de Personas
    personas_parquet = bronze_path / "cnpv_5per_raw.parquet"
    if not personas_parquet.exists():
        logger.error(f"Falta el dataset principal de Personas: {personas_parquet}")
        return {"status": "failed", "error": "Parquet de Personas no encontrado"}
        
    output_file = silver_path / "cnpv_poblacion_agregada.parquet"
    
    try:
        # 2. Motor dual: usa PySpark si funciona, PyArrow si no
        from utils.spark_session import query_parquet, get_engine_name
        
        engine = get_engine_name()
        logger.info(f"Ejecutando Agregación Analítica con [{engine}] sobre {personas_parquet.name}...")
        
        query = """
            SELECT 
                concat(U_DPTO, U_MPIO) AS divipola_municipio,
                COUNT(*) AS poblacion_total
            FROM datos
            GROUP BY U_DPTO, U_MPIO
        """
        
        # Ejecutar query (resultado es pequeño: ~1122 filas)
        df_agg = query_parquet(personas_parquet, query)
        
        # 3. Limpieza de datos adicionales
        df_agg = df_agg.dropna(subset=['divipola_municipio'])
        # Rellenar con ceros municipio ignorado o sin especificar
        df_agg['divipola_municipio'] = df_agg['divipola_municipio'].str.zfill(5)
        
        # 4. Añadir metadatos Silver
        df_agg['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        
        # 5. Guardar como Parquet estandarizado en la capa plata
        logger.info(f"Guardando {len(df_agg)} municipios agregados en {output_file}")
        df_agg.to_parquet(
            output_file, 
            engine='pyarrow', 
            compression='snappy', 
            index=False
        )
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros_municipios": len(df_agg),
            "timestamp": df_agg['_cleaning_timestamp'].iloc[0]
        }
        
    except Exception as e:
        logger.error(f"Fallo durante procesamiento de CNPV: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
