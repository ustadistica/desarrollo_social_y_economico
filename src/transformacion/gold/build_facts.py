"""
Construccion de tablas de hechos (Capa Gold).

Decisión clave sobre proveedores_unicos (doble conteo SECOP I vs SECOP II):

    SECOP I y SECOP II son plataformas distintas de la misma entidad
    (Colombia Compra Eficiente), pero un mismo NIT puede aparecer en
    ambas. Por eso:

    - Se PREFIERE leer las tablas transaccionales de Silver
      (silver_secop_i_transaccional.parquet, silver_secop_ii_transaccional.parquet)
      y hacer UNION + COUNT(DISTINCT nit) a granularidad municipio-año.
      Este es el cálculo correcto: un NIT presente en ambas plataformas
      cuenta UNA vez.

    - Solo como *fallback* (cuando no existan transaccionales), se usa la
      suma de agregados con MAX(proveedores_unicos) como estimador
      conservador, documentado como limitación.

Decisión sobre CNPV en fact_censo:

    CNPV 2018 es un censo fijo de un solo año. Se construye fact_censo
    con (divipola_key, anio_key=2018). El mart luego hace join por
    divipola_key (sin anio_key) para propagar este dato censal como
    atributo fijo a todos los años.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def _fact_simple(source_file: Path, gold_file: Path, schema_cols: Dict[str, str]) -> Dict[str, Any]:
    """Helper: lee Silver, valida FKs, tipa y escribe Gold."""
    logger.info(f"Construyendo Fact: {gold_file.name} <- {source_file.name if source_file.exists() else 'AUSENTE'}")
    if not source_file.exists():
        pd.DataFrame(columns=["divipola_key", "anio_key"] + list(schema_cols.keys())).to_parquet(
            gold_file, engine="pyarrow", index=False
        )
        return {
            "status": "failed_safe",
            "registros": 0,
            "error": f"Silver source no existe: {source_file}",
            "archivo": str(gold_file),
        }
    try:
        df = pd.read_parquet(source_file)
        initial_len = len(df)
        df = df.dropna(subset=["divipola_key", "anio_key"])
        for col, dtype in schema_cols.items():
            if col not in df.columns:
                df[col] = 0.0 if "float" in dtype else 0
            df[col] = df[col].astype(dtype)
        cols_keep = ["divipola_key", "anio_key"] + list(schema_cols.keys())
        df = df[[c for c in cols_keep if c in df.columns]]
        df["_creation_timestamp"] = datetime.datetime.now().isoformat()
        df.to_parquet(gold_file, engine="pyarrow", index=False)
        return {
            "status": "success",
            "archivo": str(gold_file),
            "registros": len(df),
            "registros_descartados_fks_nulas": initial_len - len(df),
            "nulls": df.isnull().sum().to_dict(),
            "duplicados": int(df.duplicated(subset=["divipola_key", "anio_key"]).sum()),
        }
    except Exception as e:
        logger.error(f"Fallo construyendo {gold_file.name}: {e}")
        pd.DataFrame(columns=["divipola_key", "anio_key"] + list(schema_cols.keys())).to_parquet(
            gold_file, engine="pyarrow", index=False
        )
        return {
            "status": "failed_safe",
            "error": str(e),
            "mensaje": "Esqueleto tabular vacio generado para no romper despliegue.",
            "archivo": str(gold_file),
            "registros": 0,
        }


def _build_fact_contratacion(silver_path: Path, out_file: Path) -> Dict[str, Any]:
    """
    Calcula fact_contratacion combinando SECOP I y II.

    Camino preferido (correcto): union de las dos tablas transaccionales
    y agregacion municipio-anio con COUNT(DISTINCT nit).

    Fallback (conservador): union de los dos agregados, sumando procesos
    y montos, con MAX() sobre proveedores_unicos.
    """
    txn_i = silver_path / "silver_secop_i_transaccional.parquet"
    txn_ii = silver_path / "silver_secop_ii_transaccional.parquet"
    agg_i = silver_path / "silver_secop_i_agregado.parquet"
    agg_ii = silver_path / "silver_secop_ii_agregado.parquet"

    # ---------- Camino preferido: transaccionales ----------
    txn_frames: List[pd.DataFrame] = []
    if txn_i.exists():
        txn_frames.append(pd.read_parquet(txn_i))
        logger.info(f"  SECOP I transaccional: {txn_i.name}")
    if txn_ii.exists():
        txn_frames.append(pd.read_parquet(txn_ii))
        logger.info(f"  SECOP II transaccional: {txn_ii.name}")

    if txn_frames:
        tx = pd.concat(txn_frames, ignore_index=True)
        tx = tx.dropna(subset=["divipola_key", "anio_key"])
        tx["nit_contratista"] = tx["nit_contratista"].astype(str)

        # Un NIT en ambas plataformas cuenta UNA sola vez (COUNT DISTINCT global)
        df = (
            tx.groupby(["divipola_key", "anio_key"], as_index=False)
            .agg(
                cantidad_procesos_adjudicados=("id_contrato", "nunique"),
                inversion_total_monto=("valor_del_contrato", "sum"),
                proveedores_unicos=("nit_contratista", "nunique"),
            )
        )
        df["_creation_timestamp"] = datetime.datetime.now().isoformat()
        df["_fuentes"] = ",".join([p.name for p in (txn_i, txn_ii) if p.exists()])
        df["_metodo_proveedores"] = "COUNT(DISTINCT nit) sobre union transaccional (correcto)"
        df.to_parquet(out_file, engine="pyarrow", compression="snappy", index=False)
        return {
            "status": "success",
            "archivo": str(out_file),
            "registros": len(df),
            "metodo_proveedores": "COUNT(DISTINCT nit) union transaccional (sin doble conteo)",
            "fuentes": [p.name for p in (txn_i, txn_ii) if p.exists()],
            "nulls": df[["divipola_key", "anio_key"]].isnull().sum().to_dict(),
            "duplicados": int(df.duplicated(subset=["divipola_key", "anio_key"]).sum()),
        }

    # ---------- Fallback: agregados ----------
    agg_frames: List[pd.DataFrame] = []
    fuentes_agg: List[str] = []
    for p in (agg_i, agg_ii):
        if p.exists():
            agg_frames.append(pd.read_parquet(p))
            fuentes_agg.append(p.name)

    if not agg_frames:
        pd.DataFrame(columns=[
            "divipola_key", "anio_key",
            "cantidad_procesos_adjudicados", "inversion_total_monto", "proveedores_unicos",
        ]).to_parquet(out_file, engine="pyarrow", index=False)
        return {
            "status": "failed_safe",
            "archivo": str(out_file),
            "registros": 0,
            "error": "No hay SECOP (ni transaccional ni agregado) en Silver.",
        }

    df_a = pd.concat(agg_frames, ignore_index=True)
    for col in ("cantidad_procesos_adjudicados", "inversion_total_monto", "proveedores_unicos"):
        if col in df_a.columns:
            df_a[col] = pd.to_numeric(df_a[col], errors="coerce").fillna(0)

    df = (
        df_a.groupby(["divipola_key", "anio_key"], as_index=False)
        .agg({
            "cantidad_procesos_adjudicados": "sum",   # cada proceso es unico por plataforma
            "inversion_total_monto": "sum",           # cada monto es unico por contrato
            "proveedores_unicos": "max",              # estimador conservador, NO sum
        })
    )
    df["_creation_timestamp"] = datetime.datetime.now().isoformat()
    df["_fuentes"] = ",".join(fuentes_agg)
    df["_metodo_proveedores"] = "MAX sobre agregados (fallback conservador, NO correcto)"
    df.to_parquet(out_file, engine="pyarrow", compression="snappy", index=False)
    return {
        "status": "success_fallback",
        "archivo": str(out_file),
        "registros": len(df),
        "metodo_proveedores": "MAX (fallback conservador: subestima cuando NITs son exclusivos de una plataforma)",
        "fuentes": fuentes_agg,
        "advertencia": "Se usaron agregados; para metodo correcto producir transaccionales en Silver.",
        "nulls": df[["divipola_key", "anio_key"]].isnull().sum().to_dict(),
        "duplicados": int(df.duplicated(subset=["divipola_key", "anio_key"]).sum()),
    }


def build_facts(silver_path: Path, gold_path: Path) -> Dict[str, Any]:
    """Construye todas las tablas de hechos del modelo."""
    gold_path.mkdir(parents=True, exist_ok=True)
    results: Dict[str, Any] = {}

    # 1. Fact Demografia (Proyecciones Censales - depto-anio)
    results["fact_demografia"] = _fact_simple(
        silver_path / "silver_proyecciones_agregado.parquet",
        gold_path / "fact_demografia_municipio_anio.parquet",
        {"poblacion_total_proyectada": "float64"},
    )

    # 2. Fact Micronegocios (EMICRON - depto-anio expandido)
    results["fact_micronegocios"] = _fact_simple(
        silver_path / "silver_emicron_agregado.parquet",
        gold_path / "fact_micronegocios_municipio_anio.parquet",
        {"volumen_micronegocios_exp": "float64"},
    )

    # 3. Fact Contratacion (SECOP I + II con logica anti-doble-conteo)
    results["fact_contratacion"] = _build_fact_contratacion(
        silver_path,
        gold_path / "fact_contratacion_municipio_anio.parquet",
    )

    # 4. Fact Censo (CNPV 2018 - municipio)
    results["fact_censo"] = _fact_simple(
        silver_path / "silver_cnpv_agregado.parquet",
        gold_path / "fact_censo_municipio.parquet",
        {"poblacion_total_base": "float64"},
    )

    return results
