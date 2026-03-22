"""
Orquestador Principal de Ingesta - Capa Bronze.

Este módulo coordina la ingesta de todas las fuentes de datos hacia la capa Bronze,
ejecutando los parsers específicos para cada fuente y validando los resultados.

Fuentes soportadas:
1. CNPV 2018 (XML Local - DANE)
2. SECOP II (API JSON - datos.gov.co)
3. EMICRON 2024 (CSV Local - DANE)
4. IPM/NBI (Genérico - Excel/CSV/JSON)

Uso:
    python main_ingestion.py --sources cnpv secop emicron
    python main_ingestion.py --all --validate
    python main_ingestion.py --source cnpv --force
"""

import logging
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Importar parsers
from bronze.parsers.parser_csv_cnpv import parse_cnpv_csv
from bronze.parsers.parser_csv_secop import parse_secop_csv
from bronze.parsers.parser_csv_emicron import parse_emicron_csv

# Importar validadores
from bronze.validators.bronze_validator import (
    validate_bronze_folder,
    generate_validation_report,
)


# Configuración de fuentes
SOURCES_CONFIG = {
    "cnpv": {
        "name": "CNPV 2018 (Microdatos)",
        "description": "Microdatos CSV del Censo Nacional de Población y Vivienda 2018",
        "type": "CSV_MICRODATA_LOCAL",
        "parser": parse_cnpv_csv,
        "enabled": True,
    },
    "secop": {
        "name": "SECOP II",
        "description": "Contrataci\u00f3n P\u00fablica (CSV Local)",
        "type": "CSV_LOCAL",
        "parser": parse_secop_csv,
        "enabled": True,
    },
    "emicron": {
        "name": "EMICRON 2024",
        "description": "M\u00f3dulo de caracter\u00edsticas del micronegocio (DANE)",
        "type": "CSV_LOCAL",
        "parser": parse_emicron_csv,
        "enabled": True,
    },
}


class IngestionOrchestrator:
    """
    Orquestador principal para ingesta de datos a capa Bronze.
    """

    def __init__(self, bronze_path: Optional[Path] = None):
        """
        Inicializar orquestador.

        Parameters:
        - bronze_path: Ruta base para almacenar datos Bronze
        """
        self.bronze_path = bronze_path or self._get_default_bronze_path()
        self.execution_results = {
            "start_time": None,
            "end_time": None,
            "status": "pending",
            "sources": {},
            "summary": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
            },
        }

    def _get_default_bronze_path(self) -> Path:
        """
        Obtener ruta por defecto para capa Bronze.

        Returns:
        - Path a la carpeta Bronze
        """
        # Ruta relativa al script actual
        base_path = Path(__file__).parent.parent.parent / "datos" / "bronze"
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path

    def run_ingestion(
        self,
        sources: Optional[List[str]] = None,
        force: bool = False,
        validate: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecutar ingesta para las fuentes especificadas.

        Parameters:
        - sources: Lista de nombres de fuentes (None = todas habilitadas)
        - force: Forzar re-ingesta incluso si existen datos
        - validate: Ejecutar validación después de ingesta

        Returns:
        - Dict con resultados de la ejecución
        """
        self.execution_results["start_time"] = datetime.now().isoformat()
        self.execution_results["status"] = "running"

        logger.info("=" * 60)
        logger.info("ORQUESTADOR DE INGESTA - CAPA BRONZE")
        logger.info("=" * 60)
        logger.info(f"Ruta Bronze: {self.bronze_path}")
        logger.info(f"Fuentes a procesar: {sources or 'todas'}")

        # Determinar fuentes a procesar
        if sources is None:
            sources = [
                name for name, config in SOURCES_CONFIG.items()
                if config.get("enabled", True)
            ]

        self.execution_results["summary"]["total"] = len(sources)

        # Procesar cada fuente
        for source_name in sources:
            logger.info("-" * 60)
            logger.info(f"Procesando fuente: {source_name.upper()}")
            logger.info("-" * 60)

            if source_name not in SOURCES_CONFIG:
                logger.warning(f"Fuente desconocida: {source_name}")
                self.execution_results["sources"][source_name] = {
                    "status": "error",
                    "error": f"Fuente desconocida: {source_name}",
                }
                self.execution_results["summary"]["failed"] += 1
                continue

            config = SOURCES_CONFIG[source_name]
            logger.info(f"Nombre: {config['name']}")
            logger.info(f"Tipo: {config['type']}")
            logger.info(f"Descripción: {config['description']}")

            # Ejecutar parser
            try:
                result = self._execute_parser(
                    source_name=source_name,
                    config=config,
                    force=force,
                )

                self.execution_results["sources"][source_name] = result

                if result.get("status") == "success":
                    self.execution_results["summary"]["success"] += 1
                    logger.info(f"✓ {source_name}: SUCCESS ({result.get('registros', 0)} registros)")
                elif result.get("status") == "skipped":
                    self.execution_results["summary"]["skipped"] += 1
                    logger.info(f"⊘ {source_name}: SKIPPED")
                else:
                    self.execution_results["summary"]["failed"] += 1
                    logger.error(f"✗ {source_name}: FAILED - {result.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error(f"Error ejecutando parser para {source_name}: {str(e)}")
                self.execution_results["sources"][source_name] = {
                    "status": "error",
                    "error": str(e),
                }
                self.execution_results["summary"]["failed"] += 1

        # Ejecutar validación si se solicita
        if validate:
            logger.info("=" * 60)
            logger.info("EJECUTANDO VALIDACIONES")
            logger.info("=" * 60)

            for source_name, result in self.execution_results["sources"].items():
                if result.get("status") == "success":
                    validation_result = self._validate_source(source_name)
                    result["validation"] = validation_result

        # Finalizar
        self.execution_results["end_time"] = datetime.now().isoformat()
        self.execution_results["status"] = "success" if self.execution_results["summary"]["failed"] == 0 else "partial"

        # Log resumen
        self._log_summary()

        return self.execution_results

    def _execute_parser(
        self,
        source_name: str,
        config: Dict[str, Any],
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Ejecutar parser para una fuente específica.

        Parameters:
        - source_name: Nombre de la fuente
        - config: Configuración de la fuente
        - force: Forzar re-ingesta

        Returns:
        - Dict con resultado del parser
        """
        parser_func = config.get("parser")

        if parser_func is None:
            return {
                "status": "error",
                "error": "Parser no disponible",
            }

        # Determinar ruta de salida
        output_path = self.bronze_path / source_name

        # Ejecutar parser con parámetros apropiados
        if source_name == "cnpv":
            return parser_func(
                output_path=output_path,
            )
        elif source_name == "secop":
            return parser_func(
                output_path=output_path,
                force_ingestion=force,
            )
        elif source_name == "emicron":
            return parser_func(
                output_path=output_path,
            )
        else:
            return {
                "status": "error",
                "error": f"Parser no implementado para {source_name}",
            }

    def _validate_source(self, source_name: str) -> Dict[str, Any]:
        """
        Validar datos ingeridos para una fuente.

        Parameters:
        - source_name: Nombre de la fuente

        Returns:
        - Dict con resultado de validación
        """
        logger.info(f"Validando {source_name}...")

        source_path = self.bronze_path / source_name

        if not source_path.exists():
            return {
                "status": "error",
                "message": f"Carpeta no encontrada: {source_path}",
            }

        result = validate_bronze_folder(
            folder_path=source_path,
            source_name=source_name,
        )

        # Generar reporte
        report_path = self.bronze_path / source_name / "validation_report.txt"
        generate_validation_report(result, report_path)

        return result

    def _log_summary(self):
        """Registrar resumen final de la ejecución."""
        logger.info("=" * 60)
        logger.info("RESUMEN DE EJECUCIÓN")
        logger.info("=" * 60)

        summary = self.execution_results["summary"]
        logger.info(f"Total fuentes: {summary['total']}")
        logger.info(f"Exitosas: {summary['success']}")
        logger.info(f"Fallidas: {summary['failed']}")
        logger.info(f"Saltadas: {summary['skipped']}")

        if self.execution_results["status"] == "success":
            logger.info("Estado: ✓ SUCCESS")
        elif self.execution_results["status"] == "partial":
            logger.info("Estado: ⚠ PARTIAL (algunas fuentes fallaron)")
        else:
            logger.info("Estado: ✗ FAILED")

        logger.info(f"Inicio: {self.execution_results['start_time']}")
        logger.info(f"Fin: {self.execution_results['end_time']}")


def list_sources():
    """Listar todas las fuentes disponibles."""
    print("\n" + "=" * 60)
    print("FUENTES DE DATOS DISPONIBLES")
    print("=" * 60 + "\n")

    for name, config in SOURCES_CONFIG.items():
        status = "✓" if config.get("enabled", True) else "✗"
        print(f"{status} {name.upper()}")
        print(f"    Nombre: {config['name']}")
        print(f"    Tipo: {config['type']}")
        print(f"    Descripción: {config['description']}")
        print()


def main():
    """Función principal con argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Orquestador de Ingesta - Capa Bronze",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python main_ingestion.py --all
  python main_ingestion.py --sources cnpv secop
  python main_ingestion.py --source cnpv --force --validate
  python main_ingestion.py --list
        """,
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Ejecutar ingesta para todas las fuentes habilitadas",
    )

    parser.add_argument(
        "--sources",
        nargs="+",
        choices=list(SOURCES_CONFIG.keys()),
        help="Fuentes específicas a procesar",
    )

    parser.add_argument(
        "--source",
        choices=list(SOURCES_CONFIG.keys()),
        help="Fuente única a procesar",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Forzar re-ingesta incluso si existen datos",
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        default=True,
        help="Ejecutar validación después de ingesta (default: True)",
    )

    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Saltar validación después de ingesta",
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar todas las fuentes disponibles",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Nivel de logging",
    )

    args = parser.parse_args()

    # Configurar nivel de logging
    logging.getLogger().setLevel(args.log_level)

    # Listar fuentes
    if args.list:
        list_sources()
        return 0

    # Determinar fuentes a procesar
    sources = None

    if args.source:
        sources = [args.source]
    elif args.sources:
        sources = args.sources
    elif args.all:
        sources = None  # Todas las habilitadas
    else:
        parser.print_help()
        return 1

    # Ejecutar ingesta
    orchestrator = IngestionOrchestrator()

    validate = not args.no_validate and args.validate

    results = orchestrator.run_ingestion(
        sources=sources,
        force=args.force,
        validate=validate,
    )

    # Retornar código de salida
    if results["summary"]["failed"] == 0:
        return 0
    elif results["summary"]["success"] > 0:
        return 2  # Partial success
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
