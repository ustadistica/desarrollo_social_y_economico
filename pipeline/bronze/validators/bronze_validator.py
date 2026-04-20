"""
Módulo de Validación para Capa Bronze.

Este módulo implementa validaciones de esquema básicas para los datos ingeridos
en la capa Bronze, incluyendo:
- Conteo de registros
- Verificación de tipos de datos
- Detección de valores nulos críticos
- Validación de integridad referencial básica
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import json

logger = logging.getLogger(__name__)

# Configuración de validación
DEFAULT_NULL_THRESHOLD = 0.5  # 50% de nulos máximo permitido
CRITICAL_COLUMNS = ["divipola_municipio", "divipola_departamento"]  # Columnas críticas que no pueden ser nulas


class BronzeValidator:
    """
    Validador para datos de la capa Bronze.
    """

    def __init__(self, null_threshold: float = DEFAULT_NULL_THRESHOLD):
        """
        Inicializar validador.

        Parameters:
        - null_threshold: Umbral máximo de valores nulos permitidos (0-1)
        """
        self.null_threshold = null_threshold
        self.validation_results = {}

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        source_name: str,
        schema: Optional[Dict[str, str]] = None,
        critical_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validar un DataFrame completo.

        Parameters:
        - df: DataFrame a validar
        - source_name: Nombre de la fuente
        - schema: Schema esperado (columna: tipo)
        - critical_columns: Columnas críticas que no pueden tener nulos

        Returns:
        - Dict con resultados de validación
        """
        logger.info(f"Validando DataFrame de {source_name}...")

        results = {
            "source": source_name,
            "timestamp": datetime.now().isoformat(),
            "valid": True,
            "checks": {},
            "errors": [],
            "warnings": [],
        }

        # 1. Conteo de registros
        results["checks"]["row_count"] = self._check_row_count(df)

        # 2. Conteo de columnas
        results["checks"]["column_count"] = self._check_column_count(df)

        # 3. Valores nulos
        results["checks"]["null_check"] = self._check_null_values(
            df,
            critical_columns or CRITICAL_COLUMNS,
        )

        # 4. Tipos de datos
        if schema:
            results["checks"]["schema_check"] = self._check_schema(df, schema)

        # 5. Duplicados
        results["checks"]["duplicate_check"] = self._check_duplicates(df)

        # 6. Estadísticas básicas
        results["checks"]["statistics"] = self._get_statistics(df)

        # Determinar si es válido
        has_errors = any(
            check.get("status") == "error"
            for check in results["checks"].values()
        )

        results["valid"] = not has_errors
        results["errors"] = [
            check.get("message")
            for check in results["checks"].values()
            if check.get("status") == "error"
        ]
        results["warnings"] = [
            check.get("message")
            for check in results["checks"].values()
            if check.get("status") == "warning"
        ]

        # Log resultados
        self._log_validation_results(results)

        return results

    def _check_row_count(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verificar conteo de registros.

        Parameters:
        - df: DataFrame a validar

        Returns:
        - Dict con resultado del check
        """
        row_count = len(df)

        if row_count == 0:
            return {
                "status": "error",
                "message": "DataFrame vacío (0 registros)",
                "value": 0,
            }
        elif row_count < 100:
            return {
                "status": "warning",
                "message": f"Pocos registros: {row_count}",
                "value": row_count,
            }
        else:
            return {
                "status": "success",
                "message": f"Registros: {row_count}",
                "value": row_count,
            }

    def _check_column_count(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verificar conteo de columnas.

        Parameters:
        - df: DataFrame a validar

        Returns:
        - Dict con resultado del check
        """
        column_count = len(df.columns)

        if column_count == 0:
            return {
                "status": "error",
                "message": "DataFrame sin columnas",
                "value": 0,
            }
        else:
            return {
                "status": "success",
                "message": f"Columnas: {column_count}",
                "value": column_count,
                "columns": list(df.columns),
            }

    def _check_null_values(
        self,
        df: pd.DataFrame,
        critical_columns: List[str],
    ) -> Dict[str, Any]:
        """
        Verificar valores nulos.

        Parameters:
        - df: DataFrame a validar
        - critical_columns: Columnas críticas que no pueden tener nulos

        Returns:
        - Dict con resultado del check
        """
        null_summary = {}
        errors = []
        warnings = []

        # Verificar columnas críticas
        for col in critical_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                null_pct = null_count / len(df) if len(df) > 0 else 0

                null_summary[col] = {
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct * 100, 2),
                }

                if null_count > 0:
                    errors.append(f"Columna crítica '{col}' tiene {null_count} nulos ({null_pct:.2%})")

        # Verificar todas las columnas para warning
        for col in df.columns:
            if col not in critical_columns:
                null_count = df[col].isnull().sum()
                null_pct = null_count / len(df) if len(df) > 0 else 0

                if null_pct > self.null_threshold:
                    warnings.append(f"Columna '{col}' tiene {null_pct:.2%} nulos")

                null_summary[col] = {
                    "null_count": int(null_count),
                    "null_percentage": round(null_pct * 100, 2),
                }

        if errors:
            return {
                "status": "error",
                "message": "; ".join(errors),
                "null_summary": null_summary,
            }
        elif warnings:
            return {
                "status": "warning",
                "message": "; ".join(warnings),
                "null_summary": null_summary,
            }
        else:
            return {
                "status": "success",
                "message": "No hay valores nulos críticos",
                "null_summary": null_summary,
            }

    def _check_schema(
        self,
        df: pd.DataFrame,
        schema: Dict[str, str],
    ) -> Dict[str, Any]:
        """
        Verificar schema de datos.

        Parameters:
        - df: DataFrame a validar
        - schema: Schema esperado (columna: tipo)

        Returns:
        - Dict con resultado del check
        """
        errors = []
        warnings = []

        # Verificar columnas esperadas
        columnas_esperadas = set(schema.keys())
        columnas_reales = set(df.columns)

        columnas_faltantes = columnas_esperadas - columnas_reales
        columnas_extra = columnas_reales - columnas_esperadas

        if columnas_faltantes:
            errors.append(f"Columnas faltantes: {columnas_faltantes}")

        if columnas_extra:
            warnings.append(f"Columnas adicionales: {columnas_extra}")

        # Verificar tipos de datos
        type_mismatches = []
        for col, tipo_esperado in schema.items():
            if col in df.columns:
                tipo_real = str(df[col].dtype)
                if tipo_real != tipo_esperado:
                    type_mismatches.append(f"{col}: {tipo_real} != {tipo_esperado}")

        if type_mismatches:
            warnings.append(f"Tipos no coinciden: {type_mismatches}")

        if errors:
            return {
                "status": "error",
                "message": "; ".join(errors),
                "schema_match": False,
            }
        elif warnings:
            return {
                "status": "warning",
                "message": "; ".join(warnings),
                "schema_match": True,
            }
        else:
            return {
                "status": "success",
                "message": "Schema válido",
                "schema_match": True,
            }

    def _check_duplicates(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Verificar registros duplicados.

        Parameters:
        - df: DataFrame a validar

        Returns:
        - Dict con resultado del check
        """
        # Verificar duplicados completos
        duplicate_count = df.duplicated().sum()
        duplicate_pct = duplicate_count / len(df) if len(df) > 0 else 0

        if duplicate_count > 0:
            return {
                "status": "warning",
                "message": f"{duplicate_count} registros duplicados ({duplicate_pct:.2%})",
                "duplicate_count": int(duplicate_count),
                "duplicate_percentage": round(duplicate_pct * 100, 2),
            }
        else:
            return {
                "status": "success",
                "message": "No hay registros duplicados",
                "duplicate_count": 0,
            }

    def _get_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Obtener estadísticas básicas del DataFrame.

        Parameters:
        - df: DataFrame a validar

        Returns:
        - Dict con estadísticas
        """
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage_bytes": df.memory_usage(deep=True).sum(),
            "column_types": {col: str(df[col].dtype) for col in df.columns},
        }

        # Estadísticas para columnas numéricas
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()

        return stats

    def _log_validation_results(self, results: Dict[str, Any]):
        """
        Registrar resultados de validación en el log.

        Parameters:
        - results: Resultados de validación
        """
        status = results.get("status", "unknown")
        source = results.get("source", "unknown")

        if results.get("valid"):
            logger.info(f"Validación {source}: SUCCESS")
        else:
            logger.error(f"Validación {source}: FAILED")

        for check_name, check_result in results.get("checks", {}).items():
            status = check_result.get("status", "unknown")
            message = check_result.get("message", "")
            logger.info(f"  {check_name}: {status} - {message}")

        for error in results.get("errors", []):
            logger.error(f"  ERROR: {error}")

        for warning in results.get("warnings", []):
            logger.warning(f"  WARNING: {warning}")


def validate_bronze_file(
    file_path: Path,
    source_name: str,
    schema: Optional[Dict[str, str]] = None,
    critical_columns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validar archivo Parquet de la capa Bronze.

    Parameters:
    - file_path: Ruta al archivo Parquet
    - source_name: Nombre de la fuente
    - schema: Schema esperado (columna: tipo)
    - critical_columns: Columnas críticas que no pueden tener nulos

    Returns:
    - Dict con resultados de validación
    """
    logger.info(f"Validando archivo Bronze: {file_path}")

    if not file_path.exists():
        return {
            "status": "error",
            "message": f"Archivo no encontrado: {file_path}",
            "valid": False,
        }

    try:
        # Leer archivo Parquet
        df = pd.read_parquet(file_path)

        # Validar
        validator = BronzeValidator()
        results = validator.validate_dataframe(
            df=df,
            source_name=source_name,
            schema=schema,
            critical_columns=critical_columns,
        )

        results["file_path"] = str(file_path)

        return results

    except Exception as e:
        return {
            "status": "error",
            "message": f"Error leyendo archivo: {str(e)}",
            "valid": False,
        }


def validate_bronze_folder(
    folder_path: Path,
    source_name: str,
    schema: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Validar todos los archivos Parquet en una carpeta Bronze.

    Parameters:
    - folder_path: Ruta a la carpeta Bronze
    - source_name: Nombre de la fuente
    - schema: Schema esperado (columna: tipo)

    Returns:
    - Dict con resultados de validación combinados
    """
    logger.info(f"Validando carpeta Bronze: {folder_path}")

    if not folder_path.exists():
        return {
            "status": "error",
            "message": f"Carpeta no encontrada: {folder_path}",
            "valid": False,
        }

    # Buscar archivos Parquet
    parquet_files = list(folder_path.glob("**/*.parquet"))

    if not parquet_files:
        return {
            "status": "warning",
            "message": "No hay archivos Parquet en la carpeta",
            "valid": False,
        }

    # Validar cada archivo
    results = {
        "source": source_name,
        "folder": str(folder_path),
        "timestamp": datetime.now().isoformat(),
        "files": {},
        "summary": {
            "total_files": len(parquet_files),
            "valid_files": 0,
            "invalid_files": 0,
            "total_rows": 0,
        },
    }

    for pf in parquet_files:
        file_result = validate_bronze_file(
            file_path=pf,
            source_name=source_name,
            schema=schema,
        )
        results["files"][pf.name] = file_result

        if file_result.get("valid"):
            results["summary"]["valid_files"] += 1
        else:
            results["summary"]["invalid_files"] += 1

        # Sumar filas
        row_count = file_result.get("checks", {}).get("row_count", {}).get("value", 0)
        results["summary"]["total_rows"] += row_count

    # Determinar validez general
    results["valid"] = results["summary"]["invalid_files"] == 0

    return results


def generate_validation_report(
    validation_results: Dict[str, Any],
    output_path: Optional[Path] = None,
) -> str:
    """
    Generar reporte de validación en formato texto.

    Parameters:
    - validation_results: Resultados de validación
    - output_path: Ruta de salida para el reporte (None = retornar string)

    Returns:
    - Reporte en formato string
    """
    lines = [
        "=" * 60,
        "REPORTE DE VALIDACIÓN - CAPA BRONZE",
        "=" * 60,
        f"Fuente: {validation_results.get('source', 'N/A')}",
        f"Timestamp: {validation_results.get('timestamp', 'N/A')}",
        f"Estado: {'VÁLIDO' if validation_results.get('valid') else 'INVÁLIDO'}",
        "",
        "-" * 60,
        "CHECKS REALIZADOS:",
        "-" * 60,
    ]

    if "files" in validation_results and "summary" in validation_results:
        # Es un reporte de carpeta
        summary = validation_results["summary"]
        lines.append(f"  Total Archivos Parquet: {summary.get('total_files', 0)}")
        lines.append(f"  Archivos Válidos:       {summary.get('valid_files', 0)}")
        lines.append(f"  Archivos Inválidos:     {summary.get('invalid_files', 0)}")
        lines.append(f"  Total de Registros:     {summary.get('total_rows', 0):,}")
        
        # Opcional: enumerar errores si los hay en subarchivos
        if summary.get('invalid_files', 0) > 0:
            lines.append("\n  [!] ERRORES EN ARCHIVOS:")
            for fname, fresult in validation_results["files"].items():
                if not fresult.get("valid"):
                    for msg in fresult.get("errors", ["Error desconocido"]):
                        lines.append(f"   -> {fname}: {msg}")
    else:
        # Es reporte de archivo único
        for check_name, check_result in validation_results.get("checks", {}).items():
            status = check_result.get("status", "unknown").upper()
            message = check_result.get("message", "")
            lines.append(f"  [{status}] {check_name}: {message}")

    lines.append("")
    lines.append("=" * 60)

    report = "\n".join(lines)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info(f"Reporte guardado en: {output_path}")

    return report


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Ejemplo: validar archivo Parquet
    from config.settings import settings

    # Validar SECOP II
    secop_path = settings.get_bronze_path("secop_ii")
    if secop_path.exists():
        results = validate_bronze_folder(
            folder_path=secop_path,
            source_name="secop_ii",
        )
        logger.info(f"Resultados SECOP II: {results}")

        # Generar reporte
        report = generate_validation_report(results)
        logger.info(f"Reporte:\n{report}")
