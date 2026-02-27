"""
Punto de entrada del pipeline de transformacion.

Uso:
    poetry run python -m src.transformacion.main

Este script toma los datos crudos de datos/raw/, aplica limpieza,
normalizacion y joins, y genera los datos procesados en datos/processed/.
"""

from pathlib import Path

RAW_DIR = Path("datos/raw")
PROCESSED_DIR = Path("datos/processed")


def main():
    """Ejecutar pipeline de transformacion completo."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: Implementar transformaciones del proyecto
    print("Pipeline de transformacion ejecutado correctamente.")


if __name__ == "__main__":
    main()
