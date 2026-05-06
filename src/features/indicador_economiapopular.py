import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = current_dir

print("=======================================================")
print(" INDICADOR: ECONOMÍA POPULAR")
print(" PARTICIPACIÓN MICRO/PEQUEÑOS PROVEEDORES POR MUNICIPIO")
print("=======================================================")

# ── Rutas de entrada y salida ──────────────────────────────────────────────────
INPUT_FILE  = os.path.join(project_root, 'datos', 'secop_nuevos1.parquet')
OUTPUT_FILE = os.path.join(project_root, 'datos', 'processed',
                           'indicador_economia_popular.csv')

# ── Umbrales de clasificación ──────────────────────────────────────────────────
# Basado en la Ley 905 de 2004 (Colombia) y umbrales SECOP de mínima cuantía:
#   - Mínima cuantía 2024: contratos <= 40 SMMLV ~ 52 millones COP
#   - Usamos 50 millones como umbral conservador para micro/pequeño
UMBRAL_MICRO_PEQUENO_COP = 50_000_000

# Modalidades que típicamente corresponden a micro/pequeños proveedores
MODALIDADES_ECONOMIA_POPULAR = [
    'MINIMA CUANTIA',
    'MÍNIMA CUANTÍA',
    'MINIMA CUANTÍA',
    'CONTRATACION DIRECTA',
    'CONTRATACIÓN DIRECTA',
    'SELECCION ABREVIADA',
    'SELECCIÓN ABREVIADA',
]

# ── 1. Lectura ─────────────────────────────────────────────────────────────────
print("[1/5] Leyendo datos...")
df = pd.read_parquet(INPUT_FILE)
print(f"      Registros cargados: {len(df):,}")

# Muestra modalidades disponibles para referencia
print("\n      Modalidades de contratación encontradas:")
for m in df['modalidad_de_contratacion'].dropna().unique():
    print(f"       · {m}")

# ── 2. Limpieza y estandarización ─────────────────────────────────────────────
print("\n[2/5] Limpiando y estandarizando columnas...")

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

# Modalidad normalizada (mayúsculas sin tildes para comparación)
df['modalidad_norm'] = (
    df['modalidad_de_contratacion']
    .astype(str)
    .str.upper()
    .str.strip()
)

# ── 3. Filtrado ────────────────────────────────────────────────────────────────
print("[3/5] Filtrando registros válidos (desde 2018, valor > 0)...")
df_clean = df[
    (df['anio_firma'] >= 2018) &
    (df['valor'] > 0) &
    (df['orden_entidad'].isin(['NACIONAL', 'TERRITORIAL'])) &
    (df['ciudad_entidad'].notna())
].copy()

print(f"      Registros válidos: {len(df_clean):,}")

# ── 4. Clasificación micro/pequeño ────────────────────────────────────────────
# Un contrato se clasifica como de economía popular si cumple AL MENOS UNO:
#   (A) Valor <= umbral de mínima cuantía
#   (B) Modalidad típica de pequeños proveedores
print("[4/5] Clasificando contratos de economía popular...")

por_valor     = df_clean['valor'] <= UMBRAL_MICRO_PEQUENO_COP
por_modalidad = df_clean['modalidad_norm'].isin(MODALIDADES_ECONOMIA_POPULAR)

df_clean['es_economia_popular'] = (por_valor | por_modalidad)

# Desglose para transparencia metodológica
solo_valor     = (por_valor & ~por_modalidad).sum()
solo_modalidad = (~por_valor & por_modalidad).sum()
ambos          = (por_valor & por_modalidad).sum()
total_ep       = df_clean['es_economia_popular'].sum()

print(f"      Contratos clasificados como economía popular : {total_ep:,}")
print(f"        · Solo por valor (<= {UMBRAL_MICRO_PEQUENO_COP/1e6:.0f}M COP) : {solo_valor:,}")
print(f"        · Solo por modalidad                       : {solo_modalidad:,}")
print(f"        · Por ambos criterios                      : {ambos:,}")

# ── 5. Cálculo del indicador ───────────────────────────────────────────────────
print("[5/5] Calculando indicador por ciudad/año/orden...")

# Totales generales (denominador)
totales = (
    df_clean
    .groupby(['anio_firma', 'ciudad_entidad', 'orden_entidad'])
    .agg(
        total_contratos     = ('valor', 'count'),
        inversion_total_cop = ('valor', 'sum')
    )
    .reset_index()
)

# Totales economía popular (numerador)
ep = (
    df_clean[df_clean['es_economia_popular']]
    .groupby(['anio_firma', 'ciudad_entidad', 'orden_entidad'])
    .agg(
        contratos_economia_popular     = ('valor', 'count'),
        inversion_economia_popular_cop = ('valor', 'sum')
    )
    .reset_index()
)

# Une y calcula porcentajes
resultado = totales.merge(
    ep,
    on=['anio_firma', 'ciudad_entidad', 'orden_entidad'],
    how='left'
)

resultado['contratos_economia_popular']     = resultado['contratos_economia_popular'].fillna(0).astype(int)
resultado['inversion_economia_popular_cop'] = resultado['inversion_economia_popular_cop'].fillna(0)

resultado['participacion_contratos_pct'] = (
    resultado['contratos_economia_popular'] /
    resultado['total_contratos'] * 100
).round(2)

resultado['participacion_inversion_pct'] = (
    resultado['inversion_economia_popular_cop'] /
    resultado['inversion_total_cop'] * 100
).round(2)

resultado['inversion_total_cop']             = resultado['inversion_total_cop'].round(2)
resultado['inversion_economia_popular_cop']  = resultado['inversion_economia_popular_cop'].round(2)

# Ordena: año más reciente, luego mayor participación
resultado = resultado.sort_values(
    ['anio_firma', 'participacion_inversion_pct'],
    ascending=[False, False]
).reset_index(drop=True)

# Columnas finales
resultado = resultado[[
    'anio_firma',
    'ciudad_entidad',
    'orden_entidad',
    'total_contratos',
    'contratos_economia_popular',
    'participacion_contratos_pct',
    'inversion_total_cop',
    'inversion_economia_popular_cop',
    'participacion_inversion_pct'
]]

# ── 6. Guardado ────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
resultado.to_csv(OUTPUT_FILE, index=False, sep=';', encoding='utf-8-sig')

print(f"\n      Registros generados : {len(resultado):,}")
print(f"      Archivo guardado en : {OUTPUT_FILE}")

# Vista previa
print("\n=== VISTA PREVIA (top 10 por participación en inversión) ===")
print(resultado.head(10).to_string(index=False))

print("\n=== RESUMEN POR AÑO ===")
resumen = (
    resultado
    .groupby('anio_firma')
    .agg(
        municipios                  = ('ciudad_entidad', 'nunique'),
        total_contratos             = ('total_contratos', 'sum'),
        contratos_economia_popular  = ('contratos_economia_popular', 'sum'),
        participacion_promedio_pct  = ('participacion_inversion_pct', 'mean')
    )
    .reset_index()
    .sort_values('anio_firma', ascending=False)
)
resumen['participacion_promedio_pct'] = resumen['participacion_promedio_pct'].round(2)
print(resumen.to_string(index=False))

print("\n=======================================================")
print(" PROCESAMIENTO COMPLETADO EXITOSAMENTE")
print("=======================================================")
