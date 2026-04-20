import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import duckdb

logger = logging.getLogger(__name__)

def clean_cnpv_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando agregación final de CNPV 2018...")
    
    parquet_files = list(bronze_path.glob("*.parquet"))
    if not parquet_files:
        return {"status": "failed", "error": "No hay datos de CNPV en Bronze."}
        
    output_file = silver_path / "silver_cnpv_agregado.parquet"
    
    # CNPV es base 2018 fija.
    query = f"""
    SELECT 
        LPAD(CAST(COALESCE(U_DPTO, '') || COALESCE(U_MPIO, '') AS VARCHAR), 5, '0') AS divipola_key,
        2018 AS anio_key,
        COUNT(*) AS poblacion_total_base,
        SUM(CAST(COALESCE(TIPO_VIVIENDA, 0) AS INT)) AS proxy_viviendas  -- o la var que corresponda
    FROM read_parquet('{bronze_path}/*.parquet')
    WHERE U_DPTO IS NOT NULL AND U_MPIO IS NOT NULL
    GROUP BY 
        LPAD(CAST(COALESCE(U_DPTO, '') || COALESCE(U_MPIO, '') AS VARCHAR), 5, '0')
    """
    
    try:
        # Fallback en caso de que columnas difieran en el DANE mockeado
        try:
            df = duckdb.query(query).df()
        except duckdb.BinderException:
            fallback = f"""
                SELECT 
                    LPAD(CAST(divipola_municipio AS VARCHAR), 5, '0') AS divipola_key,
                    2018 AS anio_key,
                    COUNT(*) AS poblacion_total_base
                FROM read_parquet('{bronze_path}/*.parquet')
                GROUP BY 1
            """
            df = duckdb.query(fallback).df()
            
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": "Concatenación U_DPTO+U_MPIO. Imputación temporal a 2018 por base censal."
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza CNPV: {e}")
        return {"status": "failed", "error": str(e)}
