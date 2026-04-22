"""
Creación de tablas de dimensión para capa Plata.

Tablas:
- dim_municipio: Dimensiones geográficas
- dim_tiempo: Dimensiones temporales
- dim_sector_ciiu: Clasificación económica CIIU
- dim_sector_unspsc: Clasificación de compras UNSPSC
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def create_dim_municipio(
    geoportal_df: Optional[pd.DataFrame] = None,
    cnpv_df: Optional[pd.DataFrame] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear dimensión de municipios.
    
    Parameters:
    - geoportal_df: DataFrame del Geoportal DANE (geometría)
    - cnpv_df: DataFrame del CNPV (población proyectada)
    - output_path: Ruta de salida para archivo Parquet
    
    Returns:
    - Dict con metadata de creación y ruta del archivo
    """
    logger.info("Creando dim_municipio...")
    
    # Cargar catálogo DIVIPOLA base
    from pipeline.transform.standardize_geo import load_divipola_catalog
    dim = load_divipola_catalog()
    
    # Agregar región (mapeo departamento -> región)
    REGION_MAP = {
        'Bogotá': 'Bogotá D.C.',
        'Antioquia': 'Antioquia',
        'Valle del Cauca': 'Valle del Cauca',
        'Atlántico': 'Caribe',
        'Bolívar': 'Caribe',
        'Córdoba': 'Caribe',
        'Sucre': 'Caribe',
        'Magdalena': 'Caribe',
        'Cesar': 'Caribe',
        'La Guajira': 'Caribe',
        'Santander': 'Santanderes',
        'Norte de Santander': 'Santanderes',
        'Boyacá': 'Centro Oriente',
        'Cundinamarca': 'Centro Oriente',
        'Meta': 'Centro Oriente',
        'Casanare': 'Centro Oriente',
        'Arauca': 'Centro Oriente',
        'Nariño': 'Pacífico',
        'Cauca': 'Pacífico',
        'Valle del Cauca': 'Pacífico',
        'Chocó': 'Pacífico',
        'Amazonas': 'Amazonía',
        'Guainía': 'Amazonía',
        'Guaviare': 'Amazonía',
        'Vaupés': 'Amazonía',
        'Vichada': 'Amazonía',
        'Putumayo': 'Amazonía',
        'Caquetá': 'Amazonía',
        'Huila': 'Pacífico',
        'Tolima': 'Pacífico',
        'Caldas': 'Pacífico',
        'Risaralda': 'Pacífico',
        'Quindío': 'Pacífico',
        'San Andrés y Providencia': 'Insular',
    }
    
    dim['region'] = dim['nombre_departamento'].map(REGION_MAP).fillna('Otra')
    
    # Categoría municipal (simplificada - en producción usar clasificación oficial)
    def get_categoria_municipal(row) -> str:
        # Clasificación basada en población (simplificada)
        # En producción, usar clasificación del DNP
        return 'Clasificación pendiente'
    
    dim['categoria_municipal'] = dim.apply(get_categoria_municipal, axis=1)
    
    # Área km² (de geoportal si está disponible)
    dim['area_km2'] = np.nan
    if geoportal_df is not None and 'area_km2' in geoportal_df.columns:
        geo_area = geoportal_df[['divipola_municipio', 'area_km2']].drop_duplicates()
        dim = dim.merge(geo_area, on='divipola_municipio', how='left')
    
    # Población proyectada (de CNPV si está disponible)
    dim['poblacion_proyectada'] = None
    if cnpv_df is not None and 'poblacion_total' in cnpv_df.columns:
        cnpv_pop = cnpv_df[['divipola_municipio', 'poblacion_total']].drop_duplicates()
        dim = dim.merge(cnpv_pop, on='divipola_municipio', how='left')
        dim['poblacion_proyectada'] = dim['poblacion_total']
        dim = dim.drop(columns=['poblacion_total'])
    
    # Coordenadas (centroide - en producción usar geoportal)
    dim['latitud'] = np.nan
    dim['longitud'] = np.nan
    
    # Geometría (WKT - en producción usar geoportal)
    dim['geom_wkt'] = None
    
    # Vigencia
    dim['vigencia'] = datetime.now().year
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.get_plata_path('dim_municipio')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'dim_municipio.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dim.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"dim_municipio creada: {len(dim)} municipios")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(dim),
        'columnas': list(dim.columns),
    }


def create_dim_tiempo(
    anio_inicio: int = 2018,
    anio_fin: Optional[int] = None,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear dimensión de tiempo.
    
    Parameters:
    - anio_inicio: Año inicial
    - anio_fin: Año final (default: año actual + 1)
    - output_path: Ruta de salida para archivo Parquet
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando dim_tiempo...")
    
    if anio_fin is None:
        anio_fin = datetime.now().year + 1
    
    # Generar rango de fechas
    fechas = pd.date_range(
        start=f'{anio_inicio}-01-01',
        end=f'{anio_fin}-12-31',
        freq='D',
    )
    
    dim = pd.DataFrame({'fecha': fechas})
    
    # Fecha key (YYYYMMDD)
    dim['fecha_key'] = dim['fecha'].dt.strftime('%Y%m%d').astype(int)
    
    # Componentes de fecha
    dim['anio'] = dim['fecha'].dt.year
    dim['trimestre'] = dim['fecha'].dt.quarter
    dim['mes'] = dim['fecha'].dt.month
    dim['dia'] = dim['fecha'].dt.day
    dim['dia_semana'] = dim['fecha'].dt.dayofweek
    dim['dia_anio'] = dim['fecha'].dt.dayofyear
    
    # Año fiscal (en Colombia = año calendario)
    dim['anio_fiscal'] = dim['anio']
    
    # Banderas de periodo
    dim['es_fin_mes'] = dim['dia'] == dim['fecha'].dt.daysinmonth
    dim['es_fin_trimestre'] = dim['mes'].isin([3, 6, 9, 12]) & dim['es_fin_mes']
    dim['es_fin_anio'] = (dim['mes'] == 12) & dim['es_fin_mes']
    dim['es_inicio_mes'] = dim['dia'] == 1
    dim['es_inicio_anio'] = (dim['mes'] == 1) & (dim['dia'] == 1)
    
    # Nombre de mes
    mes_nombres = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
    }
    dim['nombre_mes'] = dim['mes'].map(mes_nombres)
    
    # Trimestre texto
    trimestre_nombres = {
        1: 'Q1', 2: 'Q2', 3: 'Q3', 4: 'Q4',
    }
    dim['nombre_trimestre'] = dim['trimestre'].map(trimestre_nombres)
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.get_plata_path('dim_tiempo')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'dim_tiempo.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dim.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"dim_tiempo creada: {len(dim)} días")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(dim),
        'columnas': list(dim.columns),
    }


def create_dim_sector_ciiu(
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear dimensión de sectores económicos CIIU.
    
    Parameters:
    - output_path: Ruta de salida para archivo Parquet
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando dim_sector_ciiu...")
    
    # CIIU Rev. 4 A.C. (muestra - completar con todos los códigos)
    ciiu_data = [
        # Sección A - Agricultura, ganadería, caza y silvicultura
        {'codigo_ciiu': 'A01', 'descripcion': 'Agricultura, ganadería, caza y actividades de servicios relacionadas', 'seccion': 'A', 'division': '01', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'A011', 'descripcion': 'Cultivo de plantas no perennes', 'seccion': 'A', 'division': '01', 'grupo': '011', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'A0111', 'descripcion': 'Cultivo de cereales (excepto arroz), legumbres y semillas oleaginosas', 'seccion': 'A', 'division': '01', 'grupo': '011', 'clase': '0111', 'categoria': '01110'},
        {'codigo_ciiu': 'A0112', 'descripcion': 'Cultivo de arroz', 'seccion': 'A', 'division': '01', 'grupo': '011', 'clase': '0112', 'categoria': '01120'},
        {'codigo_ciiu': 'A012', 'descripcion': 'Cultivo de plantas perennes', 'seccion': 'A', 'division': '01', 'grupo': '012', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'A02', 'descripcion': 'Explotación forestal y extracción de madera', 'seccion': 'A', 'division': '02', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'A03', 'descripcion': 'Pesca y acuicultura', 'seccion': 'A', 'division': '03', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección B - Explotación de minas y canteras
        {'codigo_ciiu': 'B05', 'descripcion': 'Explotación de minas de carbón y lignito', 'seccion': 'B', 'division': '05', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'B06', 'descripcion': 'Extracción de petróleo crudo y gas natural', 'seccion': 'B', 'division': '06', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'B07', 'descripcion': 'Explotación de minas de minerales metálicos', 'seccion': 'B', 'division': '07', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'B08', 'descripcion': 'Explotación de minas y canteras de otros minerales no metálicos', 'seccion': 'B', 'division': '08', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección C - Industrias manufactureras
        {'codigo_ciiu': 'C10', 'descripcion': 'Elaboración de productos alimenticios', 'seccion': 'C', 'division': '10', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C101', 'descripcion': 'Elaboración y preservación de carne, pescado, crustáceos y moluscos', 'seccion': 'C', 'division': '10', 'grupo': '101', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C1010', 'descripcion': 'Elaboración y preservación de carne, pescado, crustáceos y moluscos', 'seccion': 'C', 'division': '10', 'grupo': '101', 'clase': '1010', 'categoria': '10100'},
        {'codigo_ciiu': 'C11', 'descripcion': 'Elaboración de bebidas', 'seccion': 'C', 'division': '11', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C13', 'descripcion': 'Fabricación de textiles', 'seccion': 'C', 'division': '13', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C14', 'descripcion': 'Fabricación de prendas de vestir', 'seccion': 'C', 'division': '14', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C20', 'descripcion': 'Fabricación de sustancias y productos químicos', 'seccion': 'C', 'division': '20', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C21', 'descripcion': 'Fabricación de productos farmacéuticos y preparados farmacéuticos', 'seccion': 'C', 'division': '21', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C22', 'descripcion': 'Fabricación de productos de caucho y plástico', 'seccion': 'C', 'division': '22', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C23', 'descripcion': 'Fabricación de otros productos minerales no metálicos', 'seccion': 'C', 'division': '23', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C24', 'descripcion': 'Fabricación de metales comunes', 'seccion': 'C', 'division': '24', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C25', 'descripcion': 'Fabricación de productos elaborados de metal, excepto maquinaria y equipo', 'seccion': 'C', 'division': '25', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C26', 'descripcion': 'Fabricación de productos informáticos, electrónicos y ópticos', 'seccion': 'C', 'division': '26', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C27', 'descripcion': 'Fabricación de maquinaria y aparatos eléctricos', 'seccion': 'C', 'division': '27', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C28', 'descripcion': 'Fabricación de maquinaria y equipo n.c.p.', 'seccion': 'C', 'division': '28', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C29', 'descripcion': 'Fabricación de vehículos automotores, remolques y semirremolques', 'seccion': 'C', 'division': '29', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C30', 'descripcion': 'Fabricación de otro tipo de equipo de transporte', 'seccion': 'C', 'division': '30', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C31', 'descripcion': 'Fabricación de muebles', 'seccion': 'C', 'division': '31', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C32', 'descripcion': 'Otras industrias manufactureras', 'seccion': 'C', 'division': '32', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'C33', 'descripcion': 'Instalación y mantenimiento de maquinaria y equipo', 'seccion': 'C', 'division': '33', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección D - Suministro de electricidad, gas, vapor y aire acondicionado
        {'codigo_ciiu': 'D35', 'descripcion': 'Suministro de electricidad, gas, vapor y aire acondicionado', 'seccion': 'D', 'division': '35', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección E - Suministro de agua; actividades de saneamiento ambiental
        {'codigo_ciiu': 'E36', 'descripcion': 'Captación, tratamiento y suministro de agua', 'seccion': 'E', 'division': '36', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'E37', 'descripcion': 'Alcantarillado', 'seccion': 'E', 'division': '37', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'E38', 'descripcion': 'Actividades de gestión de desechos', 'seccion': 'E', 'division': '38', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'E39', 'descripcion': 'Actividades de saneamiento ambiental', 'seccion': 'E', 'division': '39', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección F - Construcción
        {'codigo_ciiu': 'F41', 'descripcion': 'Construcción de edificios', 'seccion': 'F', 'division': '41', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'F410', 'descripcion': 'Construcción de edificios', 'seccion': 'F', 'division': '41', 'grupo': '410', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'F4101', 'descripcion': 'Construcción de edificios residenciales', 'seccion': 'F', 'division': '41', 'grupo': '410', 'clase': '4101', 'categoria': '41010'},
        {'codigo_ciiu': 'F4102', 'descripcion': 'Construcción de edificios no residenciales', 'seccion': 'F', 'division': '41', 'grupo': '410', 'clase': '4102', 'categoria': '41020'},
        {'codigo_ciiu': 'F42', 'descripcion': 'Construcción de obras de infraestructura', 'seccion': 'F', 'division': '42', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'F421', 'descripcion': 'Construcción de carreteras y vías férreas', 'seccion': 'F', 'division': '42', 'grupo': '421', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'F4210', 'descripcion': 'Construcción de carreteras y vías férreas', 'seccion': 'F', 'division': '42', 'grupo': '421', 'clase': '4210', 'categoria': '42100'},
        {'codigo_ciiu': 'F422', 'descripcion': 'Construcción de proyectos de servicio público', 'seccion': 'F', 'division': '42', 'grupo': '422', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'F4220', 'descripcion': 'Construcción de proyectos de servicio público', 'seccion': 'F', 'division': '42', 'grupo': '422', 'clase': '4220', 'categoria': '42200'},
        {'codigo_ciiu': 'F43', 'descripcion': 'Actividades de construcción especializada', 'seccion': 'F', 'division': '43', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección G - Comercio al por mayor y al por menor
        {'codigo_ciiu': 'G45', 'descripcion': 'Venta, mantenimiento y reparación de vehículos automotores', 'seccion': 'G', 'division': '45', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'G46', 'descripcion': 'Comercio al por mayor', 'seccion': 'G', 'division': '46', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'G47', 'descripcion': 'Comercio al por menor', 'seccion': 'G', 'division': '47', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección H - Transporte y almacenamiento
        {'codigo_ciiu': 'H49', 'descripcion': 'Transporte terrestre y por tuberías', 'seccion': 'H', 'division': '49', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'H50', 'descripcion': 'Transporte por agua', 'seccion': 'H', 'division': '50', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'H51', 'descripcion': 'Transporte aéreo', 'seccion': 'H', 'division': '51', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'H52', 'descripcion': 'Almacenamiento y actividades conexas de transporte', 'seccion': 'H', 'division': '52', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'H53', 'descripcion': 'Actividades de correos y mensajería', 'seccion': 'H', 'division': '53', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección I - Alojamiento y servicios de comida
        {'codigo_ciiu': 'I55', 'descripcion': 'Alojamiento', 'seccion': 'I', 'division': '55', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'I56', 'descripcion': 'Actividades de servicios de comidas y bebidas', 'seccion': 'I', 'division': '56', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección J - Información y comunicaciones
        {'codigo_ciiu': 'J58', 'descripcion': 'Actividades editoriales', 'seccion': 'J', 'division': '58', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'J59', 'descripcion': 'Actividades cinematográficas, de video y de programas de televisión', 'seccion': 'J', 'division': '59', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'J60', 'descripcion': 'Actividades de programación y emisión de radio y televisión', 'seccion': 'J', 'division': '60', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'J61', 'descripcion': 'Telecomunicaciones', 'seccion': 'J', 'division': '61', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'J62', 'descripcion': 'Desarrollo de sistemas informáticos', 'seccion': 'J', 'division': '62', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'J63', 'descripcion': 'Actividades de servicios de información', 'seccion': 'J', 'division': '63', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección K - Actividades financieras y de seguros
        {'codigo_ciiu': 'K64', 'descripcion': 'Actividades de servicios financieros', 'seccion': 'K', 'division': '64', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'K65', 'descripcion': 'Actividades de seguros, de reaseguros y de fondos de pensiones', 'seccion': 'K', 'division': '65', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'K66', 'descripcion': 'Actividades auxiliares de las actividades financieras y de seguros', 'seccion': 'K', 'division': '66', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección L - Actividades inmobiliarias
        {'codigo_ciiu': 'L68', 'descripcion': 'Actividades inmobiliarias', 'seccion': 'L', 'division': '68', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección M - Actividades profesionales, científicas y técnicas
        {'codigo_ciiu': 'M69', 'descripcion': 'Actividades jurídicas y de contabilidad', 'seccion': 'M', 'division': '69', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M70', 'descripcion': 'Actividades de oficinas principales', 'seccion': 'M', 'division': '70', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M71', 'descripcion': 'Actividades de arquitectura e ingeniería', 'seccion': 'M', 'division': '71', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M72', 'descripcion': 'Actividades de investigación científica y desarrollo', 'seccion': 'M', 'division': '72', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M73', 'descripcion': 'Publicidad y estudios de mercado', 'seccion': 'M', 'division': '73', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M74', 'descripcion': 'Otras actividades profesionales, científicas y técnicas', 'seccion': 'M', 'division': '74', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'M75', 'descripcion': 'Actividades veterinarias', 'seccion': 'M', 'division': '75', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección N - Actividades administrativas y de servicios de apoyo
        {'codigo_ciiu': 'N77', 'descripcion': 'Actividades de alquiler y arrendamiento', 'seccion': 'N', 'division': '77', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'N78', 'descripcion': 'Actividades relacionadas con el empleo', 'seccion': 'N', 'division': '78', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'N79', 'descripcion': 'Actividades de agencias de viajes y servicios de reservas', 'seccion': 'N', 'division': '79', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'N80', 'descripcion': 'Actividades de seguridad e investigación', 'seccion': 'N', 'division': '80', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'N81', 'descripcion': 'Actividades relacionadas con edificios y jardines', 'seccion': 'N', 'division': '81', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'N82', 'descripcion': 'Actividades administrativas y de apoyo de oficina', 'seccion': 'N', 'division': '82', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección O - Administración pública y defensa
        {'codigo_ciiu': 'O84', 'descripcion': 'Administración pública y defensa; planes de seguridad social de afiliación obligatoria', 'seccion': 'O', 'division': '84', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección P - Educación
        {'codigo_ciiu': 'P85', 'descripcion': 'Educación', 'seccion': 'P', 'division': '85', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección Q - Atención de la salud humana y de apoyo social
        {'codigo_ciiu': 'Q86', 'descripcion': 'Actividades de atención de la salud humana', 'seccion': 'Q', 'division': '86', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'Q87', 'descripcion': 'Actividades de atención residencial', 'seccion': 'Q', 'division': '87', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'Q88', 'descripcion': 'Actividades de apoyo social sin alojamiento', 'seccion': 'Q', 'division': '88', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección R - Actividades artísticas, de entretenimiento y recreación
        {'codigo_ciiu': 'R90', 'descripcion': 'Actividades creativas, de artes y entretenimiento', 'seccion': 'R', 'division': '90', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'R91', 'descripcion': 'Actividades de bibliotecas, archivos, museos y actividades culturales', 'seccion': 'R', 'division': '91', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'R92', 'descripcion': 'Actividades de juegos de azar y apuestas', 'seccion': 'R', 'division': '92', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'R93', 'descripcion': 'Actividades deportivas, de entretenimiento y recreativas', 'seccion': 'R', 'division': '93', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección S - Otras actividades de servicios
        {'codigo_ciiu': 'S94', 'descripcion': 'Actividades asociativas', 'seccion': 'S', 'division': '94', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'S95', 'descripcion': 'Actividades de reparación de computadores y efectos personales', 'seccion': 'S', 'division': '95', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'S96', 'descripcion': 'Otras actividades de servicios personales', 'seccion': 'S', 'division': '96', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección T - Actividades de los hogares
        {'codigo_ciiu': 'T97', 'descripcion': 'Actividades de los hogares privados que actúan como empleadores de personal doméstico', 'seccion': 'T', 'division': '97', 'grupo': '', 'clase': '', 'categoria': ''},
        {'codigo_ciiu': 'T98', 'descripcion': 'Actividades de los hogares privados que producen bienes y servicios para uso propio', 'seccion': 'T', 'division': '98', 'grupo': '', 'clase': '', 'categoria': ''},
        
        # Sección U - Actividades de organizaciones y órganos extraterritoriales
        {'codigo_ciiu': 'U99', 'descripcion': 'Actividades de organizaciones y órganos extraterritoriales', 'seccion': 'U', 'division': '99', 'grupo': '', 'clase': '', 'categoria': ''},
    ]
    
    dim = pd.DataFrame(ciiu_data)
    
    # Identificar economía popular (simplificado - en producción usar definición DANE)
    ECONOMIA_POPULAR_SECCIONES = ['G', 'I', 'C', 'F', 'N']
    dim['economia_popular'] = dim['seccion'].isin(ECONOMIA_POPULAR_SECCIONES)
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.get_plata_path('dim_sector_ciiu')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'dim_sector_ciiu.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dim.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"dim_sector_ciiu creada: {len(dim)} códigos")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(dim),
        'columnas': list(dim.columns),
    }


def create_dim_sector_unspsc(
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Crear dimensión de sectores UNSPSC para SECOP II.
    
    Parameters:
    - output_path: Ruta de salida para archivo Parquet
    
    Returns:
    - Dict con metadata de creación
    """
    logger.info("Creando dim_sector_unspsc...")
    
    # UNSPSC (muestra - completar con todos los códigos relevantes)
    unspsc_data = [
        {'codigo_unspsc': '10000000', 'descripcion': 'Materiales y suministros para laboratorio y química', 'segmento': '10', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '20000000', 'descripcion': 'Minerales y estructuras y materiales y suministros para extracción', 'segmento': '20', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '30000000', 'descripcion': 'Suministros y equipos para industria petrolera y gas natural', 'segmento': '30', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '40000000', 'descripcion': 'Equipo y suministros para distribución y almacenamiento de electricidad', 'segmento': '40', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '50000000', 'descripcion': 'Productos alimenticios, bebidas y tabaco y productos de cultivo', 'segmento': '50', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '60000000', 'descripcion': 'Productos químicos y biológicos y materiales y suministros', 'segmento': '60', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '70000000', 'descripcion': 'Equipos y suministros para construcción y mantenimiento de edificios', 'segmento': '70', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '72000000', 'descripcion': 'Servicios de construcción', 'segmento': '72', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '72100000', 'descripcion': 'Servicios de construcción de edificios', 'segmento': '72', 'familia': '7210', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '72200000', 'descripcion': 'Servicios de construcción de infraestructura', 'segmento': '72', 'familia': '7220', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '80000000', 'descripcion': 'Equipos y suministros para transporte y almacenamiento', 'segmento': '80', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '90000000', 'descripcion': 'Equipos y suministros para servicios médicos y de salud', 'segmento': '90', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '1000000', 'descripcion': 'Servicios de tecnología de información y telecomunicaciones', 'segmento': '10', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '11000000', 'descripcion': 'Equipos y suministros para minería y procesamiento de minerales', 'segmento': '11', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '12000000', 'descripcion': 'Equipos y suministros para agricultura y silvicultura', 'segmento': '12', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '13000000', 'descripcion': 'Equipos y suministros para pesca y acuicultura', 'segmento': '13', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '14000000', 'descripcion': 'Equipos y suministros para industria manufacturera', 'segmento': '14', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '15000000', 'descripcion': 'Equipos y suministros para industria textil y de cuero', 'segmento': '15', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '16000000', 'descripcion': 'Equipos y suministros para industria de papel y impresión', 'segmento': '16', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '17000000', 'descripcion': 'Equipos y suministros para servicios educativos y de capacitación', 'segmento': '17', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '18000000', 'descripcion': 'Equipos y suministros para servicios de seguridad y protección', 'segmento': '18', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '19000000', 'descripcion': 'Equipos y suministros para servicios ambientales', 'segmento': '19', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '21000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria', 'segmento': '21', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '22000000', 'descripcion': 'Vehículos y accesorios y suministros para transporte', 'segmento': '22', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '23000000', 'descripcion': 'Equipos y suministros para fuerzas del orden público y defensa', 'segmento': '23', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '24000000', 'descripcion': 'Equipos y suministros para servicios deportivos y recreativos', 'segmento': '24', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '25000000', 'descripcion': 'Equipos y suministros para servicios de oficinas', 'segmento': '25', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '26000000', 'descripcion': 'Equipos y suministros para servicios de limpieza', 'segmento': '26', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '27000000', 'descripcion': 'Equipos y suministros para servicios de jardinería', 'segmento': '27', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '28000000', 'descripcion': 'Equipos y suministros para servicios de alojamiento y comida', 'segmento': '28', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '29000000', 'descripcion': 'Equipos y suministros para servicios de entretenimiento', 'segmento': '29', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '31000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de petróleo y gas', 'segmento': '31', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '32000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria minera', 'segmento': '32', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '41000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria eléctrica', 'segmento': '41', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '42000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria electrónica', 'segmento': '42', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '43000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de telecomunicaciones', 'segmento': '43', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '44000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de servicios públicos', 'segmento': '44', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '45000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de construcción', 'segmento': '45', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '46000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de transporte', 'segmento': '46', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '47000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de servicios médicos', 'segmento': '47', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '48000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de servicios financieros', 'segmento': '48', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '49000000', 'descripcion': 'Maquinaria y accesorios y suministros para industria de servicios educativos', 'segmento': '49', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '51000000', 'descripcion': 'Servicios profesionales', 'segmento': '51', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '52000000', 'descripcion': 'Servicios de transporte y almacenamiento', 'segmento': '52', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '53000000', 'descripcion': 'Servicios de telecomunicaciones y broadcasting', 'segmento': '53', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '54000000', 'descripcion': 'Servicios de tecnología de información', 'segmento': '54', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '55000000', 'descripcion': 'Servicios de investigación y desarrollo', 'segmento': '55', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '56000000', 'descripcion': 'Servicios de educación y capacitación', 'segmento': '56', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '57000000', 'descripcion': 'Servicios de medios y publicidad', 'segmento': '57', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '58000000', 'descripcion': 'Servicios de alojamiento y comida', 'segmento': '58', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '59000000', 'descripcion': 'Servicios de entretenimiento y recreación', 'segmento': '59', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '61000000', 'descripcion': 'Servicios de salud y asistencia social', 'segmento': '61', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '62000000', 'descripcion': 'Servicios de asociaciones y organizaciones', 'segmento': '62', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '63000000', 'descripcion': 'Servicios de reparación y mantenimiento', 'segmento': '63', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '64000000', 'descripcion': 'Servicios de administración pública', 'segmento': '64', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '65000000', 'descripcion': 'Servicios de seguridad y protección', 'segmento': '65', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '66000000', 'descripcion': 'Servicios ambientales', 'segmento': '66', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '67000000', 'descripcion': 'Servicios de limpieza y saneamiento', 'segmento': '67', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '68000000', 'descripcion': 'Servicios de jardinería y paisajismo', 'segmento': '68', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '71000000', 'descripcion': 'Servicios de alquiler y arrendamiento', 'segmento': '71', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '73000000', 'descripcion': 'Servicios de empleo y recursos humanos', 'segmento': '73', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '74000000', 'descripcion': 'Servicios de agencias de viajes', 'segmento': '74', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '75000000', 'descripcion': 'Servicios de seguros y financieros', 'segmento': '75', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '76000000', 'descripcion': 'Servicios legales', 'segmento': '76', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '77000000', 'descripcion': 'Servicios de contabilidad y auditoría', 'segmento': '77', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '78000000', 'descripcion': 'Servicios de consultoría de gestión', 'segmento': '78', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '79000000', 'descripcion': 'Servicios de arquitectura e ingeniería', 'segmento': '79', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '81000000', 'descripcion': 'Servicios de diseño', 'segmento': '81', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '82000000', 'descripcion': 'Servicios de fotografía', 'segmento': '82', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '83000000', 'descripcion': 'Servicios de traducción e interpretación', 'segmento': '83', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '84000000', 'descripcion': 'Servicios de eventos y conferencias', 'segmento': '84', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '85000000', 'descripcion': 'Servicios de seguridad y vigilancia', 'segmento': '85', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '86000000', 'descripcion': 'Servicios de investigación', 'segmento': '86', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '87000000', 'descripcion': 'Servicios de cobranza', 'segmento': '87', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '88000000', 'descripcion': 'Servicios funerarios', 'segmento': '88', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '89000000', 'descripcion': 'Servicios personales', 'segmento': '89', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '91000000', 'descripcion': 'Servicios de fuerzas del orden público y defensa', 'segmento': '91', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '92000000', 'descripcion': 'Servicios de extracción de petróleo y gas', 'segmento': '92', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '93000000', 'descripcion': 'Servicios de minería', 'segmento': '93', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '94000000', 'descripcion': 'Servicios de agricultura y silvicultura', 'segmento': '94', 'familia': '', 'clase': '', 'commodity': ''},
        {'codigo_unspsc': '95000000', 'descripcion': 'Servicios de pesca y acuicultura', 'segmento': '95', 'familia': '', 'clase': '', 'commodity': ''},
    ]
    
    dim = pd.DataFrame(unspsc_data)
    
    # Agregar columna de relación con CIIU (mapeo simplificado)
    # En producción, usar mapeo completo desde utils/ciiu_unspsc_mapping.py
    dim['relacionado_ciiu'] = None
    
    # Mapeo básico segmento -> sección CIIU
    segmento_ciiu_map = {
        '70': 'F',   # Construcción
        '72': 'F',   # Servicios de construcción
        '50': 'A',   # Alimentos -> Agricultura
        '12': 'A',   # Agricultura
        '45': 'F',   # Construcción
        '51': 'M',   # Profesionales
        '79': 'M',   # Arquitectura e ingeniería
    }
    
    dim['relacionado_ciiu'] = dim['segmento'].map(segmento_ciiu_map)
    
    # Guardar
    if output_path is None:
        from pipeline.config.settings import settings
        output_path = settings.get_plata_path('dim_sector_unspsc')
    
    output_path = Path(output_path)
    if not output_path.suffix:
        output_path = output_path / 'dim_sector_unspsc.parquet'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    dim.to_parquet(output_path, index=False, compression='snappy')
    
    logger.info(f"dim_sector_unspsc creada: {len(dim)} códigos")
    
    return {
        'status': 'success',
        'archivo': str(output_path),
        'registros': len(dim),
        'columnas': list(dim.columns),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de creación de dimensiones
    print("Creando dimensiones...")
    
    # dim_tiempo
    resultado = create_dim_tiempo(anio_inicio=2018, anio_fin=2026)
    print(f"dim_tiempo: {resultado}")
    
    # dim_sector_ciiu
    resultado = create_dim_sector_ciiu()
    print(f"dim_sector_ciiu: {resultado}")
    
    # dim_sector_unspsc
    resultado = create_dim_sector_unspsc()
    print(f"dim_sector_unspsc: {resultado}")
