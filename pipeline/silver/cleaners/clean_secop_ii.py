import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import duckdb

logger = logging.getLogger(__name__)

def clean_secop_ii_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando limpieza y agregación de SECOP II...")
    
    parquet_files = list(bronze_path.glob("*.parquet"))
    if not parquet_files:
        return {"status": "failed", "error": "No hay datos de SECOP II en Bronze."}
        
    output_file = silver_path / "silver_secop_ii_agregado.parquet"
    
    # DuckDB Query homologando con SECOP I
    query = f"""
    SELECT 
        LPAD(CAST(codigo_de_la_entidad AS VARCHAR), 5, '0') AS divipola_key,
        CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT) AS anio_key,
        COUNT(DISTINCT id_contrato) AS cantidad_procesos_adjudicados,
        SUM(CAST(valor_del_contrato AS DOUBLE)) AS inversion_total_monto,
        COUNT(DISTINCT nit_del_contratista) AS proveedores_unicos
    FROM read_parquet('{bronze_path}/*.parquet')
    WHERE 
        fecha_de_firma IS NOT NULL 
        AND codigo_de_la_entidad IS NOT NULL
    GROUP BY 
        LPAD(CAST(codigo_de_la_entidad AS VARCHAR), 5, '0'),
        CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT)
    HAVING CAST(SUBSTRING(fecha_de_firma, 1, 4) AS INT) BETWEEN 2018 AND 2025
    """
    
    try:
        df = duckdb.query(query).df()
        
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        df['_fuente_origen'] = 'SECOP_II'
        
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"SECOP II agregado exitosamente (Grano: Municipio-Año). Filas: {len(df)}")
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": "Igual a SECOP I, mapeando `codigo_de_la_entidad`, `valor_del_contrato`."
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza SECOP II: {e}")
        return {"status": "failed", "error": str(e)}
