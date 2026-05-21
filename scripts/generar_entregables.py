import pandas as pd
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')
print("--------------------------------------------------")
print("[Iniciando Generacion de Entregables SPRINT 2]")
print("--------------------------------------------------")

silver_dir = Path("data/silver")

try:
    cnpv_file = silver_dir / "silver_cnpv_agregado.parquet"
    secop_file = silver_dir / "silver_secop_ii_agregado.parquet"
    emicron_file = silver_dir / "silver_emicron_agregado.parquet"
    
    cnpv = pd.read_parquet(cnpv_file)
    secop = pd.read_parquet(secop_file)
    emicron = pd.read_parquet(emicron_file)
except Exception as e:
    print(f"[Error] Archivos faltantes: {e}")
    exit(1)

print("[OK] Bases de datos leidas. Calculando indicadores...\n")

# 1. INDICADORES SOCIALES (CNPV)
df_social = cnpv[['divipola_key', 'poblacion_total_base']].sort_values(by='poblacion_total_base', ascending=False)
df_social = df_social.rename(columns={'divipola_key': 'divipola_municipio', 'poblacion_total_base': 'poblacion_total'})
f1 = "1_INDICADORES_SOCIALES_CNPV.csv"
df_social.to_csv(f1, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f1} (Top:\n{df_social.head(3).to_string()})\n")

# 2. INDICADORES INVERSION PUBLICA (SECOP)
df_inversion = secop.groupby('divipola_key', as_index=False).agg(
    numero_contratos=('cantidad_procesos_adjudicados', 'sum'),
    inversion_publica_total=('inversion_total_monto', 'sum')
).sort_values(by='inversion_publica_total', ascending=False)
f2 = "2_INDICADORES_INVERSION_SECOP.csv"
df_inversion.to_csv(f2, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f2} (Top:\n{df_inversion.head(3).to_string()})\n")

# 3. INDICADORES ECONOMIA POPULAR (EMICRON)
df_economia = emicron.groupby('divipola_depto', as_index=False).agg(
    total_empresas_estimadas=('volumen_micronegocios_exp', 'sum')
).sort_values(by='total_empresas_estimadas', ascending=False)
df_economia = df_economia.rename(columns={'divipola_depto': 'cod_departamento'})
f3 = "3_INDICADORES_ECONOMIA_POPULAR.csv"
df_economia.to_csv(f3, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f3} (Top:\n{df_economia.head(3).to_string()})\n")

print("==================================================")
print("[EXITO COMPLETADO] Tienes los 3 archivos CSV listos en tu carpeta.")
print("==================================================")
