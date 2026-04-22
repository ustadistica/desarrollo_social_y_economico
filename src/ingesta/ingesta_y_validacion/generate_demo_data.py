import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Rutas
ROOT = Path("c:/Users/user/Documents/001 Uni/Octavo/CONSULTORIA/desarrolo eco/desarrollo_social_y_economico-main (2)/desarrollo_social_y_economico-main")
DATOS_BRONZE = ROOT / "datos" / "bronze"

def create_mock_cnpv():
    # 5 Municipios de ejemplo
    data = {
        'municipio': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena'],
        'divipola_municipio': ['11001', '05001', '76001', '08001', '13001'],
        'ipm': [10.5, 12.3, 15.1, 18.2, 22.4],
        'nbi': [5.2, 6.1, 8.4, 10.2, 12.5],
        'poblacion': [7900000, 2500000, 2200000, 1300000, 1000000],
        'pobreza_monetaria': [25.0, 28.5, 32.1, 35.4, 40.2],
        'deficit_habitacional_cuantitativo': [1.2, 2.1, 3.4, 4.2, 5.5],
        'anio': [2024]*5
    }
    df = pd.DataFrame(data)
    
    # Metadata técnica (requerida por el pipeline)
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = 'Mock Server'
    
    out_dir = DATOS_BRONZE / "dane_cnpv" / f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "cnpv_data.parquet")
    print(f"Mock CNPV creado en {out_dir}")

def create_mock_cenu():
    data = {
        'municipio': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena'],
        'divipola_municipio': ['11001', '05001', '76001', '08001', '13001'],
        'total_micronegocios': [150000, 80000, 70000, 45000, 35000],
        'economia_popular_unidades': [60000, 35000, 30000, 20000, 15000],
        'codigo_ciiu': ['G47', 'I56', 'G46', 'C14', 'I55'],
        'anio': [2024]*5
    }
    df = pd.DataFrame(data)
    df['_ingestion_timestamp'] = datetime.now().isoformat()
    df['_source'] = 'Mock Server'
    
    out_dir = DATOS_BRONZE / "dane_cenu" / f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "cenu_data.parquet")
    print(f"Mock CENU creado en {out_dir}")

def setup_secop_data():
    source = ROOT / "datos" / "secop_nuevos1.parquet"
    if source.exists():
        df = pd.read_parquet(source)
        # Adaptar nombres mínimamente si es necesario
        df['_ingestion_timestamp'] = datetime.now().isoformat()
        
        out_dir = DATOS_BRONZE / "secop_ii" / f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}"
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_dir / "secop_data.parquet")
        print(f"Datos SECOP reales movidos a {out_dir}")
    else:
        print("No se encontró secop_nuevos1.parquet")

if __name__ == "__main__":
    create_mock_cnpv()
    create_mock_cenu()
    setup_secop_data()
