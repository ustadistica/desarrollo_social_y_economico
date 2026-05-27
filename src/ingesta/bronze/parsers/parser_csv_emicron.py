r"""
Parser para EMICRON - Encuesta de Micronegocios DANE (Multi-año 2019-2024).

Este módulo implementa la ingesta de todos los módulos de la EMICRON para
múltiples años (2019-2024), detectando automáticamente encoding y separador.

Cada año tiene ~11-14 subcarpetas de módulos (TIC, identificación, ventas, etc.)
con archivos CSV, DTA y SAV. Se extraen únicamente los CSV.

Estructura esperada en disco:
    Datos/
    ├── EMICRON 2019/
    │   ├── Modulo de caracteristicas del micronegocio/
    │   │   └── Módulo de características del micronegocio.csv
    │   ├── Modulo de ventas o ingresos/
    │   │   └── Módulo de ventas o ingresos.csv
    │   └── ...
    ├── EMICRON 2020/
    │   └── ...
    └── EMICRON 2024/
        ├── BDATOS-EMICRON-Modulo_Caracteristicas_Micronegocios-2024/
        │   └── Módulo de características del micronegocio.csv
        └── ...
"""

import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import hashlib
import chardet

logger = logging.getLogger(__name__)

# Importar configuración
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

try:
    from src.config.settings import Settings
except ImportError:
    from src.config.settings import Settings

# Encodings comunes a probar (en orden de prioridad)
COMMON_ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1", "utf-8-sig"]

# Separadores comunes a probar
COMMON_SEPARATORS = [",", ";", "\t", "|"]

# Schema estandarizado de trazabilidad para Bronze (los campos raw varían por módulo)
EMICRON_SCHEMA = {
    "_ingestion_timestamp": "string",
    "_source": "string",
    "_source_version": "string",
    "_extraction_method": "string",
    "_checksum_md5": "string",
}


def parse_emicron_csv(
    csv_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    detect_encoding: bool = True,
    detect_separator: bool = True,
    validate_schema: bool = True,
    chunk_size: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Parsear archivos CSV de EMICRON (multi-año 2019-2024) y convertirlos en Parquet.

    Si csv_path apunta a un directorio que contiene carpetas "EMICRON YYYY",
    se procesan TODOS los años encontrados. Si apunta a una carpeta de un solo
    año (e.g., "EMICRON 2024"), se procesa solo ese año.

    Cada CSV se guarda como un Parquet independiente en:
        data/bronze/emicron/<año>/emicron_<modulo>_<año>_raw.parquet

    Parameters:
    - csv_path: Ruta al directorio base o a una carpeta EMICRON de un año
    - output_path: Ruta de salida para archivos Parquet (default: capa Bronze / emicron)
    - detect_encoding: Si True, detecta automáticamente el encoding
    - detect_separator: Si True, detecta automáticamente el separador
    - validate_schema: Si True, valida el schema antes de guardar
    - chunk_size: Tamaño de chunk para procesamiento (None = todo en memoria)

    Returns:
    - Dict con metadata de extracción y ruta del archivo
    """
    settings = Settings()

    # Determinar ruta de entrada
    if csv_path is None:
        csv_path = settings.EMICRON_CSV_PATH

    if not csv_path.exists():
        error_msg = f"Ruta EMICRON no encontrada: {csv_path}"
        logger.error(error_msg)
        logger.info(
            "Asegúrate de configurar EMICRON_CSV_PATH en tu archivo .env "
            "o de colocar las carpetas EMICRON en ../Datos/"
        )
        return {"status": "error", "error": error_msg}

    # Determinar ruta de salida
    if output_path is None:
        output_path = settings.BRONZE_PATH / "emicron"
    output_path.mkdir(parents=True, exist_ok=True)

    # Descubrir qué años hay disponibles
    emicron_years = _discover_years(csv_path)

    if not emicron_years:
        # Quizás csv_path ES una carpeta de un solo año (o directorio con CSVs)
        year = _extract_year_from_path(csv_path)
        if year:
            emicron_years = [(year, csv_path)]
        else:
            # Fallback: tratar como directorio plano con CSVs
            logger.info(f"Procesando como directorio único con CSVs: {csv_path}")
            return _process_single_directory(
                csv_path, output_path, None,
                detect_encoding, detect_separator, validate_schema, chunk_size
            )

    logger.info(f"Años EMICRON encontrados: {[y for y, _ in emicron_years]}")

    # Procesar cada año
    resultados_por_anio = {}
    total_csvs = 0
    total_registros = 0

    for year, year_path in emicron_years:
        logger.info("=" * 50)
        logger.info(f"EMICRON {year} - Procesando: {year_path}")
        logger.info("=" * 50)

        year_output = output_path / str(year)
        year_output.mkdir(parents=True, exist_ok=True)

        result = _process_single_directory(
            year_path, year_output, year,
            detect_encoding, detect_separator, validate_schema, chunk_size
        )

        resultados_por_anio[year] = result

        if result.get("status") == "success":
            total_csvs += result.get("archivos_procesados", 0)
            total_registros += result.get("total_registros", 0)

    return {
        "status": "success",
        "archivos_procesados": total_csvs,
        "registros": total_registros,
        "anios_procesados": [y for y, _ in emicron_years],
        "detalles_por_anio": resultados_por_anio,
        "fuente": "emicron",
        "tipo": "CSV_LOCAL",
    }


def _discover_years(base_path: Path) -> List[Tuple[int, Path]]:
    """Descubrir carpetas EMICRON YYYY dentro del directorio base."""
    years = []
    if base_path.is_dir():
        for child in sorted(base_path.iterdir()):
            if child.is_dir():
                match = re.match(r"EMICRON\s+(\d{4})", child.name)
                if match:
                    years.append((int(match.group(1)), child))
    return years


def _extract_year_from_path(path: Path) -> Optional[int]:
    """Extraer año del nombre de una carpeta EMICRON."""
    match = re.search(r"EMICRON\s+(\d{4})", path.name)
    if match:
        return int(match.group(1))
    return None


def _process_single_directory(
    dir_path: Path,
    output_path: Path,
    year: Optional[int],
    detect_encoding: bool,
    detect_separator: bool,
    validate_schema: bool,
    chunk_size: Optional[int],
) -> Dict[str, Any]:
    """Procesar todos los CSVs encontrados recursivamente en un directorio."""
    csv_files = list(dir_path.rglob("*.csv"))
    if not csv_files:
        logger.warning(f"No se encontraron archivos CSV en: {dir_path}")
        return {"status": "warning", "error": "No se encontraron archivos CSV"}

    logger.info(f"Encontrados {len(csv_files)} archivos CSV en {dir_path.name}")

    resultados = []
    total_registros = 0

    for file in csv_files:
        logger.info(f"  → Procesando: {file.relative_to(dir_path)}")
        resultado = _procesar_un_archivo(
            file, output_path, year,
            detect_encoding, detect_separator, validate_schema, chunk_size
        )
        resultados.append(resultado)
        if resultado.get("status") == "success":
            total_registros += resultado.get("registros", 0)

    return {
        "status": "success",
        "archivos_procesados": len(resultados),
        "total_registros": total_registros,
        "detalles": resultados,
    }


def _procesar_un_archivo(
    csv_path: Path,
    output_path: Path,
    year: Optional[int],
    detect_encoding: bool,
    detect_separator: bool,
    validate_schema: bool,
    chunk_size: Optional[int],
) -> Dict[str, Any]:
    """Procesar un solo archivo CSV de EMICRON a Parquet."""
    logger.info(f"Leyendo archivo CSV: {csv_path.name}")

    try:
        # Detectar encoding
        encoding = _detect_encoding(csv_path) if detect_encoding else "utf-8"
        logger.info(f"  Encoding: {encoding}")

        # Detectar separador
        separator = _detect_separator(csv_path, encoding) if detect_separator else ","
        logger.info(f"  Separador: '{separator}'")

        # Leer CSV
        df = _read_csv_to_dataframe(csv_path, encoding, separator, chunk_size)

        if df.empty:
            logger.warning(f"  Archivo CSV vacío: {csv_path.name}")
            return {"status": "warning", "archivo": None, "mensaje": "Dataset vacío"}

        # Agregar metadatos de ingesta
        year_label = str(year) if year else "desconocido"
        df = _add_ingestion_metadata(df, year_label)

        # Validar schema (solo warning, no bloquea)
        if validate_schema:
            validation_result = _validate_schema(df, EMICRON_SCHEMA)
            if not validation_result["valid"]:
                logger.warning(f"  Validación schema: {validation_result['message']}")

        output_path.mkdir(parents=True, exist_ok=True)

        # Nombre seguro para el archivo de salida
        safe_name = csv_path.stem.replace(" ", "_").replace(",", "").replace("-", "_").lower()
        safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)

        archivo_salida = output_path / f"emicron_{safe_name}_{year_label}_raw.parquet"

        # Guardar en Parquet
        df.to_parquet(archivo_salida, index=False, compression="snappy")

        logger.info(f"  ✓ {len(df):,} registros → {archivo_salida.name}")

        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(df),
            "columnas": list(df.columns),
            "fuente": f"emicron_{year_label}_{safe_name}",
            "tipo": "CSV_LOCAL",
            "encoding_detectado": encoding,
            "separador_detectado": separator,
        }

    except UnicodeDecodeError as e:
        error_msg = f"Error de decodificación en {csv_path.name}: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "archivo": None, "error": error_msg}
    except Exception as e:
        error_msg = f"Error en parser EMICRON ({csv_path.name}): {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "archivo": None, "error": error_msg}


def _detect_encoding(file_path: Path, sample_size: int = 100000) -> str:
    """
    Detectar encoding del archivo usando chardet.

    Parameters:
    - file_path: Ruta al archivo
    - sample_size: Tamaño de muestra para análisis

    Returns:
    - Encoding detectado (default: utf-8 si falla)
    """
    try:
        with open(file_path, "rb") as f:
            raw_data = f.read(sample_size)

        result = chardet.detect(raw_data)

        if result and result["confidence"] > 0.7:
            encoding = result["encoding"]
            if encoding and encoding.lower() in ["utf-8", "ascii"]:
                return "utf-8"
            elif encoding and encoding.lower() in ["latin-1", "iso-8859-1", "cp1252"]:
                return "latin-1"
            else:
                return encoding if encoding else "utf-8"
        else:
            return "utf-8"

    except Exception as e:
        logger.warning(f"Error detectando encoding: {str(e)}, usando utf-8")
        return "utf-8"


def _detect_separator(file_path: Path, encoding: str, sample_lines: int = 10) -> str:
    """
    Detectar separador del archivo CSV analizando las primeras líneas.

    Parameters:
    - file_path: Ruta al archivo
    - encoding: Encoding del archivo
    - sample_lines: Número de líneas a analizar

    Returns:
    - Separador detectado (default: ,)
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            lines = [f.readline() for _ in range(sample_lines)]

        separator_counts = {sep: 0 for sep in COMMON_SEPARATORS}

        for line in lines:
            for sep in COMMON_SEPARATORS:
                count = line.count(sep)
                if count > 0:
                    separator_counts[sep] += count

        best_separator = max(separator_counts, key=separator_counts.get)

        if separator_counts[best_separator] == 0:
            return ","

        return best_separator

    except Exception as e:
        logger.warning(f"Error detectando separador: {str(e)}, usando ','")
        return ","


def _read_csv_to_dataframe(
    file_path: Path,
    encoding: str,
    separator: str,
    chunk_size: Optional[int] = None,
) -> pd.DataFrame:
    """
    Leer archivo CSV y convertirlo en DataFrame.

    Parameters:
    - file_path: Ruta al archivo
    - encoding: Encoding del archivo
    - separator: Separador del CSV
    - chunk_size: Tamaño de chunk (None = todo en memoria)

    Returns:
    - DataFrame con los datos leídos
    """
    if chunk_size is None:
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                engine="python",
                on_bad_lines="warn",
                skipinitialspace=True,
            )
            return df
        except Exception:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                engine="python",
                on_bad_lines="skip",
                skipinitialspace=True,
                dtype=str,
            )
            return df
    else:
        chunks = []
        for chunk in pd.read_csv(
            file_path,
            encoding=encoding,
            sep=separator,
            engine="python",
            chunksize=chunk_size,
            on_bad_lines="warn",
            skipinitialspace=True,
        ):
            chunks.append(chunk)

        df = pd.concat(chunks, ignore_index=True)
        return df


def _add_ingestion_metadata(df: pd.DataFrame, year_label: str) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta al DataFrame.

    Parameters:
    - df: DataFrame original
    - year_label: Año de la encuesta (e.g., "2019", "2024")

    Returns:
    - DataFrame con metadatos agregados
    """
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_source"] = "emicron"
    df["_source_version"] = f"EMICRON_{year_label}"
    df["_extraction_method"] = "CSV_LOCAL_PARSER"
    df["_emicron_year"] = year_label

    checksum = hashlib.md5(str(len(df)).encode()).hexdigest()
    df["_checksum_md5"] = checksum

    return df


def _validate_schema(df: pd.DataFrame, schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Validar que el DataFrame cumple con el schema esperado.

    Parameters:
    - df: DataFrame a validar
    - schema: Schema esperado (columna: tipo)

    Returns:
    - Dict con resultado de validación
    """
    errores = []
    advertencias = []

    columnas_esperadas = set(schema.keys())
    columnas_reales = set(df.columns)

    columnas_faltantes = columnas_esperadas - columnas_reales
    columnas_extra = columnas_reales - columnas_esperadas

    if columnas_faltantes:
        advertencias.append(f"Columnas faltantes: {columnas_faltantes}")

    if columnas_extra:
        advertencias.append(f"Columnas adicionales: {columnas_extra}")

    for col, tipo_esperado in schema.items():
        if col in df.columns:
            tipo_real = str(df[col].dtype)
            if tipo_real != tipo_esperado:
                try:
                    if tipo_esperado == "float64":
                        df[col] = df[col].astype("float64")
                    elif tipo_esperado == "int64":
                        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                    elif tipo_esperado == "string":
                        df[col] = df[col].astype(str)
                except Exception:
                    errores.append(f"Columna {col}: tipo {tipo_real} no compatible con {tipo_esperado}")

    es_valido = len(errores) == 0

    return {
        "valid": es_valido,
        "errores": errores,
        "advertencias": advertencias,
        "message": "Schema válido" if es_valido else "; ".join(errores),
    }


def inspect_csv_structure(
    csv_path: Optional[Path] = None,
    encoding: Optional[str] = None,
    separator: Optional[str] = None,
    preview_rows: int = 5,
) -> Dict[str, Any]:
    """
    Inspeccionar la estructura del archivo CSV para debugging.

    Parameters:
    - csv_path: Ruta al archivo CSV
    - encoding: Encoding (None = detectar automáticamente)
    - separator: Separador (None = detectar automáticamente)
    - preview_rows: Número de filas para previsualizar

    Returns:
    - Dict con información de la estructura CSV
    """
    settings = Settings()

    if csv_path is None:
        csv_path = settings.EMICRON_CSV_PATH

    if not csv_path.exists():
        return {"error": f"Archivo no encontrado: {csv_path}"}

    try:
        if encoding is None:
            encoding = _detect_encoding(csv_path)
        if separator is None:
            separator = _detect_separator(csv_path, encoding)

        df_preview = pd.read_csv(
            csv_path,
            encoding=encoding,
            sep=separator,
            engine="python",
            nrows=preview_rows,
        )

        file_size = os.path.getsize(csv_path)

        estructura = {
            "archivo": str(csv_path),
            "tamaño_bytes": file_size,
            "tamaño_mb": round(file_size / (1024 * 1024), 2),
            "encoding": encoding,
            "separador": separator,
            "columnas": list(df_preview.columns),
            "num_columnas": len(df_preview.columns),
            "preview": df_preview.to_dict(orient="records"),
            "tipos_datos": {col: str(df_preview[col].dtype) for col in df_preview.columns},
        }

        return estructura

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Ejecutando parser EMICRON multi-año...")
    resultado = parse_emicron_csv()
    logger.info(f"Resultado: {resultado.get('status')}")
    if resultado.get("anios_procesados"):
        logger.info(f"Años: {resultado['anios_procesados']}")
    logger.info(f"Total archivos: {resultado.get('archivos_procesados', 0)}")
    logger.info(f"Total registros: {resultado.get('registros', 0)}")
