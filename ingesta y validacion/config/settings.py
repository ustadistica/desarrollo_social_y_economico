"""
Configuración general del pipeline ETL/ELT.
"""

import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import yaml
from dotenv import load_dotenv

# Cargar variables del .env
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


class Settings:
    """
    Clase de configuración centralizada para el pipeline.
    Soporta variables de entorno y archivos de configuración YAML.
    """
    
    def __init__(self):
        # Rutas base
        self.PROJECT_ROOT = Path(__file__).parent.parent.parent
        self.PIPELINE_ROOT = Path(__file__).parent.parent
        
        # Rutas de capas de datos
        self.DATOS_ROOT = self.PROJECT_ROOT / "datos"
        # Capas de datos (Medallion Architecture)
        self.BRONZE_PATH = self.DATOS_ROOT / "bronze"
        self.SILVER_PATH = self.DATOS_ROOT / "plata"
        self.GOLD_PATH = self.DATOS_ROOT / "oro"
        
        # Alias legacy para compatibilidad
        self.PLATA_PATH = self.SILVER_PATH
        self.ORO_PATH = self.GOLD_PATH
        
        # Rutas de artefactos
        self.ARTIFACTS_PATH = self.PROJECT_ROOT / "artifacts"
        self.QUALITY_REPORTS_PATH = self.ARTIFACTS_PATH / "data_quality_reports"
        
        # Directorio de Modelo Estrella Parquet (PySpark)
        self.MODELO_ESTRELLA_PATH = self.PROJECT_ROOT / "modelo_estrella_pyspark"
        
        # Configuración de APIs - datos.gov.co
        # API Token para SODA API (datos.gov.co)
        self.SODA_APP_TOKEN: Optional[str] = os.getenv("SODA_APP_TOKEN", "579j8r2q0n5wl8u0okmc3blo6")
        self.SODA_APP_SECRET: Optional[str] = os.getenv("SODA_APP_SECRET", "3jrwo4zsarden485vhot5q31zks79ubgtppfo2en2fx7fkzte7")
        self.DANE_API_KEY: Optional[str] = os.getenv("DANE_API_KEY")
        
        # Parámetros de extracción SECOP II y CNPV
        self.SECOP_BATCH_SIZE = int(os.getenv("SECOP_BATCH_SIZE", "50000"))
        self.SECOP_MAX_RETRIES = int(os.getenv("SECOP_MAX_RETRIES", "3"))
        self.SECOP_BASE_URL = "https://www.datos.gov.co/resource/287p-52ht.json"
        
        # Leemos las rutas de los CSV locales desde variables de entorno (o .env)
        # Por defecto, si el compañero de equipo no tiene el .env listado, buscamos en una carpeta dummy local.
        secop_default = r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\SECOP_II_-_Contratos_Electrónicos_20260322.csv"
        cnpv_default = r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\CENSO 2018 dep"
        emicron_default = r"C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\Módulo de características del micronegocio.csv"
        
        self.SECOP_CSV_PATH = Path(os.getenv("SECOP_CSV_PATH", secop_default))
        self.CNPV_CSV_DIR = Path(os.getenv("CNPV_CSV_DIR", cnpv_default))
        self.EMICRON_CSV_PATH = Path(os.getenv("EMICRON_CSV_PATH", emicron_default))
        
        # Parámetros de calidad de datos
        self.NULL_THRESHOLD_WARNING = float(os.getenv("NULL_THRESHOLD_WARNING", "0.5"))
        self.NULL_THRESHOLD_BLOCKING = float(os.getenv("NULL_THRESHOLD_BLOCKING", "0.9"))
        self.DUPLICATE_CHECK_COLUMNS = ["id_contrato", "divipola_municipio"]
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        # Fecha de corte para extracción
        self.CORTE_DATE = self._parse_corte_date(os.getenv("CORTE_DATE", "latest"))
        
        # Crear directorios si no existen
        self._create_directories()
    
    def _parse_corte_date(self, date_str: str) -> datetime:
        """
        Parsear fecha de corte desde string.
        
        Parameters:
        - date_str: 'latest' para fecha actual, o YYYY-MM-DD
        
        Returns:
        - datetime object
        """
        if date_str == "latest":
            return datetime.now()
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return datetime.now()
    
    def _create_directories(self):
        """Crear directorios de salida si no existen."""
        for path in [
            self.BRONZE_PATH,
            self.PLATA_PATH,
            self.ORO_PATH,
            self.ARTIFACTS_PATH,
            self.QUALITY_REPORTS_PATH,
        ]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_bronze_path(self, fuente: str, fecha: Optional[datetime] = None) -> Path:
        """
        Obtener ruta para archivo en capa Bronce.
        
        Parameters:
        - fuente: Nombre de la fuente (dane_cnpv, secop_ii, etc.)
        - fecha: Fecha de ingesta (default: hoy)
        
        Returns:
        - Path completo
        """
        if fecha is None:
            fecha = datetime.now()
        
        return self.BRONZE_PATH / fuente / f"ingestion_date={fecha.strftime('%Y-%m-%d')}"
    
    def get_plata_path(self, tabla: str) -> Path:
        """
        Obtener ruta para archivo en capa Plata.
        
        Parameters:
        - tabla: Nombre de la tabla (dim_municipio, fact_contratacion, etc.)
        
        Returns:
        - Path completo
        """
        return self.PLATA_PATH / tabla
    
    def get_oro_path(self, datamart: str, tabla: str) -> Path:
        """
        Obtener ruta para archivo en capa Oro.
        
        Parameters:
        - datamart: Nombre del data mart (social, economico, cubos_analiticos)
        - tabla: Nombre de la tabla
        
        Returns:
        - Path completo
        """
        return self.ORO_PATH / datamart
    
    def get_quality_report_path(self, fecha: Optional[datetime] = None) -> Path:
        """
        Obtener ruta para reporte de calidad.
        
        Parameters:
        - fecha: Fecha del reporte (default: hoy)
        
        Returns:
        - Path completo
        """
        if fecha is None:
            fecha = datetime.now()
        
        return self.QUALITY_REPORTS_PATH / f"quality_report_{fecha.strftime('%Y-%m-%d')}.html"


def get_settings() -> Settings:
    """
    Factory function para obtener instancia de Settings.
    
    Returns:
    - Settings instance
    """
    return Settings()


# Instancia global de configuración
settings = get_settings()
