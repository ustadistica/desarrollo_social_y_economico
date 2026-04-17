import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir

print("=======================================================")
print(" INDICADOR: INVERSIÓN PÚBLICA ANUAL POR MUNICIPIO")
print("=======================================================")

# ── Rutas de entrada y salida ──────────────────────────────────────────────────
INPUT_FILE  = os.path.join(project_root, 'datos', 'secop_nuevos1.parquet')
OUTPUT_FILE = os.path.join(project_root, 'datos', 'processed',
                           'indicador_inversion_publica.csv')

# ── 1. Lectura ─────────────────────────────────────────────────────────────────
print("[1/5] Leyendo datos...")
df = pd.read_parquet(INPUT_FILE)
print(f"      Registros cargados: {len(df):,}")

# ── 2. Limpieza y estandarización ─────────────────────────────────────────────
print("[2/5] Limpiando y estandarizando columnas...")

# Ciudad
df['ciudad_entidad'] = df['ciudad_entidad'].astype(str).str.upper().str.strip()

# Orden entidad → NACIONAL / TERRITORIAL / OTRO
def clasificar_orden(val):
    v = str(val).upper()
    if 'NACIONAL' in v:
        return 'NACIONAL'
    elif 'TERRITORIAL' in v:
        return 'TERRITORIAL'
    else:
        return 'OTRO'

df['orden_entidad'] = df['ordenentidad'].apply(clasificar_orden)

# Año: extrae 4 dígitos tipo 20XX de la fecha de adjudicación
df['anio_firma'] = (
    df['fecha_adjudicacion']
    .astype(str)
    .str.extract(r'(20[1-2][0-9])')[0]
    .astype('Int64')
)

# Valor: elimina cualquier carácter que no sea dígito ni punto
df['valor'] = (
    pd.to_numeric(
        df['valor_total_adjudicacion']
          .astype(str)
          .str.replace(r'[^0-9\.]', '', regex=True),
        errors='coerce'
    )
)

# ── 3. Filtrado ────────────────────────────────────────────────────────────────
print("[3/5] Filtrando registros válidos (desde 2018, valor > 0)...")
df_clean = df[
    (df['anio_firma'] >= 2018) &
    (df['valor'] > 0) &
    (df['orden_entidad'].isin(['NACIONAL', 'TERRITORIAL'])) &
    (df['ciudad_entidad'].notna())
].copy()

print(f"      Registros válidos para el indicador: {len(df_clean):,}")

# ── 4. Cálculo del indicador ───────────────────────────────────────────────────
print("[4/5] Calculando indicador de inversión pública...")

# 4a. Inversión total nacional por año y orden (denominador para participación %)
totales_nacionales = (
    df_clean
    .groupby(['anio_firma', 'orden_entidad'])['valor']
    .sum()
    .reset_index()
    .rename(columns={'valor': 'inversion_nacional_total'})
)

# 4b. Inversión agregada por ciudad / año / orden
inversion_ciudad = (
    df_clean
    .groupby(['anio_firma', 'ciudad_entidad', 'orden_entidad'])
    .agg(
        total_contratos     = ('valor', 'count'),
        inversion_total_cop = ('valor', 'sum')
    )
    .reset_index()
)

# 4c. Une para calcular participación %
resultado = inversion_ciudad.merge(
    totales_nacionales,
    on=['anio_firma', 'orden_entidad'],
    how='left'
)

resultado['ticket_promedio_cop'] = (
    resultado['inversion_total_cop'] / resultado['total_contratos']
).round(2)

resultado['participacion_pct'] = (
    resultado['inversion_total_cop'] / resultado['inversion_nacional_total'] * 100
).round(4)

resultado['inversion_total_cop'] = resultado['inversion_total_cop'].round(2)

# Ordena: año más reciente primero, luego mayor inversión
resultado = resultado.sort_values(
    ['anio_firma', 'inversion_total_cop'],
    ascending=[False, False]
).reset_index(drop=True)

# Columnas finales en orden legible
resultado = resultado[[
    'anio_firma',
    'ciudad_entidad',
    'orden_entidad',
    'total_contratos',
    'inversion_total_cop',
    'ticket_promedio_cop',
 2018.
#
# Los resultados muestran una alta concentración de recursos en
# pocos municipios, especialmente en Bogotá, que representa la mayor
# proporción de la inversión analizada.
#
# Sin embargo, el número reducido de registros válidos sugiere que
# el indicador no refleja completamente la realidad nacional, por lo
# que debe interpretarse como un análisis exploratorio y no definitivo.
#
# Además, se identifican contratos de alto valor individual (megaproyectos)
# y algunos registros sin ciudad definida, lo que evidencia limitaciones
# en la calidad de los datos.
# =======================================================