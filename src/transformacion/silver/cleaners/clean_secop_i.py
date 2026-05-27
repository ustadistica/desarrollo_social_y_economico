"""
Limpieza SECOP I (Capa Silver).

Normaliza nombres de columnas reales del CSV oficial (con espacios/tildes) a un
schema canonico. Produce dos outputs:

  - silver_secop_i_agregado.parquet     : municipio-año con COUNT(DISTINCT nit)
  - silver_secop_i_transaccional.parquet: granularidad contrato, homologado con
                                          SECOP II para permitir COUNT(DISTINCT
                                          nit) unificado en Gold sin doble
                                          conteo entre ambas plataformas.

Mapeo de columnas reales:
  UID                              -> id_contrato
  divipola_key_mapped              -> divipola_key (si el parser lo inyectó)
  Municipio Entidad + Dpto Entidad -> divipola_key (lookup por nombre)
  Fecha de Firma del Contrato      -> fecha_firma
  Cuantia Contrato ($1.234.567)    -> valor_del_contrato
  Identificacion del Contratista   -> nit_contratista
  Orden Entidad                    -> orden_entidad
"""

import logging
import datetime
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.dataset as ds

logger = logging.getLogger(__name__)


def _norm(s: str) -> str:
    """Normaliza a upper snake, sin tildes, sin espacios duplicados."""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_").upper()
    return s


def _build_col_index(cols: list) -> dict:
    return {_norm(c): c for c in cols}


def _pick(idx: dict, candidates_norm: tuple) -> str | None:
    for c in candidates_norm:
        if c in idx:
            return idx[c]
    return None


def _classify_orden_entidad(value: object) -> str:
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


_MONEDA_RE = re.compile(r"[^\d\-]")

def _parse_cuantia(s: pd.Series) -> pd.Series:
    """$1.234.567,89 -> 1234567 (elimina TODO lo no dígito; formato colombiano)."""
    return pd.to_numeric(
        s.astype(str).str.replace(_MONEDA_RE, "", regex=True).replace("", None),
        errors="coerce",
    ).fillna(0.0)


def _parse_fecha(s: pd.Series) -> pd.Series:
    """Intenta DD/MM/YYYY y luego ISO como fallback."""
    out = pd.to_datetime(s, errors="coerce", format="%d/%m/%Y")
    mask = out.isna()
    if mask.any():
        out2 = pd.to_datetime(s[mask], errors="coerce")
        out.loc[mask] = out2
    return out


def clean_secop_i_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando limpieza SECOP I (granular + agregado)...")
    out_agg = silver_path / "silver_secop_i_agregado.parquet"
    out_txn = silver_path / "silver_secop_i_transaccional.parquet"

    parquet_files = sorted(bronze_path.rglob("*.parquet"))
    if not parquet_files:
        logger.warning(f"No hay datos de SECOP I en Bronze ({bronze_path}).")
        return {
            "status": "failed",
            "error": "No hay datos de SECOP I en Bronze.",
            "pendiente": "Ingestar SECOP I desde CSV local.",
        }

    try:
        schema_ref = pq.read_schema(str(parquet_files[0]))
        idx = _build_col_index(schema_ref.names)

        c_uid = _pick(idx, ("UID", "ID_CONTRATO"))
        c_fecha = _pick(idx, ("FECHA_DE_FIRMA_DEL_CONTRATO", "FECHA_DE_FIRMA", "FECHA_FIRMA"))
        c_cuantia = _pick(idx, ("CUANTIA_CONTRATO", "VALOR_CONTRATO_CON_ADICIONES", "VALOR_DEL_CONTRATO"))
        c_nit = _pick(idx, ("IDENTIFICACION_DEL_CONTRATISTA", "NIT_DEL_CONTRATISTA", "DOCUMENTO_PROVEEDOR"))
        c_orden = _pick(idx, ("ORDEN_ENTIDAD", "ORDEN"))

        # Preferir divipola_key_mapped si existe, si no, tomar Municipio Entidad + Departamento
        c_divi = _pick(idx, ("DIVIPOLA_KEY_MAPPED", "DIVIPOLA_KEY"))
        c_muni_txt = _pick(idx, ("MUNICIPIO_ENTIDAD", "CIUDAD", "MUNICIPIO"))
        c_dpto_txt = _pick(idx, ("DEPARTAMENTO_ENTIDAD", "DEPARTAMENTO"))
        c_muni_cod = _pick(idx, ("CODIGO_MUNICIPIO_ENTIDAD", "COD_MUNICIPIO"))

        if not c_divi and not c_muni_cod and not (c_muni_txt and c_dpto_txt):
            return {
                "status": "failed",
                "error": "SECOP I: no hay columna DIVIPOLA ni (Municipio+Departamento) para mapear geografia.",
                "columnas_disponibles": list(idx.values()),
            }

        faltantes = [n for n, col in [
            ("id_contrato (UID)", c_uid),
            ("fecha_firma", c_fecha),
            ("valor_contrato", c_cuantia),
            ("nit_contratista", c_nit),
        ] if col is None]
        if faltantes:
            return {
                "status": "failed",
                "error": f"SECOP I: columnas criticas no encontradas: {faltantes}",
                "columnas_disponibles": list(idx.values()),
            }

        cargar = list({c for c in [c_uid, c_fecha, c_cuantia, c_nit, c_orden,
                                    c_divi, c_muni_txt, c_dpto_txt, c_muni_cod] if c})
        dataset = ds.dataset([str(f) for f in parquet_files], format="parquet")
        df = dataset.to_table(columns=cargar).to_pandas()

        # DIVIPOLA: usar key_mapped si existe, si no intentar lookup por nombre
        if c_divi:
            divipola = df[c_divi].astype(str).str.strip().str.zfill(5)
        elif c_muni_cod:
            divipola = df[c_muni_cod].astype(str).str.strip().str.zfill(5)
        else:
            from src.utils.divipola_catalog import DIVIPOLA_COMPLETO
            lookup = {
                (_norm(info["nombre_departamento"]), _norm(info["nombre_municipio"])): k
                for k, info in DIVIPOLA_COMPLETO.items()
            }
            # SECOP I usa "BOGOTa D.C." tanto para dpto como mpio
            # _norm("BOGOTa D.C.") = "BOGOTA_D_C", pero catalogo tiene dpto "BOGOTA" y mpio "BOGOTA_D_C"
            _DEPT_ALIASES = {
                "BOGOTA_D_C": "BOGOTA",
                "DISTRITO_CAPITAL_DE_BOGOTA": "BOGOTA",
                "DC": "BOGOTA",
            }
            _MUNI_ALIASES = {
                "BOGOTA": "BOGOTA_D_C",
            }
            def _resolve(d: str, m: str):
                d_n = _DEPT_ALIASES.get(d, d)
                m_n = _MUNI_ALIASES.get(m, m)
                return lookup.get((d_n, m_n)) or lookup.get((d_n, m)) or lookup.get((d, m_n)) or lookup.get((d, m))
            dp = df[c_dpto_txt].fillna("").map(_norm)
            mp = df[c_muni_txt].fillna("").map(_norm)
            divipola = pd.Series([_resolve(d, m) for d, m in zip(dp, mp)], index=df.index)

        txn = pd.DataFrame({
            "id_contrato": df[c_uid].astype(str).str.strip(),
            "divipola_key": divipola,
            "fecha_firma": _parse_fecha(df[c_fecha]),
            "valor_del_contrato": _parse_cuantia(df[c_cuantia]),
            "nit_contratista": df[c_nit].astype(str).str.replace(r"\D", "", regex=True).str.strip(),
        })
        if c_orden:
            txn["orden_entidad"] = df[c_orden].map(_classify_orden_entidad)
        else:
            txn["orden_entidad"] = "NO_DEFINIDO"
        txn["anio_key"] = txn["fecha_firma"].dt.year.astype("Int64")
        txn["_fuente_origen"] = "SECOP_I"

        # Calidad
        total = len(txn)
        txn = txn[txn["divipola_key"].fillna("").astype(str).str.match(r"^\d{5}$")]
        txn = txn[txn["anio_key"].notna()]
        txn = txn[txn["anio_key"].between(2018, 2030)]
        filtrados = total - len(txn)

        silver_path.mkdir(parents=True, exist_ok=True)
        txn_out = txn[["id_contrato", "divipola_key", "anio_key", "fecha_firma",
                       "valor_del_contrato", "nit_contratista", "orden_entidad",
                       "_fuente_origen"]].copy()
        txn_out["anio_key"] = txn_out["anio_key"].astype(int)
        txn_out.to_parquet(out_txn, engine="pyarrow", compression="snappy", index=False)

        agg = (
            txn_out.groupby(["divipola_key", "anio_key"], as_index=False)
            .agg(
                cantidad_procesos_adjudicados=("id_contrato", "nunique"),
                inversion_total_monto=("valor_del_contrato", "sum"),
                proveedores_unicos=("nit_contratista", "nunique"),
            )
        )
        agg["_cleaning_timestamp"] = datetime.datetime.now().isoformat()
        agg["_fuente_origen"] = "SECOP_I"
        agg.to_parquet(out_agg, engine="pyarrow", compression="snappy", index=False)

        logger.info(
            f"SECOP I: {len(txn_out):,} contratos validos, {filtrados:,} filtrados. "
            f"Agregado municipio-anio: {len(agg):,} filas."
        )
        return {
            "status": "success",
            "archivo_agregado": str(out_agg),
            "archivo_transaccional": str(out_txn),
            "registros": len(agg),
            "contratos_transaccionales": len(txn_out),
            "registros_filtrados_calidad": int(filtrados),
            "nulls": agg[["divipola_key", "anio_key"]].isnull().sum().to_dict(),
            "duplicados": int(agg.duplicated(subset=["divipola_key", "anio_key"]).sum()),
            "reglas_aplicadas": (
                "Normalizacion nombres de columnas reales (UID, Cuantia Contrato, "
                "Fecha de Firma del Contrato, Identificacion del Contratista). "
                "DIVIPOLA desde divipola_key_mapped o lookup Municipio+Departamento. "
                "Limpieza de formato moneda colombiano. NIT a solo digitos. "
                "Orden Entidad normalizado para analisis HHI. "
                "Agregado con COUNT(DISTINCT nit) intra-plataforma y output "
                "transaccional para union posterior con SECOP II."
            ),
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza SECOP I: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
