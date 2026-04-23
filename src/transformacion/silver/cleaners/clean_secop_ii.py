"""
Limpieza SECOP II (Capa Silver).

Normaliza nombres reales del CSV oficial. Mismo patrón que SECOP I:
produce agregado municipio-año y output transaccional homologado.

Mapeo de columnas reales:
  ID Contrato                      -> id_contrato
  divipola_key_mapped              -> divipola_key (si existe)
  Departamento + Ciudad            -> divipola_key (lookup por nombre)
  Fecha de Firma                   -> fecha_firma
  Valor del Contrato               -> valor_del_contrato
  Documento Proveedor              -> nit_contratista
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


_MONEDA_RE = re.compile(r"[^\d\-]")

def _parse_valor(s: pd.Series) -> pd.Series:
    """$1.234.567 -> 1234567 (elimina TODO lo no dígito; formato colombiano con punto como miles)."""
    s2 = s.astype(str).str.replace(_MONEDA_RE, "", regex=True).replace("", None)
    return pd.to_numeric(s2, errors="coerce").fillna(0.0)


def _parse_fecha(s: pd.Series) -> pd.Series:
    out = pd.to_datetime(s, errors="coerce")
    return out


def clean_secop_ii_data(bronze_path: Path, silver_path: Path, settings: Any) -> Dict[str, Any]:
    logger.info("Iniciando limpieza SECOP II (granular + agregado)...")
    out_agg = silver_path / "silver_secop_ii_agregado.parquet"
    out_txn = silver_path / "silver_secop_ii_transaccional.parquet"

    parquet_files = sorted(bronze_path.rglob("*.parquet"))
    if not parquet_files:
        logger.warning(f"No hay datos de SECOP II en Bronze ({bronze_path}).")
        return {
            "status": "failed",
            "error": "No hay datos de SECOP II en Bronze.",
            "pendiente": "Ingestar SECOP II desde CSV local.",
        }

    try:
        schema_ref = pq.read_schema(str(parquet_files[0]))
        idx = _build_col_index(schema_ref.names)

        c_uid = _pick(idx, ("ID_CONTRATO", "REFERENCIA_DEL_CONTRATO", "UID"))
        c_fecha = _pick(idx, ("FECHA_DE_FIRMA", "FECHA_DE_FIRMA_DEL_CONTRATO"))
        c_valor = _pick(idx, ("VALOR_DEL_CONTRATO", "VALOR_CONTRATO", "CUANTIA_CONTRATO"))
        c_nit = _pick(idx, ("DOCUMENTO_PROVEEDOR", "NIT_DEL_CONTRATISTA", "IDENTIFICACION_DEL_CONTRATISTA"))

        c_divi = _pick(idx, ("DIVIPOLA_KEY_MAPPED", "DIVIPOLA_KEY"))
        c_muni_txt = _pick(idx, ("CIUDAD", "MUNICIPIO", "MUNICIPIO_ENTIDAD"))
        c_dpto_txt = _pick(idx, ("DEPARTAMENTO", "DEPARTAMENTO_ENTIDAD"))
        c_muni_cod = _pick(idx, ("CODIGO_DE_LA_ENTIDAD", "CODIGO_ENTIDAD", "COD_MUNICIPIO"))

        if not c_divi and not c_muni_cod and not (c_muni_txt and c_dpto_txt):
            return {
                "status": "failed",
                "error": "SECOP II: sin columna DIVIPOLA ni (Departamento+Ciudad).",
                "columnas_disponibles": list(idx.values()),
            }

        faltantes = [n for n, col in [
            ("id_contrato", c_uid),
            ("fecha_firma", c_fecha),
            ("valor_contrato", c_valor),
            ("nit_contratista", c_nit),
        ] if col is None]
        if faltantes:
            return {
                "status": "failed",
                "error": f"SECOP II: columnas criticas no encontradas: {faltantes}",
                "columnas_disponibles": list(idx.values()),
            }

        cargar = list({c for c in [c_uid, c_fecha, c_valor, c_nit,
                                    c_divi, c_muni_txt, c_dpto_txt, c_muni_cod] if c})
        dataset = ds.dataset([str(f) for f in parquet_files], format="parquet")
        df = dataset.to_table(columns=cargar).to_pandas()

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
            dp = df[c_dpto_txt].fillna("").map(_norm)
            mp = df[c_muni_txt].fillna("").map(_norm)
            divipola = pd.Series([lookup.get((d, m)) for d, m in zip(dp, mp)], index=df.index)

        txn = pd.DataFrame({
            "id_contrato": df[c_uid].astype(str).str.strip(),
            "divipola_key": divipola,
            "fecha_firma": _parse_fecha(df[c_fecha]),
            "valor_del_contrato": _parse_valor(df[c_valor]),
            "nit_contratista": df[c_nit].astype(str).str.replace(r"\D", "", regex=True).str.strip(),
        })
        txn["anio_key"] = txn["fecha_firma"].dt.year.astype("Int64")
        txn["_fuente_origen"] = "SECOP_II"

        total = len(txn)
        txn = txn[txn["divipola_key"].fillna("").astype(str).str.match(r"^\d{5}$")]
        txn = txn[txn["anio_key"].notna()]
        txn = txn[txn["anio_key"].between(2018, 2030)]
        filtrados = total - len(txn)

        silver_path.mkdir(parents=True, exist_ok=True)
        txn_out = txn[["id_contrato", "divipola_key", "anio_key", "fecha_firma",
                       "valor_del_contrato", "nit_contratista", "_fuente_origen"]].copy()
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
        agg["_fuente_origen"] = "SECOP_II"
        agg.to_parquet(out_agg, engine="pyarrow", compression="snappy", index=False)

        logger.info(
            f"SECOP II: {len(txn_out):,} contratos validos, {filtrados:,} filtrados. "
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
                "Normalizacion nombres reales (ID Contrato, Fecha de Firma, Valor del "
                "Contrato, Documento Proveedor). DIVIPOLA desde divipola_key_mapped o "
                "lookup Departamento+Ciudad. NIT a solo digitos. "
                "Output transaccional para union posterior sin doble conteo."
            ),
        }
    except Exception as e:
        logger.error(f"Fallo en limpieza SECOP II: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
