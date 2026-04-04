r"""
Parser para EMICRON 2024 - DANE (Archivo CSV Local).

Este módulo implementa la lectura del Módulo de características del micronegocio
con detección automática de encoding (latin-1 o utf-8) y manejo de separadores.

Fuente: C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\Módulo de características del micronegocio.csv
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import hashlib
import chardet

logger = logging.getLogger(__name__)

# Ruta al archivo CSV local leída desde el entorno unificado (.env)
from config.settings import settings
EMICRON_CSV_PATH = settings.EMICRON_CSV_PATH

# Encodings comunes a probar (en orden de prioridad)
COMMON_ENCODINGS = ["utf-8", "latin-1", "cp1252", "iso-8859-1", "utf-8-sig"]

# Separadores comunes a probar
COMMON_SEPARATORS = [",", ";", "\t", "|"]

# Schema esperado para validación (ajustar según estructura real del CSV)
EMICRON_SCHEMA = {
    "codigo_dane_municipio": "string",
    "nombre_municipio": "string",
    "codigo_dane_departamento": "string",
    "nombre_departamento": "string",
    "total_micronegocios": "int64",
    "micronegocios_formales": "int64",
    "micronegocios_informales": "int64",
    "economia_popular_unidades": "int64",
    "economia_popular_empleo": "int64",
    "codigo_ciiu": "string",
    "descripcion_ciiu": "string",
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
    Parsear archivo CSV de EMICRON 2024 y convertirlo en DataFrame.

    Parameters:
    - csv_path: Ruta al directorio EMICRON 2024 o al archivo CSV (default: EMICRON_CSV_PATH)
    - output_path: Ruta de salida para archivo Parquet (default: capa Bronze)
    - detect_encoding: Si True, detecta automáticamente el encoding
    - detect_separator: Si True, detecta automáticamente el separador
    - validate_schema: Si True, valida el schema antes de guardar
    - chunk_size: Tamaño de chunk para procesamiento (None = todo en memoria)

    Returns:
    - Dict con metadata de extracción y ruta del archivo

    Raises:
    - FileNotFoundError: Si no existe el archivo CSV
    - UnicodeDecodeError: Si no se puede decodificar el archivo
    """
    logger.info("Iniciando parser de EMICRON 2024 (CSV)")

    # Determinar ruta de entrada
    if csv_path is None:
        csv_path = EMICRON_CSV_PATH

    # Verificar existencia del archivo o directorio
    if not csv_path.exists():
        error_msg = f"Ruta no encontrada: {csv_path}"
        logger.error(error_msg)
        return {
            "status": "error",
            "archivo": None,
            "error": error_msg,
        }

    # Si es directorio, buscar todos los CSV e iterar
    if csv_path.is_dir():
        logger.info(f"Ruta es un directorio, buscando CSVs en: {csv_path}")
        csv_files = list(csv_path.rglob("*.csv"))
        if not csv_files:
            return {"status": "error", "error": "No se encontraron archivos CSV en el directorio"}
            
        resultados = []
        for file in csv_files:
            logger.info(f"Procesando sub-archivo: {file.name}")
            resultado = _procesar_un_archivo(
                file, output_path, detect_encoding, detect_separator, validate_schema, chunk_size
            )
            resultados.append(resultado)
        return {"status": "success", "archivos_procesados": len(resultados), "detalles": resultados}
    else:
        # Procesar archivo único
        return _procesar_un_archivo(
            csv_path, output_path, detect_encoding, detect_separator, validate_schema, chunk_size
        )

def _procesar_un_archivo(
    csv_path: Path,
    output_path: Optional[Path],
    detect_encoding: bool,
    detect_separator: bool,
    validate_schema: bool,
    chunk_size: Optional[int],
) -> Dict[str, Any]:
    logger.info(f"Leyendo archivo CSV: {csv_path}")

    try:
        # Detectar encoding si se solicita
        encoding = None
        if detect_encoding:
            encoding = _detect_encoding(csv_path, sample_size=50000)
            logger.info(f"Encoding detectado: {encoding}")
        else:
            encoding = "utf-8"

        # Detectar separador si se solicita
        separator = None
        if detect_separator:
            separator = _detect_separator(csv_path, encoding)
            logger.info(f"Separador detectado: '{separator}'")
        else:
            separator = ","

        # Leer CSV
        df = _read_csv_to_dataframe(csv_path, encoding, separator, chunk_size)

        if df.empty:
            logger.warning("El archivo CSV no contiene datos procesables")
            return {
                "status": "warning",
                "archivo": None,
                "mensaje": "Dataset vacío en el archivo CSV",
            }

        # Agregar metadatos de ingesta
        df = _add_ingestion_metadata(df)

        # Validar schema si se solicita (ignorado para raw directory scan sin estricto fail)
        if validate_schema:
            validation_result = _validate_schema(df, EMICRON_SCHEMA)
            if not validation_result["valid"]:
                logger.warning(f"Validación de schema: {validation_result['message']}")

        # Determinar ruta de salida
        if output_path is None:
            from config.settings import settings
            output_path = settings.get_bronze_path("emicron")

        output_path.mkdir(parents=True, exist_ok=True)

        # Usar nombre del archivo de origen limpio para no sobrescribir, más fecha de ingesta
        safe_name = csv_path.stem.replace(" ", "_").replace(",", "").replace("-", "_").lower()
        import re
        safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)
        
        ingestion_date = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_salida = output_path / f"emicron_{safe_name}_{ingestion_date}_raw.parquet"

        # Guardar en Parquet
        df.to_parquet(
            archivo_salida,
            index=False,
            compression="snappy",
        )

        logger.info(f"Extracción completada: {len(df)} registros guardados en {archivo_salida}")

        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(df),
            "columnas": list(df.columns),
            "fecha_extraccion": datetime.now().isoformat(),
            "fuente": f"emicron_2024_{safe_name}",
            "tipo": "CSV_LOCAL",
            "encoding_detectado": encoding,
            "separador_detectado": separator,
        }

    except UnicodeDecodeError as e:
        error_msg = f"Error de decodificación en {csv_path.name}: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "archivo": None, "error": error_msg}
    except Exception as e:
        error_msg = f"Error en parser de EMICRON CSV ({csv_path.name}): {str(e)}"
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
    logger.info("Detectando encoding del archivo...")

    try:
        # Leer muestra del archivo
        with open(file_path, "rb") as f:
            raw_data = f.read(sample_size)

        # Analizar con chardet
        result = chardet.detect(raw_data)

        if result and result["confidence"] > 0.7:
            encoding = result["encoding"]
            confidence = result["confidence"]
            logger.info(f"Encoding detectado: {encoding} (confianza: {confidence:.2%})")

            # Mapear encodings comunes
            if encoding and encoding.lower() in ["utf-8", "ascii"]:
                return "utf-8"
            elif encoding and encoding.lower() in ["latin-1", "iso-8859-1", "cp1252"]:
                return "latin-1"
            else:
                return encoding if encoding else "utf-8"
        else:
            logger.warning("No se pudo detectar encoding con confianza, probando utf-8 primero")
            return "utf-8"

    except Exception as e:
        logger.warning(f"Error detectando encoding: {str(e)}, usando utf-8 por defecto")
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
    logger.info("Detectando separador del CSV...")

    try:
        # Leer primeras líneas
        with open(file_path, "r", encoding=encoding) as f:
            lines = [f.readline() for _ in range(sample_lines)]

        # Contar ocurrencias de cada separador
        separator_counts = {sep: 0 for sep in COMMON_SEPARATORS}

        for line in lines:
            for sep in COMMON_SEPARATORS:
                count = line.count(sep)
                if count > 0:
                    separator_counts[sep] += count

        # Encontrar el separador más consistente
        best_separator = max(separator_counts, key=separator_counts.get)

        if separator_counts[best_separator] == 0:
            logger.warning("No se encontró separador común, usando ',' por defecto")
            return ","

        logger.info(f"Separador más probable: '{best_separator}'")
        return best_separator

    except Exception as e:
        logger.warning(f"Error detectando separador: {str(e)}, usando ',' por defecto")
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
    logger.info("Leyendo archivo CSV...")

    if chunk_size is None:
        # Leer todo el archivo en memoria
        try:
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                engine="python",  # Más robusto para CSVs complejos
                on_bad_lines="warn",  # Manejar líneas problemáticas
                skipinitialspace=True,  # Ignorar espacios después del separador
            )
            logger.info(f"Archivo leído: {len(df)} registros, {len(df.columns)} columnas")
            return df

        except Exception as e:
            logger.warning(f"Error leyendo CSV: {str(e)}, intentando con opciones alternativas")

            # Intentar con opciones más permisivas
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                sep=separator,
                engine="python",
                on_bad_lines="skip",
                skipinitialspace=True,
                dtype=str,  # Leer todo como string inicialmente
            )
            logger.info(f"Archivo leído (modo permisivo): {len(df)} registros")
            return df

    else:
        # Leer en chunks para archivos grandes
        chunks = []
        chunk_count = 0

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
            chunk_count += 1
            logger.info(f"  Chunk {chunk_count} leído: {len(chunk)} registros")

        # Combinar todos los chunks
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Total combinado: {len(df)} registros")
        return df


def _add_ingestion_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta al DataFrame.

    Parameters:
    - df: DataFrame original

    Returns:
    - DataFrame con metadatos agregados
    """
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_source"] = "emicron"
    df["_source_version"] = "EMICRON_2024"
    df["_extraction_method"] = "CSV_LOCAL_PARSER"

    checksum = hashlib.md5(df.to_json().encode()).hexdigest()
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

    # Verificar columnas esperadas
    columnas_esperadas = set(schema.keys())
    columnas_reales = set(df.columns)

    columnas_faltantes = columnas_esperadas - columnas_reales
    columnas_extra = columnas_reales - columnas_esperadas

    if columnas_faltantes:
        advertencias.append(f"Columnas faltantes: {columnas_faltantes}")

    if columnas_extra:
        advertencias.append(f"Columnas adicionales: {columnas_extra}")

    # Verificar tipos de datos
    for col, tipo_esperado in schema.items():
        if col in df.columns:
            tipo_real = str(df[col].dtype)
            if tipo_real != tipo_esperado:
                # Intentar conversión
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
    if csv_path is None:
        csv_path = EMICRON_CSV_PATH

    if not csv_path.exists():
        return {"error": f"Archivo no encontrado: {csv_path}"}

    logger.info(f"Inspeccionando estructura CSV: {csv_path}")

    try:
        # Detectar encoding y separador si no se proporcionan
        if encoding is None:
            encoding = _detect_encoding(csv_path)

        if separator is None:
            separator = _detect_separator(csv_path, encoding)

        # Leer primeras filas
        df_preview = pd.read_csv(
            csv_path,
            encoding=encoding,
            sep=separator,
            engine="python",
            nrows=preview_rows,
        )

        # Obtener información del archivo
        import os
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

    # Inspeccionar estructura primero
    logger.info("Inspeccionando estructura del CSV...")
    estructura = inspect_csv_structure()
    logger.info(f"Estructura: {estructura}")

    # Ejecutar parser
    logger.info("Ejecutando parser...")
    resultado = parse_emicron_csv()
    logger.info(f"Resultado: {resultado}")
