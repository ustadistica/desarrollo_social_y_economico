"""
Validador para la capa Silver.

Este validador usa las rutas canonicas actuales de `data/silver`. En
particular, EMICRON se valida sobre `silver_emicron_agregado.parquet`, que ya
debe traer `volumen_micronegocios_exp` calculado con `factor_expansion`.
"""

import logging
from pathlib import Path
from typing import Any, Dict

import pandas as pd

logger = logging.getLogger(__name__)


class SilverValidator:
    """Implementa validaciones de datos para la capa Silver."""

    def __init__(self, data_path: Path):
        self.data_path = data_path

    def validate_cnpv(self) -> Dict[str, Any]:
        """Valida que la limpieza del CNPV sea correcta."""
        file_path = self.data_path / "silver_cnpv_agregado.parquet"
        if not file_path.exists():
            return {"status": "failed", "error": f"Parquet de CNPV Silver no encontrado: {file_path}"}

        df = pd.read_parquet(file_path)
        errors = []

        if df.get("divipola_key") is None:
            errors.append("Falta divipola_key")
        elif df["divipola_key"].isna().any() or (df["divipola_key"].astype(str).str.strip() == "").any():
            errors.append("Existen registros sin divipola_key")

        if "poblacion_total_base" in df.columns and (pd.to_numeric(df["poblacion_total_base"], errors="coerce") < 0).any():
            errors.append("Existen municipios con poblacion_total_base negativa")

        if df.duplicated(subset=["divipola_key", "anio_key"]).any():
            errors.append("Existen duplicados por (divipola_key, anio_key)")

        if errors:
            return {"status": "failed", "errors": errors}

        return {"status": "success", "filas_validadas": len(df)}

    def validate_secop(self) -> Dict[str, Any]:
        """Valida agregados y transaccionales SECOP disponibles."""
        expected = [
            "silver_secop_i_agregado.parquet",
            "silver_secop_ii_agregado.parquet",
            "silver_secop_i_transaccional.parquet",
            "silver_secop_ii_transaccional.parquet",
        ]
        missing = [name for name in expected if not (self.data_path / name).exists()]
        if missing:
            return {"status": "failed", "error": f"Parquets SECOP faltantes: {missing}"}

        errors = []
        filas = 0
        for name in expected[:2]:
            df = pd.read_parquet(self.data_path / name)
            filas += len(df)
            if df.duplicated(subset=["divipola_key", "anio_key"]).any():
                errors.append(f"{name} tiene duplicados por (divipola_key, anio_key)")
            if "inversion_total_monto" in df.columns:
                monto = pd.to_numeric(df["inversion_total_monto"], errors="coerce")
                if (monto < 0).any():
                    errors.append(f"{name} contiene inversion_total_monto negativa")

        if errors:
            return {"status": "failed", "errors": errors}

        return {"status": "success", "filas_validadas": filas}

    def validate_emicron(self) -> Dict[str, Any]:
        """Valida la expansion EMICRON corregida."""
        file_path = self.data_path / "silver_emicron_agregado.parquet"
        if not file_path.exists():
            return {"status": "failed", "error": f"Parquet de EMICRON Silver no encontrado: {file_path}"}

        df = pd.read_parquet(file_path)
        required = {
            "divipola_key",
            "divipola_depto",
            "anio_key",
            "volumen_micronegocios_exp",
            "n_registros_encuesta",
        }
        missing = sorted(required - set(df.columns))
        if missing:
            return {"status": "failed", "error": f"Faltan columnas EMICRON: {missing}"}

        errors = []
        if df.duplicated(subset=["divipola_key", "anio_key"]).any():
            errors.append("Duplicados por (divipola_key, anio_key)")

        annual = (
            df.groupby("anio_key", as_index=False)
            .agg(
                volumen=("volumen_micronegocios_exp", "sum"),
                registros=("n_registros_encuesta", "sum"),
                deptos=("divipola_depto", "nunique"),
            )
        )
        zero_years = annual[(annual["registros"] > 0) & (annual["volumen"] <= 0)]["anio_key"].tolist()
        if zero_years:
            errors.append(f"Anios EMICRON con registros pero expansion cero: {zero_years}")

        expected_years = set(range(2019, 2025))
        actual_years = set(pd.to_numeric(df["anio_key"], errors="coerce").dropna().astype(int))
        missing_years = sorted(expected_years - actual_years)
        if missing_years:
            errors.append(f"Faltan anios EMICRON esperados: {missing_years}")

        if "_factor_expansion_origen" in df.columns:
            origenes = df.groupby("anio_key")["_factor_expansion_origen"].agg(lambda s: ",".join(sorted(set(s))))
            for year in (2019, 2020):
                if year in origenes.index and "F_EXP" == origenes.loc[year]:
                    errors.append(f"{year} sigue usando solo F_EXP; se esperaba fallback de factores")

        if errors:
            return {"status": "failed", "errors": errors, "resumen_anual": annual.to_dict("records")}

        return {
            "status": "success",
            "filas_validadas": len(df),
            "resumen_anual": annual.to_dict("records"),
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """Ejecuta todas las validaciones disponibles."""
        results = {
            "cnpv": self.validate_cnpv(),
            "secop": self.validate_secop(),
            "emicron": self.validate_emicron(),
        }

        overall_status = "success"
        for result in results.values():
            if result.get("status") == "failed":
                overall_status = "failed"
                break

        return {
            "status": overall_status,
            "details": results,
        }
