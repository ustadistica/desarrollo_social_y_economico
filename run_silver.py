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
    from silver.cleaners.clean_cnpv import clean_cnpv_data
    from silver.cleaners.clean_emicron import clean_emicron_data
    from silver.cleaners.clean_secop_i import clean_secop_i_data
    from silver.cleaners.clean_secop_ii import clean_secop_ii_data
    from silver.cleaners.clean_proyecciones import clean_proyecciones_data
except ImportError as e:
    logger.error(f"Falla crítica modular: {e}")
    sys.exit(1)

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO ORQUESTACIÓN SILVER (LIMPIEZA, HOMOLOGACIÓN Y AGREGACIÓN)")
    logger.info("=" * 60)
    
    settings = get_settings()
    bronze_base = settings.BRONZE_PATH
    silver_base = settings.SILVER_PATH
    silver_base.mkdir(parents=True, exist_ok=True)
    
    # Fuentes a procesar
    results = {}
    
    try:
        results['cnpv'] = clean_cnpv_data(bronze_base / 'cnpv', silver_base, settings)
    except Exception as e:
        results['cnpv'] = {'status': 'failed', 'error': str(e)}

    try:
        results['emicron'] = clean_emicron_data(bronze_base / 'emicron', silver_base, settings)
    except Exception as e:
        results['emicron'] = {'status': 'failed', 'error': str(e)}
        
    try:
        results['secop_i'] = clean_secop_i_data(bronze_base / 'secop_i', silver_base, settings)
    except Exception as e:
        results['secop_i'] = {'status': 'failed', 'error': str(e)}

    try:
        results['secop_ii'] = clean_secop_ii_data(bronze_base / 'secop_ii', silver_base, settings)
    except Exception as e:
        results['secop_ii'] = {'status': 'failed', 'error': str(e)}
        
    try:
        results['proyecciones'] = clean_proyecciones_data(bronze_base / 'proyecciones', silver_base, settings)
    except Exception as e:
        results['proyecciones'] = {'status': 'failed', 'error': str(e)}

    # Generar Reporte de Calidad de Datos Silver
    report_path = BASE_DIR / 'documentacion_tecnica' / 'SILVER_DATA_QUALITY_REPORT.md'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# REPORTE DE CALIDAD DE DATOS - CAPA SILVER\n\n")
        f.write("> Este reporte audita el proceso de transformación, homologación y agregación espacial (grano: Municipio-Año).\n\n")
        
        for name, outcome in results.items():
            f.write(f"## Fuente: {name.upper()}\n")
            f.write(f"**Estado:** {outcome.get('status', 'failed').upper()}\n\n")
            if outcome.get('status') == 'success':
                f.write(f"- **Archivo generado:** `{Path(outcome.get('archivo', '')).name}`\n")
                f.write(f"- **Registros consolidados (Grano Municipio-Año):** {outcome.get('registros', 0):,}\n")
                if 'nulls' in outcome:
                    f.write(f"- **Completitud (Nulls en variables clave):** {outcome['nulls']}\n")
                if 'duplicados' in outcome:
                    f.write(f"- **Unicidad (PK):** {outcome['duplicados']} duplicados.\n")
                if 'reglas_aplicadas' in outcome:
                    f.write(f"- **Reglas Aplicadas:** {outcome['reglas_aplicadas']}\n")
            else:
                err = outcome.get('error', 'Error desconocido')
                f.write(f"❌ Fallo en la limpieza: {err}\n")
            f.write("\n---\n")
            
    logger.info(f"Reporte de Calidad Silver generado exitosamente en: {report_path.relative_to(BASE_DIR)}")

if __name__ == "__main__":
    main()
