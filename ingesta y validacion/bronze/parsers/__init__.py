"""
Parsers para capa Bronze.

Módulos disponibles:
- parser_csv_cnpv: Parser para microdatos CSV del CNPV 2018
- parser_csv_secop: Parser para archivos CSV de SECOP II (Contratos Electrónicos)
- parser_csv_secop_i: Parser para archivos CSV de SECOP I (Procesos de Compra Pública)
- parser_csv_emicron: Parser para archivos CSV de EMICRON 2024
- parser_csv_proyecciones: Parser para Proyecciones Censales DANE
"""

from .parser_csv_cnpv import parse_cnpv_csv
from .parser_csv_secop import parse_secop_csv
from .parser_csv_secop_i import parse_secop_i_csv
from .parser_csv_emicron import parse_emicron_csv, inspect_csv_structure
from .parser_csv_proyecciones import parse_proyecciones_csv

__all__ = [
    "parse_cnpv_csv",
    "parse_secop_csv",
    "parse_secop_i_csv",
    "parse_emicron_csv",
    "inspect_csv_structure",
    "parse_proyecciones_csv",
]
