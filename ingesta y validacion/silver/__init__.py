"""
Capa de Transformación (Silver).

Recibe los datos crudos en Parquet (Capa Bronze),
aplica limpieza, estandarización técnica de columnas
(tipos de datos, tratamiento de nulos, estandarización de diccionarios),
genera y cruza variables espaciales (DIVIPOLA)
y crea las Tablas de Hechos y Dimensiones para el Modelo Estrella.

Módulos:
    - `cleaners`: Módulos de limpieza específicos por fuente.
    - `validators`: Módulos para validación de la capa Silver.
    - `main_transformation`: Script orquestador del pipeline de la capa Silver.
"""

from .main_transformation import TransformationOrchestrator

__all__ = [
    "TransformationOrchestrator",
]
