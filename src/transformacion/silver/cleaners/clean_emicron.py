"""
Limpieza y agregación de EMICRON (Capa Silver).

EMICRON es una encuesta muestral (no censo). Corrección metodológica crítica:

1. Cada encuesta física se replica en ~12 módulos (identificación, ventas,
   características, costos, etc.). Concatenar todos los módulos duplicaría
   F_EXP ~12 veces e inflaría la estimación de micronegocios.
   => Se usa UN SOLO módulo (módulo de identificación) como fuente
      autoritativa de la unidad muestral y su F_EXP.
2. Las carpetas `2024/` e `ingestion_date=YYYY-MM-DD/` pueden contener
   snapshots de ingesta distintos de los MISMOS datos.
   => Se deduplica por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA,
      _emicron_year) antes de agregar.
3. La granularidad disponible es DEPARTAMENTO (COD_DEPTO), no municipio.
   => La agregación se realiza a nivel departamento-año.
4. Fórmula: volumen_micronegocios_exp = SUM(F_EXP) por (COD_DEPTO, año)
   sobre las unidades únicas de la encuesta.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
import datetime
import re
import pandas as pd
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


# Palabras clave priorizadas que identifican el módulo de identificación/caracterización
# (se evalúan en orden; el primer match gana). Los módulos "identificacin" / "identificacion"
# se prefieren porque tienen una fila por unidad muestral única y contienen COD_DEPTO y F_EXP.
_MODULOS_PREFERIDOS = (
    "identificacin",
    "identificacion",
    "caractersticas_del_micronegocio",
    "caracteristicas_del_micronegocio",
    "identificaci",
)


def _clasificar_archivos(archivos: List[Path]) -> Dict[str, List[Path]]:
    """Clasifica archivos EMICRON por tipo de módulo."""
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


def clean_emicron_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando consolidacion y agregacion de EMICRON (Silver)...")
    output_file = silver_path / "silver_emicron_agregado.parquet"

    try:
        parquet_files = sorted(bronze_path.rglob("*.parquet"))
        if not parquet_files:
            raise ValueError("No se encontraron archivos parquet en Bronze/emicron.")

        buckets = _clasificar_archivos(parquet_files)
        logger.info(
            f"Clasificacion EMICRON: "
            f"identificacion={len(buckets['identificacion'])}, "
            f"otros_con_depto={len(buckets['otros_con_depto'])}, "
            f"sin_depto={len(buckets['sin_depto'])}"
        )

        # Fuente autoritativa: modulo de identificacion. Si no existe, usamos
        # el primer modulo con COD_DEPTO (cualquier modulo tiene las mismas
        # unidades, pero identificacion es mas canonico).
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

        def _derivar_anio_encuesta(df_part: pd.DataFrame, filename: str) -> pd.Series:
            """
            Prioridad para el año EMICRON (año de la encuesta, NO de ingesta):
              1. _source_version == 'EMICRON_YYYY'  (más confiable)
              2. _emicron_year si cae en rango [2019, 2024]
              3. Último token 20YY del nombre del archivo, restringido a rango EMICRON
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

            # Fallback: año EMICRON (2019-2024) que aparezca en el nombre
            matches = re.findall(r"(20(?:19|20|21|22|23|24))", filename)
            yr = int(matches[0]) if matches else 2024
            return pd.Series([yr] * n, index=df_part.index, dtype="float64")

        dfs = []
        for f in autoritativos:
            try:
                df_part = pd.read_parquet(f)
                cols_presentes = [c for c in keep_cols if c in df_part.columns]
                df_part = df_part[cols_presentes].copy()
                df_part["_emicron_year"] = _derivar_anio_encuesta(df_part, f.name)
                dfs.append(df_part)
                logger.info(f"  + {f.name}: {len(df_part)} filas (año={int(df_part['_emicron_year'].mode().iat[0])})")
            except Exception as e:
                logger.warning(f"  Error leyendo {f.name}: {e}")

        if not dfs:
            raise ValueError("Todos los archivos autoritativos fallaron al leerse.")

        df_raw = pd.concat(dfs, ignore_index=True)
        logger.info(f"EMICRON consolidado (modulos autoritativos): {len(df_raw)} filas, {len(df_raw.columns)} cols")

        # Normalizacion de tipos
        df_raw["F_EXP"] = pd.to_numeric(df_raw.get("F_EXP"), errors="coerce").fillna(0.0)
        df_raw["_emicron_year"] = pd.to_numeric(df_raw["_emicron_year"], errors="coerce").fillna(2024).astype(int)
        df_raw["COD_DEPTO"] = df_raw["COD_DEPTO"].astype(str).str.strip().str.zfill(2)

        # DEDUPLICACION CRITICA: mismo DIRECTORIO-SECUENCIA-AÑO no puede contarse 2 veces
        # (puede pasar si dos snapshots de ingesta traen los mismos datos).
        claves_unicas = ["DIRECTORIO", "SECUENCIA_P", "SECUENCIA_ENCUESTA", "_emicron_year"]
        claves_existentes = [c for c in claves_unicas if c in df_raw.columns]
        if set(claves_existentes) >= {"DIRECTORIO", "_emicron_year"}:
            antes = len(df_raw)
            df_raw = df_raw.drop_duplicates(subset=claves_existentes, keep="first")
            logger.info(f"Deduplicado por {claves_existentes}: {antes} -> {len(df_raw)}")

        # Filtrar departamentos validos (2 digitos)
        df_raw = df_raw[df_raw["COD_DEPTO"].str.match(r"^\d{2}$")]
        df_raw = df_raw[df_raw["_emicron_year"].between(2018, 2030)]

        # Construir claves
        df_raw["divipola_depto"] = df_raw["COD_DEPTO"]
        df_raw["divipola_key"] = df_raw["divipola_depto"] + "000"  # agregado departamental
        df_raw["anio_key"] = df_raw["_emicron_year"].astype(int)

        # AGREGACION METODOLOGICAMENTE CORRECTA
        df = (
            df_raw.groupby(["divipola_key", "divipola_depto", "anio_key"])
            .agg(
                volumen_micronegocios_exp=("F_EXP", "sum"),
                n_registros_encuesta=("F_EXP", "count"),
            )
            .reset_index()
        )

        df["anio_key"] = df["anio_key"].astype(int)
        df["_cleaning_timestamp"] = datetime.datetime.now().isoformat()
        df["_granularidad"] = "departamento"
        df["_metodo_expansion"] = (
            "SUM(F_EXP) sobre modulo_autoritativo deduplicado por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio)"
        )
        df["_fuentes_autoritativas"] = ",".join(f.name for f in autoritativos)

        silver_path.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_file, engine="pyarrow", compression="snappy", index=False)

        nulls = df[["divipola_key", "anio_key"]].isnull().sum().to_dict()
        duplicates = int(df.duplicated(subset=["divipola_key", "anio_key"]).sum())

        logger.info(
            f"EMICRON agregado. Departamentos: {df['divipola_depto'].nunique()}, "
            f"Anios: {sorted(df['anio_key'].unique().tolist())}, "
            f"Filas: {len(df)}, SUM(volumen_micronegocios_exp)={df['volumen_micronegocios_exp'].sum():,.0f}"
        )

        return {
            "status": "success",
            "archivo": str(output_file),
            "registros": len(df),
            "departamentos": int(df["divipola_depto"].nunique()),
            "anios": sorted(df["anio_key"].unique().tolist()),
            "nulls": nulls,
            "duplicados": duplicates,
            "reglas_aplicadas": (
                "Uso exclusivo del modulo autoritativo (identificacion) para evitar "
                "multiplicar F_EXP por el numero de modulos. Deduplicacion por "
                "(DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio). "
                "SUM(F_EXP) -> volumen expandido de micronegocios por depto-anio."
            ),
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza EMICRON: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
