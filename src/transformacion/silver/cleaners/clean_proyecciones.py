import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd

logger = logging.getLogger(__name__)

def clean_proyecciones_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    """
    Limpieza y agregación de Proyecciones Poblacionales DANE para capa Silver.
    
    Las proyecciones DANE tienen granularidad DEPARTAMENTAL (no municipal).
    Columnas reales: DP (código depto), DPNOM (nombre), AÑO, ÁREA GEOGRÁFICA, TOTAL.
    
    Se filtra por 'Total' en ÁREA GEOGRÁFICA para obtener la población total
    del departamento (no solo cabecera o resto).
    
    El campo TOTAL viene como string con formato '4.972.962' (puntos como separador de miles).
    """
    logger.info("Iniciando limpieza de Proyecciones Poblacionales DANE...")
    
    parquet_files = list(bronze_path.glob("**/*.parquet"))
    if not parquet_files:
        return {"status": "failed", "error": "No hay datos de Proyecciones en Bronze."}
        
    output_file = silver_path / "silver_proyecciones_agregado.parquet"
    
    try:
        import pyarrow.dataset as ds
        
        parquet_str = [str(f) for f in parquet_files]
        dataset = ds.dataset(parquet_str, format="parquet")
        df_raw = dataset.to_table().to_pandas()
        
        logger.info(f"Proyecciones Bronze cargado: {len(df_raw)} registros")
        logger.info(f"Columnas disponibles: {list(df_raw.columns)}")
        
        # --- Identificar columnas reales ---
        # Las columnas reales del DANE son: DP, DPNOM, AÑO, ÁREA GEOGRÁFICA, TOTAL
        # Pero pueden tener encoding issues con tildes
        
        # Columna de departamento (DP = código DIVIPOLA 2 dígitos)
        dp_col = next((c for c in df_raw.columns if c.upper() in ('DP', 'DPMP')), None)
        if not dp_col:
            dp_col = next((c for c in df_raw.columns if 'dp' in c.lower() and len(c) <= 4), None)
        
        # Columna de año
        anio_col = next((c for c in df_raw.columns if 'AÑO' in c.upper() or 'A\x91O' in c or 'ANO' in c.upper() or 'ANIO' in c.upper() or 'YEAR' in c.upper()), None)
        if not anio_col:
            # Fallback: buscar columna que contenga años numéricos
            for c in df_raw.columns:
                if df_raw[c].astype(str).str.match(r'^\d{4}$').mean() > 0.5:
                    anio_col = c
                    break
        
        # Columna de área geográfica (para filtrar por Total)
        area_col = next((c for c in df_raw.columns if 'REA' in c.upper() or 'AREA' in c.upper()), None)
        
        # Columna de población total
        total_col = next((c for c in df_raw.columns if c.upper() == 'TOTAL'), None)
        if not total_col:
            total_col = next((c for c in df_raw.columns if 'total' in c.lower() or 'pobla' in c.lower()), None)
        
        if not dp_col:
            raise ValueError(f"No se encontró columna de departamento. Columnas: {list(df_raw.columns)}")
        if not total_col:
            raise ValueError(f"No se encontró columna de población. Columnas: {list(df_raw.columns)}")
            
        logger.info(f"Columnas identificadas: DP={dp_col}, AÑO={anio_col}, AREA={area_col}, TOTAL={total_col}")
        
        # --- Filtrar por área 'Total' si la columna existe ---
        if area_col:
            # Filtrar solo las filas con Total (no solo Cabecera o Resto)
            mask_total = df_raw[area_col].astype(str).str.strip().str.lower().isin(['total', 'total '])
            df_filtered = df_raw[mask_total].copy()
            if df_filtered.empty:
                logger.warning(f"No se encontraron filas con AREA='Total'. Usando todas las filas.")
                df_filtered = df_raw.copy()
            else:
                logger.info(f"Filtrado por AREA='Total': {len(df_filtered)} de {len(df_raw)} filas")
        else:
            df_filtered = df_raw.copy()
        
        # --- Construir columnas estandarizadas ---
        # Departamento: 2 dígitos, zero-padded → divipola_key = depto + '000'
        df_filtered['divipola_depto'] = df_filtered[dp_col].astype(str).str.strip().str.zfill(2)
        df_filtered['divipola_key'] = df_filtered['divipola_depto'] + '000'
        
        # Año
        if anio_col:
            df_filtered['anio_key'] = pd.to_numeric(df_filtered[anio_col], errors='coerce')
        else:
            df_filtered['anio_key'] = 2024
        
        # Población: limpiar formato '4.972.962' → 4972962
        df_filtered['poblacion_total_proyectada'] = (
            df_filtered[total_col]
            .astype(str)
            .str.replace('.', '', regex=False)  # Quitar separador de miles
            .str.replace(',', '', regex=False)  # Quitar separador alternativo
            .str.strip()
        )
        df_filtered['poblacion_total_proyectada'] = pd.to_numeric(
            df_filtered['poblacion_total_proyectada'], errors='coerce'
        )
        
        # Eliminar filas sin datos válidos
        df_filtered = df_filtered.dropna(subset=['divipola_key', 'anio_key', 'poblacion_total_proyectada'])
        df_filtered = df_filtered[df_filtered['anio_key'].between(2018, 2050)]
        
        # --- Agregar a departamento-año ---
        df = df_filtered.groupby(['divipola_key', 'divipola_depto', 'anio_key']).agg(
            poblacion_total_proyectada=('poblacion_total_proyectada', 'sum')
        ).reset_index()
        
        df['anio_key'] = df['anio_key'].astype(int)
        
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_cleaning_timestamp'] = datetime.datetime.now().isoformat()
        df['_granularidad'] = 'departamento'
        
        df.to_parquet(output_file, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"Proyecciones agregadas: {len(df)} filas, "
                     f"Departamentos: {df['divipola_depto'].nunique()}, "
                     f"Años: {df['anio_key'].min()}-{df['anio_key'].max()}")
        
        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "departamentos": int(df['divipola_depto'].nunique()),
            "rango_anios": f"{int(df['anio_key'].min())}-{int(df['anio_key'].max())}",
            "nulls": nulls,
            "duplicados": int(duplicates),
            "reglas_aplicadas": (
                "Filtrado por AREA='Total'. "
                "Limpieza de formato numérico (separador de miles). "
                "Agregación a departamento-año."
            )
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza Proyecciones: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
