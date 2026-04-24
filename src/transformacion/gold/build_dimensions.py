"""
Construcción de dimensiones del modelo estrella (Capa Gold).

- dim_tiempo: atributos descriptivos por año.
- dim_territorio: se arma a partir del catálogo oficial DIVIPOLA
  (pipeline/utils/divipola_catalog.py), que trae nombres REALES. Se
  enriquece con los códigos efectivamente presentes en los facts Silver
  (por si aparecen agregados departamentales tipo 05000 o municipios no
  listados), y para estos últimos se toma el nombre del departamento
  desde el mismo catálogo — nunca se generan nombres sintéticos tipo
  'Municipio 11001'.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Set
import datetime
import pandas as pd

from src.utils.divipola_catalog import DIVIPOLA_COMPLETO

logger = logging.getLogger(__name__)


def build_dim_tiempo(gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo dimension: dim_tiempo")
    out_file = gold_path / "dim_tiempo.parquet"
    anios = list(range(2018, 2030))
    df = pd.DataFrame({"anio_key": anios})
    df["es_anio_electoral_presidencial"] = df["anio_key"].isin([2018, 2022, 2026])
    df["es_anio_electoral_regional"] = df["anio_key"].isin([2019, 2023, 2027])
    df["es_pandemia"] = df["anio_key"].isin([2020, 2021])
    df["_creation_timestamp"] = datetime.datetime.now().isoformat()
    df.to_parquet(out_file, engine="pyarrow", index=False)
    logger.info(f"dim_tiempo: {len(df)} registros ({df['anio_key'].min()}-{df['anio_key'].max()})")
    return {
        "status": "success",
        "archivo": str(out_file),
        "registros": len(df),
        "nulls": df.isnull().sum().to_dict(),
        "duplicados": int(df.duplicated("anio_key").sum()),
    }


def _indice_departamentos(catalogo: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
    """Construye {cod_depto_2d: {nombre_departamento, region}} desde el catálogo."""
    idx: Dict[str, Dict[str, str]] = {}
    for _, info in catalogo.items():
        cod = info.get("divipola_departamento", "")
        if cod and cod not in idx:
            idx[cod] = {
                "nombre_departamento": info.get("nombre_departamento", ""),
                "region": info.get("region", ""),
            }
    return idx


def _codigos_en_silver(silver_path: Path) -> Set[str]:
    """Devuelve todos los divipola_key que aparecen en tablas Silver."""
    codigos: Set[str] = set()
    if not silver_path.exists():
        return codigos
    for f in silver_path.rglob("*.parquet"):
        try:
            sch = pd.read_parquet(f, columns=None, engine="pyarrow").columns
        except Exception:
            continue
        if "divipola_key" in sch:
            try:
                s = pd.read_parquet(f, columns=["divipola_key"])["divipola_key"]
                codigos.update(
                    s.dropna().astype(str).str.strip().str.zfill(5).unique().tolist()
                )
            except Exception as e:
                logger.warning(f"  No se pudo leer divipola_key en {f.name}: {e}")
    return codigos


def build_dim_territorio(silver_path: Path, gold_path: Path) -> Dict[str, Any]:
    logger.info("Construyendo dimension: dim_territorio (catalogo DIVIPOLA + enriquecimiento Silver)")
    out_file = gold_path / "dim_territorio.parquet"

    # 1) Base: catálogo oficial
    registros = []
    for divipola_key, info in DIVIPOLA_COMPLETO.items():
        registros.append({
            "divipola_key": str(divipola_key).zfill(5),
            "nombre_municipio_referencia": info.get("nombre_municipio", ""),
            "nombre_departamento": info.get("nombre_departamento", ""),
            "divipola_departamento": info.get("divipola_departamento", str(divipola_key)[:2]),
            "region": info.get("region", ""),
            "categoria_municipio": info.get("categoria", ""),
            "fuente_nombre": "catalogo_divipola_oficial",
        })
    df = pd.DataFrame(registros)
    logger.info(f"  Catalogo DIVIPOLA base: {len(df)} municipios")

    # 2) Enriquecer con códigos reales presentes en Silver
    idx_dept = _indice_departamentos(DIVIPOLA_COMPLETO)
    codigos_silver = _codigos_en_silver(silver_path)
    conocidos = set(df["divipola_key"])
    nuevos = []
    for key in codigos_silver:
        if key in conocidos:
            continue
        cod_d = key[:2]
        ddata = idx_dept.get(cod_d, {})
        nombre_depto = ddata.get("nombre_departamento") or f"Departamento {cod_d}"
        region = ddata.get("region") or ""
        # Si es agregado departamental (XX000), marcar explícitamente;
        # si es un municipio no listado, usar nombre departamental como fallback
        # honesto — sin inventar nombres de municipio.
        if key.endswith("000"):
            nombre_muni = f"Agregado departamental ({nombre_depto})"
            categoria = "Agregado departamental"
            fuente = "construido_agregado_depto"
        else:
            nombre_muni = f"Municipio sin catalogar ({nombre_depto})"
            categoria = "Sin catalogar"
            fuente = "silver_sin_catalogar"
        nuevos.append({
            "divipola_key": key,
            "nombre_municipio_referencia": nombre_muni,
            "nombre_departamento": nombre_depto,
            "divipola_departamento": cod_d,
            "region": region,
            "categoria_municipio": categoria,
            "fuente_nombre": fuente,
        })

    if nuevos:
        df = pd.concat([df, pd.DataFrame(nuevos)], ignore_index=True)
        logger.info(f"  + {len(nuevos)} codigos Silver enriquecidos (agregados/no catalogados)")

    df = df.drop_duplicates(subset=["divipola_key"], keep="first")
    df["_creation_timestamp"] = datetime.datetime.now().isoformat()
    df.to_parquet(out_file, engine="pyarrow", index=False)

    logger.info(f"dim_territorio final: {len(df)} registros")

    return {
        "status": "success",
        "archivo": str(out_file),
        "registros": len(df),
        "municipios_catalogados": int((df["fuente_nombre"] == "catalogo_divipola_oficial").sum()),
        "agregados_departamentales": int((df["fuente_nombre"] == "construido_agregado_depto").sum()),
        "sin_catalogar": int((df["fuente_nombre"] == "silver_sin_catalogar").sum()),
        "codigos_silver_detectados": len(codigos_silver),
        "nulls": df.isnull().sum().to_dict(),
        "duplicados": int(df.duplicated("divipola_key").sum()),
    }
