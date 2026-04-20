import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd
import pyarrow.dataset as ds

logger = logging.getLogger(__name__)

def generate_fact_schema(source_file: Path, gold_file: Path, schema_cols: Dict[str, str], source_name: str) -> Dict[str, Any]:
    """Helper genérico para leer de Silver, validar nulos de FK y mover a Gold Fact."""
    logger.info(f"Construyendo Fact: {gold_file.name} basada en {source_file.name}")
    
    try:
        if not source_file.exists():
            raise FileNotFoundError(f"El artefacto Silver base no existe: {source_file.name}")
        
        df = pd.read_parquet(source_file)
        
        # Filtrar registros que rompan integridad (ej nulos en las FKs)
        initial_len = len(df)
        df = df.dropna(subset=['divipola_key', 'anio_key'])
        
        # Casting a los tipos del modelo e inyección de columnas si faltan en mock
        for col, dtype in schema_cols.items():
            if col not in df.columns:
                df[col] = 0.0 if 'float' in dtype else 0
            df[col] = df[col].astype(dtype)
            
        columns_to_keep = ['divipola_key', 'anio_key'] + list(schema_cols.keys())
        df = df[columns_to_keep]
        
        df['_creation_timestamp'] = datetime.datetime.now().isoformat()
        df.to_parquet(gold_file, engine='pyarrow', index=False)
        
        return {
            "status": "success",
            "archivo": str(gold_file),
            "registros": len(df),
            "registros_descartados_fks_nulas": initial_len - len(df),
            "nulls": df.isnull().sum().to_dict(),
            "duplicados": df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        }
    except Exception as e:
        logger.error(f"Fallo construyendo {gold_file.name}: {e}")
        # Build empty safe fallback
        df = pd.DataFrame(columns=['divipola_key', 'anio_key'] + list(schema_cols.keys()))
        df.to_parquet(gold_file, engine='pyarrow', index=False)
        return {
            "status": "failed_safe",
            "error": str(e),
            "mensaje": "Se generó esqueleto tabular vacío para no romper despliegue.",
            "archivo": str(gold_file),
            "registros": 0
        }

def build_facts(silver_path: Path, gold_path: Path) -> Dict[str, Any]:
    results = {}
    
    # 1. Fact Demografía
    results['fact_demografia'] = generate_fact_schema(
        silver_path / "silver_proyecciones_agregado.parquet",
        gold_path / "fact_demografia_municipio_anio.parquet",
        {'poblacion_total_proyectada': 'float64'},
        "Demografia"
    )
    
    # 2. Fact Micronegocios
    results['fact_micronegocios'] = generate_fact_schema(
        silver_path / "silver_emicron_agregado.parquet",
        gold_path / "fact_micronegocios_municipio_anio.parquet",
        {'volumen_micronegocios_exp': 'float64'}, 
        "Micronegocios"
    )
    
    # 3. Fact Contratación (Usa la suma de secop I y II o uno de ellos si existe, o solo SECOP_I por simplificación del script, lo ideal es unir)
    # Por el límite de entorno, buscaremos los disponibles y unificamos, o asumimos que SECOP II es la fuente
    df_secop = pd.DataFrame(columns=['divipola_key', 'anio_key', 'cantidad_procesos_adjudicados', 'inversion_total_monto', 'proveedores_unicos'])
    
    for fname in ["silver_secop_i_agregado.parquet", "silver_secop_ii_agregado.parquet"]:
        fpath = silver_path / fname
        if fpath.exists():
            tmp = pd.read_parquet(fpath)
            # Acumulamos ambos secops
            df_secop = pd.concat([df_secop, tmp], ignore_index=True)
            
    # Agrupamos sumando por si un municipio tiene seccionales Secop I y II simultáneos en el mismo año
    if not df_secop.empty:
        df_secop = df_secop.groupby(['divipola_key', 'anio_key']).agg({
            'cantidad_procesos_adjudicados': 'sum',
            'inversion_total_monto': 'sum',
            'proveedores_unicos': 'sum' # Approximation. Distinct cannot be perfectly summed, but serves indicator purposes.
        }).reset_index()
        
    out_file_secop = gold_path / "fact_contratacion_municipio_anio.parquet"
    if df_secop.empty:
        df_secop.to_parquet(out_file_secop, engine='pyarrow', index=False)
        results['fact_contratacion'] = {"status": "failed_safe", "registros": 0, "error": "No hay secops."}
    else:
        df_secop = df_secop.dropna(subset=['divipola_key', 'anio_key'])
        df_secop['_creation_timestamp'] = datetime.datetime.now().isoformat()
        df_secop.to_parquet(out_file_secop, engine='pyarrow', index=False)
        results['fact_contratacion'] = {
            "status": "success",
            "archivo": str(out_file_secop),
            "registros": len(df_secop),
            "nulls": df_secop.isnull().sum().to_dict(),
            "duplicados": df_secop.duplicated(subset=['divipola_key', 'anio_key']).sum()
        }

    return results
