"""
Orquestador de Transformación (Capa Silver).

Este script lee los datos crudos (Parquet) desde la capa Bronze,
ejecuta los pipelines de limpieza específicos para cada fuente,
cruza las tablas estandarizadas con las dimensiones globales
y genera las tablas de hechos en la capa Silver.

Uso:
    python -m silver.main_transformation --all
    python -m silver.main_transformation --source secop
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil

# Asegurar que importamos desde la raíz del proyecto ('ingesta y validacion')
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from config.settings import Settings

# Importar cleaners (Se crearán a continuación)
try:
    from silver.cleaners.clean_cnpv import clean_cnpv_data
    from silver.cleaners.clean_secop import clean_secop_data
    from silver.cleaners.clean_emicron import clean_emicron_data
except ImportError:
    # Si aún no existen, creamos stubs temporales
    def clean_cnpv_data(*args, **kwargs): return pd.DataFrame()
    def clean_secop_data(*args, **kwargs): return pd.DataFrame()
    def clean_emicron_data(*args, **kwargs): return pd.DataFrame()

# Configuración de limpieza por fuente
TRANSFORM_CONFIG = {
    "cnpv": {
        "name": "CNPV 2018 (Agregación)",
        "cleaner": clean_cnpv_data,
        "enabled": True,
    },
    "secop": {
        "name": "SECOP II (Limpieza CSV)",
        "cleaner": clean_secop_data,
        "enabled": True,
    },
    "emicron": {
        "name": "EMICRON 2024 (Limpieza CSV)",
        "cleaner": clean_emicron_data,
        "enabled": True,
    }
}

class TransformationOrchestrator:
    """Orquestador principal para la capa Silver."""
    
    def __init__(self):
        """Inicializa el orquestador."""
        self.settings = Settings()
        self.logger = logging.getLogger(__name__)
        
        # Configurar logging
        logging.basicConfig(
            level=getattr(logging, self.settings.LOG_LEVEL),
            format=self.settings.LOG_FORMAT
        )
        
        self.bronze_path = self.settings.BRONZE_PATH
        self.silver_path = self.settings.SILVER_PATH
        
        # Asegurar directorio silver
        self.silver_path.mkdir(parents=True, exist_ok=True)
        
        self.execution_results = {
            "start_time": datetime.now().isoformat(),
            "sources_processed": {},
            "status": "running"
        }
        
    def _execute_cleaner(self, source_name: str, config: dict, force: bool = False) -> dict:
        """
        Ejecuta la función de limpieza para una fuente específica.
        """
        self.logger.info("-" * 60)
        self.logger.info(f"Transformando fuente: {source_name.upper()} - {config['name']}")
        self.logger.info("-" * 60)
        
        source_bronze_path = self.bronze_path / source_name
        if not source_bronze_path.exists():
            self.logger.error(f"Directorio Bronze no encontrado para {source_name}: {source_bronze_path}")
            return {"status": "failed", "error": "Directorio Bronze no encontrado"}
            
        source_silver_path = self.silver_path / source_name
        
        # Mode force limpia el output
        if force and source_silver_path.exists():
            self.logger.info(f"Modo force: Limpiando directorio silver previo: {source_silver_path}")
            shutil.rmtree(source_silver_path)
            
        source_silver_path.mkdir(parents=True, exist_ok=True)
        
        try:
            cleaner_func = config["cleaner"]
            
            # Ejecutar el cleaner
            # Los cleaners de silver leen de bronze_path y escriben en silver_path
            result = cleaner_func(
                bronze_path=source_bronze_path,
                silver_path=source_silver_path,
                settings=self.settings
            )
            
            self.logger.info(f"Transformación {source_name.upper()} exitosa.")
            return result
        except Exception as e:
            self.logger.error(f"Error transformando {source_name}: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    def run_transformation(self, sources: list = None, force: bool = False) -> dict:
        """
        Ejecuta la transformación para las fuentes solicitadas.
        """
        if not sources or "all" in sources:
            sources_to_run = [k for k, v in TRANSFORM_CONFIG.items() if v["enabled"]]
        else:
            sources_to_run = [s for s in sources if s in TRANSFORM_CONFIG and TRANSFORM_CONFIG[s]["enabled"]]
            
        self.logger.info(f"Fuentes a transformar: {sources_to_run}")
        
        for source in sources_to_run:
            config = TRANSFORM_CONFIG[source]
            result = self._execute_cleaner(source, config, force)
            self.execution_results["sources_processed"][source] = result
            
        success_count = sum(1 for k, v in self.execution_results["sources_processed"].items() if v.get("status") == "success")
        
        # Resumen Final
        self.logger.info("=" * 60)
        self.logger.info(f"TRANSFORMACIÓN SILVER FINALIZADA: {success_count}/{len(sources_to_run)} exitosos")
        self.logger.info("=" * 60)
        
        self.execution_results["status"] = "completed"
        self.execution_results["end_time"] = datetime.now().isoformat()
        return self.execution_results

def main():
    parser = argparse.ArgumentParser(description="Orquestador de Datos - Capa Silver (Plata)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Transformar todas las fuentes habilitadas")
    group.add_argument("--source", type=str, choices=list(TRANSFORM_CONFIG.keys()), help="Transformar una fuente específica")
    group.add_argument("--list", action="store_true", help="Listar fuentes disponibles y su estado")
    
    parser.add_argument("--force", action="store_true", help="Forzar re-transformación eliminando datos previos")
    parser.add_argument("--validate", action="store_true", help="Ejecutar las validaciones funcionales post-transformación")
    
    args = parser.parse_args()
    
    # Listar fuentes
    if args.list:
        print("\n=== Fuentes Disponibles (Capa Silver) ===")
        for key, config in TRANSFORM_CONFIG.items():
            status = "[ON] Activa" if config["enabled"] else "[OFF] Deshabilitada"
            print(f"- {key}: {config['name']} {status}")
        print("==========================================\n")
        return
        
    orchestrator = TransformationOrchestrator()
    
    sources = ["all"] if args.all else [args.source]
    orchestrator.run_transformation(sources=sources, force=args.force)

if __name__ == "__main__":
    main()
