"""
Parsers para capa Bronze.

Módulos disponibles:
- parser_csv_cnpv: Parser para microdatos CSV del CNPV 2018 (NUEVO)
- parser_csv_secop: Parser para archivos CSV de SECOP II (NUEVO)
- parser_csv_emicron: Parser para archivos CSV de EMICRON 2024
"""

from .parser_csv_cnpv import parse_cnpv_csv
from .parser_csv_secop import parse_secop_csv
from .parser_csv_emicron import parse_emicron_csv, inspect_csv_structure

__all__ = [
    "parse_cnpv_csv",
    "parse_secop_csv",
    "parse_emicron_csv",
    "inspect_csv_structure",
]
