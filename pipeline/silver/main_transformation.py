"""
Orquestador de Transformación (Capa Silver).

Lee los datos crudos (Parquet) desde la capa Bronze, ejecuta los cleaners
específicos para cada fuente, y genera las tablas Silver agregadas a
granularidad Municipio-Año (o Departamento-Año para EMICRON y Proyecciones).

Flujo oficial:
    socioeco-silver          # via CLI
    python -m pipeline silver  # via módulo
"""

import argparse
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import shutil

from pipeline.config.settings import Settings
from pipeline.silver.cleaners.clean_cnpv import clean_cnpv_data
from pipeline.silver.cleaners.clean_secop_i import clean_secop_i_data
from pipeline.silver.cleaners.clean_secop_ii import clean_secop_ii_data
from pipeline.silver.cleaners.clean_emicron import clean_emicron_data
from pipeline.silver.cleaners.clean_proyecciones import clean_proyecciones_data

# Configuración de limpieza por fuente
TRANSFORM_CONFIG = {
    "cnpv": {
        "name": "CNPV 2018 (Censo - Agregación Poblacional)",
        "cleaner": clean_cnpv_data,
        "bronze_subdir": "cnpv",
        "enabled": True,
    },
    "secop_i": {
        "name": "SECOP I (Procesos de Compra Pública)",
        "cleaner": clean_secop_i_data,
        "bronze_subdir": "secop_i",
        "enabled": True,
    },
    "secop_ii": {
        "name": "SECOP II (Contratos Electrónicos)",
        "cleaner": clean_secop_ii_data,
        "bronze_subdir": "secop_ii",
        "enabled": True,
    },
    "emicron": {
        "name": "EMICRON 2019-2024 (Micronegocios - Encuesta Muestral)",
        "cleaner": clean_emicron_data,
        "bronze_subdir": "emicron",
        "enabled": True,
    },
    "proyecciones": {
        "name": "Proyecciones Poblacionales DANE",
        "cleaner": clean_proyecciones_data,
        "bronze_subdir": "proyecciones",
        "enabled": True,
    },
}

class TransformationOrchestrator:
    """Orquestador principal para la capa Silver."""
    
    def __init__(self):
        self.settings = Settings()
        self.logger = logging.getLogger(__name__)
        
        logging.basicConfig(
            level=getattr(logging, self.settings.LOG_LEVEL),
            format=self.settings.LOG_FORMAT
        )
        
        self.bronze_path = self.settings.BRONZE_PATH
        self.silver_path = self.settings.SILVER_PATH
        self.silver_path.mkdir(parents=True, exist_ok=True)
        
        self.execution_results = {
            "start_time": datetime.now().isoformat(),
            "sources_processed": {},
            "status": "running"
        }
        
    def _execute_cleaner(self, source_name: str, config: dict, force: bool = False) -> dict:
        """Ejecuta la función de limpieza para una fuente específica."""
        self.logger.info("-" * 60)
        self.logger.info(f"Transformando fuente: {source_name.upper()} - {config['name']}")
        self.logger.info("-" * 60)
        
        source_bronze_path = self.bronze_path / config["bronze_subdir"]
        if not source_bronze_path.exists():
            self.logger.warning(f"Directorio Bronze no encontrado para {source_name}: {source_bronze_path}")
            return {"status": "skipped", "error": f"Directorio Bronze no encontrado: {source_bronze_path}"}
            
        source_silver_path = self.silver_path / source_name
        
        if force and source_silver_path.exists():
            self.logger.info(f"Modo force: Limpiando directorio silver previo: {source_silver_path}")
            shutil.rmtree(source_silver_path)
            
        source_silver_path.mkdir(parents=True, exist_ok=True)
        
        try:
            cleaner_func = config["cleaner"]
            result = cleaner_func(
                bronze_path=source_bronze_path,
                silver_path=source_silver_path,
                settings=self.settings
            )
            
            status = result.get("status", "unknown")
            registros = result.get("registros", 0)
            self.logger.info(f"Transformacion {source_name.upper()}: {status} ({registros} registros)")
            return result
        except Exception as e:
            self.logger.error(f"Error transformando {source_name}: {str(e)}", exc_info=True)
            return {"status": "failed", "error": str(e)}

    def run_transformation(self, sources: list = None, force: bool = False) -> dict:
        """Ejecuta la transformación para las fuentes solicitadas."""
        if not sources or "all" in sources:
            sources_to_run = [k for k, v in TRANSFORM_CONFIG.items() if v["enabled"]]
        else:
            sources_to_run = [s for s in sources if s in TRANSFORM_CONFIG and TRANSFORM_CONFIG[s]["enabled"]]
            
        self.logger.info(f"Fuentes a transformar: {sources_to_run}")
        
        for source in sources_to_run:
            config = TRANSFORM_CONFIG[source]
            result = self._execute_cleaner(source, config, force)
            self.execution_results["sources_processed"][source] = result
            
        success_count = sum(1 for v in self.execution_results["sources_processed"].values() 
                           if v.get("status") == "success")
        total = len(sources_to_run)
        
        self.logger.info("=" * 60)
        self.logger.info(f"TRANSFORMACION SILVER FINALIZADA: {success_count}/{total} exitosos")
        self.logger.info("=" * 60)
        
        self.execution_results["status"] = "completed"
        self.execution_results["end_time"] = datetime.now().isoformat()
        return self.execution_results

def main():
    parser = argparse.ArgumentParser(description="Orquestador de Datos - Capa Silver (Plata)")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Transformar todas las fuentes habilitadas")
    group.add_argument("--source", type=str, choices=list(TRANSFORM_CONFIG.keys()), help="Transformar una fuente especifica")
    group.add_argument("--list", action="store_true", help="Listar fuentes disponibles")
    
    parser.add_argument("--force", action="store_true", help="Forzar re-transformacion")
    
    args = parser.parse_args()
    
    if args.list:
        print("\n=== Fuentes Disponibles (Capa Silver) ===")
        for key, config in TRANSFORM_CONFIG.items():
            status = "[ON]" if config["enabled"] else "[OFF]"
            print(f"  {status} {key}: {config['name']}")
        return
        
    orchestrator = TransformationOrchestrator()
    sources = ["all"] if args.all else [args.source]
    orchestrator.run_transformation(sources=sources, force=args.force)

if __name__ == "__main__":
    main()
