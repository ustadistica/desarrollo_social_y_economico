import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import duckdb

logger = logging.getLogger(__name__)

def build_datamart(gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo Datamart Analítico Orientado a Indicadores (OBT)")
    
    # Directorio de versionado estipulado en diseño
    hoy_dir = gold_path / "marts" / f"version_{datetime.datetime.now().strftime('%Y%m%d')}"
    latest_dir = gold_path / "marts" / "latest"
    
    hoy_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)
    
    out_file_versionado = hoy_dir / "mart_desarrollo_social_economico_municipio_anio.parquet"
    out_file_latest = latest_dir / "mart_desarrollo_social_economico_municipio_anio.parquet"
    
    # Query de OBT integrando Estrellas. Usamos un LEFT JOIN sobre las llaves. 
    # El tronco puede ser el cruce de territorio X tiempo o derivarse usando FULL OUTER para no purgar años/territorios asimétricos
    query = f"""
    -- Tronco principal: Combinación de dimensión territorial y temporal
    WITH spine AS (
        SELECT t.divipola_key, t.nombre_municipio_referencia, t.divipola_departamento, p.anio_key, p.es_año_electoral_presidencial
        FROM read_parquet('{gold_path}/dim_territorio.parquet') t
        CROSS JOIN read_parquet('{gold_path}/dim_tiempo.parquet') p
    ),
    fact_cnt AS (
        SELECT * FROM read_parquet('{gold_path}/fact_contratacion_municipio_anio.parquet')
    ),
    fact_mic AS (
        SELECT * FROM read_parquet('{gold_path}/fact_micronegocios_municipio_anio.parquet')
    ),
    fact_dem AS (
        SELECT * FROM read_parquet('{gold_path}/fact_demografia_municipio_anio.parquet')
    )
    SELECT 
        s.divipola_key,
        s.anio_key,
        s.nombre_municipio_referencia,
        s.divipola_departamento,
        s.es_año_electoral_presidencial,
        
        -- Facts Originales
        COALESCE(c.inversion_total_monto, 0) AS inversion_total_monto,
        COALESCE(c.cantidad_procesos_adjudicados, 0) AS cantidad_procesos_adjudicados,
        COALESCE(m.volumen_micronegocios_exp, 0) AS volumen_micronegocios_exp,
        COALESCE(d.poblacion_total_proyectada, 1) AS poblacion_total_proyectada, -- fallback 1 previsor para divisiones
        
        -- Indicadores Derivados para el analista
        CASE 
            WHEN COALESCE(d.poblacion_total_proyectada, 1) > 0 THEN COALESCE(c.inversion_total_monto, 0) / d.poblacion_total_proyectada
            ELSE 0 
        END AS indicador_inversion_per_capita,
        
        CASE 
            WHEN COALESCE(d.poblacion_total_proyectada, 1) > 0 THEN COALESCE(m.volumen_micronegocios_exp, 0) / d.poblacion_total_proyectada
            ELSE 0 
        END AS indicador_densidad_micronegocios
        
    FROM spine s
    LEFT JOIN fact_cnt c ON s.divipola_key = c.divipola_key AND s.anio_key = c.anio_key
    LEFT JOIN fact_mic m ON s.divipola_key = m.divipola_key AND s.anio_key = m.anio_key
    LEFT JOIN fact_dem d ON s.divipola_key = d.divipola_key AND s.anio_key = d.anio_key
    WHERE 
        -- Restringimos el mart para no tener matriz explosiva de todos los tiempos vacíos
        -- Solo traemos municipio-años donde exista AL MENOS UN fact real asociado
        c.divipola_key IS NOT NULL 
        OR m.divipola_key IS NOT NULL 
        OR d.divipola_key IS NOT NULL
    """
    
    try:
        df = duckdb.query(query).df()
        
        nulls = df[['divipola_key', 'anio_key']].isnull().sum().to_dict()
        duplicates = df.duplicated(subset=['divipola_key', 'anio_key']).sum()
        
        df['_mart_generation_timestamp'] = datetime.datetime.now().isoformat()
        
        # Persistencia Dual (Versionado e instantánea final)
        df.to_parquet(out_file_versionado, engine='pyarrow', compression='snappy', index=False)
        df.to_parquet(out_file_latest, engine='pyarrow', compression='snappy', index=False)
        
        logger.info(f"Datamart (OBT) unificado con éxito. Filas: {len(df)}")
        
        return {
            "status": "success",
            "archivo_latest": str(out_file_latest),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates
        }
    except Exception as e:
        logger.error(f"Fallo en generación Datamart OBT: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
