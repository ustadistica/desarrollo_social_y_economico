import pandas as pd
from pathlib import Path

file_path = Path('../datos/plata/fact_vulnerabilidad/fact_vulnerabilidad.parquet')
if file_path.exists():
    df = pd.read_parquet(file_path)
    print(f"Columns: {list(df.columns)}")
    if 'divipola_municipio' in df.columns:
        print(f"Nulls in divipola_municipio: {df['divipola_municipio'].isna().sum()}")
        print(f"Unique values: {df['divipola_municipio'].unique()[:10]}")
    else:
        print("COLUMN divipola_municipio IS MISSING")
else:
    print(f"File not found: {file_path}")
