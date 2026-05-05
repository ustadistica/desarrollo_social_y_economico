"""
Orquestador principal del Pipeline ETL/ELT.

Este módulo coordina todas las fases del pipeline:
1. Extracción (Capa Bronce)
2. Transformación (Capa Plata)
3. Carga (Capa Oro)
4. Validación (Data Quality)
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

from src.config.settings import settings, get_settings
from src.config.vigencia_config import VIGENCIA_CONFIG, get_fuentes_auto_update, is_update_due
# La ingesta vía API fue eliminada. Toda extracción se realiza desde CSV locales
# a través de src/ingesta/bronze/main_ingestion.py (run_bronze.py).
from src.transformacion.gold.schema.create_dimensions import (
    create_dim_municipio,
    create_dim_tiempo,
    create_dim_sector_ciiu,
    create_dim_sector_unspsc,
)
from src.transformacion.gold.schema.create_facts import (
    create_fact_vulnerabilidad,
    create_fact_tejido_productivo,
    create_fact_contratacion,
)
from src.transformacion.gold.marts.create_datamart_social import create_datamart_social
from src.transformacion.gold.marts.create_datamart_economico import create_datamart_economico
from src.transformacion.gold.marts.create_cubos_analiticos import create_cubo_completo
from src.validate import (
    validate_bronze_layer,
    validate_plata_layer,
    validate_oro_layer,
    generate_quality_report,
)
from src.utils.logger import setup_logging, get_logger, get_log_file_path

logger = get_logger(__name__)


class PipelineOrchestrator:
    """
    Orquestador principal del pipeline ETL/ELT.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializar orquestador.
        
        Parameters:
        - config_path: Ruta a archivo de configuración (opcional)
        """
        self.settings = get_settings()
        self.config_path = config_path
        
        # Resultados de la ejecución
        self.execution_results = {
            'start_time': None,
            'end_time': None,
            'status': 'pending',
            'phases': {},
            'errors': [],
            'warnings': [],
        }
    
    def run_full_pipeline(
        self,
        fuentes: Optional[List[str]] = None,
        force_update: bool = False,
        skip_extraction: bool = False,
        skip_validation: bool = False,
    ) -> Dict[str, Any]:
        """
        Ejecutar pipeline completo.
        
        Parameters:
        - fuentes: Lista de fuentes a procesar (default: todas)
        - force_update: Forzar actualización incluso si hay datos recientes
        - skip_extraction: Omitir fase de extracción (usar datos en Bronce)
        - skip_validation: Omitir validaciones de calidad
        
        Returns:
        - Dict con resultados de la ejecución
        """
        self.execution_results['start_time'] = datetime.now().isoformat()
        self.execution_results['status'] = 'running'
        
        logger.info("=" * 60)
        logger.info("INICIANDO PIPELINE ETL/ELT")
        logger.info("Observatorio de Desarrollo Socioeconómico")
        logger.info("=" * 60)
        
        try:
            # Fase 0: Verificar vigencia (solo si no se salta extracción)
            if not skip_extraction:
                self.execution_results['phases']['vigencia'] = self._check_vigencia(force_update)
            
            # Determinar qué fuentes procesar
            if fuentes is None:
                if skip_extraction:
                    # Si se salta extracción, usamos todas las configuradas
                    from src.config.vigencia_config import VIGENCIA_CONFIG
                    fuentes = list(VIGENCIA_CONFIG.keys())
                else:
                    fuentes = self._get_fuentes_to_process(force_update)
            
            if not fuentes and not skip_extraction:
                logger.info("No hay fuentes que requieran actualización")
                self.execution_results['status'] = 'skipped'
                self.execution_results['end_time'] = datetime.now().isoformat()
                return self.execution_results
            
            # Fase 1: Extracción (Bronce)
            if not skip_extraction:
                logger.info(f"Fuentes a procesar: {fuentes}")
                self.execution_results['phases']['extraction'] = self._run_extraction(fuentes)
            else:
                logger.info("Saltando fase de extracción. Usando datos locales en Bronce.")
            
            # Fase 2: Transformación (Plata)
            self.execution_results['phases']['transformation'] = self._run_transformation()
            
            # Fase 3: Carga (Oro)
            self.execution_results['phases']['load'] = self._run_load()
            
            # Fase 4: Validación
            if not skip_validation:
                self.execution_results['phases']['validation'] = self._run_validation()
            
            self.execution_results['status'] = 'success'
            
        except Exception as e:
            logger.error(f"Error en pipeline: {str(e)}")
            self.execution_results['status'] = 'error'
            self.execution_results['errors'].append(str(e))
            import traceback
            logger.error(traceback.format_exc())
        
        self.execution_results['end_time'] = datetime.now().isoformat()
        
        # Resumen final
        self._log_summary()
        
        return self.execution_results
        
        return self.execution_results
    
    def _check_vigencia(self, force_update: bool) -> Dict[str, Any]:
        """
        Verificar vigencia de todas las fuentes.
        
        Parameters:
        - force_update: Si True, ignorar verificación de vigencia
        
        Returns:
        - Dict con estado de vigencia
        """
        logger.info("Fase 0: Verificando vigencia de fuentes...")
        
        vigencia_status = {}
        
        for fuente, config in VIGENCIA_CONFIG.items():
            if force_update:
                requiere_actualizacion = True
            else:
                requiere_actualizacion = is_update_due(fuente)
            
            vigencia_status[fuente] = {
                'ultima_version': config.get('ultima_version'),
                'auto_update': config.get('auto_update', False),
                'requiere_actualizacion': requiere_actualizacion,
            }
            
            logger.info(f"  {fuente}: {'REQUIERE ACTUALIZACIÓN' if requiere_actualizacion else 'ACTUALIZADA'}")
        
        return vigencia_status
    
    def _get_fuentes_to_process(self, force_update: bool) -> List[str]:
        """
        Determinar qué fuentes requieren procesamiento.
        
        Parameters:
        - force_update: Si True, incluir todas las fuentes
        
        Returns:
        - Lista de nombres de fuentes
        """
        if force_update:
            return list(VIGENCIA_CONFIG.keys())
        
        return [
            fuente for fuente, config in VIGENCIA_CONFIG.items()
            if is_update_due(fuente)
        ]
    
    def _run_extraction(self, fuentes: List[str]) -> Dict[str, Any]:
        """
        Ejecutar fase de extracción (Capa Bronce).
        
        Parameters:
        - fuentes: Lista de fuentes a extraer
        
        Returns:
        - Dict con resultados de extracción
        """
        logger.info("=" * 60)
        logger.info("FASE 1: EXTRACCIÓN (CAPA BRONCE)")
        logger.info("=" * 60)
        
        resultados = {}
        
        for fuente in fuentes:
            logger.info(f"Extrayendo {fuente}...")
            
            try:
                # La ingesta vía API fue eliminada. Toda extracción se realiza desde
                # CSV locales a través de src/ingesta/bronze/main_ingestion.py.
                # Para ingestar, ejecutar: python src/ingesta/run_bronze.py
                logger.warning(
                    f"Fuente '{fuente}': extracción vía API eliminada. "
                    "Use run_bronze.py para ingestar desde CSV locales."
                )
                resultado = {"status": "skipped", "fuente": fuente}
                
                resultados[fuente] = resultado
                logger.info(f"  Estado: {resultado.get('status', 'unknown')}")
                
                if resultado.get('registros'):
                    logger.info(f"  Registros: {resultado['registros']}")
                
            except Exception as e:
                logger.error(f"Error extrayendo {fuente}: {str(e)}")
                resultados[fuente] = {
                    'status': 'error',
                    'error': str(e),
                }
        
        return resultados
    
    def _load_bronze_data(self, fuente: str) -> pd.DataFrame:
        """
        Cargar datos más recientes de la Capa Bronce.
        
        Parameters:
        - fuente: Nombre de la fuente ('dane_cnpv', 'dane_cenu', 'secop_ii', etc.)
        
        Returns:
        - DataFrame con los datos más recientes de Bronce
        """
        bronze_path = self.settings.BRONZE_PATH / fuente
        
        if not bronze_path.exists():
            logger.warning(f"No existe directorio Bronce para {fuente}: {bronze_path}")
            return pd.DataFrame()
        
        # Buscar el directorio de ingesta más reciente (ingestion_date=YYYY-MM-DD)
        ingestion_dirs = sorted(bronze_path.glob('ingestion_date=*'), reverse=True)
        
        if not ingestion_dirs:
            logger.warning(f"No hay datos de ingesta en {bronze_path}")
            return pd.DataFrame()
        
        latest_dir = ingestion_dirs[0]
        logger.info(f"  Cargando datos Bronce de {fuente} desde {latest_dir.name}")
        
        # Buscar archivos Parquet en el directorio
        parquet_files = list(latest_dir.glob('*.parquet'))
        
        if not parquet_files:
            logger.warning(f"No hay archivos Parquet en {latest_dir}")
            return pd.DataFrame()
        
        # Leer y concatenar todos los Parquet
        dfs = []
        for pf in parquet_files:
            try:
                dfs.append(pd.read_parquet(pf))
            except Exception as e:
                logger.warning(f"Error leyendo {pf}: {e}")
        
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            logger.info(f"  {fuente}: {len(df)} registros cargados desde Bronce")
            return df
        
        return pd.DataFrame()
    
    def _load_plata_data(self, tabla: str) -> pd.DataFrame:
        """
        Cargar datos de la Capa Plata.
        
        Parameters:
        - tabla: Nombre de la tabla ('fact_vulnerabilidad', 'dim_municipio', etc.)
        
        Returns:
        - DataFrame con datos de Plata
        """
        plata_path = self.settings.PLATA_PATH / tabla
        
        if not plata_path.exists():
            logger.warning(f"No existe directorio Plata para {tabla}: {plata_path}")
            return pd.DataFrame()
        
        parquet_files = list(plata_path.glob('*.parquet'))
        
        if not parquet_files:
            logger.warning(f"No hay archivos Parquet en {plata_path}")
            return pd.DataFrame()
        
        # Leer el archivo más reciente
        latest = max(parquet_files, key=lambda p: p.stat().st_mtime)
        try:
            df = pd.read_parquet(latest)
            logger.info(f"  {tabla}: {len(df)} registros cargados desde Plata")
            return df
        except Exception as e:
            logger.warning(f"Error leyendo {latest}: {e}")
            return pd.DataFrame()
    
    def _run_transformation(self) -> Dict[str, Any]:
        """
        Ejecutar fase de transformación (Capa Plata).
        
        Lee datos de la Capa Bronce y genera dimensiones y hechos.
        
        Returns:
        - Dict con resultados de transformación
        """
        logger.info("=" * 60)
        logger.info("FASE 2: TRANSFORMACIÓN (CAPA PLATA)")
        logger.info("=" * 60)
        
        resultados = {}
        
        try:
            # Cargar datos de Bronce
            logger.info("Cargando datos de Capa Bronce...")
            cnpv_df = self._load_bronze_data('dane_cnpv')
            cenu_df = self._load_bronze_data('dane_cenu')
            secop_df = self._load_bronze_data('secop_ii')
            geoportal_df = self._load_bronze_data('dane_geoportal')
            
            # Crear dimensiones
            logger.info("Creando dimensiones...")
            
            logger.info("  dim_tiempo...")
            resultados['dim_tiempo'] = create_dim_tiempo(anio_inicio=2018, anio_fin=2026)
            
            logger.info("  dim_sector_ciiu...")
            resultados['dim_sector_ciiu'] = create_dim_sector_ciiu()
            
            logger.info("  dim_sector_unspsc...")
            resultados['dim_sector_unspsc'] = create_dim_sector_unspsc()
            
            logger.info("  dim_municipio...")
            resultados['dim_municipio'] = create_dim_municipio(
                geoportal_df=geoportal_df if not geoportal_df.empty else None,
                cnpv_df=cnpv_df if not cnpv_df.empty else None,
            )
            
            # Crear tablas de hechos con datos reales de Bronce
            logger.info("Creando tablas de hechos...")
            
            logger.info("  fact_vulnerabilidad...")
            resultados['fact_vulnerabilidad'] = create_fact_vulnerabilidad(
                cnpv_df=cnpv_df,
            )
            
            logger.info("  fact_tejido_productivo...")
            resultados['fact_tejido_productivo'] = create_fact_tejido_productivo(
                cenu_df=cenu_df,
            )
            
            logger.info("  fact_contratacion...")
            resultados['fact_contratacion'] = create_fact_contratacion(
                secop_df=secop_df,
            )
            
        except Exception as e:
            logger.error(f"Error en transformación: {str(e)}")
            resultados['error'] = str(e)
        
        return resultados
    
    def _run_load(self) -> Dict[str, Any]:
        """
        Ejecutar fase de carga (Capa Oro).
        
        Lee datos de la Capa Plata y genera Data Marts y Cubos Analíticos.
        
        Returns:
        - Dict con resultados de carga
        """
        logger.info("=" * 60)
        logger.info("FASE 3: CARGA (CAPA ORO)")
        logger.info("=" * 60)
        
        resultados = {}
        
        try:
            # Cargar datos de Plata
            logger.info("Cargando datos de Capa Plata...")
            fact_vulnerabilidad_df = self._load_plata_data('fact_vulnerabilidad')
            fact_contratacion_df = self._load_plata_data('fact_contratacion')
            fact_tejido_productivo_df = self._load_plata_data('fact_tejido_productivo')
            dim_municipio_df = self._load_plata_data('dim_municipio')
            
            # Data Mart Social
            logger.info("Creando Data Mart Social...")
            resultados['datamart_social'] = create_datamart_social(
                fact_vulnerabilidad_df=fact_vulnerabilidad_df,
                fact_contratacion_df=fact_contratacion_df,
                dim_municipio_df=dim_municipio_df,
            )
            
            # Data Mart Económico
            logger.info("Creando Data Mart Económico...")
            resultados['datamart_economico'] = create_datamart_economico(
                fact_tejido_productivo_df=fact_tejido_productivo_df,
                fact_contratacion_df=fact_contratacion_df,
                dim_municipio_df=dim_municipio_df,
            )
            
            # Cubos Analíticos
            logger.info("Creando Cubos Analíticos...")
            resultados['cubos_analiticos'] = create_cubo_completo(
                fact_contratacion_df=fact_contratacion_df,
                fact_vulnerabilidad_df=fact_vulnerabilidad_df,
                fact_tejido_productivo_df=fact_tejido_productivo_df,
                dim_municipio_df=dim_municipio_df,
            )
            
        except Exception as e:
            logger.error(f"Error en carga: {str(e)}")
            resultados['error'] = str(e)
        
        return resultados
    
    def _run_validation(self) -> Dict[str, Any]:
        """
        Ejecutar validaciones de calidad.
        
        Returns:
        - Dict con resultados de validación
        """
        logger.info("=" * 60)
        logger.info("FASE 4: VALIDACIÓN (DATA QUALITY)")
        logger.info("=" * 60)
        
        resultados = {}
        
        try:
            # Validar capa Bronce
            logger.info("Validando Capa Bronce...")
            resultados['bronze'] = validate_bronze_layer()
            
            # Validar capa Plata
            logger.info("Validando Capa Plata...")
            resultados['plata'] = validate_plata_layer()
            
            # Validar capa Oro
            logger.info("Validando Capa Oro...")
            resultados['oro'] = validate_oro_layer()
            
            # Generar reporte
            logger.info("Generando reporte de calidad...")
            reporte = generate_quality_report(resultados)
            resultados['reporte'] = reporte
            
        except Exception as e:
            logger.error(f"Error en validación: {str(e)}")
            resultados['error'] = str(e)
        
        return resultados
    
    def _log_summary(self):
        """Registrar resumen final de la ejecución."""
        logger.info("=" * 60)
        logger.info("RESUMEN DE EJECUCIÓN")
        logger.info("=" * 60)
        
        estado = self.execution_results['status']
        inicio = self.execution_results['start_time']
        fin = self.execution_results['end_time']
        
        logger.info(f"Estado: {estado.upper()}")
        logger.info(f"Inicio: {inicio}")
        logger.info(f"Fin: {fin}")
        
        if self.execution_results['errors']:
            logger.error(f"Errores: {len(self.execution_results['errors'])}")
            for error in self.execution_results['errors']:
                logger.error(f"  - {error}")
        
        if self.execution_results['warnings']:
            logger.warning(f"Advertencias: {len(self.execution_results['warnings'])}")


def main():
    """
    Función principal para ejecutar el pipeline.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pipeline ETL/ELT - Observatorio de Desarrollo Socioeconómico'
    )
    
    parser.add_argument(
        '--fuentes',
        nargs='+',
        help='Fuentes a procesar (default: todas)'
    )
    
    parser.add_argument(
        '--force-update',
        action='store_true',
        help='Forzar actualización incluso si hay datos recientes'
    )
    
    parser.add_argument(
        '--skip-extraction',
        action='store_true',
        help='Omitir fase de extracción (usar datos existentes en Bronce)'
    )
    
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Omitir validaciones de calidad'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Nivel de logging'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    log_file = get_log_file_path()
    setup_logging(
        log_level=args.log_level,
        log_file=log_file,
    )
    
    logger.info(f"Log file: {log_file}")
    
    # Ejecutar pipeline
    orchestrator = PipelineOrchestrator()
    
    resultados = orchestrator.run_full_pipeline(
        fuentes=args.fuentes,
        force_update=args.force_update,
        skip_extraction=args.skip_extraction,
        skip_validation=args.skip_validation,
    )
    
    # Retornar código de salida
    if resultados['status'] == 'success':
        return 0
    elif resultados['status'] == 'skipped':
        return 2
    else:
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
