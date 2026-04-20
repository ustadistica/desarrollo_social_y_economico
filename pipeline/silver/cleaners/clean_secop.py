"""
Limpieza de SECOP II (Capa Silver).

Convierte la data cruda del CSV de SECOP extraída de la API histórica
en Parquet en el esquema de Plata listo para Dimensiones.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def clean_secop_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info(f"Iniciando limpieza de SECOP II desde {bronze_path}")
    
    parquets = list(bronze_path.glob("*.parquet"))
    if not parquets:
        logger.error(f"Falta el dataset de SECOP en: {bronze_path}")
        return {"status": "failed", "error": "Parquet de SECOP no encontrado"}
    secop_parquet = parquets[0]
        
    output_file = silver_path / "secop_clean.parquet"
    
    try:
        # Leer de bronze
        df = pd.read_parquet(secop_parquet)
        
        # Filtrar valores no relevantes/vacios (si los hubo) en columnas obligatorias
        if 'id_contrato' in df.columns:
            df = df.dropna(subset=['id_contrato'])
            
        # Cast de fechas
        if 'fecha_publicacion' in df.columns:
            df['fecha_publicacion'] = pd.to_datetime(df['fecha_publicacion'], errors='coerce')
            
        # Cast de montos a numéricos (remover puntuación si hace falta, aunque bronze debería haberlos traido como floats si no era API)
        monto_cols = ['monto_contrato', 'monto_ejecutado']
        for col in monto_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # Estandarizar nombre divs (completar ceros a izquierda)
        if 'divipola_municipio' in df.columns:
            df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)
            
        # Metadatos Silver
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        
        logger.info(f"Guardando {len(df)} contratos limpios en {output_file}")
        df.to_parquet(
            output_file, 
            engine='pyarrow', 
            compression='snappy', 
            index=False
        )
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros_contratos": len(df),
            "timestamp": df['_cleaning_timestamp'].iloc[0]
        }
    except Exception as e:
        logger.error(f"Fallo durante limpieza de SECOP: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
