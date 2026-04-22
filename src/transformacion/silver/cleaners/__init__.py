"""
Módulo de limpiadores de la Capa Silver.

Cada limpiador toma los datos estandarizados en formatos Parquet/Capa Bronze,
los limpia y moldea para encajar en el esquema estrella.
"""

from .clean_cnpv import clean_cnpv_data
from .clean_secop import clean_secop_data
from .clean_emicron import clean_emicron_data

__all__ = [
    "clean_cnpv_data",
    "clean_secop_data",
    "clean_emicron_data",
]
