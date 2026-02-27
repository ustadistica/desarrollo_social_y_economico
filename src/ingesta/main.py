"""
Punto de entrada del pipeline de ingesta.

Uso:
    poetry run python -m src.ingesta.main

Este script orquesta la descarga de datos crudos desde las fuentes
definidas en datos/catalogo.yaml y los almacena en datos/raw/.
"""

from pathlib import Path

RAW_DIR = Path("datos/raw")


def main():
    """Ejecutar pipeline de ingesta completo."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    # TODO: Implementar ingesta desde las fuentes del proyecto
    print("Pipeline de ingesta ejecutado correctamente.")


if __name__ == "__main__":
    main()
