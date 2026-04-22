"""
Limpieza y agregación de CNPV 2018 (Capa Silver).

CNPV es un censo completo (no muestra). Agrega a nivel municipio con año
fijo 2018. Implementado con PyArrow + pandas (consistente con la migración
del pipeline desde DuckDB).
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import datetime
import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


# Columnas habituales en microdatos CNPV 2018 DANE
_DPTO_CANDIDATAS = ("U_DPTO", "DPTO", "DIVIPOLA_DEPARTAMENTO", "COD_DEPTO")
_MPIO_CANDIDATAS = ("U_MPIO", "MPIO", "DIVIPOLA_MUNICIPIO", "COD_MPIO")
_DIVIPOLA_CANDIDATAS = ("DIVIPOLA_MUNICIPIO", "DIVIPOLA", "COD_DIVIPOLA")


def _match_col(cols_upper: set, candidates: tuple) -> str | None:
    for c in candidates:
        if c in cols_upper:
            return c
    return None


def clean_cnpv_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando agregacion final de CNPV 2018...")
    output_file = silver_path / "silver_cnpv_agregado.parquet"

    parquet_files = sorted(bronze_path.rglob("*.parquet"))
    if not parquet_files:
        logger.warning(f"No hay datos de CNPV en Bronze ({bronze_path}).")
        return {
            "status": "failed",
            "error": "No hay datos de CNPV en Bronze.",
            "pendiente": "Ingestar CNPV desde fuente DANE (CSV por departamento).",
        }

    try:
        dfs: List[pd.DataFrame] = []
        for f in parquet_files:
            try:
                schema = pq.read_schema(str(f))
                cols_upper = {c.upper(): c for c in schema.names}
            except Exception as e:
                logger.warning(f"  Skip {f.name}: {e}")
                continue

            dpto_col = _match_col(set(cols_upper.keys()), _DPTO_CANDIDATAS)
            mpio_col = _match_col(set(cols_upper.keys()), _MPIO_CANDIDATAS)
            divi_col = _match_col(set(cols_upper.keys()), _DIVIPOLA_CANDIDATAS)

            if not (divi_col or (dpto_col and mpio_col)):
                logger.warning(f"  Skip {f.name}: no trae DIVIPOLA ni DPTO+MPIO")
                continue

            # Cargar solo columnas minimas para mantener footprint bajo
            cargar = [cols_upper[c] for c in (dpto_col, mpio_col, divi_col) if c]
            df_part = pd.read_parquet(f, columns=cargar)

            if divi_col:
                df_part["divipola_key"] = (
                    df_part[cols_upper[divi_col]].astype(str).str.strip().str.zfill(5)
                )
            else:
                # construir DIVIPOLA = depto(2) + mpio(3)
                df_part["__d"] = df_part[cols_upper[dpto_col]].astype(str).str.strip().str.zfill(2)
                df_part["__m"] = df_part[cols_upper[mpio_col]].astype(str).str.strip().str.zfill(3)
                df_part["divipola_key"] = df_part["__d"] + df_part["__m"]

            dfs.append(df_part[["divipola_key"]])

        if not dfs:
            raise ValueError("Ningun archivo CNPV trae columnas geograficas utilizables.")

        df_raw = pd.concat(dfs, ignore_index=True)
        # Eliminar DIVIPOLA mal formadas
        df_raw = df_raw[df_raw["divipola_key"].str.match(r"^\d{5}$")]

        df = (
            df_raw.groupby("divipola_key")
            .size()
            .reset_index(name="poblacion_total_base")
        )
        df["anio_key"] = 2018

        nulls = df[["divipola_key", "anio_key"]].isnull().sum().to_dict()
        duplicates = int(df.duplicated(subset=["divipola_key", "anio_key"]).sum())

        df["_cleaning_timestamp"] = datetime.datetime.now().isoformat()
        df["_granularidad"] = "municipio"
        df["_metodo"] = "COUNT(*) sobre personas censadas por DIVIPOLA municipio"

        silver_path.mkdir(parents=True, exist_ok=True)
        df = df[["divipola_key", "anio_key", "poblacion_total_base",
                 "_cleaning_timestamp", "_granularidad", "_metodo"]]
        df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)

        logger.info(
            f"CNPV agregado: {len(df)} municipios, poblacion total censada = "
            f"{int(df['poblacion_total_base'].sum()):,}"
        )

        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": (
                "Construccion DIVIPOLA = U_DPTO(2) + U_MPIO(3). "
                "Conteo de registros censados por municipio. anio_key=2018 fijo."
            ),
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza CNPV: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
