import os
import sys
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
consultoria_root = os.path.dirname(project_root)

print("=======================================================")
print(" PROCESAMIENTO PANDAS - HHI CON CRUCE SECOP-DANE")
print("=======================================================")

parquet_cruce = os.path.join(consultoria_root, 'datos', 'processed', 'cruce_secop_dane.parquet')
out_dir_hhi = os.path.join(consultoria_root, 'datos', 'HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv')

print("[1/3] Leyendo dataset cruzado (Parquet)...")
if not os.path.exists(parquet_cruce):
    print(f"ALERTA: No se encontró el cruce en: {parquet_cruce}")
    print("Por favor, ejecuta primero cruce_secop_dane.py para generar el cruce.")
    sys.exit(1)

df_cruce = pd.read_parquet(parquet_cruce)
print(f"    -> Registros cargados: {len(df_cruce)}")

print("[2/3] Preparando y calculando HHI...")

# Filtrar nulos esenciales
df = df_cruce.dropna(subset=['divipola_municipio', 'valor_contrato', 'documento_proveedor']).copy()

# Limpiar año
df['anio_firma'] = df['fecha_de_firma_del_contrato'].astype(str).str.extract(r'(20[1-2][0-9])')[0]
df['anio_firma'] = pd.to_numeric(df['anio_firma'], errors='coerce')

# Limpiar valor
df['valor'] = df['valor_contrato'].astype(str).str.replace(r'[^0-9]', '', regex=True)
df['valor'] = pd.to_numeric(df['valor'], errors='coerce')

# Estandarizar orden_entidad
df['nivel_entidad'] = df.get('nivel_entidad', '').astype(str).str.upper()
df['orden_entidad'] = np.where(df['nivel_entidad'].str.contains('NACIONAL'), 'NACIONAL',
                      np.where(df['nivel_entidad'].str.contains('TERRITORIAL'), 'TERRITORIAL', 'OTRO'))

# Filtrar: anio >= 2018, valor > 0, orden_entidad válida
df_filtrado = df[(df['anio_firma'] >= 2018) & (df['valor'] > 0) & (df['orden_entidad'].isin(['NACIONAL', 'TERRITORIAL']))].copy()

# Totales municipio
totales = df_filtrado.groupby(['anio_firma', 'divipola_municipio', 'orden_entidad']).agg(
    inversion_total=('valor', 'sum'),
    total_contratos=('valor', 'count')
).reset_index()

# Sumas proveedor
sumas_prov = df_filtrado.groupby(['anio_firma', 'divipola_municipio', 'orden_entidad', 'documento_proveedor']).agg(
    suma_proveedor=('valor', 'sum')
).reset_index()

# Unir y calcular cuadrado de participación
hhi_df = pd.merge(sumas_prov, totales, on=['anio_firma', 'divipola_municipio', 'orden_entidad'])
hhi_df['participacion_sq'] = ((hhi_df['suma_proveedor'] / hhi_df['inversion_total']) * 100) ** 2

# Agrupar HHI final
hhi_final = hhi_df.groupby(['anio_firma', 'divipola_municipio', 'orden_entidad']).agg(
    hhi_concentracion=('participacion_sq', 'sum'),
    inversion_total=('inversion_total', 'first'),
    total_contratos=('total_contratos', 'first')
).reset_index()
hhi_final['hhi_concentracion'] = hhi_final['hhi_concentracion'].round(2)

# Identificar columnas DANE
columnas_dane = [c for c in df_cruce.columns if 'nbi_' in c.lower() or 'ipm_' in c.lower() or 'etnia_' in c.lower()]
if columnas_dane:
    print(f"    -> Integrando columnas DANE: {columnas_dane}")
    dane_unique = df_cruce[['divipola_municipio'] + columnas_dane].drop_duplicates(subset=['divipola_municipio'])
    hhi_final = pd.merge(hhi_final, dane_unique, on='divipola_municipio', how='left')

# Agregar nombre del municipio desde el dataset original
nombres_mun = df_cruce[['divipola_municipio', 'municipio_entidad', 'departamento_entidad']].drop_duplicates(subset=['divipola_municipio'])
hhi_final = pd.merge(hhi_final, nombres_mun, on='divipola_municipio', how='left')
# Renombrar columnas para claridad
hhi_final.rename(columns={'municipio_entidad': 'nombre_municipio', 'departamento_entidad': 'nombre_departamento'}, inplace=True)

# Reordenar columnas para que el nombre quede junto al codigo
cols = list(hhi_final.columns)
cols.insert(2, cols.pop(cols.index('nombre_municipio')))
cols.insert(3, cols.pop(cols.index('nombre_departamento')))
hhi_final = hhi_final[cols]

hhi_final = hhi_final.sort_values(by=['anio_firma', 'hhi_concentracion'], ascending=[False, False])
print(f"    -> Procesadas y filtradas: {len(hhi_final)} registros de HHI resultantes.")

print("\n--- VISTA PREVIA DE LOS RESULTADOS (Top 10) ---")
print(hhi_final.head(10).to_string(index=False))

print("\n[3/3] Guardando CSV final...")
hhi_final.to_csv(out_dir_hhi, index=False, sep=';', encoding='utf-8-sig')
print(f"    -> Archivo final guardado en: {out_dir_hhi}")
print("=======================================================")
print(" PROCESAMIENTO COMPLETADO EXITOSAMENTE")
print("=======================================================")
