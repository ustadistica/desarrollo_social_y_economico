import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd
import duckdb

logger = logging.getLogger(__name__)

def clean_secop_i_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando limpieza y agregación de SECOP I...")
    
    parquet_files = list(bronze_path.glob("*.parquet"))
    if not parquet_files:
        return {"status": "failed", "error": "No hay datos de SECOP I en Bronze."}
        
    output_file = silver_path / "silver_secop_i_agregado.parquet"
    
    # Usar DuckDB para limpieza analítica y agregación inmediata a Municipio-Año
    query = f"""
    SELECT 
        LPAD(CAST(COALESCE(codigo_municipio_entidad, codigo_entidad) AS VARCHAR), 5, '0') AS divipola_key,
        CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT) AS anio_key,
        COUNT(DISTINCT uid) AS cantidad_procesos_adjudicados,
        SUM(CAST(COALESCE(cuantia_contrato, 0) AS DOUBLE)) AS inversion_total_monto,
        COUNT(DISTINCT nit_del_contratista) AS proveedores_unicos
    FROM read_parquet('{bronze_path}/*.parquet')
    WHERE 
        fecha_de_firma IS NOT NULL 
        AND (codigo_municipio_entidad IS NOT NULL OR codigo_entidad IS NOT NULL)
    GROUP BY 
        LPAD(CAST(COALESCE(codigo_municipio_entidad, codigo_entidad) AS VARCHAR), 5, '0'),
        CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT)
    HAVING CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT) BETWEEN 2018 AND 2025
    """
    
    try:
        df = duckdb.query(query).df()
        
        # Validar nulls críticos
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        df['_fuente_origen'] = 'SECOP_I'
        
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"SECOP I agregado exitosamente (Grano: Municipio-Año). Filas: {len(df)}")
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": "Cast matemático, Extracción Año, Agrupación sumatoria y cuenta distinta de contratistas. Zero-padding a 5 dígitos."
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza SECOP I: {e}")
        return {"status": "failed", "error": str(e)}
