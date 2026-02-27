"""Tests para el modulo de ingesta."""

from pathlib import Path


def test_catalogo_exists():
    """Verificar que el catalogo de datos existe."""
    assert Path("datos/catalogo.yaml").exists()
