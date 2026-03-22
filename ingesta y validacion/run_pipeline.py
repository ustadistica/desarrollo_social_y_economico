"""
Orquestador Principal End-to-End (Medallion Architecture).

Ejecuta de manera secuencial las tres capas:
1. Bronze (Extracción/Ingesta cruda)
2. Silver (Limpieza/Estandarización)
3. Gold (Modelo Estrella y Datamarts)
"""

import sys
import os
import argparse
import subprocess
import logging

def configure_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - pipeline_end_to_end - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    return logging.getLogger("pipeline")

def run_script(script_path: str, args: list, logger):
    cmd = [sys.executable, script_path] + args
    logger.info(f"Ejecutando: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        logger.error(f"Error en {script_path}:\n{result.stderr}")
        return False
        
    logger.info(f"{script_path} finalizó correctamente.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Ejecutar Pipeline End-to-End Medallion")
    parser.add_argument("--source", type=str, help="Ejecutar capa temporal específica (ej: cnpv, secop)")
    parser.add_argument("--force", action="store_true", help="Forzar re-ejecución sobrescribiendo datos")
    
    args = parser.parse_args()
    logger = configure_logger()
    
    logger.info("=" * 70)
    logger.info("INICIANDO PIPELINE END-TO-END (MEDALLION ARCHITECTURE)")
    logger.info("=" * 70)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. BRONZE LAYER
    logger.info(">>> FASE 1: CAPA BRONZE (Ingesta) <<<")
    bronze_script = os.path.join(base_dir, "bronze", "main_ingestion.py")
    bronze_args = []
    if args.source:
        bronze_args.extend(["--source", args.source])
    else:
        bronze_args.append("--all")
    if args.force:
        bronze_args.append("--force")
        
    if not run_script(bronze_script, bronze_args, logger):
        logger.error("Pipeline abortado en capa Bronze.")
        sys.exit(1)
        
    # 2. SILVER LAYER
    logger.info(">>> FASE 2: CAPA SILVER (Limpieza y Agregación) <<<")
    silver_script = os.path.join(base_dir, "silver", "main_transformation.py")
    silver_args = []
    if args.source:
        silver_args.extend(["--source", args.source])
    else:
        silver_args.append("--all")
    if args.force:
        silver_args.append("--force")
        
    if not run_script(silver_script, silver_args, logger):
        logger.error("Pipeline abortado en capa Silver.")
        sys.exit(1)
        
    # 3. GOLD LAYER
    logger.info(">>> FASE 3: CAPA GOLD (Esquema Estrella y Data Marts) <<<")
    gold_script = os.path.join(base_dir, "gold", "main_gold.py")
    gold_args = ["--all"]  # Gold procesa todo el estrella
    
    if not run_script(gold_script, gold_args, logger):
        logger.error("Pipeline abortado en capa Gold.")
        sys.exit(1)
        
    logger.info("=" * 70)
    logger.info("PIPELINE END-TO-END FINALIZADO EXITOSAMENTE")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
