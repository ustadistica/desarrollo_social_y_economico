"""Calculo reproducible del HHI de contratacion publica.

El mercado base es municipio x anio x orden_entidad. Los contratos se leen
desde Silver transaccional para conservar la misma correccion de ingesta usada
por Gold: union SECOP I + SECOP II y deduplicacion por id_contrato.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
import pyarrow.parquet as pq


YEAR_MIN = 2018
YEAR_MAX = 2026

TXN_COLUMNS = [
    "id_contrato",
    "divipola_key",
    "anio_key",
    "valor_del_contrato",
    "nit_contratista",
    "_fuente_origen",
]

OUTPUT_NAMES = {
    "master": "HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv",
    "anio": "hhi_por_anio.csv",
    "nivel": "hhi_por_nivel.csv",
    "departamento": "hhi_por_departamento.csv",
    "municipio": "hhi_por_municipio.csv",
}


@dataclass(frozen=True)
class HHIPaths:
    project_root: Path
    data_dir: Path
    bronze_dir: Path
    silver_dir: Path
    mart_path: Path

    @classmethod
    def from_project_root(cls, project_root: Path) -> "HHIPaths":
        data_dir = project_root / "data"
        return cls(
            project_root=project_root,
            data_dir=data_dir,
            bronze_dir=data_dir / "bronze",
            silver_dir=data_dir / "silver",
            mart_path=data_dir
            / "gold"
            / "marts"
            / "latest"
            / "mart_desarrollo_social_economico_municipio_anio.parquet",
        )


def classify_order(value: object) -> str:
    """Clasifica variantes textuales de SECOP en categorias estables."""
    raw = "" if pd.isna(value) else str(value).upper().strip()
    if "NACIONAL" in raw:
        return "NACIONAL"
    if (
        "TERRITORIAL" in raw
        or "DISTRITO CAPITAL" in raw
        or "AREA METROPOLITANA" in raw
    ):
        return "TERRITORIAL"
    if "CORPOR" in raw or "AUTONOMA" in raw or "AUTÓNOMA" in raw:
        return "OTRO"
    if not raw or raw == "NAN" or "NO DEFINIDO" in raw:
        return "NO_DEFINIDO"
    return "OTRO"


def concentration_level(hhi: float) -> str:
    if hhi >= 2500:
        return "alta"
    if hhi >= 1500:
        return "moderada"
    return "baja"


def _read_existing_columns(path: Path, columns: Iterable[str]) -> pd.DataFrame:
    schema = pq.read_schema(path)
    available = [col for col in columns if col in schema.names]
    if not available:
        return pd.DataFrame()
    return pd.read_parquet(path, columns=available)


def load_transactions(silver_dir: Path) -> pd.DataFrame:
    """Carga y prepara SECOP I+II transaccional desde Silver."""
    frames: list[pd.DataFrame] = []
    for filename in (
        "silver_secop_i_transaccional.parquet",
        "silver_secop_ii_transaccional.parquet",
    ):
        path = silver_dir / filename
        if not path.exists():
            continue
        df = _read_existing_columns(path, TXN_COLUMNS + ["orden_entidad"])
        missing = [col for col in TXN_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"{path} no tiene columnas requeridas: {missing}")
        frames.append(df)

    if not frames:
        raise FileNotFoundError(
            f"No hay transaccionales SECOP en Silver: {silver_dir}"
        )

    tx = pd.concat(frames, ignore_index=True)
    tx = prepare_transactions(tx)
    return tx


def prepare_transactions(
    tx: pd.DataFrame,
    year_min: int = YEAR_MIN,
    year_max: int = YEAR_MAX,
) -> pd.DataFrame:
    """Normaliza, filtra y deduplica contratos para el HHI."""
    tx = tx.copy()
    tx["id_contrato"] = tx["id_contrato"].astype(str).str.strip()
    tx["divipola_key"] = tx["divipola_key"].astype(str).str.strip().str.zfill(5)
    tx["anio_key"] = pd.to_numeric(tx["anio_key"], errors="coerce")
    tx["valor_del_contrato"] = pd.to_numeric(
        tx["valor_del_contrato"], errors="coerce"
    )
    tx["nit_contratista"] = (
        tx["nit_contratista"].astype(str).str.replace(r"\D", "", regex=True).str.strip()
    )

    valid = tx[
        tx["id_contrato"].ne("")
        & tx["divipola_key"].str.match(r"^\d{5}$", na=False)
        & tx["anio_key"].between(year_min, year_max)
        & tx["valor_del_contrato"].gt(0)
        & tx["nit_contratista"].ne("")
    ].copy()
    valid["anio_key"] = valid["anio_key"].astype(int)
    return valid.drop_duplicates(subset=["id_contrato"], keep="first").reset_index(
        drop=True
    )


def load_order_mapping(bronze_dir: Path) -> pd.DataFrame:
    """Carga orden_entidad desde Bronze para compatibilidad con Silver antiguo."""
    specs = [
        (
            bronze_dir / "secop_i" / "secop_i_raw.parquet",
            {"UID": "id_contrato", "Orden Entidad": "orden_raw"},
        ),
        (
            bronze_dir / "secop_ii" / "secop_ii_raw.parquet",
            {"ID Contrato": "id_contrato", "Orden": "orden_raw"},
        ),
    ]
    frames: list[pd.DataFrame] = []
    for path, rename_map in specs:
        if not path.exists():
            continue
        cols = list(rename_map)
        df = _read_existing_columns(path, cols)
        if set(cols).issubset(df.columns):
            frames.append(df.rename(columns=rename_map))

    if not frames:
        return pd.DataFrame(columns=["id_contrato", "orden_entidad"])

    order = pd.concat(frames, ignore_index=True)
    order["id_contrato"] = order["id_contrato"].astype(str).str.strip()
    order["orden_entidad"] = order["orden_raw"].map(classify_order)
    return order[["id_contrato", "orden_entidad"]].drop_duplicates(
        subset=["id_contrato"], keep="first"
    )


def attach_order(tx: pd.DataFrame, bronze_dir: Path) -> pd.DataFrame:
    """Asegura orden_entidad sin imputar faltantes como territorial."""
    out = tx.copy().reset_index(drop=True)
    if "orden_entidad" in out.columns:
        out["orden_entidad"] = out["orden_entidad"].map(classify_order)
    else:
        out["orden_entidad"] = "NO_DEFINIDO"

    if out["orden_entidad"].eq("NO_DEFINIDO").any():
        mapping = load_order_mapping(bronze_dir)
        if not mapping.empty:
            out = out.merge(mapping, on="id_contrato", how="left", suffixes=("", "_map"))
            missing = out["orden_entidad"].eq("NO_DEFINIDO")
            mapped = out["orden_entidad_map"].notna()
            out.loc[missing & mapped, "orden_entidad"] = out.loc[
                missing & mapped, "orden_entidad_map"
            ]
            out = out.drop(columns=["orden_entidad_map"])

    out["orden_entidad"] = out["orden_entidad"].fillna("NO_DEFINIDO")
    return out


def compute_hhi(tx: pd.DataFrame, mart_path: Path | None = None) -> pd.DataFrame:
    """Calcula HHI por municipio, anio y orden_entidad."""
    keys = ["anio_key", "divipola_key", "orden_entidad"]

    market = (
        tx.groupby(keys, as_index=False)
        .agg(
            inversion_total=("valor_del_contrato", "sum"),
            total_contratos=("id_contrato", "nunique"),
            total_proveedores=("nit_contratista", "nunique"),
        )
    )
    provider = (
        tx.groupby(keys + ["nit_contratista"], as_index=False)
        .agg(suma_proveedor=("valor_del_contrato", "sum"))
    )
    calc = provider.merge(market, on=keys, how="inner")
    calc["participacion_sq"] = (
        (calc["suma_proveedor"] / calc["inversion_total"]) * 100
    ) ** 2

    master = (
        calc.groupby(keys, as_index=False)
        .agg(
            HHI=("participacion_sq", "sum"),
            inversion_total=("inversion_total", "first"),
            total_contratos=("total_contratos", "first"),
            total_proveedores=("total_proveedores", "first"),
        )
        .sort_values(keys)
        .reset_index(drop=True)
    )
    master["nivel_concentracion"] = master["HHI"].map(concentration_level)

    if mart_path and mart_path.exists():
        geo = pd.read_parquet(
            mart_path,
            columns=[
                "divipola_key",
                "nombre_municipio_referencia",
                "nombre_departamento",
                "divipola_departamento",
                "region",
            ],
        )
        geo["divipola_key"] = geo["divipola_key"].astype(str).str.zfill(5)
        geo = geo.drop_duplicates(subset=["divipola_key"], keep="first")
        master = master.merge(geo, on="divipola_key", how="left")

    if ((master["HHI"] < -1e-9) | (master["HHI"] > 10000.000001)).any():
        raise ValueError("HHI fuera del rango esperado 0-10000.")

    return master


def summarize_outputs(master: pd.DataFrame) -> dict[str, pd.DataFrame]:
    common_aggs = dict(
        HHI_promedio=("HHI", "mean"),
        HHI_mediana=("HHI", "median"),
        mercados=("HHI", "size"),
        total_contratos=("total_contratos", "sum"),
        inversion_total=("inversion_total", "sum"),
    )
    by_year = (
        master.groupby("anio_key", as_index=False)
        .agg(**common_aggs)
        .sort_values("anio_key")
    )
    by_level = (
        master.groupby(["anio_key", "orden_entidad"], as_index=False)
        .agg(**common_aggs)
        .sort_values(["anio_key", "orden_entidad"])
    )

    dept_keys = ["anio_key", "nombre_departamento", "divipola_departamento"]
    by_department = (
        master.groupby(dept_keys, dropna=False, as_index=False)
        .agg(**common_aggs)
        .sort_values(["anio_key", "HHI_promedio"], ascending=[True, False])
    )

    municipality_cols = [
        "anio_key",
        "divipola_key",
        "nombre_municipio_referencia",
        "nombre_departamento",
        "orden_entidad",
        "HHI",
        "nivel_concentracion",
        "total_contratos",
        "total_proveedores",
        "inversion_total",
    ]
    by_municipality = master[
        [col for col in municipality_cols if col in master.columns]
    ].sort_values(["anio_key", "HHI"], ascending=[True, False])

    return {
        "master": master,
        "anio": by_year,
        "nivel": by_level,
        "departamento": by_department,
        "municipio": by_municipality,
    }


def write_outputs(outputs: dict[str, pd.DataFrame], data_dir: Path) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for key, filename in OUTPUT_NAMES.items():
        outputs[key].to_csv(data_dir / filename, index=False, encoding="utf-8")


def run(project_root: Path | None = None, write: bool = True) -> dict[str, pd.DataFrame]:
    root = (project_root or Path.cwd()).resolve()
    paths = HHIPaths.from_project_root(root)
    tx = load_transactions(paths.silver_dir)
    tx = attach_order(tx, paths.bronze_dir)
    master = compute_hhi(tx, paths.mart_path)
    outputs = summarize_outputs(master)
    if write:
        write_outputs(outputs, paths.data_dir)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Calcula indicadores HHI SECOP.")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Raiz del repositorio. Por defecto: directorio actual.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Calcula en memoria sin escribir CSV.",
    )
    args = parser.parse_args()

    outputs = run(args.project_root, write=not args.no_write)
    print("HHI calculado desde Silver transaccional corregido.")
    for key, df in outputs.items():
        print(f"  {OUTPUT_NAMES[key]:45s} {len(df):,} filas")


if __name__ == "__main__":
    main()
