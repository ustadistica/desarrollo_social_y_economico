import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd
import duckdb

logger = logging.getLogger(__name__)

def build_dim_tiempo(gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo dimensión: dim_tiempo")
    out_file = gold_path / "dim_tiempo.parquet"
    
    # Generar años 2018 a 2025 estáticamente
    anios = list(range(2000, 2030))
    df = pd.DataFrame({'anio_key': anios})
    
    # Atributos descriptivos documentados en el diseño
    df['es_año_electoral_presidencial'] = df['anio_key'].isin([2018, 2022, 2026])
    df['es_año_electoral_regional'] = df['anio_key'].isin([2019, 2023, 2027])
    df['es_pandemia'] = df['anio_key'].isin([2020, 2021])
    
    df['_creation_timestamp'] = datetime.datetime.now().isoformat()
    
    df.to_parquet(out_file, engine='pyarrow', index=False)
    
    return {
        "status": "success",
        "archivo": str(out_file),
        "registros": len(df),
        "nulls": df.isnull().sum().to_dict(),
        "duplicados": df.duplicated('anio_key').sum()
    }

def build_dim_territorio(silver_path: Path, gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo dimensión: dim_territorio a partir del universo Silver")
    out_file = gold_path / "dim_territorio.parquet"
    
    # Extraer divipolas únicas del universo de todas las tablas Silver
    query = f"""
    WITH divipolas AS (
        SELECT divipola_key FROM read_parquet('{silver_path}/*.parquet', union_by_name=True)
        WHERE divipola_key IS NOT NULL
        GROUP BY 1
    )
    SELECT 
        LPAD(CAST(divipola_key AS VARCHAR), 5, '0') AS divipola_key,
        'Municipio ' || LPAD(CAST(divipola_key AS VARCHAR), 5, '0') AS nombre_municipio_referencia,
        SUBSTRING(LPAD(CAST(divipola_key AS VARCHAR), 5, '0'), 1, 2) AS divipola_departamento
    FROM divipolas
    """
    
    try:
        df = duckdb.query(query).df()
    except Exception as e:
        logger.warning(f"Silver tables missing or error reading from them for dim_territorio: {e}. Creando maestra vacía segura.")
        df = pd.DataFrame(columns=['divipola_key', 'nombre_municipio_referencia', 'divipola_departamento'])
        
    df['_creation_timestamp'] = datetime.datetime.now().isoformat()
    df.to_parquet(out_file, engine='pyarrow', index=False)
    
    return {
        "status": "success",
        "archivo": str(out_file),
        "registros": len(df),
        "nulls": df.isnull().sum().to_dict(),
        "duplicados": df.duplicated('divipola_key').sum() if not df.empty else 0
    }
