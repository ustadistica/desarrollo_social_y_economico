"""
Framework de validación de calidad de datos.

Usa Pandera para validación de esquemas y Great Expectations
para validaciones más complejas.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

try:
    import pandera as pa
    from pandera import Column, DataFrameSchema, Check
    PANDERA_AVAILABLE = True
except ImportError:
    PANDERA_AVAILABLE = False
    logging.warning("Pandera no disponible. Validaciones limitadas.")

logger = logging.getLogger(__name__)


class DataQualityChecker:
    """
    Clase principal para validación de calidad de datos.
    
    Soporta:
    - Validación de esquemas
    - Validación de rangos
    - Validación de integridad referencial
    - Detección de duplicados
    - Conteo de nulos
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializar checker de calidad.
        
        Parameters:
        - config_path: Ruta a archivo de configuración de validaciones
        """
        self.config_path = config_path
        self.results = {}
        self.errors = []
        self.warnings = []
    
    def validate_schema(
        self,
        df: pd.DataFrame,
        schema_name: str,
        expected_columns: List[str],
        required_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validar que el DataFrame tiene el esquema esperado.
        
        Parameters:
        - df: DataFrame a validar
        - schema_name: Nombre del esquema
        - expected_columns: Columnas esperadas
        - required_columns: Columnas obligatorias (subset de expected)
        
        Returns:
        - Dict con resultados de validación
        """
        result = {
            'valid': True,
            'schema_name': schema_name,
            'missing_columns': [],
            'extra_columns': [],
            'required_missing': [],
        }
        
        actual_columns = set(df.columns)
        expected_set = set(expected_columns)
        
        # Columnas faltantes
        missing = expected_set - actual_columns
        result['missing_columns'] = list(missing)
        
        if missing:
            result['valid'] = False
            self.warnings.append(f"Schema {schema_name}: faltan columnas {missing}")
        
        # Columnas extra
        extra = actual_columns - expected_set
        result['extra_columns'] = list(extra)
        
        # Columnas requeridas faltantes
        if required_columns:
            required_missing = set(required_columns) - actual_columns
            result['required_missing'] = list(required_missing)
            
            if required_missing:
                result['valid'] = False
                self.errors.append(f"Schema {schema_name}: faltan columnas requeridas {required_missing}")
        
        self.results[f'schema_{schema_name}'] = result
        
        return result
    
    def validate_nulls(
        self,
        df: pd.DataFrame,
        column: str,
        threshold_warning: float = 0.5,
        threshold_blocking: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Validar porcentaje de valores nulos en una columna.
        
        Parameters:
        - df: DataFrame
        - column: Columna a validar
        - threshold_warning: Umbral para warning (0-1)
        - threshold_blocking: Umbral para error blocking (0-1)
        
        Returns:
        - Dict con resultados
        """
        if column not in df.columns:
            return {
                'valid': False,
                'error': f'Columna {column} no existe',
            }
        
        null_count = df[column].isna().sum()
        null_pct = null_count / len(df) if len(df) > 0 else 0
        
        result = {
            'column': column,
            'null_count': int(null_count),
            'null_pct': float(null_pct),
            'valid': True,
            'level': 'ok',
        }
        
        if null_pct >= threshold_blocking:
            result['valid'] = False
            result['level'] = 'blocking'
            self.errors.append(f"Columna {column}: {null_pct:.1%} nulos (blocking)")
        elif null_pct >= threshold_warning:
            result['level'] = 'warning'
            self.warnings.append(f"Columna {column}: {null_pct:.1%} nulos (warning)")
        
        self.results[f'nulls_{column}'] = result
        
        return result
    
    def validate_uniqueness(
        self,
        df: pd.DataFrame,
        columns: List[str],
        must_be_unique: bool = True,
    ) -> Dict[str, Any]:
        """
        Validar unicidad de columnas (PK).
        
        Parameters:
        - df: DataFrame
        - columns: Columnas a verificar
        - must_be_unique: Si debe ser único
        
        Returns:
        - Dict con resultados
        """
        valid_cols = [c for c in columns if c in df.columns]
        
        if len(valid_cols) != len(columns):
            return {
                'valid': False,
                'error': f'Columnas faltantes: {set(columns) - set(valid_cols)}',
            }
        
        # Contar duplicados
        duplicates = df.duplicated(subset=valid_cols, keep=False)
        dup_count = duplicates.sum()
        dup_pct = dup_count / len(df) if len(df) > 0 else 0
        
        result = {
            'columns': columns,
            'duplicate_rows': int(dup_count),
            'duplicate_pct': float(dup_pct),
            'valid': True,
        }
        
        if must_be_unique and dup_count > 0:
            result['valid'] = False
            self.errors.append(f"Unicidad violada en {columns}: {dup_count} duplicados")
        
        self.results[f'uniqueness_{"_".join(columns)}'] = result
        
        return result
    
    def validate_referential_integrity(
        self,
        df_hechos: pd.DataFrame,
        df_dim: pd.DataFrame,
        fk_column: str,
        pk_column: str,
    ) -> Dict[str, Any]:
        """
        Validar integridad referencial entre hecho y dimensión.
        
        Parameters:
        - df_hechos: Tabla de hechos
        - df_dim: Tabla de dimensión
        - fk_column: Columna FK en hechos
        - pk_column: Columna PK en dimensión
        
        Returns:
        - Dict con resultados
        """
        if fk_column not in df_hechos.columns:
            return {
                'valid': False,
                'error': f'FK {fk_column} no existe en hechos',
            }
        
        if pk_column not in df_dim.columns:
            return {
                'valid': False,
                'error': f'PK {pk_column} no existe en dimensión',
            }
        
        # Obtener valores únicos
        fk_values = set(df_hechos[fk_column].dropna().unique())
        pk_values = set(df_dim[pk_column].unique())
        
        # Encontrar huérfanos
        orphan_values = fk_values - pk_values
        
        result = {
            'fk_column': fk_column,
            'pk_column': pk_column,
            'fk_unique_count': len(fk_values),
            'pk_unique_count': len(pk_values),
            'orphan_count': len(orphan_values),
            'orphan_values': list(orphan_values)[:10],  # Primeros 10
            'valid': len(orphan_values) == 0,
        }
        
        if not result['valid']:
            self.errors.append(f"Integridad referencial violada: {len(orphan_values)} huérfanos en {fk_column}")
        
        self.results[f'referential_{fk_column}_to_{pk_column}'] = result
        
        return result
    
    def validate_ranges(
        self,
        df: pd.DataFrame,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Validar que los valores están dentro de un rango.
        
        Parameters:
        - df: DataFrame
        - column: Columna a validar
        - min_value: Valor mínimo permitido
        - max_value: Valor máximo permitido
        
        Returns:
        - Dict con resultados
        """
        if column not in df.columns:
            return {
                'valid': False,
                'error': f'Columna {column} no existe',
            }
        
        # Convertir a numérico
        numeric = pd.to_numeric(df[column], errors='coerce')
        
        violations = []
        
        if min_value is not None:
            below_min = numeric < min_value
            violations.extend(['below_min'] * below_min.sum())
        
        if max_value is not None:
            above_max = numeric > max_value
            violations.extend(['above_max'] * above_max.sum())
        
        result = {
            'column': column,
            'min_allowed': min_value,
            'max_allowed': max_value,
            'actual_min': float(numeric.min()) if not numeric.isna().all() else None,
            'actual_max': float(numeric.max()) if not numeric.isna().all() else None,
            'violations': len(violations),
            'valid': len(violations) == 0,
        }
        
        if not result['valid']:
            self.warnings.append(f"Rango violado en {column}: {len(violations)} valores fuera de rango")
        
        self.results[f'range_{column}'] = result
        
        return result
    
    def validate_financial_coherence(
        self,
        df: pd.DataFrame,
        monto_contrato_col: str = 'monto_contrato',
        monto_ejecutado_col: str = 'monto_ejecutado',
        tolerance_pct: float = 0.05,
    ) -> Dict[str, Any]:
        """
        Validar coherencia financiera (ejecutado <= contratado).
        
        Parameters:
        - df: DataFrame
        - monto_contrato_col: Columna de monto contratado
        - monto_ejecutado_col: Columna de monto ejecutado
        - tolerance_pct: Tolerancia porcentual
        
        Returns:
        - Dict con resultados
        """
        if monto_contrato_col not in df.columns or monto_ejecutado_col not in df.columns:
            return {
                'valid': False,
                'error': 'Columnas de monto no existen',
            }
        
        contrato = pd.to_numeric(df[monto_contrato_col], errors='coerce').fillna(0)
        ejecutado = pd.to_numeric(df[monto_ejecutado_col], errors='coerce').fillna(0)
        
        # Permitir tolerancia
        max_ejecutado = contrato * (1 + tolerance_pct)
        
        incoherentes = ejecutado > max_ejecutado
        incoherente_count = incoherentes.sum()
        
        result = {
            'monto_contrato_col': monto_contrato_col,
            'monto_ejecutado_col': monto_ejecutado_col,
            'tolerance_pct': tolerance_pct,
            'incoherente_count': int(incoherente_count),
            'incoherente_pct': float(incoherente_count / len(df)) if len(df) > 0 else 0,
            'valid': incoherente_count == 0,
        }
        
        if not result['valid']:
            self.warnings.append(f"Coherencia financiera: {incoherente_count} contratos con ejecución > contrato")
        
        self.results['financial_coherence'] = result
        
        return result
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen de todas las validaciones.
        
        Returns:
        - Dict con resumen
        """
        total_validations = len(self.results)
        total_errors = len(self.errors)
        total_warnings = len(self.warnings)
        
        return {
            'total_validations': total_validations,
            'total_errors': total_errors,
            'total_warnings': total_warnings,
            'overall_valid': total_errors == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'timestamp': datetime.now().isoformat(),
        }


def run_quality_checks(
    df: pd.DataFrame,
    layer: str = 'bronze',
    schema_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Ejecutar validaciones de calidad según capa.
    
    Parameters:
    - df: DataFrame a validar
    - layer: Capa del pipeline ('bronze', 'plata', 'oro')
    - schema_name: Nombre del esquema esperado
    
    Returns:
    - Dict con resultados de validaciones
    """
    checker = DataQualityChecker()
    
    # Validaciones comunes
    checker.validate_nulls(df, 'divipola_municipio', threshold_warning=0.1)
    
    if layer == 'bronze':
        # Validaciones específicas de Bronce
        if '_ingestion_timestamp' in df.columns:
            checker.validate_nulls(df, '_ingestion_timestamp', threshold_blocking=0.9)
        
        if '_checksum_md5' in df.columns:
            checker.validate_nulls(df, '_checksum_md5', threshold_blocking=0.9)
    
    elif layer == 'plata':
        # Validaciones específicas de Plata
        if 'monto_contrato' in df.columns:
            checker.validate_ranges(df, 'monto_contrato', min_value=0)
        
        if 'ipm_total' in df.columns:
            checker.validate_ranges(df, 'ipm_total', min_value=0, max_value=1)
    
    elif layer == 'oro':
        # Validaciones específicas de Oro
        if 'monto_contrato' in df.columns and 'monto_ejecutado' in df.columns:
            checker.validate_financial_coherence(df)
    
    return checker.get_summary()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    df = pd.DataFrame({
        'divipola_municipio': ['11001', '05001', None],
        'monto_contrato': [1000000, 2000000, -100],
        'ipm_total': [0.25, 0.35, 1.5],
    })
    
    checker = DataQualityChecker()
    
    print("Validando nulls...")
    result = checker.validate_nulls(df, 'divipola_municipio')
    print(f"Nulls: {result}")
    
    print("\nValidando rangos...")
    result = checker.validate_ranges(df, 'monto_contrato', min_value=0)
    print(f"Rangos: {result}")
    
    print("\nResumen:")
    print(checker.get_summary())
