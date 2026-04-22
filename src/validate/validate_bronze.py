"""
Validaciones específicas para capa Bronce.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import hashlib

logger = logging.getLogger(__name__)


def validate_bronze_layer(
    bronze_path: Optional[Path] = None,
    fuentes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validar todos los archivos en capa Bronce.
    
    Parameters:
    - bronze_path: Ruta base de capa Bronce
    - fuentes: Lista de fuentes a validar (default: todas)
    
    Returns:
    - Dict con resultados de validación
    """
    from src.config.settings import settings
    
    if bronze_path is None:
        bronze_path = settings.BRONZE_PATH
    
    if fuentes is None:
        fuentes = ['dane_cnpv', 'dane_cenu', 'secop_ii', 'terridata', 'dane_geoportal']
    
    resultados = {}
    
    for fuente in fuentes:
        logger.info(f"Validando Bronce: {fuente}")
        resultados[fuente] = _validate_fuente_bronce(bronze_path / fuente, fuente)
    
    # Resumen
    total_archivos = sum(r.get('archivos_validados', 0) for r in resultados.values())
    total_errores = sum(r.get('errores', 0) for r in resultados.values())
    
    return {
        'status': 'error' if total_errores > 0 else 'success',
        'fuentes_validadas': len(fuentes),
        'total_archivos': total_archivos,
        'total_errores': total_errores,
        'resultados_por_fuente': resultados,
        'timestamp': datetime.now().isoformat(),
    }


def _validate_fuente_bronce(fuente_path: Path, fuente: str) -> Dict[str, Any]:
    """
    Validar archivos de una fuente específica.
    
    Parameters:
    - fuente_path: Ruta de la fuente
    - fuente: Nombre de la fuente
    
    Returns:
    - Dict con resultados
    """
    resultados = {
        'archivos_validados': 0,
        'errores': 0,
        'warnings': 0,
        'detalles': [],
    }
    
    if not fuente_path.exists():
        resultados['errores'] += 1
        resultados['detalles'].append({
            'nivel': 'error',
            'mensaje': f'Directorio no existe: {fuente_path}',
        })
        return resultados
    
    # Buscar archivos Parquet
    parquet_files = list(fuente_path.rglob('*.parquet'))
    
    if not parquet_files:
        resultados['warnings'] += 1
        resultados['detalles'].append({
            'nivel': 'warning',
            'mensaje': f'No se encontraron archivos Parquet en {fuente_path}',
        })
        return resultados
    
    for archivo in parquet_files:
        resultado_archivo = _validate_parquet_file(archivo, fuente)
        resultados['archivos_validados'] += 1
        
        if resultado_archivo['errores'] > 0:
            resultados['errores'] += resultado_archivo['errores']
        
        if resultado_archivo['warnings'] > 0:
            resultados['warnings'] += resultado_archivo['warnings']
        
        resultados['detalles'].append({
            'archivo': str(archivo),
            **resultado_archivo,
        })
    
    return resultados


def _validate_parquet_file(archivo_path: Path, fuente: str) -> Dict[str, Any]:
    """
    Validar un archivo Parquet individual.
    
    Validaciones:
    - Checksum MD5 (si existe en metadatos)
    - Record count dentro de rangos esperados
    - Columnas obligatorias presentes
    - Null ratio en columnas clave
    
    Parameters:
    - archivo_path: Ruta del archivo
    - fuente: Nombre de la fuente
    
    Returns:
    - Dict con resultados
    """
    resultado = {
        'errores': 0,
        'warnings': 0,
        'checksum_valid': None,
        'record_count': 0,
        'columnas': [],
        'null_ratios': {},
    }
    
    try:
        # Leer archivo
        df = pd.read_parquet(archivo_path)
        resultado['record_count'] = len(df)
        resultado['columnas'] = list(df.columns)
        
        # Validar columnas de metadatos
        metadata_cols = ['_ingestion_timestamp', '_source', '_checksum_md5']
        for col in metadata_cols:
            if col in df.columns:
                null_ratio = df[col].isna().mean()
                resultado['null_ratios'][col] = null_ratio
                
                if null_ratio > 0.9:
                    resultado['errores'] += 1
                elif null_ratio > 0.5:
                    resultado['warnings'] += 1
            else:
                resultado['warnings'] += 1  # Metadata opcional
        
        # Validar checksum si existe
        if '_checksum_md5' in df.columns and len(df) > 0:
            checksum_guardado = df['_checksum_md5'].iloc[0]
            checksum_calculado = _calculate_checksum(df)
            
            if checksum_guardado and checksum_calculado:
                resultado['checksum_valid'] = checksum_guardado == checksum_calculado
                
                if not resultado['checksum_valid']:
                    resultado['errores'] += 1
        
        # Validar record count (rangos esperados por fuente)
        rangos_esperados = _get_expected_record_ranges(fuente)
        if rangos_esperados:
            min_expected, max_expected = rangos_esperados
            
            if len(df) < min_expected:
                resultado['warnings'] += 1
        
        # Validar null ratio en columnas clave
        columnas_clave = _get_key_columns(fuente)
        for col in columnas_clave:
            if col in df.columns:
                null_ratio = df[col].isna().mean()
                resultado['null_ratios'][col] = null_ratio
                
                if null_ratio > 0.9:
                    resultado['errores'] += 1
                elif null_ratio > 0.5:
                    resultado['warnings'] += 1
        
    except Exception as e:
        resultado['errores'] += 1
        resultado['error_detalle'] = str(e)
    
    return resultado


def _calculate_checksum(df: pd.DataFrame) -> Optional[str]:
    """
    Calcular checksum MD5 de un DataFrame.
    
    Parameters:
    - df: DataFrame
    
    Returns:
    - Hash MD5 o None si falla
    """
    try:
        # Excluir columnas de metadatos del cálculo
        data_cols = [c for c in df.columns if not c.startswith('_')]
        return hashlib.md5(df[data_cols].to_json().encode()).hexdigest()
    except Exception:
        return None


def _get_expected_record_ranges(fuente: str) -> tuple:
    """
    Obtener rangos esperados de registros por fuente.
    
    Parameters:
    - fuente: Nombre de la fuente
    
    Returns:
    - Tupla (min, max) o None si no hay rango definido
    """
    rangos = {
        'dane_cnpv': (1100, 1200),  # ~1102 municipios
        'dane_cenu': (1000, 50000),  # Varía según nivel de agregación
        'secop_ii': (1, None),  # Sin límite superior
        'terridata': (1100, 1200),
        'dane_geoportal': (1100, 1102),
    }
    
    return rangos.get(fuente)


def _get_key_columns(fuente: str) -> List[str]:
    """
    Obtener columnas clave por fuente.
    
    Parameters:
    - fuente: Nombre de la fuente
    
    Returns:
    - Lista de columnas clave
    """
    columnas = {
        'dane_cnpv': ['divipola_municipio', 'ipm_total'],
        'dane_cenu': ['divipola_municipio', 'codigo_ciiu'],
        'secop_ii': ['id_contrato', 'divipola_municipio', 'monto_contrato'],
        'terridata': ['divipola_municipio'],
        'dane_geoportal': ['divipola', 'geometry'] if 'geometry' in ['divipola'] else ['divipola'],
    }
    
    return columnas.get(fuente, [])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resultado = validate_bronze_layer()
    print(f"Resultado: {resultado}")
