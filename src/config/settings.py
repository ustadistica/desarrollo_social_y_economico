"""
Configuración general del pipeline ETL/ELT.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Configurar logger
logger = logging.getLogger(__name__)

# Cargar variables del .env (desde la raíz del proyecto)
env_path = Path(__file__).parent.parent.parent / '.env'
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
        self.DATOS_ROOT = self.PROJECT_ROOT / "data"
        # Capas de datos (Medallion Architecture)
        self.BRONZE_PATH = self.DATOS_ROOT / "bronze"
        self.SILVER_PATH = self.DATOS_ROOT / "silver"
        self.GOLD_PATH = self.DATOS_ROOT / "gold"
        
        # Alias legacy para compatibilidad
        self.PLATA_PATH = self.SILVER_PATH
        self.ORO_PATH = self.GOLD_PATH
        
        # Rutas de artefactos
        self.ARTIFACTS_PATH = self.PROJECT_ROOT / "artifacts"
        self.QUALITY_REPORTS_PATH = self.ARTIFACTS_PATH / "data_quality_reports"
        
        # Directorio de Modelo Estrella Parquet (PySpark)
        self.MODELO_ESTRELLA_PATH = self.PROJECT_ROOT / "modelo_estrella_pyspark"
        
        # Leemos las rutas de los CSV locales desde variables de entorno (o .env)
        # Por defecto, si el compañero de equipo no tiene el .env listado,
        # buscamos en una carpeta Datos relativa al proyecto.
        # Estrategia de búsqueda:
        # 1. ../Datos/ (un nivel arriba: para estructura Desarrollo/desarrollo_proyecto/src)
        # 2. ../../Datos/ (dos niveles: para estructura CONSULTORIA/Desarrollo/proyecto/src)
        # Se usan glob patterns para no depender de la fecha en el nombre del archivo.
        datos_folder = None
        candidate_paths = [
            self.PROJECT_ROOT / "Datos",  # Dentro del proyecto
            self.PROJECT_ROOT.parent / "Datos",  # Un nivel arriba
            self.PROJECT_ROOT.parent.parent / "Datos",  # Dos niveles arriba (CONSULTORIA/Datos)
        ]
        for candidate in candidate_paths:
            if candidate.exists():
                datos_folder = candidate
                break

        if datos_folder is None:
            # Si no encuentra en ningún lado, usar la ubicación por defecto (y error después)
            datos_folder = self.PROJECT_ROOT.parent.parent / "Datos"
            logger.warning(
                f"Carpeta 'Datos' no encontrada en las ubicaciones esperadas:\n"
                f"  • {self.PROJECT_ROOT / 'Datos'}\n"
                f"  • {self.PROJECT_ROOT.parent / 'Datos'}\n"
                f"  • {self.PROJECT_ROOT.parent.parent / 'Datos'}\n"
                f"Buscaré en: {datos_folder}\n"
                f"Si no está allí, configura el .env con las rutas explícitas."
            )
        
        cnpv_default = datos_folder / "CENSO 2018 dep"
        emicron_default = datos_folder / "EMICRON 2024"
        proyecciones_default = datos_folder / "PPED-AreaDep-2018-2050_VP.csv"
        
        # SECOP I - Procesos de Compra Pública (nuevo)
        secop_i_env = os.getenv("SECOP_I_CSV_PATH")
        if secop_i_env:
            self.SECOP_I_CSV_PATH = Path(secop_i_env)
        else:
            self.SECOP_I_CSV_PATH = self._resolve_glob_path(
                datos_folder, "SECOP_I_-_Procesos_de_Compra*.*csv"
            )
        
        # SECOP II - Contratos Electrónicos
        secop_ii_env = os.getenv("SECOP_CSV_PATH")
        if secop_ii_env:
            self.SECOP_CSV_PATH = Path(secop_ii_env)
        else:
            self.SECOP_CSV_PATH = self._resolve_glob_path(
                datos_folder, "SECOP_II_-_Contratos_Electr*.*csv"
            )
        
        self.CNPV_ROOT_DIR = Path(os.getenv("CNPV_ROOT_DIR", cnpv_default))
        self.PROYECCIONES_CENSO_PATH = Path(os.getenv("PROYECCIONES_CENSO_PATH", proyecciones_default))
        
        # EMICRON - Encuesta de Micronegocios (multi-año: 2019-2024)
        # EMICRON_CSV_PATH apunta al directorio BASE que contiene las carpetas
        # "EMICRON 2019", "EMICRON 2020", ..., "EMICRON 2024"
        emicron_env = os.getenv("EMICRON_CSV_PATH")
        if emicron_env:
            self.EMICRON_CSV_PATH = Path(emicron_env)
        else:
            self.EMICRON_CSV_PATH = datos_folder
        
        # Descubrir automáticamente qué años de EMICRON están disponibles
        self.EMICRON_YEARS = self._discover_emicron_years(self.EMICRON_CSV_PATH)
        
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
    
    @staticmethod
    def _resolve_glob_path(folder: Path, pattern: str) -> Path:
        """
        Buscar un archivo en la carpeta usando un patrón glob.
        
        Retorna la ruta del primer archivo que coincida con el patrón.
        Si no se encuentra ninguno, retorna folder / pattern como placeholder
        para que el error sea descriptivo al intentar abrirlo.
        
        Parameters:
        - folder: Directorio donde buscar
        - pattern: Patrón glob (e.g., 'SECOP_I_*.csv')
        
        Returns:
        - Path al primer archivo encontrado, o placeholder si no existe
        """
        if folder.exists():
            matches = sorted(folder.glob(pattern))
            if matches:
                return matches[-1]  # El más reciente si hay varios
        return folder / pattern
    
    @staticmethod
    def _discover_emicron_years(base_path: Path) -> list:
        """
        Descubrir automáticamente qué años de EMICRON están disponibles.
        
        Busca carpetas con el patrón 'EMICRON YYYY' en el directorio base.
        
        Parameters:
        - base_path: Directorio base donde buscar carpetas EMICRON
        
        Returns:
        - Lista ordenada de tuplas (año, ruta) encontradas
        """
        import re
        years = []
        if base_path.exists() and base_path.is_dir():
            for child in sorted(base_path.iterdir()):
                if child.is_dir():
                    match = re.match(r"EMICRON\s+(\d{4})", child.name)
                    if match:
                        years.append((int(match.group(1)), child))
        return years
    
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
