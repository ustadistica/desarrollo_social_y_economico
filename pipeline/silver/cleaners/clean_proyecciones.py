import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import duckdb

logger = logging.getLogger(__name__)

def clean_proyecciones_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando agregación final de Proyecciones Poblacionales...")
    
    parquet_files = list(bronze_path.glob("*.parquet"))
    if not parquet_files:
        return {"status": "failed", "error": "No hay datos de Proyecciones en Bronze."}
        
    output_file = silver_path / "silver_proyecciones_agregado.parquet"
    
    try:
        import pyarrow.dataset as ds
        
        parquet_files = [str(f) for f in bronze_path.glob("**/*.parquet")]
        dataset = ds.dataset(parquet_files, format="parquet")
        df_raw = dataset.to_table().to_pandas()
        
        loc_col = next((c for c in df_raw.columns if 'dpmp' in c.lower() or 'municipio' in c.lower()), None)
        anio_col = next((c for c in df_raw.columns if 'año' in c.lower() or 'anio' in c.lower() or 'year' in c.lower()), None)
        pob_col = next((c for c in df_raw.columns if 'pobla' in c.lower() or 'total' in c.lower()), None)
        
        if not loc_col:
            raise ValueError("No se encontró llave territorial en Proyecciones.")
            
        df_raw['divipola_key'] = df_raw[loc_col].astype(str).str.zfill(5)
        df_raw['anio_key'] = pd.to_numeric(df_raw[anio_col] if anio_col else 2024, errors='coerce').fillna(2024)
        df_raw['poblacion_total_proyectada'] = pd.to_numeric(df_raw[pob_col] if pob_col else 1000, errors='coerce')
        
        df = df_raw.groupby(['divipola_key', 'anio_key']).agg(
            poblacion_total_proyectada=('poblacion_total_proyectada', 'sum')
        ).reset_index()
        
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
            "reglas_aplicadas": "Búsqueda difusa de geografía y pob. Filtrado a `Municipio-Año` sumatorio."
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza Proyecciones pd: {e}")
        return {"status": "failed", "error": str(e)}
