import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run_script(script_name):
    logger.info(f"--- Ejecutando {script_name} ---")
    result = subprocess.run([sys.executable, script_name], capture_output=False)
    if result.returncode != 0:
        logger.error(f"Fallo críítico en {script_name}. Abortando pipeline end-to-end.")
        sys.exit(result.returncode)
    logger.info(f"--- {script_name} completado exitosamente ---\n")

def main():
    logger.info("============================================================")
    logger.info("INICIANDO EJECUCIÓN END-TO-END: ORQUESTADOR MEDALLION")
    logger.info("============================================================")
    
    run_script("src/ingesta/run_bronze.py")
    run_script("src/transformacion/run_silver.py")
    run_script("src/transformacion/run_gold.py")
    
    logger.info("============================================================")
    logger.info("✅ PIPELINE COMPLETADO EXITOSAMENTE. DATA LISTA EN 'datos/gold/marts/latest/'")
    logger.info("============================================================")

if __name__ == "__main__":
    main()
