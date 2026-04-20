import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import duckdb

logger = logging.getLogger(__name__)

def clean_emicron_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando consolidación y agregación de EMICRON (Silver)...")
    
    output_file = silver_path / "silver_emicron_agregado.parquet"
    
    try:
        import pyarrow.dataset as ds
        
        # Leer todos los parquets de emicron tolerando esquemas dispares
        parquet_files = [str(f) for f in bronze_path.glob("**/*.parquet")]
        if not parquet_files:
            raise ValueError("No se encontraron archivos parquet en la ruta.")
            
        dataset = ds.dataset(parquet_files, format="parquet")
        df_raw = dataset.to_table().to_pandas()
        
        # Búsqueda difusa de columnas llave para consolidar
        loc_col = next((c for c in df_raw.columns if 'divipola' in c.lower() or 'muni' in c.lower() or 'p303' in c.lower()), None)
        fex_col = next((c for c in df_raw.columns if 'fex_c' in c.lower()), None)
        
        if not loc_col:
            raise ValueError("No se encontró columna territorial en EMICRON.")
            
        # Extraer el año y limpiar la PK
        if '_source_version' in df_raw.columns:
            df_raw['anio_key'] = df_raw['_source_version'].str.extract(r'(\d{4})').astype(float)
        else:
            df_raw['anio_key'] = 2024 # fallback estricto
            
        df_raw['divipola_key'] = df_raw[loc_col].astype(str).str.zfill(5)
        
        if fex_col:
            df_raw['fex_c_clean'] = pd.to_numeric(df_raw[fex_col], errors='coerce').fillna(1.0)
        else:
            df_raw['fex_c_clean'] = 1.0
            
        # Agregación analítica obligatoria a Municipio-Año
        df = df_raw.groupby(['divipola_key', 'anio_key']).agg(
            volumen_micronegocios_exp=('fex_c_clean', 'sum')
        ).reset_index()
        
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"EMICRON agregado exitosamente (Grano: Municipio-Año). Filas: {len(df)}")
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": "Búsqueda difusa de geografía y `fex_c`. Agregación sumatoria a Municipio-Año."
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza EMICRON pd: {e}")
        return {"status": "failed", "error": str(e)}
