import sys
import os
from pathlib import Path
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = BASE_DIR / 'pipeline'

if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

try:
    from config.settings import get_settings
    from gold.build_dimensions import build_dim_tiempo, build_dim_territorio
    from gold.build_facts import build_facts
    from gold.build_mart import build_datamart
except ImportError as e:
    logger.error(f"Falla crítica modular: {e}")
    sys.exit(1)

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO EJECUCIÓN MODELO ESTRELLA - CAPA GOLD")
    logger.info("=" * 60)
    
    settings = get_settings()
    silver_base = settings.SILVER_PATH
    gold_base = settings.GOLD_PATH
    gold_base.mkdir(parents=True, exist_ok=True)
    
    resultados_dims = {}
    resultados_facts = {}
    
    # 1. Dimensiones (Soporte Estructural)
    resultados_dims['dim_tiempo'] = build_dim_tiempo(gold_base)
    resultados_dims['dim_territorio'] = build_dim_territorio(silver_base, gold_base)
    
    # 2. Hechos
    resultados_facts = build_facts(silver_base, gold_base)
    
    # 3. Datamart (OBT Integrado para Analistas sin PySpark)
    resultado_mart = build_datamart(gold_base)
    
    # Generar Reporte Físico Exigido (GOLD_VALIDATION_REPORT.md)
    report_path = BASE_DIR / 'documentacion_tecnica' / 'GOLD_VALIDATION_REPORT.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# REPORTE DE VALIDACIÓN Y CARGA - CAPA GOLD\n\n")
        f.write("> **Unidad de Integridad:** Granularidad estricta (Municipio-Año).\n")
        f.write("> Todas las relaciones son One-to-Many entre las Dimensiones y las Fact Tables.\n\n")
        
        f.write("## 1. Dimensiones Estandardizadas (Conformed Dimensions)\n")
        for k, res in resultados_dims.items():
            f.write(f"- **{k.upper()}**: Estado `{res.get('status', 'ERROR')}` | Registros Inyectados: {res.get('registros', 0):,} | 🔑 Duplicados de PK: {res.get('duplicados', 'N/A')}\n")
            
        f.write("\n## 2. Tablas de Hecho Consolidadas (Fact Tables)\n")
        for k, res in resultados_facts.items():
            f.write(f"- **{k.upper()}**: Estado `{res.get('status', 'ERROR')}` | Registros Consolidados: {res.get('registros', 0):,} | 🔑 Duplicados de FK-Set: {res.get('duplicados', 'N/A')}\n")
            
        f.write("\n## 3. Certificación del Modelo y Datamart Analítico Unificado\n")
        mart = resultado_mart
        f.write(f"- **Estado de Ensamblaje OBT:** `{mart.get('status', 'ERROR')}`\n")
        f.write(f"- **Filas del Cubo Final Analítico:** {mart.get('registros', 0):,}\n")
        f.write(f"- **Integridad Referencial Unívoca:** Se valida la NO duplicación del cruce Mpio-Año: {mart.get('duplicados', 'N/A')} registros solapados.\n")
        if 'archivo_latest' in mart:
             f.write(f"- **Ruta Simbólica Entregada al Analista:** `{mart['archivo_latest']}`\n")
             
    logger.info("Modelo Estrella inyectado. La data se encuentra en 'datos/gold'.")

if __name__ == "__main__":
    main()
