"""
Construcción del Datamart Analitico (OBT) — Capa Gold.

El OBT cruza las dimensiones y los hechos para producir la tabla final
orientada a indicadores sociales y económicos. Implementado con pandas
para ser consistente con el uso de PyArrow en el pipeline.

Decisiones clave:
  - Spine: se construye a partir de los divipola_key REALES presentes en
    al menos un fact, no con el producto cartesiano territorio x tiempo
    (que producía ~13k filas mayoritariamente vacías).
  - fact_censo (CNPV 2018): se propaga por divipola_key a todos los años
    como atributo fijo (censo base).
  - fact_demografia / fact_micronegocios: se unen tanto por municipio
    como por depto. agregado (divipola_key XX000) porque EMICRON y
    proyecciones DANE son de granularidad DEPARTAMENTAL.
  - Derivados: indicador_inversion_per_capita, densidad_micronegocios.
  - Se marca la celda "componente social" explícitamente (poblacion y censo)
    y "componente economico" (contratación y micronegocios) para trazabilidad.
"""

import logging
from pathlib import Path
from typing import Dict, Any
import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def _read_or_empty(p: Path, cols: list) -> pd.DataFrame:
    if p.exists():
        try:
            df = pd.read_parquet(p)
            return df
        except Exception as e:
            logger.warning(f"No se pudo leer {p}: {e}")
    return pd.DataFrame(columns=cols)


def build_datamart(gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo Datamart Analitico (OBT)")
    marts_dir = gold_path / "marts"
    hoy_dir = marts_dir / f"version_{datetime.datetime.now().strftime('%Y%m%d')}"
    latest_dir = marts_dir / "latest"
    hoy_dir.mkdir(parents=True, exist_ok=True)
    latest_dir.mkdir(parents=True, exist_ok=True)

    out_ver = hoy_dir / "mart_desarrollo_social_economico_municipio_anio.parquet"
    out_latest = latest_dir / "mart_desarrollo_social_economico_municipio_anio.parquet"

    dim_terr = _read_or_empty(gold_path / "dim_territorio.parquet", [
        "divipola_key", "nombre_municipio_referencia", "nombre_departamento",
        "divipola_departamento", "region",
    ])
    dim_tiempo = _read_or_empty(gold_path / "dim_tiempo.parquet", [
        "anio_key", "es_anio_electoral_presidencial", "es_pandemia",
    ])
    f_cnt = _read_or_empty(gold_path / "fact_contratacion_municipio_anio.parquet", [
        "divipola_key", "anio_key", "cantidad_procesos_adjudicados",
        "inversion_total_monto", "proveedores_unicos",
    ])
    f_mic = _read_or_empty(gold_path / "fact_micronegocios_municipio_anio.parquet", [
        "divipola_key", "anio_key", "volumen_micronegocios_exp",
    ])
    f_dem = _read_or_empty(gold_path / "fact_demografia_municipio_anio.parquet", [
        "divipola_key", "anio_key", "poblacion_total_proyectada",
    ])
    f_cen = _read_or_empty(gold_path / "fact_censo_municipio.parquet", [
        "divipola_key", "anio_key", "poblacion_total_base",
    ])

    if dim_terr.empty or dim_tiempo.empty:
        return {"status": "failed", "error": "dim_territorio o dim_tiempo vacias."}

    # Normalizar tipos
    for df_ in (f_cnt, f_mic, f_dem, f_cen, dim_terr):
        if "divipola_key" in df_.columns:
            df_["divipola_key"] = df_["divipola_key"].astype(str).str.strip().str.zfill(5)
    for df_ in (f_cnt, f_mic, f_dem, f_cen, dim_tiempo):
        if "anio_key" in df_.columns:
            df_["anio_key"] = pd.to_numeric(df_["anio_key"], errors="coerce").astype("Int64")

    # Descartar metadatos que podrían colisionar entre dataframes durante merges
    for df_name, df_ in (("f_cnt", f_cnt), ("f_mic", f_mic), ("f_dem", f_dem),
                          ("f_cen", f_cen), ("dim_terr", dim_terr), ("dim_tiempo", dim_tiempo)):
        cols_drop = [c for c in df_.columns if c.startswith("_")]
        if cols_drop:
            df_.drop(columns=cols_drop, inplace=True)

    # ---- Spine: solo pares (divipola, anio) con al menos 1 fact real ----
    # Limitar a los años definidos en dim_tiempo (2018-2029); fact_demografia
    # cubre proyecciones DANE hasta 2050, pero el mart analítico solo contempla
    # el horizonte definido por la dimensión tiempo.
    anios_validos = set(dim_tiempo["anio_key"].dropna().astype(int).tolist())

    pares = []
    for df_ in (f_cnt, f_mic, f_dem):
        if not df_.empty and "divipola_key" in df_.columns and "anio_key" in df_.columns:
            sub = df_[["divipola_key", "anio_key"]].dropna().copy()
            sub["anio_key"] = pd.to_numeric(sub["anio_key"], errors="coerce").astype("Int64")
            sub = sub[sub["anio_key"].isin(anios_validos)]
            pares.append(sub)

    if pares:
        spine = pd.concat(pares, ignore_index=True).drop_duplicates()
    else:
        spine = pd.DataFrame(columns=["divipola_key", "anio_key"])

    # Incluir también filas solo-censo (propagar CNPV a todos los años)
    if not f_cen.empty:
        cen_div = f_cen[["divipola_key"]].dropna().drop_duplicates()
        if not cen_div.empty:
            # Años existentes en spine o, si spine vacía, años dim_tiempo
            if not spine.empty:
                anios_existentes = spine["anio_key"].dropna().unique().tolist()
            else:
                anios_existentes = dim_tiempo["anio_key"].dropna().unique().tolist()
            extra = cen_div.assign(key=1).merge(
                pd.DataFrame({"anio_key": anios_existentes, "key": 1}),
                on="key",
            ).drop(columns="key")
            spine = pd.concat([spine, extra], ignore_index=True).drop_duplicates()

    if spine.empty:
        logger.error("Spine vacía: ninguna tabla de hechos tiene datos. Mart no se puede construir.")
        pd.DataFrame().to_parquet(out_latest, engine="pyarrow", index=False)
        return {"status": "failed", "error": "Todas las facts vacías", "registros": 0}

    spine["anio_key"] = spine["anio_key"].astype(int)

    # ---- Joins ----
    df = spine.merge(dim_terr, on="divipola_key", how="left")
    df = df.merge(dim_tiempo, on="anio_key", how="left")

    df = df.merge(f_cnt, on=["divipola_key", "anio_key"], how="left")

    # fact_micronegocios y fact_demografia son de granularidad DEPARTAMENTAL
    # (divipola XX000). Se unen por divipola_key para que SOLAMENTE el
    # agregado departamental contenga este valor, evitando duplicar 
    # poblaciones y negocios en cada municipio.
    df = df.merge(f_mic, on=["divipola_key", "anio_key"], how="left")
    df = df.merge(f_dem, on=["divipola_key", "anio_key"], how="left")

    # CNPV: broadcast por divipola (censo es snapshot 2018)
    cen_broadcast = f_cen[["divipola_key", "poblacion_total_base"]].rename(
        columns={"poblacion_total_base": "poblacion_censo_2018"}
    ).drop_duplicates(subset=["divipola_key"])
    df = df.merge(cen_broadcast, on="divipola_key", how="left")

    # Rellenar numericos ausentes
    for col in ("cantidad_procesos_adjudicados", "inversion_total_monto",
                "proveedores_unicos", "volumen_micronegocios_exp",
                "poblacion_total_proyectada", "poblacion_censo_2018"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # ---- Indicadores derivados ----
    # Usar poblacion_censo_2018 para municipios, y fallback a poblacion_total_proyectada para agregados
    pob = df["poblacion_censo_2018"].where(df["poblacion_censo_2018"] > 0, df["poblacion_total_proyectada"])
    pob = pob.where(pob > 0)
    df["indicador_inversion_per_capita"] = df["inversion_total_monto"] / pob
    df["indicador_densidad_micronegocios"] = df["volumen_micronegocios_exp"] / pob

    # ---- Flags de trazabilidad social/economico ----
    df["tiene_componente_social"] = (df["poblacion_total_proyectada"] > 0) | (df["poblacion_censo_2018"] > 0)
    df["tiene_componente_economico"] = (df["inversion_total_monto"] > 0) | (df["volumen_micronegocios_exp"] > 0)

    df["_mart_generation_timestamp"] = datetime.datetime.now().isoformat()

    df.to_parquet(out_ver, engine="pyarrow", compression="snappy", index=False)
    df.to_parquet(out_latest, engine="pyarrow", compression="snappy", index=False)

    # Metadatos de salida
    try:
        from src.config.settings import get_settings
        relative_latest = out_latest.relative_to(get_settings().PROJECT_ROOT)
    except Exception:
        relative_latest = out_latest.name

    logger.info(
        f"Mart generado: {len(df)} filas, {df['divipola_key'].nunique()} territorios, "
        f"anios {sorted(df['anio_key'].unique().tolist())}"
    )

    return {
        "status": "success",
        "archivo_latest": str(relative_latest),
        "archivo_versionado": str(out_ver),
        "registros": len(df),
        "territorios_unicos": int(df["divipola_key"].nunique()),
        "anios_cubiertos": sorted(df["anio_key"].unique().tolist()),
        "filas_con_social": int(df["tiene_componente_social"].sum()),
        "filas_con_economico": int(df["tiene_componente_economico"].sum()),
        "nulls_pk": df[["divipola_key", "anio_key"]].isnull().sum().to_dict(),
        "duplicados_pk": int(df.duplicated(subset=["divipola_key", "anio_key"]).sum()),
    }
