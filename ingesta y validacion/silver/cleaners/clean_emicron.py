"""
Limpieza de EMICRON (Capa Silver).

Filtra, estandariza y normaliza la base del DANE Emicron en Parquet.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def clean_emicron_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info(f"Iniciando limpieza de EMICRON desde {bronze_path}")
    
    emicron_parquet = bronze_path / "emicron_raw.parquet"
    if not emicron_parquet.exists():
        logger.error(f"Falta el dataset de EMICRON: {emicron_parquet}")
        return {"status": "failed", "error": "Parquet de EMICRON no encontrado"}
        
    output_file = silver_path / "emicron_clean.parquet"
    
    try:
        # Leer bronze
        df = pd.read_parquet(emicron_parquet)
        
        # Estandarizar nombre municipio a divipola 
        # (ej. si era 'codigo_dane_municipio', renombrar a divipola_municipio)
        if 'codigo_dane_municipio' in df.columns:
            df = df.rename(columns={'codigo_dane_municipio': 'divipola_municipio'})
            
        if 'divipola_municipio' in df.columns:
            # Drop nulls en divipola
            df = df.dropna(subset=['divipola_municipio'])
            df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)
            
        # Normalizar otros campos importantes (Ej. booleanos sobre formalidad que puedan venir como 1/2)
        # O campos numéricos
        if 'tasa_formalizacion' in df.columns:
            df['tasa_formalizacion'] = pd.to_numeric(df['tasa_formalizacion'], errors='coerce')
            
        # Añadir timestamp
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        
        # Guardar en Silver
        logger.info(f"Guardando {len(df)} registros EMICRON limpios en {output_file}")
        df.to_parquet(
            output_file, 
            engine='pyarrow', 
            compression='snappy', 
            index=False
        )
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros_emicron": len(df),
            "timestamp": df['_cleaning_timestamp'].iloc[0]
        }
        
    except Exception as e:
        logger.error(f"Fallo durante limpieza de EMICRON: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
