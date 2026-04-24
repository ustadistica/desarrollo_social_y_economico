"""
Extractor de datos del DANE Geoportal - Marco Geoestadístico Nacional (MGN).

Fuente: DANE Geoportal
URL: https://geoportal.dane.gov.co/
Formato: Shapefile / GeoJSON

Nota: Este extractor descarga cartografía oficial para análisis espacial.
      Proporciona geometría y códigos DIVIPOLA para cruces geográficos.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import hashlib

logger = logging.getLogger(__name__)

# URLs de descarga del MGN
MGN_DOWNLOAD_URLS = {
    "municipios": "https://geoportal.dane.gov.co/descargas/MGN_2024_MUNICIPIOS.zip",
    "departamentos": "https://geoportal.dane.gov.co/descargas/MGN_2024_DEPARTAMENTOS.zip",
    "centros_poblados": "https://geoportal.dane.gov.co/descargas/MGN_2024_CENTROS_POBLADOS.zip",
}


def extract_dane_geoportal(
    output_path: Optional[Path] = None,
    nivel: str = "municipal",
    formato_salida: str = "GeoJSON",
    version_mgn: str = "2024",
    force_download: bool = False,
) -> Dict[str, Any]:
    """
    Extraer datos cartográficos del DANE Geoportal.
    
    Parameters:
    - output_path: Ruta de salida para archivos (default: capa Bronce)
    - nivel: Nivel geográfico ('municipal', 'departamental', 'centros_poblados')
    - formato_salida: Formato de salida ('GeoJSON', 'Parquet')
    - version_mgn: Versión del MGN ('2024', 'latest')
    - force_download: Forzar descarga incluso si existe archivo local
    
    Returns:
    - Dict con metadata de extracción y ruta del archivo
    
    Raises:
    - ValueError: Si el nivel no es válido
    - ConnectionError: Si falla la descarga
    """
    logger.info(f"Iniciando extracción de DANE Geoportal (nivel: {nivel})")
    
    # Validar nivel
    NIVELES_VALIDOS = ["municipal", "departamental", "centros_poblados"]
    if nivel not in NIVELES_VALIDOS:
        raise ValueError(f"Nivel no válido: {nivel}. Opciones: {NIVELES_VALIDOS}")
    
    # Determinar versión
    if version_mgn == "latest":
        version_mgn = "2024"  # Última versión disponible
    
    # Verificar si ya existe archivo descargado
    if output_path is None:
        from src.config.settings import settings
        output_path = settings.get_bronze_path("dane_geoportal")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Nombre de archivo según formato
    if formato_salida == "GeoJSON":
        archivo_salida = output_path / f"mgn_{version_mgn}_{nivel}.geojson"
    elif formato_salida == "Parquet":
        archivo_salida = output_path / f"mgn_{version_mgn}_{nivel}.parquet"
    else:
        raise ValueError(f"Formato no válido: {formato_salida}")
    
    if archivo_salida.exists() and not force_download:
        logger.info(f"Archivo ya existe: {archivo_salida}")
        return {
            "status": "skipped",
            "archivo": str(archivo_salida),
            "mensaje": "Archivo ya existe. Use force_download=True para re-descargar.",
        }
    
    # Extracción de datos
    logger.info("Conectando con DANE Geoportal...")
    
    try:
        # Descargar y procesar shapefile
        gdf = _download_and_process_shapefile(
            nivel=nivel,
            version_mgn=version_mgn,
        )
        
        if gdf.empty:
            logger.warning("No se obtuvieron datos del Geoportal")
            return {
                "status": "warning",
                "archivo": None,
                "mensaje": "Dataset vacío",
            }
        
        # Guardar en formato solicitado
        if formato_salida == "GeoJSON":
            gdf.to_file(archivo_salida, driver="GeoJSON")
        elif formato_salida == "Parquet":
            # Convertir geometría a WKT para Parquet
            gdf_df = gdf.copy()
            gdf_df["geom_wkt"] = gdf_df.geometry.to_wkt()
            gdf_df = gdf_df.drop(columns=["geometry"])
            gdf_df.to_parquet(archivo_salida, index=False, compression="snappy")
        
        logger.info(f"Extracción completada: {len(gdf)} registros guardados en {archivo_salida}")
        
        return {
            "status": "success",
            "archivo": str(archivo_salida),
            "registros": len(gdf),
            "nivel": nivel,
            "formato": formato_salida,
            "version_mgn": version_mgn,
            "fecha_extraccion": datetime.now().isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Error en extracción de DANE Geoportal: {str(e)}")
        return {
            "status": "error",
            "archivo": None,
            "error": str(e),
        }


def _download_and_process_shapefile(nivel: str, version_mgn: str):
    """
    Descargar y procesar shapefile del MGN.
    
    Parameters:
    - nivel: Nivel geográfico
    - version_mgn: Versión del MGN
    
    Returns:
    - GeoDataFrame con los datos
    """
    try:
        import geopandas as gpd
        import requests
        import zipfile
        import io
    except ImportError:
        logger.error("Se requiere geopandas y requests para esta función")
        raise
    
    # Obtener URL de descarga
    url = MGN_DOWNLOAD_URLS.get(nivel)
    if not url:
        raise ValueError(f"Nivel no encontrado: {nivel}")
    
    # Actualizar URL con versión
    url = url.replace("2024", version_mgn)
    
    logger.info(f"Descargando desde: {url}")
    
    try:
        # Descargar ZIP
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Extraer ZIP en memoria
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            # Encontrar archivo .shp
            shp_files = [f for f in z.namelist() if f.endswith(".shp")]
            
            if not shp_files:
                raise ValueError("No se encontró archivo .shp en el ZIP")
            
            # Leer shapefile con geopandas
            gdf = gpd.read_file(z.open(shp_files[0]))
            
        # Estandarizar columnas
        gdf = _standardize_geo_columns(gdf, nivel)
        
        return gdf
        
    except Exception as e:
        logger.error(f"Error procesando shapefile: {str(e)}")
        
        # Retornar GeoDataFrame vacío con schema correcto
        return _create_empty_geodataframe(nivel)


def _standardize_geo_columns(gdf, nivel: str):
    """
    Estandarizar nombres de columnas del shapefile.
    
    Parameters:
    - gdf: GeoDataFrame original
    - nivel: Nivel geográfico
    
    Returns:
    - GeoDataFrame con columnas estandarizadas
    """
    # Mapeo de columnas (ajustar según estructura real del shapefile)
    column_mapping = {
        "DIVIPOLA": "divipola",
        "NOM_MUN": "nombre_municipio",
        "NOM_DEP": "nombre_departamento",
        "DPTO_CAB": "divipola_departamento",
        "MPIO_CAB": "divipola_municipio",
        "AREA_KM2": "area_km2",
    }
    
    # Renombrar columnas existentes
    existing_mapping = {k: v for k, v in column_mapping.items() if k in gdf.columns}
    gdf = gdf.rename(columns=existing_mapping)
    
    # Asegurar sistema de coordenadas WGS84
    if gdf.crs is not None:
        gdf = gdf.to_crs("EPSG:4326")
    
    return gdf


def _create_empty_geodataframe(nivel: str):
    """
    Crear GeoDataFrame vacío con schema correcto.
    
    Parameters:
    - nivel: Nivel geográfico
    
    Returns:
    - GeoDataFrame vacío
    """
    import geopandas as gpd
    from shapely.geometry import Point
    
    columns = [
        "divipola",
        "divipola_municipio",
        "divipola_departamento",
        "nombre_municipio",
        "nombre_departamento",
        "area_km2",
        "geometry",
    ]
    
    gdf = gpd.GeoDataFrame(columns=columns, crs="EPSG:4326")
    gdf["geometry"] = gpd.GeoSeries([Point(0, 0)])
    
    return gdf


def _add_ingestion_metadata(df: pd.DataFrame, version_mgn: str) -> pd.DataFrame:
    """
    Agregar metadatos de ingesta al DataFrame.
    """
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_source"] = "dane_geoportal"
    df["_source_version"] = f"MGN_{version_mgn}"
    df["_extraction_method"] = "DESCARGA_DIRECTA"
    
    checksum = hashlib.md5(df.to_json().encode()).hexdigest()
    df["_checksum_md5"] = checksum
    
    return df


def check_geoportal_vigencia() -> Dict[str, Any]:
    """
    Verificar versión más reciente del MGN.
    
    Returns:
    - Dict con información de versión disponible
    """
    # TODO: Implementar scraping de DANE Geoportal
    return {
        "ultima_version": "MGN_2024",
        "proxima_actualizacion": "2025-Q2",
        "frecuencia": "semestral",
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    resultado = extract_dane_geoportal(
        nivel="municipal",
        formato_salida="GeoJSON",
        force_download=False,
    )
    print(f"Resultado: {resultado}")
