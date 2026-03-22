"""
Procesamiento de archivos descargados manualmente del DANE.

Este script convierte los archivos Excel/CSV descargados manualmente
de los portales del DANE a formato Parquet para la capa Bronce.

Instrucciones previas:
1. Descargar archivos de los portales del DANE o datos.gov.co
2. Guardar en: datos/bronze/[fuente]/raw/
3. Ejecutar este script
"""

import logging
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Agregar el path del pipeline
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuración de fuentes a procesar
FUENTES_CONFIG = {
    'cnpv': {
        'nombre': 'CNPV 2018',
        'raw_folder': 'dane_cnpv/raw',
        'output_folder': 'dane_cnpv',
        'output_file': 'cnpv_data.parquet',
        'columnas_esperadas': [
            'divipola', 'divipola_municipio', 'codigo_dane', 'dpmp',  # DIVIPOLA (cualquiera de estas)
            'municipio', 'nombre_municipio',  # Municipio
            'departamento', 'nombre_departamento',  # Departamento
            'ipm', 'ipm_total',  # IPM
            'nbi', 'nbi_total',  # NBI
            'poblacion', 'poblacion_total',  # Población
            'pobreza', 'pobreza_monetaria',  # Pobreza monetaria
            'deficit', 'deficit_habitacional',  # Déficit habitacional
        ],
    },
    'ipm': {
        'nombre': 'IPM Municipal',
        'raw_folder': 'dane_ipm/raw',
        'output_folder': 'dane_ipm',
        'output_file': 'ipm_data.parquet',
        'columnas_esperadas': [
            'divipola', 'divipola_municipio', 'codigo_dane',
            'municipio', 'nombre_municipio',
            'departamento', 'nombre_departamento',
            'ipm', 'ipm_total', 'ipm_educacion', 'ipm_ninez', 
            'ipm_trabajo', 'ipm_salud',
        ],
    },
    'nbi': {
        'nombre': 'NBI Municipal',
        'raw_folder': 'dane_nbi/raw',
        'output_folder': 'dane_nbi',
        'output_file': 'nbi_data.parquet',
        'columnas_esperadas': [
            'divipola', 'divipola_municipio', 'codigo_dane',
            'municipio', 'nombre_municipio',
            'departamento', 'nombre_departamento',
            'nbi', 'nbi_total', 'nbi_vivienda', 'nbi_servicios',
        ],
    },
    'emicron': {
        'nombre': 'EMICRON - Micronegocios',
        'raw_folder': 'dane_emicron/raw',
        'output_folder': 'dane_emicron',
        'output_file': 'emicron_data.parquet',
        'columnas_esperadas': [
            'divipola', 'divipola_municipio', 'codigo_dane',
            'municipio', 'nombre_municipio',
            'departamento', 'nombre_departamento',
            'ciiu', 'codigo_ciiu', 'actividad_economica',
            'micronegocios', 'total_micronegocios',
            'economia_popular', 'economia_popular_unidades',
            'vigencia', 'anio', 'año', 'year',
        ],
    },
    'cenu': {
        'nombre': 'CENU - Unidades Económicas',
        'raw_folder': 'dane_cenu/raw',
        'output_folder': 'dane_cenu',
        'output_file': 'cenu_data.parquet',
        'columnas_esperadas': [
            'divipola', 'divipola_municipio', 'codigo_dane',
            'municipio', 'nombre_municipio',
            'departamento', 'nombre_departamento',
            'ciiu', 'codigo_ciiu',
            'unidades', 'total_unidades', 'unidades_economicas',
            'vigencia', 'anio', 'año',
        ],
    },
}


def process_all_downloads() -> Dict[str, Any]:
    """
    Procesar todos los archivos descargados manualmente.

    Returns:
    - Dict con resultados del procesamiento
    """
    logger.info("=" * 80)
    logger.info("PROCESAMIENTO DE ARCHIVOS DESCARGADOS MANUALMENTE")
    logger.info("=" * 80)

    resultados = {}
    exitosos = 0
    fallidos = 0
    no_encontrados = 0

    for fuente_key, config in FUENTES_CONFIG.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"FUENTE: {config['nombre']} ({fuente_key})")
        logger.info(f"{'='*80}")

        # Buscar archivos en carpeta raw
        raw_path = settings.BRONZE_PATH / config['raw_folder']
        
        if not raw_path.exists():
            logger.warning(f"  ❌ Carpeta raw no existe: {raw_path}")
            logger.info(f"     Crear carpeta y guardar archivo descargado allí")
            resultados[fuente_key] = {
                'status': 'folder_not_found',
                'ruta_esperada': str(raw_path),
            }
            no_encontrados += 1
            continue

        # Buscar archivos Excel o CSV
        archivos_encontrados = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            archivos_encontrados.extend(list(raw_path.glob(ext)))

        if not archivos_encontrados:
            logger.warning(f"  ❌ No se encontraron archivos en: {raw_path}")
            logger.info(f"     Formatos buscados: .xlsx, .xls, .csv")
            resultados[fuente_key] = {
                'status': 'no_files_found',
                'ruta_esperada': str(raw_path),
            }
            no_encontrados += 1
            continue

        logger.info(f"  Archivos encontrados: {[a.name for a in archivos_encontrados]}")

        # Procesar el primer archivo encontrado (asumimos que es el más reciente)
        archivo = max(archivos_encontrados, key=lambda p: p.stat().st_mtime)
        logger.info(f"  Procesando: {archivo.name}")

        try:
            resultado = process_single_file(
                archivo=archivo,
                config=config,
            )

            if resultado['status'] == 'success':
                logger.info(f"  ✅ {config['nombre']} procesado exitosamente")
                logger.info(f"     Registros: {resultado.get('registros', 0):,}")
                logger.info(f"     Archivo: {resultado['archivo']}")
                exitosos += 1
            else:
                logger.warning(f"  ⚠️ {config['nombre']} - {resultado.get('mensaje', '')}")
                fallidos += 1

            resultados[fuente_key] = resultado

        except Exception as e:
            logger.error(f"  ❌ ERROR: {config['nombre']} - {str(e)}")
            resultados[fuente_key] = {
                'status': 'error',
                'error': str(e),
            }
            fallidos += 1

    # Resumen final
    logger.info(f"\n{'='*80}")
    logger.info("RESUMEN DE PROCESAMIENTO")
    logger.info(f"{'='*80}")
    logger.info(f"Total fuentes: {len(FUENTES_CONFIG)}")
    logger.info(f"Exitosos: {exitosos}")
    logger.info(f"Fallidos: {fallidos}")
    logger.info(f"No encontrados: {no_encontrados}")
    logger.info(f"{'='*80}")

    return resultados


def process_single_file(
    archivo: Path,
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Procesar un solo archivo descargado.

    Parameters:
    - archivo: Ruta del archivo
    - config: Configuración de la fuente

    Returns:
    - Dict con metadata de procesamiento
    """
    logger.info(f"  Leyendo archivo: {archivo.name}")

    # Leer archivo según extensión
    if archivo.suffix in ['.xlsx', '.xls']:
        # Excel - intentar leer todas las hojas
        try:
            xls = pd.ExcelFile(archivo)
            logger.info(f"  Hojas encontradas: {xls.sheet_names}")
            
            # Leer primera hoja por defecto
            df = pd.read_excel(archivo, sheet_name=0)
            logger.info(f"  Hoja leída: {xls.sheet_names[0]}")
        except Exception as e:
            logger.error(f"  Error leyendo Excel: {e}")
            return {
                'status': 'error',
                'mensaje': f'Error leyendo Excel: {str(e)}',
            }
    elif archivo.suffix == '.csv':
        # CSV - intentar diferentes codificaciones
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(archivo, encoding=encoding)
                logger.info(f"  Codificación detectada: {encoding}")
                break
            except Exception:
                continue
        
        if df is None:
            logger.error(f"  No se pudo leer CSV con ninguna codificación")
            return {
                'status': 'error',
                'mensaje': 'Error leyendo CSV - codificación no reconocida',
            }
    else:
        return {
            'status': 'error',
            'mensaje': f'Formato no soportado: {archivo.suffix}',
        }

    logger.info(f"  DataFrame crudo: {len(df):,} registros × {len(df.columns)} columnas")

    # Normalizar columnas
    df = normalize_columns(df, config['columnas_esperadas'])

    # Validar columnas mínimas
    columnas_minimas = ['divipola_municipio']
    for col in columnas_minimas:
        if col not in df.columns:
            logger.warning(f"  Columna requerida no encontrada: {col}")
            # Intentar encontrar alternativa
            alternativas = [c for c in df.columns if 'divipola' in c.lower() or 'codigo_dane' in c.lower()]
            if alternativas:
                df = df.rename(columns={alternativas[0]: 'divipola_municipio'})
                logger.info(f"  Renombrada {alternativas[0]} → divipola_municipio")
            else:
                return {
                    'status': 'error',
                    'mensaje': f'Falta columna requerida: {col}',
                }

    # Agregar metadatos
    df = add_ingestion_metadata(df, config['nombre'])

    # Guardar en Parquet
    output_path = (
        settings.BRONZE_PATH / config['output_folder'] /
        f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}" /
        config['output_file']
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False, compression='snappy')
    logger.info(f"  Archivo guardado: {output_path}")

    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(df),
        'columnas': list(df.columns),
        'archivo_original': str(archivo),
    }


def normalize_columns(df: pd.DataFrame, columnas_esperadas: List[str]) -> pd.DataFrame:
    """
    Normalizar nombres de columnas.

    Parameters:
    - df: DataFrame crudo
    - columnas_esperadas: Lista de columnas esperadas

    Returns:
    - DataFrame con columnas normalizadas
    """
    logger.info("  Normalizando columnas...")

    # Mapeo de columnas
    column_mapping = {}

    for col in df.columns:
        col_lower = col.lower().strip()
        col_normalized = col_lower.replace(' ', '_').replace('-', '_').replace('í', 'i').replace('á', 'a').replace('é', 'e').replace('ó', 'o').replace('ú', 'o').replace('ñ', 'n')

        # DIVIPOLA
        if any(x in col_normalized for x in ['divipola', 'codigo_dane', 'dpmp', 'cod_dane']):
            column_mapping[col] = 'divipola_municipio'
        # Municipio
        elif any(x in col_normalized for x in ['municipio', 'municipio_nombre']):
            column_mapping[col] = 'nombre_municipio'
        # Departamento
        elif any(x in col_normalized for x in ['departamento', 'depto']):
            column_mapping[col] = 'nombre_departamento'
        # IPM
        elif 'ipm' in col_normalized and 'total' in col_normalized:
            column_mapping[col] = 'ipm_total'
        elif 'ipm' in col_normalized:
            # Dimensiones específicas
            if 'educ' in col_normalized:
                column_mapping[col] = 'ipm_educacion'
            elif 'nin' in col_normalized or 'nino' in col_normalized:
                column_mapping[col] = 'ipm_ninez'
            elif 'trab' in col_normalized:
                column_mapping[col] = 'ipm_trabajo'
            elif 'salud' in col_normalized:
                column_mapping[col] = 'ipm_salud'
            else:
                column_mapping[col] = 'ipm_total'
        # NBI
        elif 'nbi' in col_normalized and 'total' in col_normalized:
            column_mapping[col] = 'nbi_total'
        elif 'nbi' in col_normalized:
            if 'viv' in col_normalized:
                column_mapping[col] = 'nbi_vivienda'
            elif 'serv' in col_normalized:
                column_mapping[col] = 'nbi_servicios'
            elif 'educ' in col_normalized:
                column_mapping[col] = 'nbi_educacion'
            else:
                column_mapping[col] = 'nbi_total'
        # Población
        elif 'poblacion' in col_normalized or 'poblac' in col_normalized:
            column_mapping[col] = 'poblacion_total'
        # Pobreza monetaria
        elif 'pobreza' in col_normalized and 'monetaria' in col_normalized:
            column_mapping[col] = 'pobreza_monetaria'
        # Micronegocios
        elif 'micronegocios' in col_normalized and 'total' in col_normalized:
            column_mapping[col] = 'total_micronegocios'
        elif 'micronegocios' in col_normalized:
            if 'formal' in col_normalized:
                column_mapping[col] = 'micronegocios_formales'
            elif 'informal' in col_normalized:
                column_mapping[col] = 'micronegocios_informales'
            else:
                column_mapping[col] = 'total_micronegocios'
        # Economía popular
        elif 'economia_popular' in col_normalized or 'econ_popular' in col_normalized:
            if 'unidad' in col_normalized:
                column_mapping[col] = 'economia_popular_unidades'
            elif 'empleo' in col_normalized:
                column_mapping[col] = 'economia_popular_empleo'
            else:
                column_mapping[col] = 'economia_popular_unidades'
        # CIIU
        elif 'ciiu' in col_normalized and 'cod' in col_normalized:
            column_mapping[col] = 'codigo_ciiu'
        elif 'ciiu' in col_normalized:
            column_mapping[col] = 'codigo_ciiu'
        # Vigencia
        elif col_normalized in ['anio', 'ano', 'a_o', 'año', 'year', 'vigencia']:
            column_mapping[col] = 'vigencia'

    # Aplicar mapeo
    if column_mapping:
        df = df.rename(columns=column_mapping)
        logger.info(f"  {len(column_mapping)} columnas renombradas")

    # Asegurar DIVIPOLA como string de 5 dígitos
    if 'divipola_municipio' in df.columns:
        # Convertir a string y rellenar con ceros
        df['divipola_municipio'] = df['divipola_municipio'].astype(str).str.zfill(5)
        logger.info("  DIVIPOLA estandarizada a 5 dígitos")

    # Convertir columnas numéricas
    numeric_cols = [
        'ipm_total', 'ipm_educacion', 'ipm_ninez', 'ipm_trabajo', 'ipm_salud',
        'nbi_total', 'nbi_vivienda', 'nbi_servicios',
        'poblacion_total', 'pobreza_monetaria',
        'total_micronegocios', 'micronegocios_formales', 'micronegocios_informales',
        'economia_popular_unidades', 'economia_popular_empleo',
        'vigencia',
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    logger.info("  Columnas numéricas convertidas")

    return df


def add_ingestion_metadata(df: pd.DataFrame, fuente_nombre: str) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta.

    Parameters:
    - df: DataFrame
    - fuente_nombre: Nombre de la fuente

    Returns:
    - DataFrame con metadatos
    """
    df = df.copy()

    # Timestamp
    df['_ingestion_timestamp'] = datetime.now().isoformat()

    # Fuente
    df['_source'] = f'dane_manual_{fuente_nombre.lower().replace(" ", "_")}'

    # Checksum
    def row_checksum(row):
        row_str = '|'.join(str(v) for v in row.values[:-2])
        return hashlib.md5(row_str.encode()).hexdigest()

    df['_checksum_md5'] = df.apply(row_checksum, axis=1)

    return df


def main():
    """Función principal."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Procesar archivos descargados manualmente del DANE'
    )

    parser.add_argument(
        '--fuente',
        type=str,
        choices=list(FUENTES_CONFIG.keys()),
        help='Procesar solo una fuente específica'
    )

    args = parser.parse_args()

    logger.info("Iniciando procesamiento de archivos descargados...")

    if args.fuente:
        logger.info(f"Procesando solo: {args.fuente}")
        config = FUENTES_CONFIG[args.fuente]
        # Lógica para procesar una sola fuente
        # (implementación simplificada para demo)

    resultados = process_all_downloads()

    # Contar éxitos
    exitosos = sum(1 for r in resultados.values() if r.get('status') == 'success')

    if exitosos > 0:
        logger.info(f"\n✅ Procesamiento completado: {exitosos} fuentes procesadas")
        return 0
    else:
        logger.warning("\n⚠️ No se procesó ninguna fuente. Verificar archivos descargados.")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
