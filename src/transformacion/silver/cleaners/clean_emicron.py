"""
Limpieza y agregacion de EMICRON (Capa Silver).

EMICRON es una encuesta muestral, no un censo. Reglas metodologicas:

1. Cada encuesta fisica aparece en varios modulos. Concatenar todos los
   modulos inflaria la estimacion, por lo que se usa el modulo de
   identificacion/caracteristicas como fuente autoritativa de unidad muestral.
2. Los snapshots de ingesta pueden repetir las mismas unidades. Se deduplica
   por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio).
3. La granularidad disponible para el mart actual es departamento-anio
   (COD_DEPTO), representada como DIVIPOLA departamental XX000.
4. El volumen expandido se calcula con SUM(factor_expansion). Si F_EXP viene
   ausente o en cero para un anio, se fusionan los archivos separados de
   factores de expansion por las llaves de encuesta.
"""

import datetime
import logging
from pathlib import Path
import re
from typing import Any, Dict, List

import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


_KEY_COLS = ["DIRECTORIO", "SECUENCIA_P", "SECUENCIA_ENCUESTA"]

# fex_c/FEX_C es el factor canonico documentado en el contrato del proyecto.
# fex_micro_dpto queda como respaldo si no existe el factor canonico del anio.
_FACTOR_COL_PRIORITY = ("fex_c", "FEX_C", "fex_micro_dpto", "FEX_MICRO_DPTO")

# Palabras clave priorizadas que identifican el modulo de identificacion/
# caracterizacion (se evaluan en orden; el primer match gana).
_MODULOS_PREFERIDOS = (
    "identificacin",
    "identificacion",
    "caractersticas_del_micronegocio",
    "caracteristicas_del_micronegocio",
    "identificaci",
)


def _clasificar_archivos(archivos: List[Path]) -> Dict[str, List[Path]]:
    """Clasifica archivos EMICRON por tipo de modulo."""
    buckets: Dict[str, List[Path]] = {"identificacion": [], "otros_con_depto": [], "sin_depto": []}
    for f in archivos:
        try:
            schema = pq.read_schema(str(f))
            col_names_upper = {c.upper() for c in schema.names}
        except Exception as e:
            logger.warning(f"  No se pudo leer schema de {f.name}: {e}")
            continue

        if "COD_DEPTO" not in col_names_upper:
            buckets["sin_depto"].append(f)
            continue

        name_lower = f.name.lower()
        if any(tok in name_lower for tok in _MODULOS_PREFERIDOS):
            buckets["identificacion"].append(f)
        else:
            buckets["otros_con_depto"].append(f)
    return buckets


def _extraer_anio(nombre_archivo: str) -> int | None:
    m = re.search(r"(20\d{2})", nombre_archivo)
    return int(m.group(1)) if m else None


def _derivar_anio_encuesta(df_part: pd.DataFrame, filename: str) -> pd.Series:
    """
    Prioridad para el anio EMICRON:
      1. _source_version == 'EMICRON_YYYY'
      2. _emicron_year si cae en rango [2019, 2024]
      3. token 20YY en el nombre del archivo, restringido a rango EMICRON
    """
    n = len(df_part)
    if "_source_version" in df_part.columns:
        sv = df_part["_source_version"].astype(str).str.extract(r"EMICRON_(20\d{2})", expand=False)
        yr_sv = pd.to_numeric(sv, errors="coerce")
        if yr_sv.notna().sum() > 0.5 * n:
            return yr_sv

    if "_emicron_year" in df_part.columns:
        yr_meta = pd.to_numeric(df_part["_emicron_year"], errors="coerce")
        yr_meta = yr_meta.where(yr_meta.between(2019, 2024))
        if yr_meta.notna().sum() > 0.5 * n:
            return yr_meta

    matches = re.findall(r"(20(?:19|20|21|22|23|24))", filename)
    yr = int(matches[0]) if matches else 2024
    return pd.Series([yr] * n, index=df_part.index, dtype="float64")


def _normalizar_claves_muestrales(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza llaves de encuesta para que los merges no dependan del dtype."""
    for col in _KEY_COLS:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )
    return df


def _leer_candidatos_factores(archivos: List[Path]) -> List[Dict[str, Any]]:
    """Lee archivos con factores separados y los ordena por prioridad metodologica."""
    candidatos: List[Dict[str, Any]] = []

    for f in archivos:
        try:
            schema = pq.read_schema(str(f))
            schema_cols = list(schema.names)
        except Exception as e:
            logger.warning(f"  No se pudo leer schema de factores {f.name}: {e}")
            continue

        if not all(c in schema_cols for c in _KEY_COLS):
            continue

        factor_cols = [c for c in _FACTOR_COL_PRIORITY if c in schema_cols]
        if not factor_cols:
            continue

        for factor_col in factor_cols:
            read_cols = list(dict.fromkeys(_KEY_COLS + [factor_col, "_source_version", "_emicron_year"]))
            read_cols = [c for c in read_cols if c in schema_cols]
            try:
                df_factor = pd.read_parquet(f, columns=read_cols)
            except Exception as e:
                logger.warning(f"  Error leyendo factor {factor_col} de {f.name}: {e}")
                continue

            df_factor["_emicron_year"] = _derivar_anio_encuesta(df_factor, f.name)
            df_factor["_emicron_year"] = pd.to_numeric(
                df_factor["_emicron_year"], errors="coerce"
            ).astype("Int64")
            df_factor = _normalizar_claves_muestrales(df_factor)
            df_factor["_factor_expansion_value"] = pd.to_numeric(
                df_factor[factor_col], errors="coerce"
            )
            df_factor = df_factor.dropna(subset=_KEY_COLS + ["_emicron_year"])
            df_factor = df_factor[df_factor["_emicron_year"].between(2019, 2024)]
            df_factor = df_factor.drop_duplicates(subset=_KEY_COLS + ["_emicron_year"], keep="first")

            if df_factor.empty or df_factor["_factor_expansion_value"].fillna(0).sum() <= 0:
                continue

            for anio in sorted(df_factor["_emicron_year"].dropna().astype(int).unique()):
                sub = df_factor[df_factor["_emicron_year"].astype(int).eq(anio)][
                    _KEY_COLS + ["_emicron_year", "_factor_expansion_value"]
                ].copy()
                candidatos.append(
                    {
                        "anio": int(anio),
                        "factor_col": factor_col,
                        "priority": _FACTOR_COL_PRIORITY.index(factor_col),
                        "source": f.name,
                        "df": sub,
                    }
                )

    return sorted(candidatos, key=lambda x: (x["anio"], x["priority"], x["source"]))


def _aplicar_fallback_factores(
    df_raw: pd.DataFrame,
    candidatos_factores: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Completa factor_expansion desde archivos separados cuando F_EXP no sirve."""
    if "F_EXP" not in df_raw.columns:
        df_raw["F_EXP"] = pd.NA

    df_raw["F_EXP"] = pd.to_numeric(df_raw["F_EXP"], errors="coerce").fillna(0.0)
    df_raw["factor_expansion"] = df_raw["F_EXP"]
    df_raw["_factor_expansion_origen"] = "F_EXP"

    if df_raw.empty:
        return []

    faltan_claves = [c for c in _KEY_COLS if c not in df_raw.columns]
    resumen_anual = df_raw.groupby("_emicron_year")["factor_expansion"].sum()
    anios_sin_expansion = [int(anio) for anio, total in resumen_anual.items() if total <= 0]
    if not anios_sin_expansion:
        return []

    if faltan_claves:
        raise ValueError(
            "EMICRON tiene anios con F_EXP cero, pero faltan llaves para fusionar factores: "
            + ", ".join(faltan_claves)
        )

    eventos_fallback: List[Dict[str, Any]] = []

    for anio in anios_sin_expansion:
        base_idx = df_raw.index[df_raw["_emicron_year"].eq(anio)]
        base = df_raw.loc[base_idx, _KEY_COLS + ["_emicron_year"]].copy()
        base["_row_index"] = base.index

        candidatos_anio = [c for c in candidatos_factores if c["anio"] == anio]
        elegido = None

        for candidato in candidatos_anio:
            try:
                merged = base.merge(
                    candidato["df"],
                    on=_KEY_COLS + ["_emicron_year"],
                    how="left",
                    validate="one_to_one",
                )
            except Exception as e:
                logger.warning(
                    f"  Factor descartado {candidato['source']}::{candidato['factor_col']} "
                    f"para {anio}: {e}"
                )
                continue

            factor = pd.to_numeric(merged["_factor_expansion_value"], errors="coerce")
            match_rate = float(factor.notna().mean()) if len(factor) else 0.0
            factor_sum = float(factor.fillna(0).sum())
            if match_rate == 1.0 and factor_sum > 0:
                elegido = (candidato, merged, factor)
                break

            logger.warning(
                f"  Factor incompleto {candidato['source']}::{candidato['factor_col']} "
                f"para {anio}: match_rate={match_rate:.2%}, suma={factor_sum:,.0f}"
            )

        if elegido is None:
            raise ValueError(
                f"F_EXP es cero en {anio} y no se encontro factor separado completo para fusionar."
            )

        candidato, merged, factor = elegido
        valores = pd.Series(factor.to_numpy(), index=merged["_row_index"].to_numpy())
        df_raw.loc[valores.index, "factor_expansion"] = valores
        df_raw.loc[valores.index, "_factor_expansion_origen"] = (
            f"{candidato['factor_col']}::{candidato['source']}"
        )

        eventos_fallback.append(
            {
                "anio": anio,
                "factor_col": candidato["factor_col"],
                "source": candidato["source"],
                "filas": int(len(base)),
                "suma_factor": float(valores.sum()),
            }
        )
        logger.info(
            f"Fallback EMICRON {anio}: {candidato['factor_col']} desde "
            f"{candidato['source']} ({len(base):,} filas, suma={valores.sum():,.0f})"
        )

    validacion = df_raw.groupby("_emicron_year").agg(
        registros=("factor_expansion", "size"),
        suma_factor=("factor_expansion", "sum"),
    )
    invalidos = validacion[(validacion["registros"] > 0) & (validacion["suma_factor"] <= 0)]
    if not invalidos.empty:
        raise ValueError(
            "EMICRON quedo con expansion cero despues del fallback: "
            + ", ".join(str(int(a)) for a in invalidos.index)
        )

    return eventos_fallback


def clean_emicron_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando consolidacion y agregacion de EMICRON (Silver)...")
    output_file = silver_path / "silver_emicron_agregado.parquet"

    try:
        parquet_files = sorted(bronze_path.rglob("*.parquet"))
        if not parquet_files:
            raise ValueError("No se encontraron archivos parquet en Bronze/emicron.")

        buckets = _clasificar_archivos(parquet_files)
        candidatos_factores = _leer_candidatos_factores(parquet_files)
        logger.info(
            f"Clasificacion EMICRON: "
            f"identificacion={len(buckets['identificacion'])}, "
            f"otros_con_depto={len(buckets['otros_con_depto'])}, "
            f"sin_depto={len(buckets['sin_depto'])}, "
            f"factores_candidatos={len(candidatos_factores)}"
        )

        autoritativos = buckets["identificacion"] or buckets["otros_con_depto"][:1]
        if not autoritativos:
            raise ValueError(
                "Ningun archivo EMICRON tiene COD_DEPTO. No es posible agregar a departamento."
            )

        keep_cols = [
            "DIRECTORIO", "SECUENCIA_P", "SECUENCIA_ENCUESTA",
            "COD_DEPTO", "AREA", "CLASE_TE", "F_EXP",
            "_source_version", "_emicron_year",
        ]

        dfs = []
        for f in autoritativos:
            try:
                df_part = pd.read_parquet(f)
                cols_presentes = [c for c in keep_cols if c in df_part.columns]
                df_part = df_part[cols_presentes].copy()
                df_part["_emicron_year"] = _derivar_anio_encuesta(df_part, f.name)
                dfs.append(df_part)
                logger.info(
                    f"  + {f.name}: {len(df_part)} filas "
                    f"(anio={int(df_part['_emicron_year'].mode().iat[0])})"
                )
            except Exception as e:
                logger.warning(f"  Error leyendo {f.name}: {e}")

        if not dfs:
            raise ValueError("Todos los archivos autoritativos fallaron al leerse.")

        df_raw = pd.concat(dfs, ignore_index=True)
        logger.info(
            f"EMICRON consolidado (modulos autoritativos): {len(df_raw)} filas, "
            f"{len(df_raw.columns)} cols"
        )

        df_raw = _normalizar_claves_muestrales(df_raw)
        df_raw["_emicron_year"] = pd.to_numeric(
            df_raw["_emicron_year"], errors="coerce"
        ).fillna(2024).astype(int)
        df_raw["COD_DEPTO"] = df_raw["COD_DEPTO"].astype(str).str.strip().str.zfill(2)

        claves_existentes = [c for c in _KEY_COLS + ["_emicron_year"] if c in df_raw.columns]
        if set(claves_existentes) >= {"DIRECTORIO", "_emicron_year"}:
            antes = len(df_raw)
            df_raw = df_raw.drop_duplicates(subset=claves_existentes, keep="first")
            logger.info(f"Deduplicado por {claves_existentes}: {antes} -> {len(df_raw)}")

        df_raw = df_raw[df_raw["COD_DEPTO"].str.match(r"^\d{2}$")].copy()
        df_raw = df_raw[df_raw["_emicron_year"].between(2018, 2030)].copy()

        eventos_fallback = _aplicar_fallback_factores(df_raw, candidatos_factores)

        df_raw["divipola_depto"] = df_raw["COD_DEPTO"]
        df_raw["divipola_key"] = df_raw["divipola_depto"] + "000"
        df_raw["anio_key"] = df_raw["_emicron_year"].astype(int)

        df = (
            df_raw.groupby(["divipola_key", "divipola_depto", "anio_key"])
            .agg(
                volumen_micronegocios_exp=("factor_expansion", "sum"),
                n_registros_encuesta=("factor_expansion", "count"),
                _factor_expansion_origen=(
                    "_factor_expansion_origen",
                    lambda s: ",".join(sorted(set(s.dropna().astype(str)))),
                ),
            )
            .reset_index()
        )

        df["anio_key"] = df["anio_key"].astype(int)
        df["_cleaning_timestamp"] = datetime.datetime.now().isoformat()
        df["_granularidad"] = "departamento"
        df["_metodo_expansion"] = (
            "SUM(factor_expansion) sobre modulo autoritativo deduplicado; "
            "factor_expansion usa F_EXP cuando es valido y fusiona fex_c/FEX_C "
            "por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio) cuando F_EXP es cero."
        )
        df["_fuentes_autoritativas"] = ",".join(f.name for f in autoritativos)
        df["_fuentes_factores_fallback"] = ";".join(
            f"{e['anio']}:{e['factor_col']}::{e['source']}" for e in eventos_fallback
        )

        silver_path.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)

        nulls = df[["divipola_key", "anio_key"]].isnull().sum().to_dict()
        duplicates = int(df.duplicated(subset=["divipola_key", "anio_key"]).sum())

        logger.info(
            f"EMICRON agregado. Departamentos: {df['divipola_depto'].nunique()}, "
            f"Anios: {sorted(df['anio_key'].unique().tolist())}, "
            f"Filas: {len(df)}, "
            f"SUM(volumen_micronegocios_exp)={df['volumen_micronegocios_exp'].sum():,.0f}"
        )

        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "departamentos": int(df["divipola_depto"].nunique()),
            "anios": sorted(df["anio_key"].unique().tolist()),
            "nulls": nulls,
            "duplicados": duplicates,
            "factores_fallback": eventos_fallback,
            "reglas_aplicadas": (
                "Uso exclusivo del modulo autoritativo para no multiplicar unidades. "
                "Deduplicacion por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio). "
                "SUM(factor_expansion) por depto-anio; factor_expansion usa F_EXP "
                "valido o fallback fex_c/FEX_C fusionado desde archivos de factores."
            ),
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza EMICRON: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
