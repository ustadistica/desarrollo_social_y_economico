"""
Catálogo de códigos DIVIPOLA del DANE.

Permite cargar el listado completo oficial desde un archivo CSV local.
Si el archivo no está presente, se utiliza un diccionario base de contingencia.
"""

import logging
import csv
from typing import Dict, Any, List, Optional
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# Intentar cargar desde CSV oficial si existe
CSV_PATH = Path("datos/bronze/divipola/divipola_oficial.csv")

def _cargar_catalogo_csv() -> Dict[str, Dict[str, Any]]:
    catalogo = {}
    if CSV_PATH.exists():
        try:
            with open(CSV_PATH, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    div_key = str(row.get('divipola_municipio', '')).zfill(5)
                    if len(div_key) == 5:
                        catalogo[div_key] = {
                            'nombre_municipio': row.get('nombre_municipio', ''),
                            'nombre_departamento': row.get('nombre_departamento', ''),
                            'divipola_departamento': div_key[:2],
                            'region': row.get('region', ''),
                            'categoria': row.get('categoria', 'Sexta')
                        }
            if catalogo:
                logger.info(f"Catálogo DIVIPOLA cargado desde CSV: {len(catalogo)} registros")
                return catalogo
        except Exception as e:
            logger.warning(f"Error leyendo CSV DIVIPOLA: {e}")
    return {}

_CATALOGO_DINAMICO = _cargar_catalogo_csv()

# Diccionario base de contingencia (subconjunto)
_DIVIPOLA_BASE: Dict[str, Dict[str, Any]] = {
    # Bogotá D.C.
    '11001': {
        'nombre_municipio': 'Bogotá D.C.',
        'nombre_departamento': 'Bogotá',
        'divipola_departamento': '11',
        'region': 'Bogotá D.C.',
        'categoria': 'Capital',
    },
    
    # Antioquia (05)
    '05001': {
        'nombre_municipio': 'Medellín',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Especial',
    },
    '05002': {
        'nombre_municipio': 'Abejorral',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05004': {
        'nombre_municipio': 'Abriaquí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05021': {
        'nombre_municipio': 'Alejandría',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05030': {
        'nombre_municipio': 'Amagá',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05031': {
        'nombre_municipio': 'Amalfi',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05034': {
        'nombre_municipio': 'Andes',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05036': {
        'nombre_municipio': 'Angelópolis',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05038': {
        'nombre_municipio': 'Angostura',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05040': {
        'nombre_municipio': 'Anorí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05042': {
        'nombre_municipio': 'Anzá',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05044': {
        'nombre_municipio': 'Apartadó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05045': {
        'nombre_municipio': 'Arboletes',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05051': {
        'nombre_municipio': 'Armenia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05055': {
        'nombre_municipio': 'Barbosa',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05059': {
        'nombre_municipio': 'Bello',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Primera',
    },
    '05079': {
        'nombre_municipio': 'Caldas',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05086': {
        'nombre_municipio': 'Caucasia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05088': {
        'nombre_municipio': 'Chigorodó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05101': {
        'nombre_municipio': 'Cisneros',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05107': {
        'nombre_municipio': 'Cocorná',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05113': {
        'nombre_municipio': 'Concepción',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05120': {
        'nombre_municipio': 'Concordia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05125': {
        'nombre_municipio': 'Copacabana',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05129': {
        'nombre_municipio': 'Dabeiba',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05134': {
        'nombre_municipio': 'Donmatías',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05138': {
        'nombre_municipio': 'Ebéjico',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05142': {
        'nombre_municipio': 'El Bagre',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05145': {
        'nombre_municipio': 'El Carmen de Viboral',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05147': {
        'nombre_municipio': 'El Peñol',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05148': {
        'nombre_municipio': 'El Retorno',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05150': {
        'nombre_municipio': 'El Santuario',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05154': {
        'nombre_municipio': 'Entrerríos',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05172': {
        'nombre_municipio': 'Girardota',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05190': {
        'nombre_municipio': 'Gómez Plata',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05197': {
        'nombre_municipio': 'Granada',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05206': {
        'nombre_municipio': 'Guadalupe',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05209': {
        'nombre_municipio': 'Guarne',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05212': {
        'nombre_municipio': 'Guatapé',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05234': {
        'nombre_municipio': 'Heliconia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05237': {
        'nombre_municipio': 'Hispania',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05240': {
        'nombre_municipio': 'Itagüí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Primera',
    },
    '05243': {
        'nombre_municipio': 'Ituango',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05245': {
        'nombre_municipio': 'Jardín',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05247': {
        'nombre_municipio': 'Jericó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05250': {
        'nombre_municipio': 'La Ceja',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05253': {
        'nombre_municipio': 'La Estrella',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05254': {
        'nombre_municipio': 'La Pintada',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05256': {
        'nombre_municipio': 'La Unión',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05264': {
        'nombre_municipio': 'Liborina',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05266': {
        'nombre_municipio': 'Maceo',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05282': {
        'nombre_municipio': 'Marinilla',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05306': {
        'nombre_municipio': 'Montebello',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05308': {
        'nombre_municipio': 'Murindó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05310': {
        'nombre_municipio': 'Mutatá',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05313': {
        'nombre_municipio': 'Nariño',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05315': {
        'nombre_municipio': 'Nechí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05318': {
        'nombre_municipio': 'Necoclí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05321': {
        'nombre_municipio': 'Olaya',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05347': {
        'nombre_municipio': 'Peque',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05360': {
        'nombre_municipio': 'Pueblorrico',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05361': {
        'nombre_municipio': 'Puerto Berrío',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05364': {
        'nombre_municipio': 'Puerto Nare',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05376': {
        'nombre_municipio': 'Remedios',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05380': {
        'nombre_municipio': 'Retiro',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05390': {
        'nombre_municipio': 'Rionegro',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Primera',
    },
    '05400': {
        'nombre_municipio': 'Sabanalarga',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05411': {
        'nombre_municipio': 'San Andrés de Cuerquia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05425': {
        'nombre_municipio': 'San Carlos',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05440': {
        'nombre_municipio': 'San Jerónimo',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05467': {
        'nombre_municipio': 'San Vicente Ferrer',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05475': {
        'nombre_municipio': 'Santa Bárbara',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05480': {
        'nombre_municipio': 'Santa Rosa de Osos',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05490': {
        'nombre_municipio': 'Santo Domingo',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05495': {
        'nombre_municipio': 'Segovia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05501': {
        'nombre_municipio': 'Sonsón',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05541': {
        'nombre_municipio': 'Tarazá',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05543': {
        'nombre_municipio': 'Tarso',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05576': {
        'nombre_municipio': 'Titiribí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05579': {
        'nombre_municipio': 'Toledo',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05585': {
        'nombre_municipio': 'Turbo',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Cuarta',
    },
    '05604': {
        'nombre_municipio': 'Uramita',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05607': {
        'nombre_municipio': 'Urrao',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05615': {
        'nombre_municipio': 'Valdivia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05628': {
        'nombre_municipio': 'Venecia',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05631': {
        'nombre_municipio': 'Vigía del Fuerte',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05642': {
        'nombre_municipio': 'Yalí',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05647': {
        'nombre_municipio': 'Yarumal',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    '05649': {
        'nombre_municipio': 'Yolombó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05652': {
        'nombre_municipio': 'Yondó',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Sexta',
    },
    '05659': {
        'nombre_municipio': 'Zaragoza',
        'nombre_departamento': 'Antioquia',
        'divipola_departamento': '05',
        'region': 'Antioquia',
        'categoria': 'Quinta',
    },
    
    # Valle del Cauca (76)
    '76001': {
        'nombre_municipio': 'Cali',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Especial',
    },
    '76020': {
        'nombre_municipio': 'Alcalá',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76036': {
        'nombre_municipio': 'Andalucía',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Quinta',
    },
    '76041': {
        'nombre_municipio': 'Ansermanuevo',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76054': {
        'nombre_municipio': 'Argelia',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76100': {
        'nombre_municipio': 'Buga',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Segunda',
    },
    '76109': {
        'nombre_municipio': 'Buenaventura',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Segunda',
    },
    '76111': {
        'nombre_municipio': 'Cartago',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Segunda',
    },
    '76122': {
        'nombre_municipio': 'El Águila',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76126': {
        'nombre_municipio': 'El Cairo',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76130': {
        'nombre_municipio': 'El Cerrito',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Quinta',
    },
    '76137': {
        'nombre_municipio': 'El Dovio',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76147': {
        'nombre_municipio': 'Florida',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76233': {
        'nombre_municipio': 'Ginebra',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76243': {
        'nombre_municipio': 'Guacarí',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76246': {
        'nombre_municipio': 'Jamundí',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Cuarta',
    },
    '76248': {
        'nombre_municipio': 'La Cumbre',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76250': {
        'nombre_municipio': 'La Unión',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76275': {
        'nombre_municipio': 'Obando',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76306': {
        'nombre_municipio': 'Palmira',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Primera',
    },
    '76318': {
        'nombre_municipio': 'Pradera',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Quinta',
    },
    '76364': {
        'nombre_municipio': 'Restrepo',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76373': {
        'nombre_municipio': 'Riofrío',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76377': {
        'nombre_municipio': 'Roldanillo',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76400': {
        'nombre_municipio': 'San Pedro',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76403': {
        'nombre_municipio': 'Sevilla',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76520': {
        'nombre_municipio': 'Toro',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76563': {
        'nombre_municipio': 'Trujillo',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76577': {
        'nombre_municipio': 'Tuluá',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Primera',
    },
    '76580': {
        'nombre_municipio': 'Ulloa',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76606': {
        'nombre_municipio': 'Versalles',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76616': {
        'nombre_municipio': 'Vijes',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76622': {
        'nombre_municipio': 'Yotoco',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
    '76670': {
        'nombre_municipio': 'Zarzal',
        'nombre_departamento': 'Valle del Cauca',
        'divipola_departamento': '76',
        'region': 'Valle del Cauca',
        'categoria': 'Sexta',
    },
}

DIVIPOLA_COMPLETO = _CATALOGO_DINAMICO if _CATALOGO_DINAMICO else _DIVIPOLA_BASE

def cargar_divipola_desde_csv(archivo_csv: Path) -> Dict[str, Dict[str, Any]]:
    """
    Cargar catálogo DIVIPOLA desde archivo CSV.
    
    Parameters:
    - archivo_csv: Ruta al archivo CSV
    
    Returns:
    - Dict con catálogo DIVIPOLA
    """
    import pandas as pd
    
    if not archivo_csv.exists():
        logger.warning(f"Archivo CSV no encontrado: {archivo_csv}")
        logger.info("Usando catálogo DIVIPOLA embebido")
        return DIVIPOLA_COMPLETO
    
    try:
        df = pd.read_csv(archivo_csv, encoding='utf-8')
        
        catalogo = {}
        for _, row in df.iterrows():
            divipola = str(row['DIVIPOLA']).zfill(5)
            catalogo[divipola] = {
                'nombre_municipio': row['NOMBRE_MUNICIPIO'],
                'nombre_departamento': row['NOMBRE_DEPARTAMENTO'],
                'divipola_departamento': str(row['DIVIPOLA_DEPARTAMENTO']).zfill(2),
                'region': row.get('REGION', 'Sin región'),
                'categoria': row.get('CATEGORIA', 'Sin categoría'),
            }
        
        logger.info(f"Catálogo DIVIPOLA cargado: {len(catalogo)} municipios")
        
        return catalogo
        
    except Exception as e:
        logger.error(f"Error cargando DIVIPOLA: {e}")
        logger.info("Usando catálogo DIVIPOLA embebido")
        return DIVIPOLA_COMPLETO


def get_municipio_info(divipola: str) -> Optional[Dict[str, Any]]:
    """
    Obtener información de un municipio por DIVIPOLA.
    
    Parameters:
    - divipola: Código DIVIPOLA
    
    Returns:
    - Dict con información o None si no existe
    """
    divipola = str(divipola).zfill(5)
    return DIVIPOLA_COMPLETO.get(divipola)


def get_municipios_by_departamento(divipola_dep: str) -> List[Dict[str, Any]]:
    """
    Obtener lista de municipios por departamento.
    
    Parameters:
    - divipola_dep: Código DIVIPOLA del departamento (2 dígitos)
    
    Returns:
    - Lista de dicts con información de municipios
    """
    divipola_dep = str(divipola_dep).zfill(2)
    
    return [
        {'divipola': divipola, **info}
        for divipola, info in DIVIPOLA_COMPLETO.items()
        if info['divipola_departamento'] == divipola_dep
    ]


def get_municipios_by_region(region: str) -> List[Dict[str, Any]]:
    """
    Obtener lista de municipios por región.
    
    Parameters:
    - region: Nombre de la región
    
    Returns:
    - Lista de dicts con información de municipios
    """
    return [
        {'divipola': divipola, **info}
        for divipola, info in DIVIPOLA_COMPLETO.items()
        if info.get('region', '').lower() == region.lower()
    ]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Ejemplo de uso
    print(f"Total municipios en catálogo: {len(DIVIPOLA_COMPLETO)}")
    
    # Buscar municipio
    info = get_municipio_info('11001')
    print(f"Bogotá: {info}")
    
    # Municipios de Antioquia
    antioquia = get_municipios_by_departamento('05')
    print(f"Municipios de Antioquia: {len(antioquia)}")
