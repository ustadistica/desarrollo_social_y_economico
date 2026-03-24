import pandas as pd
import numpy as np
import os
import glob
from pathlib import Path

def process_ipm_and_etnia():
    print("Iniciando agregación de IPM y Composición Étnica...")
    
    # 1. Cargar IPM
    ipm_file = '../datos/dane_2018/ipm.xlsx'
    if os.path.exists(ipm_file):
        print("1. Cargando archivo IPM...")
        ipm_df = pd.read_excel(ipm_file, sheet_name='IPM_Municipios', skiprows=12)
        ipm_df = ipm_df.rename(columns={
            ipm_df.columns[1]: 'código_municipio', # El índice 1 suele ser Código Municipio
            ipm_df.columns[3]: 'ipm_total'        # El índice 3 suele ser Total
        })
        ipm_df = ipm_df.dropna(subset=['código_municipio'])
        # Asegurar divipola de 5 digitos
        ipm_df['divipola_municipio'] = ipm_df['código_municipio'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)
        ipm_df = ipm_df[['divipola_municipio', 'ipm_total']]
        ipm_df['ipm_total'] = pd.to_numeric(ipm_df['ipm_total'], errors='coerce')
    else:
        print(f"No se encontró IPM en {ipm_file}. Saltando.")
        ipm_df = pd.DataFrame(columns=['divipola_municipio', 'ipm_total'])

    # 2. Cargar Composición Étnica
    print("2. Procesando CENSO 2018 para Etnia...")
    base_dir = r"C:\Users\Usuario\Downloads\Datos\Datos\CENSO 2018 dep"
    csv_files = glob.glob(os.path.join(base_dir, "**", "CNPV*5PER*.CSV"), recursive=True)
    
    etnia_counts = []
    
    for f in csv_files:
        print(f"  Leyendo: {Path(f).name}")
        try:
            # Solo traemos las 3 columnas
            df_chunk = pd.read_csv(f, usecols=['U_DPTO', 'U_MPIO', 'PA1_GRP_ETNIC'])
            df_chunk['divipola_municipio'] = df_chunk['U_DPTO'].astype(str).str.zfill(2) + \
                                             df_chunk['U_MPIO'].astype(str).str.zfill(3)
            
            counts = df_chunk.groupby(['divipola_municipio', 'PA1_GRP_ETNIC']).size().reset_index(name='count')
            etnia_counts.append(counts)
        except Exception as e:
            print(f"Error procesando {Path(f).name}: {e}")
            
    if etnia_counts:
        print("  Consolidando frecuencias a nivel nacional...")
        etnia_df = pd.concat(etnia_counts)
        etnia_df = etnia_df.groupby(['divipola_municipio', 'PA1_GRP_ETNIC'])['count'].sum().reset_index()
        
        etnia_pivot = etnia_df.pivot(index='divipola_municipio', columns='PA1_GRP_ETNIC', values='count').fillna(0)
        
        mapa_etnia = {
            1.0: 'indigena',
            2.0: 'rrom',
            3.0: 'raizal',
            4.0: 'palenquero',
            5.0: 'afro',
            6.0: 'ninguno',
            9.0: 'sin_info'
        }
        
        etnia_pivot.columns = [f"etnia_{mapa_etnia.get(float(c), str(c))}_count" for c in etnia_pivot.columns]
        
        # Calcular porcentajes
        total_poblacion = etnia_pivot.sum(axis=1)
        for col in etnia_pivot.columns:
            etnia_pivot[col.replace('_count', '_pct')] = (etnia_pivot[col] / total_poblacion) * 100
        
        etnia_pivot = etnia_pivot.reset_index()
        # Guardar checkpoint para no descargar de nuevo
        etnia_pivot.to_parquet('../datos/etnia_checkpoint.parquet', compression='snappy')
    else:
        print("  No se encontraron archivos de Etnia. Saltando.")
        etnia_pivot = pd.DataFrame(columns=['divipola_municipio'])

    # 3. Unir al dataset original
    print("3. Haciendo Join con dataset estructurado...")
    base_parquet = '../datos/cruce_secop_dane_sprint2.parquet'
    
    if os.path.exists(base_parquet):
        df_base = pd.read_parquet(base_parquet)
        print(f"  Dataset original: {df_base.shape}")
        
        # Merge IPM
        df_out = df_base.merge(ipm_df, on='divipola_municipio', how='left')
        
        # Merge Etnia
        df_out = df_out.merge(etnia_pivot, on='divipola_municipio', how='left')
        
        print(f"  Dataset tras cruces: {df_out.shape}")
        df_out.to_parquet(base_parquet, engine='pyarrow', compression='snappy')
        print("¡Proceso finalizado! Se actualizó exitosamente cruce_secop_dane_sprint2.parquet.")
    else:
        print(f"ERROR: {base_parquet} no encontrado. Ejecute primero cruce_dane_secop_issue13.py")

if __name__ == '__main__':
    process_ipm_and_etnia()
