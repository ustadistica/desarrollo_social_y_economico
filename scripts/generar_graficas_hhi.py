"""
Generador de visualizaciones del Índice Herfindahl-Hirschman (HHI).

Lee los CSV de HHI ya calculados por `src/features/indicador_hhi_cruce.py`
y produce tres figuras independientes en estilo ggplot (mismo estilo del
notebook EDA), más un HTML único que las agrupa.

Entradas:
  - data/hhi_por_anio.csv
  - data/hhi_por_nivel.csv
  - data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv

Salidas:
  - artifacts/hhi/hhi_tendencia_anual.png
  - artifacts/hhi/hhi_por_nivel.png
  - artifacts/hhi/hhi_distribucion_municipal.png
  - artifacts/hhi/hhi_report.html

No se inventa ningún dato: todas las etiquetas, conteos y métricas
provienen de los CSV de entrada. Los umbrales 1500 / 2500 / 5000 / 10000
son la escala estándar del HHI (convención DOJ/FTC) usada por el propio
pipeline del proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.stdout.reconfigure(encoding="utf-8")

# ── Rutas ────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT  = ROOT / "artifacts" / "hhi"
OUT.mkdir(parents=True, exist_ok=True)

# ── Estilo (idéntico al notebook EDA) ────────────────────────────────────────
plt.style.use("ggplot")
plt.rcParams.update({
    "figure.dpi": 120,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "font.size": 10,
})

C_PRIMARY     = "#4C78A8"   # azul (igual que celda "monto promedio" del EDA)
C_SECONDARY   = "#E07B54"   # naranja (igual que celda "num contratos" del EDA)
C_RED         = "#E74C3C"   # rojo (referencia / monopolio)
C_GREEN       = "#2ECC71"   # verde (competencia)
C_YELLOW      = "#F4B400"   # amarillo (moderada)
C_ORANGE      = "#E67E22"   # naranja (alta)

# Umbrales estándar HHI (convención DOJ/FTC, también usados en el pipeline)
UMBRAL_MODERADO  = 1500
UMBRAL_ALTO      = 2500
UMBRAL_MONOPOLIO = 10000


# ── Carga de datos reales ────────────────────────────────────────────────────
def _read_csv_sc(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep=";")
    df.columns = [c.strip() for c in df.columns]
    return df


print("Cargando datos HHI...")
hhi_anio  = _read_csv_sc(DATA / "hhi_por_anio.csv")
hhi_nivel = _read_csv_sc(DATA / "hhi_por_nivel.csv")
hhi_cruce = _read_csv_sc(DATA / "HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv")

hhi_anio["anio_firma"]  = hhi_anio["anio_firma"].astype(int)
hhi_nivel["anio_firma"] = hhi_nivel["anio_firma"].astype(int)
hhi_cruce["anio_firma"] = hhi_cruce["anio_firma"].astype(int)

print(f"  hhi_por_anio        : {len(hhi_anio)} filas")
print(f"  hhi_por_nivel       : {len(hhi_nivel)} filas")
print(f"  HHI_CRUCE_SECOP_DANE: {len(hhi_cruce)} filas")


# ════════════════════════════════════════════════════════════════════════════
# FIG 1 — Evolución del HHI promedio nacional 2018-2026
# ════════════════════════════════════════════════════════════════════════════
def figura_tendencia_anual() -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("Evolución del HHI Promedio Nacional (2018–2026)",
                 fontsize=16, fontweight="bold")

    x = hhi_anio["anio_firma"].values
    y = hhi_anio["HHI_Promedio"].values
    n = hhi_anio["Total_Contratos"].values
    m = hhi_anio["Total_Municipios"].values

    ax.plot(x, y, marker="o", linewidth=2.5, color=C_PRIMARY,
            markersize=9, markeredgecolor="black", zorder=5)
    ax.fill_between(x, y, alpha=0.15, color=C_PRIMARY)

    # Etiquetas con valor real + tamaño muestral
    for xi, yi, ni, mi in zip(x, y, n, m):
        ax.annotate(f"{yi:,.0f}", (xi, yi),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=9, fontweight="bold")
        ax.annotate(f"n={ni:,} contratos\n{mi} municipios",
                    (xi, yi), textcoords="offset points", xytext=(0, -28),
                    ha="center", fontsize=7, color="#555555")

    # Líneas de referencia con los umbrales estándar HHI
    ax.axhline(UMBRAL_MONOPOLIO, color=C_RED, linestyle="--",
               linewidth=1.3, alpha=0.85)
    ax.axhline(UMBRAL_ALTO, color=C_RED, linestyle="--",
               linewidth=1.0, alpha=0.55)
    ax.text(x[0] - 0.3, UMBRAL_MONOPOLIO + 180,
            f"Monopolio = {UMBRAL_MONOPOLIO:,}",
            color=C_RED, fontsize=8, ha="left")
    ax.text(x[0] - 0.3, UMBRAL_ALTO + 180,
            f"Alta concentración ≥ {UMBRAL_ALTO:,}",
            color=C_RED, fontsize=8, ha="left")

    ax.set_xticks(x)
    ax.set_xlim(x[0] - 0.6, x[-1] + 0.6)
    ax.set_ylim(0, 11400)
    ax.set_xlabel("Año de firma", fontweight="bold")
    ax.set_ylabel("HHI promedio (escala 0–10.000)", fontweight="bold")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))

    ax.set_title("Promedio anual sobre municipios con contratación SECOP "
                 "registrada en la muestra cruzada SECOP-DANE",
                 fontsize=10, color="#555555")

    plt.tight_layout()
    out = OUT / "hhi_tendencia_anual.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out


# ════════════════════════════════════════════════════════════════════════════
# FIG 2 — HHI por orden de entidad: Nacional vs Territorial
# ════════════════════════════════════════════════════════════════════════════
def figura_por_nivel() -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.suptitle("HHI por Orden de Entidad (Nacional vs Territorial)",
                 fontsize=16, fontweight="bold")

    nac  = hhi_nivel[hhi_nivel["orden_entidad"] == "NACIONAL"].sort_values("anio_firma")
    terr = hhi_nivel[hhi_nivel["orden_entidad"] == "TERRITORIAL"].sort_values("anio_firma")

    ax.plot(terr["anio_firma"], terr["HHI_Promedio"],
            marker="o", linewidth=2.5, color=C_PRIMARY, markersize=9,
            markeredgecolor="black", label="Territorial", zorder=5)
    ax.fill_between(terr["anio_firma"], terr["HHI_Promedio"],
                    alpha=0.10, color=C_PRIMARY)

    ax.plot(nac["anio_firma"], nac["HHI_Promedio"],
            marker="s", linewidth=2.5, color=C_SECONDARY, markersize=9,
            markeredgecolor="black", label="Nacional", zorder=5)
    ax.fill_between(nac["anio_firma"], nac["HHI_Promedio"],
                    alpha=0.10, color=C_SECONDARY)

    # Etiquetas: TODOS los puntos llevan su valor real
    for _, r in terr.iterrows():
        ax.annotate(f"{r['HHI_Promedio']:,.0f}",
                    (r["anio_firma"], r["HHI_Promedio"]),
                    textcoords="offset points", xytext=(0, -18),
                    ha="center", fontsize=8, color=C_PRIMARY,
                    fontweight="bold")
    for _, r in nac.iterrows():
        ax.annotate(f"{r['HHI_Promedio']:,.0f}",
                    (r["anio_firma"], r["HHI_Promedio"]),
                    textcoords="offset points", xytext=(0, 12),
                    ha="center", fontsize=8, color=C_SECONDARY,
                    fontweight="bold")

    ax.axhline(UMBRAL_MONOPOLIO, color=C_RED, linestyle="--",
               linewidth=1.3, alpha=0.85, label=f"Monopolio = {UMBRAL_MONOPOLIO:,}")
    ax.axhline(UMBRAL_ALTO, color="#777777", linestyle=":",
               linewidth=1.0, alpha=0.7,
               label=f"Alta concentración ≥ {UMBRAL_ALTO:,}")

    all_x = sorted(set(terr["anio_firma"]).union(nac["anio_firma"]))
    ax.set_xticks(all_x)
    ax.set_xlim(min(all_x) - 0.6, max(all_x) + 0.6)
    ax.set_ylim(0, 11400)
    ax.set_xlabel("Año de firma", fontweight="bold")
    ax.set_ylabel("HHI promedio (escala 0–10.000)", fontweight="bold")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.legend(loc="upper left", fontsize=9, framealpha=0.95)

    ax.set_title("Solo se grafican años con muestra disponible para cada "
                 "orden de entidad en el cruce SECOP-DANE",
                 fontsize=10, color="#555555")

    plt.tight_layout()
    out = OUT / "hhi_por_nivel.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)
    return out


# ════════════════════════════════════════════════════════════════════════════
# FIG 3 — Distribución municipal del HHI + escala estándar
# ════════════════════════════════════════════════════════════════════════════
def figura_distribucion_municipal() -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(12, 7),
                             gridspec_kw={"height_ratios": [3, 1]})
    fig.suptitle("Distribución Municipal del HHI — Cruce SECOP-DANE",
                 fontsize=16, fontweight="bold")

    # — Histograma con los valores HHI reales por (municipio × año × nivel) —
    ax = axes[0]
    valores = hhi_cruce["hhi_concentracion"].dropna().values
    bins = np.linspace(0, 10000, 41)
    n_bins, bin_edges, patches = ax.hist(
        valores, bins=bins, edgecolor="black", linewidth=0.6, alpha=0.85
    )

    # Colorear cada barra según el tramo HHI al que pertenece su centro
    centros = (bin_edges[:-1] + bin_edges[1:]) / 2
    for centro, patch in zip(centros, patches):
        if centro < UMBRAL_MODERADO:
            patch.set_facecolor(C_GREEN)
        elif centro < UMBRAL_ALTO:
            patch.set_facecolor(C_YELLOW)
        elif centro < 5000:
            patch.set_facecolor(C_ORANGE)
        else:
            patch.set_facecolor(C_RED)

    # Conteos reales por tramo
    n_total = len(valores)
    n_comp  = int((valores < UMBRAL_MODERADO).sum())
    n_mod   = int(((valores >= UMBRAL_MODERADO) & (valores < UMBRAL_ALTO)).sum())
    n_alto  = int(((valores >= UMBRAL_ALTO)     & (valores < 5000)).sum())
    n_mono  = int((valores >= 5000).sum())
    n_10k   = int((valores == UMBRAL_MONOPOLIO).sum())

    ax.axvline(UMBRAL_MODERADO,  color="black", linestyle=":",  linewidth=1)
    ax.axvline(UMBRAL_ALTO,      color="black", linestyle="--", linewidth=1)
    ax.axvline(5000,             color="black", linestyle="--", linewidth=1)
    ax.axvline(UMBRAL_MONOPOLIO, color="black", linestyle="--", linewidth=1)

    ax.set_xlim(0, 10100)
    ax.set_xlabel("HHI (escala 0–10.000)", fontweight="bold")
    ax.set_ylabel("Frecuencia (municipios × año × nivel)", fontweight="bold")
    ax.set_title(
        f"n = {n_total:,} observaciones  |  "
        f"Competencia: {n_comp:,}  |  Moderada: {n_mod:,}  |  "
        f"Alta: {n_alto:,}  |  Monopolio (≥5.000): {n_mono:,}  "
        f"({n_10k:,} en HHI = 10.000)",
        fontsize=10, color="#555555"
    )

    # — Barra inferior: escala estándar HHI con los mismos colores —
    axb = axes[1]
    axb.grid(False)
    axb.set_facecolor("white")
    axb.spines[:].set_visible(False)
    axb.tick_params(left=False, labelleft=False)

    segmentos = [
        (0,              UMBRAL_MODERADO,  C_GREEN,  "Competencia"),
        (UMBRAL_MODERADO, UMBRAL_ALTO,     C_YELLOW, "Moderada"),
        (UMBRAL_ALTO,    5000,             C_ORANGE, "Alta"),
        (5000,           UMBRAL_MONOPOLIO, C_RED,    "Monopolio"),
    ]
    for x0, x1, color, label in segmentos:
        axb.barh(0, x1 - x0, left=x0, height=0.7, color=color,
                 edgecolor="black", linewidth=0.6, align="center")
        axb.text((x0 + x1) / 2, 0, label, ha="center", va="center",
                 fontsize=10, fontweight="bold", color="black")

    axb.set_xlim(0, 10000)
    axb.set_xticks([0, UMBRAL_MODERADO, UMBRAL_ALTO, 5000, UMBRAL_MONOPOLIO])
    axb.set_xticklabels(["0", "1.500", "2.500", "5.000", "10.000"])
    axb.set_xlabel("Escala estándar HHI (convención DOJ/FTC, "
                   "usada por el pipeline del proyecto)",
                   fontweight="bold")
    axb.set_ylim(-0.6, 0.6)

    plt.tight_layout()
    out = OUT / "hhi_distribucion_municipal.png"
    plt.savefig(out, dpi=140, bbox_inches="tight")
    plt.close(fig)

    return out


# ════════════════════════════════════════════════════════════════════════════
# Reporte HTML único que agrupa las 3 figuras
# ════════════════════════════════════════════════════════════════════════════
def generar_html(img1: Path, img2: Path, img3: Path) -> Path:
    # Resumen numérico real para mostrar en la cabecera
    hhi_2018 = hhi_anio.loc[hhi_anio["anio_firma"] == 2018, "HHI_Promedio"].iloc[0]
    hhi_2024 = hhi_anio.loc[hhi_anio["anio_firma"] == 2024, "HHI_Promedio"].iloc[0]
    hhi_2026 = hhi_anio.loc[hhi_anio["anio_firma"] == 2026, "HHI_Promedio"].iloc[0]
    n_obs = len(hhi_cruce)
    n_mono_10k = int((hhi_cruce["hhi_concentracion"] == UMBRAL_MONOPOLIO).sum())
    pct_mono = 100 * n_mono_10k / n_obs

    # Tablas resumen — directamente del CSV
    tabla_anio = hhi_anio.copy()
    tabla_anio["HHI_Promedio"] = tabla_anio["HHI_Promedio"].round(0).astype(int)
    tabla_anio_html = tabla_anio.to_html(
        index=False, classes="tbl", border=0,
        formatters={
            "Suma_Inversion": lambda v: f"${v:,.0f}",
            "Total_Contratos": lambda v: f"{v:,}",
            "Total_Municipios": lambda v: f"{v:,}",
            "HHI_Promedio": lambda v: f"{v:,}",
        }
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Indicadores HHI · Cruce SECOP-DANE</title>
<style>
  body  {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
           margin: 0; padding: 32px 48px; max-width: 1280px;
           background: #fafafa; color: #222; }}
  h1    {{ font-size: 28px; margin: 0 0 4px 0; }}
  h2    {{ font-size: 20px; margin: 36px 0 6px 0;
           border-bottom: 2px solid #4C78A8; padding-bottom: 4px; }}
  .sub  {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
  .kpis {{ display: flex; gap: 16px; margin: 18px 0 28px 0; flex-wrap: wrap; }}
  .kpi  {{ flex: 1 1 200px; background: #fff; border: 1px solid #e3e3e3;
           border-left: 4px solid #4C78A8; padding: 14px 16px; border-radius: 4px; }}
  .kpi .val {{ font-size: 22px; font-weight: 700; color: #4C78A8; }}
  .kpi .lbl {{ font-size: 12px; color: #555; margin-top: 4px;
               text-transform: uppercase; letter-spacing: 0.4px; }}
  img   {{ max-width: 100%; height: auto; display: block;
           margin: 12px 0 4px 0; border: 1px solid #ddd; border-radius: 4px;
           background: #fff; }}
  .desc {{ font-size: 13px; color: #444; margin: 8px 0 0 0; }}
  table.tbl {{ border-collapse: collapse; width: 100%; font-size: 13px;
               margin-top: 10px; background: #fff; }}
  table.tbl th, table.tbl td {{
       padding: 7px 10px; border-bottom: 1px solid #eee; text-align: right; }}
  table.tbl th {{ background: #4C78A8; color: #fff; font-weight: 600;
                   text-align: center; }}
  table.tbl td:first-child {{ text-align: center; font-weight: 600; }}
  .footnote {{ font-size: 11px; color: #777; margin-top: 32px;
               border-top: 1px solid #ddd; padding-top: 10px; }}
</style>
</head>
<body>

<h1>Indicadores HHI — Cruce SECOP-DANE</h1>
<p class="sub">Concentración de mercado en la contratación pública territorial,
2018–2026. Fuente: <code>data/hhi_por_anio.csv</code>,
<code>data/hhi_por_nivel.csv</code>,
<code>data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv</code>.</p>

<div class="kpis">
  <div class="kpi"><div class="val">{hhi_2018:,.0f}</div>
                   <div class="lbl">HHI promedio 2018</div></div>
  <div class="kpi"><div class="val">{hhi_2024:,.0f}</div>
                   <div class="lbl">HHI promedio 2024</div></div>
  <div class="kpi"><div class="val">{hhi_2026:,.0f}</div>
                   <div class="lbl">HHI promedio 2026</div></div>
  <div class="kpi"><div class="val">{n_mono_10k:,}</div>
                   <div class="lbl">obs. con HHI = 10.000
                       ({pct_mono:.1f}% de {n_obs:,})</div></div>
</div>

<h2>1. Evolución del HHI promedio nacional (2018–2026)</h2>
<p class="desc">Promedio anual del HHI municipal en la muestra cruzada
SECOP-DANE. Cada punto muestra el valor real del HHI, el número de
contratos y el número de municipios incluidos ese año.</p>
<img src="hhi_tendencia_anual.png" alt="Evolución del HHI promedio nacional">

<h2>2. HHI por orden de entidad (Nacional vs Territorial)</h2>
<p class="desc">Comparación del HHI promedio según el tipo de entidad
contratante. Se grafican únicamente los años con observaciones
disponibles para cada nivel en los archivos de entrada.</p>
<img src="hhi_por_nivel.png" alt="HHI por orden de entidad">

<h2>3. Distribución municipal del HHI y escala estándar</h2>
<p class="desc">Histograma de los {n_obs:,} registros (municipio × año
× nivel) del archivo de cruce, segmentado por los tramos estándar HHI
usados por el pipeline. La barra inferior muestra la escala de
referencia.</p>
<img src="hhi_distribucion_municipal.png" alt="Distribución municipal del HHI">

<h2>Tabla — HHI promedio nacional por año</h2>
{tabla_anio_html}

<p class="footnote">Generado por
<code>scripts/generar_graficas_hhi.py</code>. Todas las cifras provienen
de los CSV de entrada producidos por
<code>src/features/indicador_hhi_cruce.py</code>; no hay valores
estimados ni interpolados.</p>

</body>
</html>
"""
    out = OUT / "hhi_report.html"
    out.write_text(html, encoding="utf-8")
    return out


# ── Ejecución ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\nGenerando figuras...")
    p1 = figura_tendencia_anual()
    print(f"  ✓ {p1.relative_to(ROOT)}")
    p2 = figura_por_nivel()
    print(f"  ✓ {p2.relative_to(ROOT)}")
    p3 = figura_distribucion_municipal()
    print(f"  ✓ {p3.relative_to(ROOT)}")

    print("\nGenerando reporte HTML...")
    p_html = generar_html(p1, p2, p3)
    print(f"  ✓ {p_html.relative_to(ROOT)}")

    print("\nListo.")
