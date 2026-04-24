"""
Módulo Bronze - Ingesta y Validación de Datos.

Este módulo implementa la capa Bronze de la arquitectura Medallion,
encargada de la ingesta raw de datos desde las fuentes originales
con validación básica de esquema.

Fuentes soportadas:
- CNPV 2018 (XML Local - DANE)
- SECOP II (API JSON - datos.gov.co)
- EMICRON 2024 (CSV Local - DANE)
- IPM/NBI (Genérico - Excel/CSV/JSON)
"""

from .main_ingestion import IngestionOrchestrator
from .parsers.parser_csv_cnpv import parse_cnpv_csv
from .parsers.parser_csv_secop import parse_secop_csv
from .validators.bronze_validator import (
    BronzeValidator,
    validate_bronze_file,
    validate_bronze_folder,
    generate_validation_report,
)

__all__ = [
    # Parsers
    "parse_cnpv_xml",
    "parse_secop_csv",
    "validate_bronze_folder",
    "generate_validation_report",
]
