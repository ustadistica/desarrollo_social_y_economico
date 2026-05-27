"""
====================================================================
INDICADORES EXPLORATORIOS - DESARROLLO SOCIAL Y ECONÓMICO
====================================================================
Script de análisis exploratorio sobre el OBT final del pipeline.
Variables adaptadas a las columnas reales del cruce.

Fuentes integradas:
  - SECOP I y II  → contratos públicos
  - EMICRON       → micronegocios
  - PPED + CNPV   → demografía
====================================================================
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 130
plt.rcParams["font.family"] = "DejaVu Sans"

Path("outputs/graficas").mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# 1. CARGAR EL OBT
# ─────────────────────────────────────────────
OBT_PATH = Path("data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet")

print("📦 Cargando OBT...")
obt = pd.read_parquet(OBT_PATH)

print(f"✅ OBT cargado: {obt.shape[0]} filas × {obt.shape[1]} columnas")
print(f"📅 Años disponibles: {sorted(obt['anio_key'].unique())}")
print(f"🗺️  Departamentos: {obt['nombre_departamento'].nunique()}")

DEPTOS_MAP = {
    'Departamento 08': 'Atlántico',
    'Departamento 13': 'Bolívar',
    'Departamento 15': 'Boyacá',
    'Departamento 17': 'Caldas',
    'Departamento 18': 'Caquetá',
    'Departamento 19': 'Cauca',
    'Departamento 20': 'Cesar',
    'Departamento 23': 'Córdoba',
    'Departamento 25': 'Cundinamarca',
    'Departamento 27': 'Chocó',
    'Departamento 41': 'Huila',
    'Departamento 44': 'La Guajira',
    'Departamento 47': 'Magdalena',
    'Departamento 50': 'Meta',
    'Departamento 52': 'Nariño',
    'Departamento 54': 'N. Santander',
    'Departamento 63': 'Quindío',
    'Departamento 66': 'Risaralda',
    'Departamento 68': 'Santander',
    'Departamento 70': 'Sucre',
    'Departamento 73': 'Tolima',
    'Departamento 81': 'Arauca',
    'Departamento 85': 'Casanare',
    'Departamento 86': 'Putumayo',
    'Departamento 88': 'San Andrés',
    'Departamento 91': 'Amazonas',
    'Departamento 94': 'Guainía',
    'Departamento 95': 'Guaviare',
    'Departamento 97': 'Vaupés',
    'Departamento 99': 'Vichada'
}
obt['nombre_departamento'] = obt['nombre_departamento'].replace(DEPTOS_MAP)
print(f"🏙️  Municipios: {obt['nombre_municipio_referencia'].nunique()}")


# ─────────────────────────────────────────────
# FUNCIÓN AUXILIAR
# ─────────────────────────────────────────────
def guardar(nombre):
    plt.tight_layout()
    plt.savefig(f"outputs/graficas/{nombre}.png", bbox_inches="tight")
    plt.show()
    print(f"   💾 Guardada: outputs/graficas/{nombre}.png\n")


# ─────────────────────────────────────────────
# INDICADOR 0 — CALIDAD DE LOS DATOS
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("INDICADOR 0 — CALIDAD DE LOS DATOS (VALORES NULOS)")
print("="*60)

nulos = (obt.isnull().sum() / len(obt) * 100).sort_values(ascending=False)
nulos = nulos[nulos > 0]

if len(nulos) > 0:
    fig, ax = plt.subplots(figsize=(12, 5))
    nulos.plot(kind="bar", ax=ax, color="#e07b54", edgecolor="white")
    ax.set_title("% de Valores Nulos por Columna en el OBT", fontsize=14, fontweight="bold")
    ax.set_ylabel("% Nulos")
    ax.set_xlabel("")
    plt.xticks(rotation=45, ha="right")
    guardar("00_nulos_por_columna")
else:
    print("✅ No hay valores nulos en el OBT.")


# ─────────────────────────────────────────────
# INDICADOR 1 — INVERSIÓN PÚBLICA PER CÁPITA
# Por departamento, último año disponible
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 1 — INVERSIÓN PÚBLICA PER CÁPITA")
print("="*60)

anio_max = 2024
df = obt[obt["anio_key"] == anio_max].copy()

df["inversion_per_capita"] = df["inversion_total_monto"] / df["poblacion_total_proyectada"]

resumen = (df.groupby("nombre_departamento")["inversion_per_capita"]
             .mean()
             .sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(14, 7))
colores = ["#1a6b3c" if v >= resumen.median() else "#a8d5b5" for v in resumen]
resumen.plot(kind="bar", ax=ax, color=colores, edgecolor="white")
ax.axhline(resumen.median(), color="red", linestyle="--",
           label=f"Mediana: ${resumen.median():,.0f}")
ax.set_title(f"Inversión Pública Per Cápita por Departamento ({anio_max})",
             fontsize=14, fontweight="bold")
ax.set_ylabel("COP por habitante")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x/1e6:.1f}M"))
ax.legend()
plt.xticks(rotation=45, ha="right")
guardar("01_inversion_per_capita")


# ─────────────────────────────────────────────
# INDICADOR 2 — EVOLUCIÓN DE INVERSIÓN TOTAL
# Top 8 departamentos a lo largo del tiempo
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 2 — EVOLUCIÓN DE INVERSIÓN PÚBLICA")
print("="*60)

evolucion = (obt.groupby(["anio_key", "nombre_departamento"])["inversion_total_monto"]
               .sum()
               .reset_index())

top_deptos = (evolucion.groupby("nombre_departamento")["inversion_total_monto"]
                       .mean()
                       .nlargest(8)
                       .index.tolist())

fig, ax = plt.subplots(figsize=(13, 6))
for depto in top_deptos:
    datos = evolucion[evolucion["nombre_departamento"] == depto]
    ax.plot(datos["anio_key"], datos["inversion_total_monto"] / 1e9,
            marker="o", label=depto, linewidth=2)

ax.set_title("Evolución de Inversión Pública — Top 8 Departamentos", fontsize=14, fontweight="bold")
ax.set_xlabel("Año")
ax.set_ylabel("Inversión Total (Miles de Millones COP)")
ax.legend(title="Departamento", bbox_to_anchor=(1.01, 1), loc="upper left")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}B"))
guardar("02_evolucion_inversion")


# ─────────────────────────────────────────────
# INDICADOR 3 — DENSIDAD DE MICRONEGOCIOS
# Micronegocios por habitante por departamento
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 3 — DENSIDAD DE MICRONEGOCIOS POR HABITANTE")
print("="*60)

df_emicron = obt[obt["anio_key"].between(2019, 2024)].copy()
anio_emicron = df_emicron["anio_key"].max()
df_em = df_emicron[df_emicron["anio_key"] == anio_emicron]

resumen_em = (df_em.groupby("nombre_departamento")["indicador_densidad_micronegocios"]
                   .mean()
                   .sort_values(ascending=False))

fig, ax = plt.subplots(figsize=(14, 7))
resumen_em.plot(kind="bar", ax=ax, color="#8e44ad", edgecolor="white")
ax.axhline(resumen_em.mean(), color="orange", linestyle="--",
           label=f"Promedio: {resumen_em.mean():.4f}")
ax.set_title(f"Densidad de Micronegocios por Habitante ({anio_emicron})",
             fontsize=14, fontweight="bold")
ax.set_ylabel("Micronegocios por habitante")
ax.legend()
plt.xticks(rotation=45, ha="right")
guardar("03_densidad_micronegocios")


# ─────────────────────────────────────────────
# INDICADOR 4 — EVOLUCIÓN DE MICRONEGOCIOS
# Volumen expandido por departamento 2019–2024
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 4 — EVOLUCIÓN DEL VOLUMEN DE MICRONEGOCIOS")
print("="*60)

df_emicron = obt[obt["anio_key"].between(2019, 2024)]
evolucion_em = (df_emicron.groupby(["anio_key", "nombre_departamento"])["volumen_micronegocios_exp"]
                           .sum()
                           .reset_index())

top_em = (evolucion_em.groupby("nombre_departamento")["volumen_micronegocios_exp"]
                      .mean()
                      .nlargest(8)
                      .index.tolist())

fig, ax = plt.subplots(figsize=(13, 6))
for depto in top_em:
    datos = evolucion_em[evolucion_em["nombre_departamento"] == depto]
    ax.plot(datos["anio_key"], datos["volumen_micronegocios_exp"],
            marker="o", label=depto, linewidth=2)

ax.set_title("Evolución del Volumen de Micronegocios — Top 8 Departamentos (2019–2024)",
             fontsize=14, fontweight="bold")
ax.set_xlabel("Año")
ax.set_ylabel("Micronegocios (estimación expandida)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(title="Departamento", bbox_to_anchor=(1.01, 1), loc="upper left")
guardar("04_evolucion_micronegocios")


# ─────────────────────────────────────────────
# INDICADOR 5 — INVERSIÓN PÚBLICA VS MICRONEGOCIOS
# Relación entre inversión pública y economía popular
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 5 — INVERSIÓN PÚBLICA VS DENSIDAD DE MICRONEGOCIOS")
print("="*60)

df_scatter = (obt[obt["anio_key"].between(2019, 2024)]
              .groupby("nombre_departamento")
              .agg(
                  inversion=("inversion_total_monto", "mean"),
                  densidad=("indicador_densidad_micronegocios", "mean"),
                  poblacion=("poblacion_total_proyectada", "mean")
              )
              .reset_index()
              .dropna())

fig, ax = plt.subplots(figsize=(12, 7))
ax.scatter(
    df_scatter["inversion"] / 1e9,
    df_scatter["densidad"],
    s=df_scatter["poblacion"] / 50000,
    alpha=0.7,
    c=range(len(df_scatter)),
    cmap="tab20",
    edgecolors="white",
    linewidth=0.5
)

for _, row in df_scatter.iterrows():
    ax.annotate(row["nombre_departamento"],
                (row["inversion"] / 1e9, row["densidad"]),
                fontsize=7, ha="left", va="bottom",
                xytext=(3, 3), textcoords="offset points")

ax.set_title("Inversión Pública vs Densidad de Micronegocios por Departamento\n(tamaño del círculo = población)",
             fontsize=13, fontweight="bold")
ax.set_xlabel("Inversión Pública Promedio (Miles de Millones COP)")
ax.set_ylabel("Densidad de Micronegocios (por habitante)")
ax.set_xscale('log')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}B"))
guardar("05_inversion_vs_micronegocios")


# ─────────────────────────────────────────────
# INDICADOR 6 — CONCENTRACIÓN DE PROVEEDORES
# Contratos adjudicados por proveedor único
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 6 — CONCENTRACIÓN DE PROVEEDORES PÚBLICOS")
print("="*60)

df_prov = (obt[obt["anio_key"] == 2024]
           .groupby("nombre_departamento")
           .agg(
               contratos=("cantidad_procesos_adjudicados", "sum"),
               proveedores=("proveedores_unicos", "sum")
           )
           .reset_index()
           .dropna())

df_prov["contratos_por_proveedor"] = df_prov["contratos"] / df_prov["proveedores"]
df_prov = df_prov.sort_values("contratos_por_proveedor", ascending=False)

fig, ax = plt.subplots(figsize=(14, 7))
colores = ["#c0392b" if v > df_prov["contratos_por_proveedor"].median() else "#2980b9"
           for v in df_prov["contratos_por_proveedor"]]
ax.bar(df_prov["nombre_departamento"], df_prov["contratos_por_proveedor"],
       color=colores, edgecolor="white")
ax.axhline(df_prov["contratos_por_proveedor"].median(), color="gray", linestyle="--",
           label=f"Mediana: {df_prov['contratos_por_proveedor'].median():.1f}")
ax.set_title(f"Contratos por Proveedor Único por Departamento ({anio_max})\n(más alto = más concentración)",
             fontsize=13, fontweight="bold")
ax.set_ylabel("Contratos por proveedor")
ax.legend()
plt.xticks(rotation=45, ha="right")
guardar("06_concentracion_proveedores")


# ─────────────────────────────────────────────
# INDICADOR 7 — IMPACTO PANDEMIA EN MICRONEGOCIOS
# Comparación 2019 vs 2021 vs 2024
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 7 — IMPACTO PANDEMIA EN MICRONEGOCIOS")
print("="*60)

anios_comparar = [2019, 2021, 2024]
anios_disponibles = [a for a in anios_comparar if a in obt["anio_key"].values]

df_pandemia = (obt[obt["anio_key"].isin(anios_disponibles)]
               .groupby(["anio_key", "nombre_departamento"])["volumen_micronegocios_exp"]
               .sum()
               .reset_index())

top_pan = (df_pandemia.groupby("nombre_departamento")["volumen_micronegocios_exp"]
                      .mean()
                      .nlargest(10)
                      .index.tolist())

df_pandemia_top = df_pandemia[df_pandemia["nombre_departamento"].isin(top_pan)]
pivot = df_pandemia_top.pivot(index="nombre_departamento", columns="anio_key",
                               values="volumen_micronegocios_exp")

fig, ax = plt.subplots(figsize=(14, 7))
pivot.plot(kind="bar", ax=ax, width=0.75,
           color=["#3498db", "#e74c3c", "#2ecc71"][:len(anios_disponibles)])
ax.set_title("Volumen de Micronegocios: Antes, Durante y Después de la Pandemia\n(Top 10 departamentos)",
             fontsize=13, fontweight="bold")
ax.set_ylabel("Micronegocios (estimación expandida)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax.legend(title="Año")
plt.xticks(rotation=45, ha="right")
guardar("07_impacto_pandemia_micronegocios")


# ─────────────────────────────────────────────
# INDICADOR 8 — MATRIZ DE CORRELACIÓN
# Variables numéricas clave del OBT
# ─────────────────────────────────────────────
print("="*60)
print("INDICADOR 8 — MATRIZ DE CORRELACIÓN")
print("="*60)

cols_corr = [
    "inversion_total_monto",
    "cantidad_procesos_adjudicados",
    "proveedores_unicos",
    "volumen_micronegocios_exp",
    "indicador_densidad_micronegocios",
    "poblacion_total_proyectada",
    "poblacion_censo_2018"
]
cols_corr = [c for c in cols_corr if c in obt.columns]

corr = obt[cols_corr].corr()

etiquetas = {
    "inversion_total_monto": "Inversión total",
    "cantidad_procesos_adjudicados": "Nº contratos",
    "proveedores_unicos": "Proveedores únicos",
    "volumen_micronegocios_exp": "Volumen micronegocios",
    "indicador_densidad_micronegocios": "Densidad micronegocios",
    "poblacion_total_proyectada": "Población proyectada",
    "poblacion_censo_2018": "Población censo 2018"
}
corr = corr.rename(index=etiquetas, columns=etiquetas)

fig, ax = plt.subplots(figsize=(11, 8))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
            center=0, ax=ax, linewidths=0.5, annot_kws={"size": 9})
ax.set_title("Matriz de Correlación — Variables Clave del OBT",
             fontsize=14, fontweight="bold")
guardar("08_correlacion_variables")


# ─────────────────────────────────────────────
# RESUMEN FINAL
# ─────────────────────────────────────────────
print("\n" + "="*60)
print("✅ ANÁLISIS EXPLORATORIO COMPLETADO")
print("="*60)
print("📁 Gráficas guardadas en: outputs/graficas/\n")
print("  00 — Mapa de valores nulos")
print("  01 — Inversión pública per cápita")
print("  02 — Evolución de inversión pública")
print("  03 — Densidad de micronegocios por habitante")
print("  04 — Evolución del volumen de micronegocios")
print("  05 — Inversión pública vs densidad de micronegocios")
print("  06 — Concentración de proveedores públicos")
print("  07 — Impacto pandemia en micronegocios")
print("  08 — Matriz de correlación")
