import sys
import os
from pathlib import Path
import logging

# Configurar logging basico
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Resolución dinámica de la ruta del empaquetado para evadir el error de "carpeta con espacios"
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PIPELINE_DIR = BASE_DIR / 'src'

if str(PIPELINE_DIR) not in sys.path:
    # insertarlo como prioridad de sys.path
    sys.path.insert(0, str(BASE_DIR))

try:
    from src.ingesta.bronze.main_ingestion import IngestionOrchestrator
    from src.config.settings import get_settings
    from src.ingesta.bronze.validators.bronze_validator import generate_validation_report
except ImportError as e:
    logger.error(f"Falla crítica modular: {e}")
    logger.error("Asegúrese de respetar el naming del directorio base.")
    sys.exit(1)

def main():
    logger.info("=" * 60)
    logger.info("INICIANDO REFACTORIZACION Y ORQUESTACION BRONZE")
    logger.info("=" * 60)
    
    settings = get_settings()
    
    # 1. Ejecutar la ingesta
    orchestrator = IngestionOrchestrator(bronze_path=settings.BRONZE_PATH)
    
    # Permite inyectar sources por command line (ej. python run_bronze.py secop_i emicron)
    args = sys.argv[1:]
    sources = args if args else None
    
    resultados = orchestrator.run_ingestion(sources=sources, force=True, validate=True)
    
    # 2. Resumen consolidado para el std-out
    logger.info("\n--- RESUMEN FINAL ---")
    logger.info(f"Total procesados: {resultados['summary']['total']}")
    logger.info(f"Éxitos:           {resultados['summary']['success']}")
    logger.info(f"Fallos:           {resultados['summary']['failed']}")
    logger.info(f"Omitidos:         {resultados['summary']['skipped']}")
    
    # 3. Lanzar validador reuniendo los reportes
    try:
        report_path = BASE_DIR / 'documentacion_tecnica' / 'BRONZE_VALIDATION_REPORT.md'
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# REPORTE DE VALIDACIÓN - CAPA BRONZE (AUTO-GENERADO)\n\n")
            f.write("A continuación se certifica la completitud y nulabilidad de los artefactos Bronze tras la inyección:\n\n")
            
            val_count = 0
            for name, source_res in resultados['sources'].items():
                val_data = source_res.get('validation')
                if val_data:
                    val_count += 1
                    reporte_str = generate_validation_report(val_data)
                    f.write(f"## {name.upper()}\n```text\n{reporte_str}\n```\n\n")
            
            if val_count == 0:
                f.write("*(No se encontraron datos validados al estar vacías o fallidas las fuentes nativas)*\n")
            
        logger.info(f"Reporte de validación persistido exitosamente en: {report_path.relative_to(BASE_DIR)}")
        
    except Exception as e:
        logger.warning(f"No se pudo generar el reporte de validación: {e}", exc_info=True)

if __name__ == "__main__":
    main()
