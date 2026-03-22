"""
Configuración de logging para el pipeline ETL/ELT.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None,
) -> None:
    """
    Configurar logging para el pipeline.
    
    Parameters:
    - log_level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    - log_file: Ruta al archivo de log (opcional)
    - log_format: Formato de log personalizado
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Crear formatter
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Configurar root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Limpiar handlers existentes
    root_logger.handlers = []
    
    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Handler para archivo (si se especifica)
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Capturar warnings de Python
    logging.captureWarnings(True)


def get_logger(name: str) -> logging.Logger:
    """
    Obtener logger con nombre específico.
    
    Parameters:
    - name: Nombre del logger (usualmente __name__)
    
    Returns:
    - Logger configurado
    """
    return logging.getLogger(name)


def get_log_file_path(base_path: Optional[Path] = None) -> Path:
    """
    Obtener ruta para archivo de log con fecha actual.
    
    Parameters:
    - base_path: Directorio base para logs (default: artifacts/logs)
    
    Returns:
    - Path completo para el archivo de log
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent.parent / "artifacts" / "logs"
    
    base_path.mkdir(parents=True, exist_ok=True)
    
    fecha = datetime.now().strftime("%Y-%m-%d")
    return base_path / f"pipeline_{fecha}.log"


class LoggingContext:
    """
    Context manager para logging con configuración temporal.
    
    Example:
    ```python
    with LoggingContext(log_level='DEBUG'):
        # Código con logging detallado
        logger.debug("Mensaje debug")
    ```
    """
    
    def __init__(self, log_level: str = "DEBUG", log_file: Optional[Path] = None):
        self.original_level = logging.root.level
        self.log_level = log_level
        self.log_file = log_file
        self.file_handler = None
    
    def __enter__(self):
        # Cambiar nivel de logging
        logging.root.setLevel(getattr(logging, self.log_level.upper()))
        
        # Agregar handler de archivo si se especifica
        if self.log_file:
            formatter = logging.root.handlers[0].formatter if logging.root.handlers else None
            if formatter is None:
                formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            
            self.file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            self.file_handler.setFormatter(formatter)
            logging.root.addHandler(self.file_handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restaurar nivel original
        logging.root.setLevel(self.original_level)
        
        # Remover handler de archivo
        if self.file_handler:
            logging.root.removeHandler(self.file_handler)
            self.file_handler.close()


if __name__ == "__main__":
    # Ejemplo de uso
    setup_logging(log_level="INFO")
    
    logger = get_logger(__name__)
    
    logger.info("Logging configurado correctamente")
    logger.debug("Mensaje de debug (no se muestra con INFO)")
    
    # Usar contexto para logging detallado
    with LoggingContext(log_level="DEBUG"):
        logger.debug("Este mensaje debug sí se muestra")
    
    logger.info("Volviendo al nivel INFO")
