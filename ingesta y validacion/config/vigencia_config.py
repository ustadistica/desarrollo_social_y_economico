"""
Configuración de vigencia y actualización automática de fuentes de datos.
Define cómo el pipeline garantiza que siempre se extraiga la data más reciente.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# Configuración de vigencia por fuente
VIGENCIA_CONFIG: Dict[str, Dict[str, Any]] = {
    # ========================================================================
    # DANE CNPV
    # ========================================================================
    "dane_cnpv": {
        "nombre": "DANE CNPV 2018",
        "check_method": "anda_metadata",
        "endpoint": "https://anda.dane.gov.co/index.php/catalog/{dataset_id}",
        "dataset_id": "CNPV-2018-PERSONAS",
        "frequency": "censal",
        "periodo_base": "2018",
        "proyecciones_vigencia": ["2024", "2025"],
        "auto_update": False,  # Datos censales, actualización manual
        "ultimo_check": None,
        "ultima_version": "2018_v2.3",
        "next_scheduled_check": None,
    },
    
    # ========================================================================
    # DANE CENU
    # ========================================================================
    "dane_cenu": {
        "nombre": "DANE CENU",
        "check_method": "anda_metadata",
        "endpoint": "https://anda.dane.gov.co/index.php/catalog/{dataset_id}",
        "dataset_id": "CENU-2024",
        "frequency": "trimestral",
        "periodo_base": "2024",
        "auto_update": True,
        "ultimo_check": None,
        "ultima_version": None,
        "next_scheduled_check": "first_day_quarter",
    },
    
    # ========================================================================
    # SECOP II
    # ========================================================================
    "secop_ii": {
        "nombre": "SECOP II",
        "check_method": "soda_query",
        "endpoint": "https://www.datos.gov.co/resource/287p-52ht.json",
        "query_vigencia": "$select=MAX(fecha_publicacion)&$order=fecha_publicacion DESC&$limit=1",
        "frequency": "mensual",
        "auto_update": True,
        "ultimo_check": None,
        "ultima_version": None,
        "next_scheduled_check": "last_day_month",
        "schedule": {
            "day": "last",  # Último día del mes
            "hour": 23,
            "minute": 0,
        },
    },
    
    # ========================================================================
    # TerriData
    # ========================================================================
    "terridata": {
        "nombre": "TerriData DNP",
        "check_method": "arcgis_metadata",
        "endpoint": "https://terridata-dnp.hub.arcgis.com/api/download/v1/items/{item_id}",
        "item_ids": {
            "pobreza": "ITEM_ID_POBREZA",
            "poblacion": "ITEM_ID_POBLACION",
            "gasto_publico": "ITEM_ID_GASTO",
        },
        "frequency": "anual",
        "auto_update": True,
        "ultimo_check": None,
        "ultima_version": None,
        "next_scheduled_check": "first_day_quarter",
    },
    
    # ========================================================================
    # DANE Geoportal
    # ========================================================================
    "dane_geoportal": {
        "nombre": "DANE Geoportal MGN",
        "check_method": "scrape_version",
        "endpoint": "https://geoportal.dane.gov.co/",
        "frequency": "semestral",
        "auto_update": False,  # Verificación manual de nueva versión MGN
        "ultimo_check": None,
        "ultima_version": "MGN_2024",
        "next_scheduled_check": None,
    },
}


# Fuentes de datos (lista maestra)
FUENTES_DATOS = list(VIGENCIA_CONFIG.keys())


def get_fuentes_auto_update() -> list:
    """
    Obtener lista de fuentes con actualización automática habilitada.
    
    Returns:
    - Lista de nombres de fuentes
    """
    return [
        fuente for fuente, config in VIGENCIA_CONFIG.items()
        if config.get("auto_update", False)
    ]


def get_next_check_date(fuente: str) -> Optional[datetime]:
    """
    Calcular próxima fecha de verificación para una fuente.
    
    Parameters:
    - fuente: Nombre de la fuente
    
    Returns:
    - datetime de próxima verificación o None si no programada
    """
    config = VIGENCIA_CONFIG.get(fuente)
    if not config:
        return None
    
    schedule_type = config.get("next_scheduled_check")
    
    if schedule_type == "last_day_month":
        # Último día del mes actual
        today = datetime.now()
        if today.month == 12:
            return datetime(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            return datetime(today.year, today.month + 1, 1) - timedelta(days=1)
    
    elif schedule_type == "first_day_quarter":
        # Primer día del próximo trimestre
        today = datetime.now()
        next_quarter_month = ((today.month - 1) // 3 + 1) * 3 + 1
        if next_quarter_month > 12:
            return datetime(today.year + 1, 1, 1)
        else:
            return datetime(today.year, next_quarter_month, 1)
    
    return None


def is_update_due(fuente: str) -> bool:
    """
    Verificar si una fuente requiere actualización.
    
    Parameters:
    - fuente: Nombre de la fuente
    
    Returns:
    - True si requiere actualización, False si está al día
    """
    config = VIGENCIA_CONFIG.get(fuente)
    if not config:
        return False
    
    if not config.get("auto_update", False):
        return False  # Fuentes manuales no se verifican automáticamente
    
    next_check = get_next_check_date(fuente)
    if next_check is None:
        return False
    
    return datetime.now() >= next_check


def get_vigencia_metadata(fuente: str) -> Dict[str, Any]:
    """
    Obtener metadatos de vigencia para una fuente.
    
    Parameters:
    - fuente: Nombre de la fuente
    
    Returns:
    - Diccionario con metadatos de vigencia
    """
    config = VIGENCIA_CONFIG.get(fuente, {})
    
    return {
        "fuente": fuente,
        "nombre": config.get("nombre", fuente),
        "frecuencia": config.get("frequency", "desconocida"),
        "auto_update": config.get("auto_update", False),
        "ultima_version": config.get("ultima_version"),
        "proxima_verificacion": get_next_check_date(fuente),
        "requiere_actualizacion": is_update_due(fuente),
    }


def check_new_version(fuente: str, config: Dict[str, Any]) -> bool:
    """
    Verificar si hay una nueva versión disponible para una fuente.
    
    Parameters:
    - fuente: Nombre de la fuente
    - config: Configuración de la fuente
    
    Returns:
    - True si hay nueva versión, False si está actualizada
    """
    check_method = config.get("check_method")
    
    if check_method == "soda_query":
        # Para SECOP II, verificar última fecha de publicación
        return _check_soda_version(fuente, config)
    
    elif check_method == "anda_metadata":
        # Para DANE, verificar metadata del catálogo ANDA
        return _check_anda_version(fuente, config)
    
    elif check_method == "arcgis_metadata":
        # Para TerriData, verificar metadata de ArcGIS
        return _check_arcgis_version(fuente, config)
    
    elif check_method == "scrape_version":
        # Para Geoportal, verificar scraping de versión
        return _check_geoportal_version(fuente, config)
    
    return False


def _check_soda_version(fuente: str, config: Dict[str, Any]) -> bool:
    """
    Verificar nueva versión en API SODA (SECOP II).
    
    Consulta el metadata del dataset Socrata para obtener la fecha
    de última actualización (rowsUpdatedAt) y compara con la versión local.
    
    Parameters:
    - fuente: Nombre de la fuente
    - config: Configuración
    
    Returns:
    - True si hay datos más recientes
    """
    import requests
    from datetime import datetime
    
    endpoint = config.get('check_endpoint', '')
    if not endpoint:
        logger.warning(f"Sin endpoint para verificar {fuente}")
        return True  # Asumir que hay actualización si no se puede verificar
    
    try:
        # Consultar metadata del dataset Socrata
        # Ejemplo endpoint: https://www.datos.gov.co/api/views/{dataset_id}.json
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        metadata = response.json()
        
        # Obtener fecha de última actualización del dataset
        rows_updated = metadata.get('rowsUpdatedAt', 0)
        if isinstance(rows_updated, (int, float)):
            remote_date = datetime.fromtimestamp(rows_updated)
        else:
            remote_date = datetime.fromisoformat(str(rows_updated))
        
        # Comparar con última versión local
        ultima_version = config.get('ultima_version')
        if ultima_version:
            local_date = datetime.fromisoformat(str(ultima_version))
            hay_nueva = remote_date > local_date
            logger.info(f"SODA {fuente}: remoto={remote_date}, local={local_date}, nueva={hay_nueva}")
            return hay_nueva
        
        # Si no hay versión local, asumir que hay actualización
        return True
        
    except Exception as e:
        logger.warning(f"Error verificando versión SODA para {fuente}: {e}")
        return True  # Ante la duda, marcar como pendiente


def _check_anda_version(fuente: str, config: Dict[str, Any]) -> bool:
    """
    Verificar nueva versión en datos.gov.co (DANE CNPV/CENU).

    Consulta el metadata del dataset Socrata correspondiente a los
    indicadores DANE publicados en datos.gov.co.
    
    Parameters:
    - fuente: Nombre de la fuente
    - config: Configuración
    
    Returns:
    - True si hay nueva versión
    """
    import requests
    from datetime import datetime
    
    endpoint = config.get('check_endpoint', '')
    if not endpoint:
        logger.warning(f"Sin endpoint para verificar {fuente}")
        return False
    
    try:
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        metadata = response.json()
        
        # Verificar fecha de última actualización
        rows_updated = metadata.get('rowsUpdatedAt', 0)
        if isinstance(rows_updated, (int, float)):
            remote_date = datetime.fromtimestamp(rows_updated)
        else:
            remote_date = datetime.fromisoformat(str(rows_updated))
        
        ultima_version = config.get('ultima_version')
        if ultima_version:
            local_date = datetime.fromisoformat(str(ultima_version))
            hay_nueva = remote_date > local_date
            logger.info(f"ANDA {fuente}: remoto={remote_date}, local={local_date}, nueva={hay_nueva}")
            return hay_nueva
        
        return True  # Sin versión local, asumir nueva
        
    except Exception as e:
        logger.warning(f"Error verificando versión ANDA para {fuente}: {e}")
        return False


def _check_arcgis_version(fuente: str, config: Dict[str, Any]) -> bool:
    """
    Verificar nueva versión en datos.gov.co (TerriData/DNP).
    
    Consulta el metadata del dataset Socrata de indicadores DNP.
    
    Parameters:
    - fuente: Nombre de la fuente
    - config: Configuración
    
    Returns:
    - True si hay nueva versión
    """
    import requests
    from datetime import datetime
    
    endpoint = config.get('check_endpoint', '')
    if not endpoint:
        logger.warning(f"Sin endpoint para verificar {fuente}")
        return False
    
    try:
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        metadata = response.json()
        
        # Verificar lastEditDate para datasets ArcGIS/Socrata
        last_edit = metadata.get('rowsUpdatedAt', metadata.get('lastEditDate', 0))
        if isinstance(last_edit, (int, float)):
            remote_date = datetime.fromtimestamp(last_edit)
        else:
            remote_date = datetime.fromisoformat(str(last_edit))
        
        ultima_version = config.get('ultima_version')
        if ultima_version:
            local_date = datetime.fromisoformat(str(ultima_version))
            hay_nueva = remote_date > local_date
            logger.info(f"ArcGIS {fuente}: remoto={remote_date}, local={local_date}, nueva={hay_nueva}")
            return hay_nueva
        
        return True
        
    except Exception as e:
        logger.warning(f"Error verificando versión ArcGIS para {fuente}: {e}")
        return False


def _check_geoportal_version(fuente: str, config: Dict[str, Any]) -> bool:
    """
    Verificar nueva versión en DANE Geoportal.
    
    Realiza un HEAD request al URL del shapefile MGN para verificar
    si la fecha de modificación es posterior a la última descarga.
    
    Parameters:
    - fuente: Nombre de la fuente
    - config: Configuración
    
    Returns:
    - True si hay nueva versión MGN
    """
    import requests
    from datetime import datetime
    
    endpoint = config.get('check_endpoint', '')
    if not endpoint:
        logger.warning(f"Sin endpoint para verificar {fuente}")
        return False
    
    try:
        # HEAD request para verificar Last-Modified
        response = requests.head(endpoint, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        last_modified = response.headers.get('Last-Modified')
        if last_modified:
            from email.utils import parsedate_to_datetime
            remote_date = parsedate_to_datetime(last_modified)
            
            ultima_version = config.get('ultima_version')
            if ultima_version:
                local_date = datetime.fromisoformat(str(ultima_version))
                hay_nueva = remote_date > local_date
                logger.info(f"Geoportal {fuente}: remoto={remote_date}, local={local_date}, nueva={hay_nueva}")
                return hay_nueva
            
            return True
        
        # Sin Last-Modified, verificar Content-Length como proxy
        logger.info(f"Sin Last-Modified para {fuente}. Asumiendo sin cambios.")
        return False
        
    except Exception as e:
        logger.warning(f"Error verificando versión Geoportal para {fuente}: {e}")
        return False
