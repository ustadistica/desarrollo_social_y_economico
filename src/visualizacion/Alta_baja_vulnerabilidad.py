import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Cargar base
df = pd.read_parquet("datos/cruce_secop_dane_sprint2.parquet")

# Seleccionar columna de vulnerabilidad (NBI)
col_nbi = "necesidades_basicas_insatisfechas_por_categorias_%_prop_de_personas_en_nbi_(%)"

# Convertir a numérico y limpiar nulos
df[col_nbi] = pd.to_numeric(df[col_nbi], errors="coerce")
df = df.dropna(subset=[col_nbi])

# Crear grupo de vulnerabilidad usando la mediana
mediana_nbi = df[col_nbi].median()
df["grupo_vulnerabilidad"] = np.where(
    df[col_nbi] >= mediana_nbi,
    "Alta vulnerabilidad",
    "Baja vulnerabilidad"
)

# Resumen comparativo
resumen = df.groupby("grupo_vulnerabilidad").agg(
    municipios=("divipola_municipio", "count"),
    contratos=("num_contratos", "sum"),
    monto_total=("monto_total_contratos", "sum")
).reset_index()

# Calcular porcentajes
resumen["pct_contratos"] = resumen["contratos"] / resumen["contratos"].sum() * 100
resumen["pct_monto"] = resumen["monto_total"] / resumen["monto_total"].sum() * 100

# Mostrar tabla resumen
print(resumen)

# Gráfica 1: porcentaje de contratos
ax = resumen.plot(
    x="grupo_vulnerabilidad",
    y="pct_contratos",
    kind="bar",
    legend=False
)

plt.title("Porcentaje de contratos por nivel de vulnerabilidad")
plt.ylabel("Porcentaje de contratos")
plt.xlabel("Grupo de vulnerabilidad")
plt.xticks(rotation=0)

for container in ax.containers:
    ax.bar_label(container, fmt="%.2f%%")

plt.tight_layout()
plt.show()

# Gráfica 2: porcentaje del monto contratado
ax = resumen.plot(
    x="grupo_vulnerabilidad",
    y="pct_monto",
    kind="bar",
    legend=False
)

plt.title("Porcentaje del monto contratado por nivel de vulnerabilidad")
plt.ylabel("Porcentaje del monto total")
plt.xlabel("Grupo de vulnerabilidad")
plt.xticks(rotation=0)

for container in ax.containers:
    ax.bar_label(container, fmt="%.2f%%")

plt.tight_layout()
plt.show()