#!/usr/bin/env python3
"""
Genera notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb

Ejecutar desde la raíz del proyecto:
    python scripts/generate_eda_notebook.py
"""
import json
from pathlib import Path

cells = []
_cid = [0]


def _id():
    _cid[0] += 1
    return f"cell-{_cid[0]:04d}"


def md(source: str):
    cells.append({"cell_type": "markdown", "id": _id(), "metadata": {}, "source": source})


def code(source: str):
    cells.append({
        "cell_type": "code",
        "execution_count": None,
        "id": _id(),
        "metadata": {},
        "outputs": [],
        "source": source,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TÍTULO
# ─────────────────────────────────────────────────────────────────────────────
md(
    "# EDA: Cruce SECOP-DANE | 2018–2024\n"
    "Análisis exploratorio sobre el **Gold Mart** del pipeline de Desarrollo Social y Económico.\n\n"
    "**Fuentes integradas:**\n"
    "- **SECOP I & II** — Contratos públicos municipales (Colombia Compra Eficiente)\n"
    "- **CNPV 2018** — Censo Nacional de Población y Vivienda (NBI, IPM, etnia)\n"
    "- **EMICRON** — Encuesta de Micronegocios DANE (economía popular)\n"
    "- **Proyecciones DANE** — Población municipal 2018–2024\n\n"
    "**Granularidad:** Municipio × Año (2018–2024) | Capa: Gold Mart\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 1 — SETUP
# ─────────────────────────────────────────────────────────────────────────────
md("## 0. Configuración")

code(
    "import pandas as pd\n"
    "import numpy as np\n"
    "import matplotlib.pyplot as plt\n"
    "import matplotlib.patches as mpatches\n"
    "from matplotlib.ticker import FuncFormatter\n"
    "from pathlib import Path\n"
    "import warnings\n"
    "warnings.filterwarnings('ignore')\n"
    "\n"
    "# ── Detección robusta de la raíz del proyecto ──────────────────────\n"
    "_here = Path().resolve()\n"
    "ROOT = _here\n"
    "for _candidate in [_here, _here.parent, _here.parent.parent]:\n"
    "    if (_candidate / 'datos' / 'oro' / 'marts' / 'latest').exists():\n"
    "        ROOT = _candidate\n"
    "        break\n"
    "\n"
    "MART_PATH    = ROOT / 'datos' / 'oro' / 'marts' / 'latest' / 'mart_desarrollo_social_economico_municipio_anio.parquet'\n"
    "SPRINT2_PATH = ROOT / 'datos' / 'cruce_secop_dane_sprint2.parquet'\n"
    "ETNIA_PATH   = ROOT / 'datos' / 'etnia_checkpoint.parquet'\n"
    "\n"
    "# ── Constantes ─────────────────────────────────────────────────────\n"
    "AÑOS          = list(range(2018, 2025))\n"
    "COL_AÑO       = 'anio_key'\n"
    "COL_NBI       = 'nbi_pct'\n"
    "COL_IPM       = 'ipm_total'\n"
    "COL_MONTO     = 'inversion_total_monto'\n"
    "COL_CONTRATOS = 'cantidad_procesos_adjudicados'\n"
    "COL_DIVIPOLA  = 'divipola_key'\n"
    "COL_MUNICIPIO = 'nombre_municipio_referencia'\n"
    "COL_DEPTO     = 'nombre_departamento'\n"
    "\n"
    "# ── Estilo ─────────────────────────────────────────────────────────\n"
    "plt.style.use('ggplot')\n"
    "plt.rcParams.update({'figure.dpi': 120, 'axes.titlesize': 13,\n"
    "                     'axes.labelsize': 11, 'font.size': 10})\n"
    "PALETA_AÑOS = plt.cm.tab10(np.linspace(0, 0.9, len(AÑOS)))\n"
    "COLOR_MAP   = dict(zip(AÑOS, PALETA_AÑOS))\n"
    "\n"
    "def fmt_moneda(x, pos=None):\n"
    "    if pd.isna(x): return 'N/A'\n"
    "    if x >= 1e12: return f'${x/1e12:.1f}T'\n"
    "    if x >= 1e9:  return f'${x/1e9:.1f}B'\n"
    "    if x >= 1e6:  return f'${x/1e6:.1f}M'\n"
    "    if x >= 1e3:  return f'${x/1e3:.0f}K'\n"
    "    return f'${x:,.0f}'\n"
    "\n"
    "def gini(array):\n"
    "    a = np.array(array, dtype=np.float64)\n"
    "    a = np.sort(a[a >= 0])\n"
    "    if len(a) == 0 or a.sum() == 0: return np.nan\n"
    "    n = len(a)\n"
    "    return (n + 1 - 2 * np.sum(np.cumsum(a)) / a.sum()) / n\n"
    "\n"
    "print(f'Raiz del proyecto : {ROOT}')\n"
    "print(f'Anos de analisis  : {AÑOS}')\n"
    "print(f'Mart existe       : {MART_PATH.exists()}')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 2 — CARGA E INSPECCIÓN
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 1. Carga e inspección inicial\n\n"
    "Partimos del **Gold Mart** (salida del pipeline) y lo enriquecemos con las variables\n"
    "de vulnerabilidad social (NBI, IPM, etnia) provenientes del CNPV 2018.\n"
    "Estas variables son un snapshot fijo del censo y se propagan a todos los años."
)

code(
    "# ── 1. Gold Mart (temporal: municipio × año) ───────────────────────\n"
    "mart = pd.read_parquet(MART_PATH)\n"
    "mart[COL_AÑO] = pd.to_numeric(mart[COL_AÑO], errors='coerce').astype('Int64')\n"
    "mart = mart[mart[COL_AÑO].isin(AÑOS)].copy()\n"
    "mart[COL_DIVIPOLA] = mart[COL_DIVIPOLA].astype(str).str.strip().str.zfill(5)\n"
    "\n"
    "# ── 2. Vulnerabilidad social (CNPV 2018 via Sprint 2) ──────────────\n"
    "sprint2 = pd.read_parquet(SPRINT2_PATH)\n"
    "sprint2['divipola_key'] = sprint2['divipola_municipio'].astype(str).str.strip().str.zfill(5)\n"
    "\n"
    "# Detecta la columna NBI independientemente del encoding del parquet\n"
    "_nbi_col = next((c for c in sprint2.columns\n"
    "                 if 'nbi' in c.lower() and not c.endswith('.1') and not c.endswith('.2')), None)\n"
    "_mis_col = next((c for c in sprint2.columns\n"
    "                 if 'miseria' in c.lower() and not c.endswith('.1') and not c.endswith('.2')), None)\n"
    "_ipm_col = 'ipm_total' if 'ipm_total' in sprint2.columns else None\n"
    "\n"
    "_vuln_map = {}\n"
    "if _nbi_col: _vuln_map[_nbi_col] = COL_NBI\n"
    "if _mis_col: _vuln_map[_mis_col] = 'miseria_pct'\n"
    "if _ipm_col: _vuln_map[_ipm_col] = COL_IPM\n"
    "\n"
    "sprint2_vuln = sprint2[['divipola_key'] + list(_vuln_map.keys())].rename(columns=_vuln_map).copy()\n"
    "for c in [COL_NBI, 'miseria_pct', COL_IPM]:\n"
    "    if c in sprint2_vuln.columns:\n"
    "        sprint2_vuln[c] = pd.to_numeric(sprint2_vuln[c], errors='coerce')\n"
    "\n"
    "# ── 3. Etnia (CNPV 2018) ───────────────────────────────────────────\n"
    "etnia = pd.read_parquet(ETNIA_PATH)\n"
    "etnia['divipola_key'] = etnia['divipola_municipio'].astype(str).str.strip().str.zfill(5)\n"
    "_etnia_cols = ['divipola_key'] + [c for c in etnia.columns\n"
    "                                   if c.startswith('etnia_') and '_pct' in c]\n"
    "etnia_sub = etnia[[c for c in _etnia_cols if c in etnia.columns]]\n"
    "\n"
    "# ── 4. Enriquecimiento del Mart ─────────────────────────────────────\n"
    "df = (mart\n"
    "      .merge(sprint2_vuln, on='divipola_key', how='left')\n"
    "      .merge(etnia_sub,    on='divipola_key', how='left'))\n"
    "\n"
    "# Solo municipios (excluir agregados departamentales XX000)\n"
    "df_mun = df[~df['divipola_key'].str.endswith('000')].copy()\n"
    "\n"
    "# Tipos numéricos\n"
    "_num_cols = [COL_MONTO, COL_CONTRATOS, 'proveedores_unicos',\n"
    "             'poblacion_total_proyectada', 'poblacion_censo_2018',\n"
    "             'volumen_micronegocios_exp', COL_NBI, 'miseria_pct', COL_IPM,\n"
    "             'indicador_inversion_per_capita', 'etnia_indigena_pct', 'etnia_afro_pct']\n"
    "for col in _num_cols:\n"
    "    if col in df_mun.columns:\n"
    "        df_mun[col] = pd.to_numeric(df_mun[col], errors='coerce')\n"
    "\n"
    "print('=' * 65)\n"
    "print('INSPECCION INICIAL — Gold Mart + Vulnerabilidad CNPV 2018')\n"
    "print('=' * 65)\n"
    "print(f'Dimensiones totales     : {df.shape[0]:,} x {df.shape[1]}')\n"
    "print(f'Solo municipios         : {df_mun.shape[0]:,} x {df_mun.shape[1]}')\n"
    "print('\\nRegistros por año (solo municipios):')\n"
    "print(df_mun[COL_AÑO].value_counts().sort_index().to_string())\n"
    "print(f'\\nMunicipios únicos  : {df_mun[COL_DIVIPOLA].nunique():,}')\n"
    "print(f'Departamentos      : {df_mun[COL_DEPTO].nunique():,}')\n"
    "print(f'Regiones           : {sorted(df_mun[\"region\"].dropna().unique())}')\n"
    "print('\\nNulos en variables clave:')\n"
    "for c in [COL_NBI, COL_IPM, COL_MONTO, COL_CONTRATOS,\n"
    "          'poblacion_total_proyectada', 'volumen_micronegocios_exp']:\n"
    "    if c in df_mun.columns:\n"
    "        n = df_mun[c].isna().sum()\n"
    "        print(f'  {c}: {n:,} ({n/len(df_mun)*100:.1f}%)')\n"
    "display(df_mun.head(3))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 3 — EVOLUCIÓN ANUAL
# ─────────────────────────────────────────────────────────────────────────────
md("## 2. Evolución temporal de la contratación (2018–2024)")

code(
    "evol = df_mun.groupby(COL_AÑO).agg(\n"
    "    monto_total        = (COL_MONTO,     'sum'),\n"
    "    num_contratos      = (COL_CONTRATOS,  'sum'),\n"
    "    proveedores        = ('proveedores_unicos', 'sum'),\n"
    "    municipios_activos = (COL_DIVIPOLA,   'nunique'),\n"
    ").reset_index()\n"
    "evol['monto_promedio'] = evol['monto_total'] / evol['municipios_activos']\n"
    "evol['var_monto_pct']  = evol['monto_total'].pct_change() * 100\n"
    "evol[COL_AÑO] = evol[COL_AÑO].astype(int)\n"
    "\n"
    "print('Resumen anual:')\n"
    "display(evol.set_index(COL_AÑO))\n"
    "\n"
    "fig, axes = plt.subplots(2, 2, figsize=(16, 10))\n"
    "fig.suptitle('Evolución de la Contratación Municipal 2018–2024',\n"
    "             fontsize=16, fontweight='bold')\n"
    "\n"
    "ax = axes[0, 0]\n"
    "bars = ax.bar(evol[COL_AÑO], evol['monto_total'],\n"
    "              color=[COLOR_MAP[a] for a in evol[COL_AÑO]],\n"
    "              edgecolor='black', alpha=0.85)\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "ax.set_title('Monto total contratado por año', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Monto total')\n"
    "for bar, val in zip(bars, evol['monto_total']):\n"
    "    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),\n"
    "            f' {fmt_moneda(val)}', ha='center', va='bottom', fontsize=8)\n"
    "\n"
    "ax = axes[0, 1]\n"
    "ax.plot(evol[COL_AÑO], evol['num_contratos'],\n"
    "        marker='o', linewidth=2.5, color='#E07B54', markersize=8)\n"
    "ax.set_title('Número total de contratos adjudicados', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Contratos')\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))\n"
    "for x, y in zip(evol[COL_AÑO], evol['num_contratos']):\n"
    "    ax.annotate(f'{y:,.0f}', (x, y), textcoords='offset points',\n"
    "                xytext=(0, 8), ha='center', fontsize=8)\n"
    "\n"
    "ax = axes[1, 0]\n"
    "ax.plot(evol[COL_AÑO], evol['monto_promedio'],\n"
    "        marker='s', linewidth=2.5, color='#4C78A8', markersize=8)\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "ax.set_title('Monto promedio por municipio activo', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Monto promedio')\n"
    "\n"
    "ax = axes[1, 1]\n"
    "colores_var = ['#E74C3C' if v < 0 else '#2ECC71'\n"
    "               for v in evol['var_monto_pct'].fillna(0)]\n"
    "ax.bar(evol[COL_AÑO], evol['var_monto_pct'].fillna(0),\n"
    "       color=colores_var, edgecolor='black', alpha=0.85)\n"
    "ax.axhline(0, color='black', linewidth=0.8)\n"
    "ax.set_title('Variación % anual del monto contratado', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Variación (%)')\n"
    "for x, v in zip(evol[COL_AÑO], evol['var_monto_pct'].fillna(0)):\n"
    "    ax.text(x, v + (1 if v >= 0 else -1.5), f'{v:.1f}%',\n"
    "            ha='center', va='bottom', fontsize=9)\n"
    "plt.tight_layout(); plt.show()\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 4 — DISTRIBUCIÓN LOG10
# ─────────────────────────────────────────────────────────────────────────────
md("## 3. Distribución de la inversión por año")

code(
    "fig, axes = plt.subplots(2, 4, figsize=(20, 9), sharey=False)\n"
    "fig.suptitle('Distribución del Monto Contratado por Año (log10)',\n"
    "             fontsize=15, fontweight='bold')\n"
    "\n"
    "for idx, año in enumerate(AÑOS):\n"
    "    ax = axes[idx // 4][idx % 4]\n"
    "    sub = df_mun[(df_mun[COL_AÑO] == año) & (df_mun[COL_MONTO] > 0)].copy()\n"
    "    sub['log_monto'] = np.log10(sub[COL_MONTO])\n"
    "    ax.hist(sub['log_monto'], bins=30, color=COLOR_MAP[año], edgecolor='black', alpha=0.8)\n"
    "    ax.axvline(sub['log_monto'].mean(),   color='red',   linestyle='--', lw=1.5,\n"
    "               label=f'Media: {sub[\"log_monto\"].mean():.2f}')\n"
    "    ax.axvline(sub['log_monto'].median(), color='green', linestyle='--', lw=1.5,\n"
    "               label=f'Mediana: {sub[\"log_monto\"].median():.2f}')\n"
    "    ax.set_title(str(año), fontweight='bold')\n"
    "    ax.set_xlabel('log10(Monto)'); ax.set_ylabel('Municipios')\n"
    "    ax.legend(fontsize=7)\n"
    "\n"
    "axes[1][3].set_visible(False)\n"
    "plt.tight_layout(); plt.show()\n"
    "\n"
    "print('\\nEstadísticas del monto contratado por año:')\n"
    "display(df_mun.groupby(COL_AÑO)[COL_MONTO].describe(percentiles=[.25, .5, .75, .9, .95]))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 5 — NBI e IPM
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 4. Distribución de vulnerabilidad social (NBI e IPM)\n\n"
    "> **Nota metodológica:** NBI e IPM provienen del CNPV 2018 (censo fijo). "
    "Se visualizan por año para mostrar con qué municipios se cruza cada corte temporal, "
    "pero el valor del indicador no varía entre años."
)

code(
    "if COL_NBI not in df_mun.columns or df_mun[COL_NBI].isna().all():\n"
    "    print('ADVERTENCIA: variable NBI no disponible — revisar datos/cruce_secop_dane_sprint2.parquet')\n"
    "else:\n"
    "    fig, axes = plt.subplots(1, 2, figsize=(16, 6))\n"
    "    fig.suptitle('Distribución de Vulnerabilidad Social por Año (CNPV 2018)',\n"
    "                 fontsize=14, fontweight='bold')\n"
    "\n"
    "    ax = axes[0]\n"
    "    datos_nbi = [df_mun.loc[df_mun[COL_AÑO] == a, COL_NBI].dropna().values for a in AÑOS]\n"
    "    bp = ax.boxplot(datos_nbi, labels=AÑOS, patch_artist=True,\n"
    "                    medianprops=dict(color='darkred', linewidth=2))\n"
    "    for patch, color in zip(bp['boxes'], PALETA_AÑOS):\n"
    "        patch.set_facecolor(color); patch.set_alpha(0.7)\n"
    "    ax.set_title('NBI (%) por año', fontweight='bold')\n"
    "    ax.set_xlabel('Año'); ax.set_ylabel('NBI (%)')\n"
    "\n"
    "    ax = axes[1]\n"
    "    if COL_IPM in df_mun.columns:\n"
    "        datos_ipm = [df_mun.loc[df_mun[COL_AÑO] == a, COL_IPM].dropna().values for a in AÑOS]\n"
    "        bp2 = ax.boxplot(datos_ipm, labels=AÑOS, patch_artist=True,\n"
    "                         medianprops=dict(color='darkblue', linewidth=2))\n"
    "        for patch, color in zip(bp2['boxes'], PALETA_AÑOS):\n"
    "            patch.set_facecolor(color); patch.set_alpha(0.7)\n"
    "        ax.set_title('IPM Total por año', fontweight='bold')\n"
    "        ax.set_xlabel('Año'); ax.set_ylabel('IPM')\n"
    "    else:\n"
    "        ax.text(0.5, 0.5, 'IPM no disponible', ha='center', va='center',\n"
    "                transform=ax.transAxes, fontsize=14)\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    print('\\nNBI promedio por año:')\n"
    "    display(df_mun.groupby(COL_AÑO)[COL_NBI].agg(['mean','median','std']).round(2))\n"
    "    if COL_IPM in df_mun.columns:\n"
    "        print('\\nIPM promedio por año:')\n"
    "        display(df_mun.groupby(COL_AÑO)[COL_IPM].agg(['mean','median','std']).round(2))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 6 — TOP 15 MUNICIPIOS
# ─────────────────────────────────────────────────────────────────────────────
md("## 5. Concentración de la inversión — Top 15 municipios por año")

code(
    "for año in AÑOS:\n"
    "    sub       = df_mun[df_mun[COL_AÑO] == año]\n"
    "    total_año = sub[COL_MONTO].sum()\n"
    "    top15     = sub.nlargest(15, COL_MONTO)\n"
    "    top10_share = top15.head(10)[COL_MONTO].sum() / total_año * 100 if total_año else 0\n"
    "\n"
    "    fig, ax = plt.subplots(figsize=(10, 6))\n"
    "    colors = plt.cm.RdYlGn(np.linspace(0.2, 0.8, len(top15)))\n"
    "    bars = ax.barh(range(len(top15)), top15[COL_MONTO], color=colors)\n"
    "    ax.set_yticks(range(len(top15)))\n"
    "    ax.set_yticklabels(top15[COL_MUNICIPIO])\n"
    "    ax.invert_yaxis()\n"
    "    ax.set_title(\n"
    "        f'{año} — Top 15 municipios por monto contratado\\n'\n"
    "        f'(Top 10 concentran {top10_share:.1f}% del total anual)',\n"
    "        fontweight='bold')\n"
    "    ax.set_xlabel('Monto total contratado')\n"
    "    ax.xaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "    for bar, val in zip(bars, top15[COL_MONTO]):\n"
    "        ax.text(val, bar.get_y() + bar.get_height()/2,\n"
    "                f' {fmt_moneda(val)}', ha='left', va='center', fontsize=8)\n"
    "    plt.tight_layout(); plt.show()\n"
    "    print(f'  Monto total {año}: {fmt_moneda(total_año)}')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 7 — GINI
# ─────────────────────────────────────────────────────────────────────────────
md("## 6. Desigualdad — Coeficiente de Gini")

code(
    "ginis = {int(a): gini(df_mun.loc[df_mun[COL_AÑO] == a, COL_MONTO].fillna(0))\n"
    "         for a in AÑOS}\n"
    "\n"
    "fig, ax = plt.subplots(figsize=(10, 5))\n"
    "años_v = list(ginis.keys()); vals_g = list(ginis.values())\n"
    "bars = ax.bar(años_v, vals_g,\n"
    "              color=[COLOR_MAP[a] for a in años_v], edgecolor='black', alpha=0.85)\n"
    "ax.set_title('Coeficiente de Gini del Monto Contratado (2018–2024)\\n'\n"
    "             '(1 = desigualdad máxima, 0 = perfecta igualdad)', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Coeficiente de Gini')\n"
    "ax.set_ylim(0, 1)\n"
    "for bar, val in zip(bars, vals_g):\n"
    "    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,\n"
    "            f'{val:.3f}', ha='center', fontsize=10, fontweight='bold')\n"
    "plt.tight_layout(); plt.show()\n"
    "\n"
    "print('\\nGini por año (desigualdad en distribución de contratos):')\n"
    "for a, g_val in ginis.items():\n"
    "    barra = '|' * int(g_val * 30)\n"
    "    print(f'  {a}: {g_val:.4f} [{barra}]')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 8 — NBI vs LOG(MONTO)
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 7. Relación inversión–vulnerabilidad (NBI vs log Monto)\n\n"
    "Dispersión de municipios por año: eje X = NBI (%), eje Y = log₁₀ del monto contratado. "
    "La línea roja es la tendencia lineal y `r` es la correlación de Pearson."
)

code(
    "if COL_NBI in df_mun.columns and not df_mun[COL_NBI].isna().all():\n"
    "    corrs = []\n"
    "    fig, axes = plt.subplots(2, 4, figsize=(22, 10), sharex=True, sharey=True)\n"
    "    fig.suptitle('NBI (%) vs log10(Monto Contratado) por Año',\n"
    "                 fontsize=15, fontweight='bold')\n"
    "\n"
    "    for idx, año in enumerate(AÑOS):\n"
    "        ax = axes[idx // 4][idx % 4]\n"
    "        sub = df_mun[(df_mun[COL_AÑO] == año) & (df_mun[COL_MONTO] > 0)] \\\n"
    "                    .dropna(subset=[COL_NBI]).copy()\n"
    "        sub['log_monto'] = np.log10(sub[COL_MONTO])\n"
    "\n"
    "        ax.scatter(sub[COL_NBI], sub['log_monto'],\n"
    "                   alpha=0.4, s=15, color=COLOR_MAP[año])\n"
    "        if len(sub) > 2:\n"
    "            z = np.polyfit(sub[COL_NBI], sub['log_monto'], 1)\n"
    "            p = np.poly1d(z)\n"
    "            xr = np.linspace(sub[COL_NBI].min(), sub[COL_NBI].max(), 100)\n"
    "            ax.plot(xr, p(xr), 'r--', linewidth=1.5)\n"
    "            r = sub[COL_NBI].corr(sub['log_monto'])\n"
    "            corrs.append({'año': año, 'r_NBI_logMonto': round(r, 4), 'n': len(sub)})\n"
    "            ax.text(0.98, 0.05, f'r = {r:.3f}', transform=ax.transAxes,\n"
    "                    ha='right', fontsize=9,\n"
    "                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))\n"
    "        ax.set_title(str(año), fontweight='bold')\n"
    "        ax.set_xlabel('NBI (%)'); ax.set_ylabel('log10(Monto)')\n"
    "        ax.grid(True, alpha=0.3)\n"
    "\n"
    "    axes[1][3].set_visible(False)\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    print('\\nCorrelacion Pearson NBI vs log10(Monto) por año:')\n"
    "    display(pd.DataFrame(corrs).set_index('año'))\n"
    "else:\n"
    "    print('NBI no disponible para este análisis.')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 9 — DEPARTAMENTO Y REGIÓN
# ─────────────────────────────────────────────────────────────────────────────
md("## 8. Análisis por departamento y región geográfica")

code(
    "dep_año = df_mun.groupby([COL_DEPTO, COL_AÑO]).agg(\n"
    "    monto_total   = (COL_MONTO,     'sum'),\n"
    "    num_contratos = (COL_CONTRATOS,  'sum'),\n"
    ").reset_index()\n"
    "dep_año[COL_AÑO] = dep_año[COL_AÑO].astype(int)\n"
    "\n"
    "top10_dep = (df_mun.groupby(COL_DEPTO)[COL_MONTO]\n"
    "               .sum().nlargest(10).index.tolist())\n"
    "\n"
    "fig, axes = plt.subplots(1, 2, figsize=(18, 7))\n"
    "fig.suptitle('Evolución del Monto Contratado 2018–2024', fontsize=14, fontweight='bold')\n"
    "\n"
    "ax = axes[0]\n"
    "for dep in top10_dep:\n"
    "    sub = dep_año[dep_año[COL_DEPTO] == dep].sort_values(COL_AÑO)\n"
    "    ax.plot(sub[COL_AÑO], sub['monto_total'], marker='o', linewidth=2, label=dep)\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "ax.set_title('Top 10 Departamentos', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Monto total')\n"
    "ax.legend(loc='upper left', fontsize=7, ncol=2)\n"
    "ax.set_xticks(AÑOS)\n"
    "\n"
    "ax = axes[1]\n"
    "reg_año = df_mun.groupby(['region', COL_AÑO]).agg(\n"
    "    monto_total = (COL_MONTO, 'sum')\n"
    ").reset_index()\n"
    "reg_año[COL_AÑO] = reg_año[COL_AÑO].astype(int)\n"
    "for reg in sorted(r for r in df_mun['region'].dropna().unique() if r):\n"
    "    sub = reg_año[reg_año['region'] == reg].sort_values(COL_AÑO)\n"
    "    ax.plot(sub[COL_AÑO], sub['monto_total'], marker='o', linewidth=2, label=reg)\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "ax.set_title('Por Región Geográfica', fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Monto total')\n"
    "ax.legend(loc='upper left', fontsize=8)\n"
    "ax.set_xticks(AÑOS)\n"
    "\n"
    "plt.tight_layout(); plt.show()\n"
    "\n"
    "print('\\nMonto acumulado 2018-2024 por departamento (Top 15):')\n"
    "display(df_mun.groupby(COL_DEPTO)[COL_MONTO].sum().nlargest(15)\n"
    "        .apply(fmt_moneda).to_frame('monto_acumulado'))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 10 — CUADRANTES
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 9. Cuadrantes de abandono relativo por año\n\n"
    "**Rojo** = alta necesidad (NBI > mediana) con poca inversión (monto < mediana). "
    "Estos municipios son los candidatos prioritarios para política pública."
)

code(
    "if COL_NBI in df_mun.columns and not df_mun[COL_NBI].isna().all():\n"
    "    resumen_cuadrantes = []\n"
    "    fig, axes = plt.subplots(2, 4, figsize=(22, 10))\n"
    "    fig.suptitle('Cuadrantes de Inversión Social por Año\\n'\n"
    "                 '(Rojo = alta necesidad / poca inversión)',\n"
    "                 fontsize=14, fontweight='bold')\n"
    "\n"
    "    for idx, año in enumerate(AÑOS):\n"
    "        ax = axes[idx // 4][idx % 4]\n"
    "        sub = df_mun[df_mun[COL_AÑO] == año].dropna(subset=[COL_NBI]).copy()\n"
    "        med_nbi   = sub[COL_NBI].median()\n"
    "        med_monto = sub[COL_MONTO].median()\n"
    "\n"
    "        prioritarios = sub[\n"
    "            (sub[COL_NBI]   > med_nbi) &\n"
    "            (sub[COL_MONTO] <= med_monto)\n"
    "        ]\n"
    "        resumen_cuadrantes.append({\n"
    "            'año': año,\n"
    "            'municipios_prioritarios': len(prioritarios),\n"
    "            'pct_sobre_total': round(len(prioritarios) / len(sub) * 100, 1)\n"
    "        })\n"
    "        ax.scatter(sub[COL_NBI], sub[COL_MONTO], alpha=0.3, color='gray', s=12)\n"
    "        ax.scatter(prioritarios[COL_NBI], prioritarios[COL_MONTO],\n"
    "                   alpha=0.8, color='red', s=15)\n"
    "        ax.axvline(med_nbi,   color='black', linestyle='--', linewidth=1)\n"
    "        ax.axhline(med_monto, color='black', linestyle='--', linewidth=1)\n"
    "        ax.set_yscale('log')\n"
    "        ax.set_title(f'{año}  |  {len(prioritarios)} mun. en abandono', fontweight='bold')\n"
    "        ax.set_xlabel('NBI (%)'); ax.set_ylabel('Monto (log)')\n"
    "\n"
    "    axes[1][3].set_visible(False)\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    print('\\nMunicipios en cuadrante de abandono relativo por año:')\n"
    "    display(pd.DataFrame(resumen_cuadrantes).set_index('año'))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 11 — MUNICIPIOS CRÍTICOS
# ─────────────────────────────────────────────────────────────────────────────
md("## 10. Municipios críticos — Alta pobreza, cero contratos")

code(
    "if COL_NBI in df_mun.columns and not df_mun[COL_NBI].isna().all():\n"
    "    criticos_res = []\n"
    "    for año in AÑOS:\n"
    "        sub = df_mun[df_mun[COL_AÑO] == año].dropna(subset=[COL_NBI])\n"
    "        umbral = sub[COL_NBI].quantile(0.75)\n"
    "        criticos = sub[(sub[COL_NBI] >= umbral) & (sub[COL_MONTO] == 0)]\n"
    "        criticos_res.append({\n"
    "            'año': año,\n"
    "            'umbral_nbi_p75': round(umbral, 1),\n"
    "            'municipios_criticos': len(criticos),\n"
    "            'pct': round(len(criticos) / len(sub) * 100, 1)\n"
    "        })\n"
    "\n"
    "    df_criticos = pd.DataFrame(criticos_res).set_index('año')\n"
    "    print('Municipios con NBI > P75 y 0 contratos:')\n"
    "    display(df_criticos)\n"
    "\n"
    "    fig, ax = plt.subplots(figsize=(10, 5))\n"
    "    bars = ax.bar(df_criticos.index, df_criticos['municipios_criticos'],\n"
    "                  color=[COLOR_MAP[a] for a in df_criticos.index],\n"
    "                  edgecolor='black', alpha=0.85)\n"
    "    ax.set_title('Municipios Críticos por Año\\n(NBI > P75 y Cero Contratos)',\n"
    "                 fontweight='bold')\n"
    "    ax.set_xlabel('Año'); ax.set_ylabel('Número de municipios')\n"
    "    for bar, val in zip(bars, df_criticos['municipios_criticos']):\n"
    "        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,\n"
    "                str(val), ha='center', fontsize=10, fontweight='bold')\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    último_año = AÑOS[-1]\n"
    "    sub_ult = df_mun[df_mun[COL_AÑO] == último_año].dropna(subset=[COL_NBI])\n"
    "    umbral_ult = sub_ult[COL_NBI].quantile(0.75)\n"
    "    criticos_ult = sub_ult[(sub_ult[COL_NBI] >= umbral_ult) & (sub_ult[COL_MONTO] == 0)]\n"
    "    print(f'\\nTop 10 municipios críticos en {último_año}:')\n"
    "    display(criticos_ult.nlargest(10, COL_NBI)\n"
    "            [[COL_DEPTO, COL_MUNICIPIO, COL_NBI, 'region']])\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 12 — TICKET PROMEDIO
# ─────────────────────────────────────────────────────────────────────────────
md("## 11. Ticket promedio por cuartil de NBI y año")

code(
    "if COL_NBI in df_mun.columns and not df_mun[COL_NBI].isna().all():\n"
    "    df_mun = df_mun.copy()\n"
    "    df_mun['ticket_promedio'] = df_mun[COL_MONTO] / df_mun[COL_CONTRATOS].replace(0, np.nan)\n"
    "    ticket_anual = []\n"
    "    for año in AÑOS:\n"
    "        sub = df_mun[df_mun[COL_AÑO] == año].dropna(subset=[COL_NBI, 'ticket_promedio']).copy()\n"
    "        sub['cuartil_nbi'] = pd.qcut(sub[COL_NBI], 4,\n"
    "                                      labels=['Bajo NBI', 'Medio-Bajo', 'Medio-Alto', 'Alto NBI'])\n"
    "        med_tick = sub.groupby('cuartil_nbi', observed=False)['ticket_promedio'].median()\n"
    "        med_tick.name = año\n"
    "        ticket_anual.append(med_tick)\n"
    "\n"
    "    ticket_df = pd.DataFrame(ticket_anual)\n"
    "\n"
    "    fig, ax = plt.subplots(figsize=(13, 6))\n"
    "    x = np.arange(len(ticket_df.columns))\n"
    "    width = 0.11\n"
    "    for i, (año, row) in enumerate(ticket_df.iterrows()):\n"
    "        ax.bar(x + i * width, row.values, width,\n"
    "               label=str(año), color=COLOR_MAP[int(año)], edgecolor='black', alpha=0.85)\n"
    "    ax.set_title('Ticket Promedio (mediana) por Cuartil de NBI y Año', fontweight='bold')\n"
    "    ax.set_xticks(x + width * (len(AÑOS) - 1) / 2)\n"
    "    ax.set_xticklabels(ticket_df.columns)\n"
    "    ax.set_ylabel('Valor mediano por contrato ($)')\n"
    "    ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "    ax.legend(title='Año', fontsize=8)\n"
    "    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    print('\\nTicket promedio mediano por cuartil y año:')\n"
    "    display(ticket_df.map(lambda x: fmt_moneda(x) if pd.notna(x) else 'N/A'))\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 13 — MATRICES DE CORRELACIÓN
# ─────────────────────────────────────────────────────────────────────────────
md("## 12. Matrices de correlación anuales")

code(
    "_COLS_CORR_CAND = [\n"
    "    COL_MONTO, COL_CONTRATOS, 'proveedores_unicos',\n"
    "    COL_NBI, COL_IPM, 'etnia_indigena_pct', 'etnia_afro_pct',\n"
    "    'poblacion_total_proyectada', 'volumen_micronegocios_exp',\n"
    "    'indicador_inversion_per_capita',\n"
    "]\n"
    "COLS_CORR = [c for c in _COLS_CORR_CAND if c in df_mun.columns]\n"
    "etiquetas_corr = [c[:14] for c in COLS_CORR]\n"
    "\n"
    "fig, axes = plt.subplots(2, 4, figsize=(24, 11))\n"
    "fig.suptitle('Matrices de Correlación Anuales (2018–2024)', fontsize=15, fontweight='bold')\n"
    "\n"
    "im_last = None\n"
    "for idx, año in enumerate(AÑOS):\n"
    "    ax = axes[idx // 4][idx % 4]\n"
    "    corr = df_mun[df_mun[COL_AÑO] == año][COLS_CORR].corr()\n"
    "    im_last = ax.imshow(corr, cmap='RdYlGn', vmin=-1, vmax=1)\n"
    "    ax.set_xticks(range(len(COLS_CORR)))\n"
    "    ax.set_xticklabels(etiquetas_corr, rotation=45, ha='right', fontsize=6)\n"
    "    ax.set_yticks(range(len(COLS_CORR)))\n"
    "    ax.set_yticklabels(COLS_CORR, fontsize=6)\n"
    "    for i in range(len(COLS_CORR)):\n"
    "        for j in range(len(COLS_CORR)):\n"
    "            ax.text(j, i, f'{corr.iloc[i, j]:.2f}', ha='center', va='center',\n"
    "                    color='black', fontsize=5.5)\n"
    "    ax.set_title(str(año), fontweight='bold')\n"
    "\n"
    "axes[1][3].set_visible(False)\n"
    "if im_last is not None:\n"
    "    fig.colorbar(im_last, ax=axes.ravel().tolist(), shrink=0.3)\n"
    "plt.tight_layout(); plt.show()\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 14 — % MONTO A ALTA VULNERABILIDAD
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 13. Alta vulnerabilidad vs. inversión recibida\n\n"
    "¿Qué proporción del monto total llega a los municipios con NBI mayor o igual a la mediana anual?"
)

code(
    "if COL_NBI in df_mun.columns and not df_mun[COL_NBI].isna().all():\n"
    "    grupos_res = []\n"
    "    for año in AÑOS:\n"
    "        sub = df_mun[df_mun[COL_AÑO] == año].dropna(subset=[COL_NBI]).copy()\n"
    "        med_nbi = sub[COL_NBI].median()\n"
    "        sub['grupo'] = np.where(sub[COL_NBI] >= med_nbi,\n"
    "                                'Alta vulnerabilidad', 'Baja vulnerabilidad')\n"
    "        res = sub.groupby('grupo').agg(\n"
    "            municipios  = (COL_DIVIPOLA,  'count'),\n"
    "            monto_total = (COL_MONTO,     'sum'),\n"
    "            contratos   = (COL_CONTRATOS,  'sum'),\n"
    "        ).reset_index()\n"
    "        res['año'] = año\n"
    "        grupos_res.append(res)\n"
    "\n"
    "    df_grupos = pd.concat(grupos_res)\n"
    "    alta = df_grupos[df_grupos['grupo'] == 'Alta vulnerabilidad'].set_index('año')\n"
    "    total_monto_año = df_grupos.groupby('año')['monto_total'].sum()\n"
    "    pct_alta = (alta['monto_total'] / total_monto_año * 100).rename('pct_monto_alta_vul')\n"
    "\n"
    "    fig, ax = plt.subplots(figsize=(11, 6))\n"
    "    ax.plot(pct_alta.index, pct_alta.values, marker='o', linewidth=2.5,\n"
    "            color='#E74C3C', markersize=9)\n"
    "    ax.axhline(50, color='gray', linestyle='--', linewidth=1,\n"
    "               label='50% (distribución equitativa)')\n"
    "    ax.set_title('% del Monto Total hacia Municipios de Alta Vulnerabilidad\\n'\n"
    "                 '(NBI >= mediana anual)', fontweight='bold')\n"
    "    ax.set_xlabel('Año'); ax.set_ylabel('% del monto total')\n"
    "    ax.set_ylim(0, 100); ax.set_xticks(AÑOS)\n"
    "    for x, y in zip(pct_alta.index, pct_alta.values):\n"
    "        ax.annotate(f'{y:.1f}%', (x, y),\n"
    "                    textcoords='offset points', xytext=(0, 10),\n"
    "                    ha='center', fontsize=10)\n"
    "    ax.legend()\n"
    "    plt.tight_layout(); plt.show()\n"
    "\n"
    "    print('\\n% del monto hacia alta vulnerabilidad por año:')\n"
    "    display(pct_alta.round(2).to_frame())\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 15 — MICRONEGOCIOS
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 14. Micronegocios y Economía Popular (EMICRON)\n\n"
    "> EMICRON tiene granularidad departamental. El mart Gold propaga el dato "
    "a los municipios de cada departamento. Aquí usamos los agregados departamentales directamente."
)

code(
    "# Agregados departamentales del mart (códigos XX000)\n"
    "df_depto = df[df['divipola_key'].str.endswith('000')].copy()\n"
    "df_depto[COL_AÑO] = df_depto[COL_AÑO].astype(int)\n"
    "AÑOS_MIC = list(range(2019, 2025))  # EMICRON arranca en 2019\n"
    "\n"
    "_mic_ok = (\n"
    "    'volumen_micronegocios_exp' in df_depto.columns\n"
    "    and df_depto['volumen_micronegocios_exp'].gt(0).any()\n"
    ")\n"
    "\n"
    "if _mic_ok:\n"
    "    evol_mic = (df_depto[df_depto[COL_AÑO].isin(AÑOS_MIC)]\n"
    "                .groupby(COL_AÑO)\n"
    "                .agg(vol_total = ('volumen_micronegocios_exp', 'sum'))\n"
    "                .reset_index())\n"
    "\n"
    "    fig, axes = plt.subplots(1, 2, figsize=(15, 6))\n"
    "    fig.suptitle('Economía Popular: Micronegocios EMICRON 2019–2024',\n"
    "                 fontsize=14, fontweight='bold')\n"
    "\n"
    "    ax = axes[0]\n"
    "    ax.plot(evol_mic[COL_AÑO], evol_mic['vol_total'],\n"
    "            marker='o', linewidth=2.5, color='#9B59B6', markersize=9)\n"
    "    ax.set_title('Volumen total de micronegocios (expandido)', fontweight='bold')\n"
    "    ax.set_xlabel('Año'); ax.set_ylabel('Micronegocios expandidos')\n"
    "    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x/1e6:.1f}M'))\n"
    "    for x, y in zip(evol_mic[COL_AÑO], evol_mic['vol_total']):\n"
    "        ax.annotate(f'{y/1e6:.1f}M', (x, y),\n"
    "                    textcoords='offset points', xytext=(0, 8), ha='center', fontsize=9)\n"
    "\n"
    "    ax = axes[1]\n"
    "    top_dep_mic = (df_depto[df_depto[COL_AÑO].isin(AÑOS_MIC)]\n"
    "                   .groupby(COL_DEPTO)['volumen_micronegocios_exp']\n"
    "                   .sum().nlargest(8).index.tolist())\n"
    "    for dep in top_dep_mic:\n"
    "        sub = df_depto[(df_depto[COL_DEPTO] == dep) &\n"
    "                       (df_depto[COL_AÑO].isin(AÑOS_MIC))]\n"
    "        ax.plot(sub[COL_AÑO], sub['volumen_micronegocios_exp'],\n"
    "                marker='o', linewidth=2, label=dep)\n"
    "    ax.set_title('Top 8 Departamentos — Volumen de Micronegocios', fontweight='bold')\n"
    "    ax.set_xlabel('Año'); ax.set_ylabel('Micronegocios expandidos')\n"
    "    ax.legend(fontsize=7, ncol=2)\n"
    "    plt.tight_layout(); plt.show()\n"
    "else:\n"
    "    print('INFO: Datos EMICRON no disponibles a nivel departamental en el mart.')\n"
    "    print('      Fuente alternativa: datos/plata/silver_emicron_agregado.parquet')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 16 — CONTEXTO PANDEMIA Y ELECCIONES
# ─────────────────────────────────────────────────────────────────────────────
md(
    "## 15. Contexto histórico — Pandemia y ciclos electorales\n\n"
    "Las dimensiones de tiempo del Gold Mart marcan años electorales y la pandemia."
)

code(
    "evol_ctx = evol.copy()\n"
    "flags_tiempo = (df_mun.groupby(COL_AÑO)\n"
    "                .agg(\n"
    "                    es_pandemia  = ('es_pandemia',                     'first'),\n"
    "                    es_elec_pres = ('es_anio_electoral_presidencial',   'first'),\n"
    "                    es_elec_reg  = ('es_anio_electoral_regional',       'first'),\n"
    "                ).reset_index())\n"
    "flags_tiempo[COL_AÑO] = flags_tiempo[COL_AÑO].astype(int)\n"
    "evol_ctx = evol_ctx.merge(flags_tiempo, on=COL_AÑO, how='left')\n"
    "\n"
    "fig, ax = plt.subplots(figsize=(14, 7))\n"
    "ax.bar(evol_ctx[COL_AÑO], evol_ctx['monto_total'],\n"
    "       color=[COLOR_MAP[a] for a in evol_ctx[COL_AÑO]], edgecolor='black', alpha=0.7)\n"
    "ax.yaxis.set_major_formatter(FuncFormatter(fmt_moneda))\n"
    "ax.set_title('Monto Total Contratado con Contexto Histórico 2018–2024',\n"
    "             fontsize=14, fontweight='bold')\n"
    "ax.set_xlabel('Año'); ax.set_ylabel('Monto total')\n"
    "\n"
    "for _, row in evol_ctx.iterrows():\n"
    "    etiquetas_ctx = []\n"
    "    if row.get('es_pandemia'):   etiquetas_ctx.append('Pandemia')\n"
    "    if row.get('es_elec_pres'):  etiquetas_ctx.append('Elec. Pres.')\n"
    "    if row.get('es_elec_reg'):   etiquetas_ctx.append('Elec. Reg.')\n"
    "    if etiquetas_ctx:\n"
    "        ax.text(int(row[COL_AÑO]), row['monto_total'] * 1.015,\n"
    "                '\\n'.join(etiquetas_ctx), ha='center', fontsize=9, style='italic')\n"
    "\n"
    "plt.tight_layout(); plt.show()\n"
    "\n"
    "print('\\nMonto contratado con contexto temporal:')\n"
    "display(evol_ctx[[COL_AÑO, 'monto_total', 'num_contratos',\n"
    "                   'es_pandemia', 'es_elec_pres', 'es_elec_reg']])\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# CELDA 17 — RESUMEN EJECUTIVO
# ─────────────────────────────────────────────────────────────────────────────
md("## 16. Resumen ejecutivo")

code(
    "print('=' * 70)\n"
    "print('RESUMEN EJECUTIVO — EDA GOLD MART SECOP-DANE 2018-2024')\n"
    "print('=' * 70)\n"
    "print(f'\\nPeriodo analizado    : 2018 - 2024')\n"
    "print(f'Municipios únicos    : {df_mun[COL_DIVIPOLA].nunique():,}')\n"
    "print(f'Departamentos        : {df_mun[COL_DEPTO].nunique():,}')\n"
    "print(f'Monto total 2018-24  : {fmt_moneda(df_mun[COL_MONTO].sum())}')\n"
    "print(f'Contratos totales    : {df_mun[COL_CONTRATOS].sum():,.0f}')\n"
    "print(f'Proveedores totales  : {df_mun[\"proveedores_unicos\"].sum():,.0f}')\n"
    "\n"
    "print('\\nIndicadores anuales clave:')\n"
    "resumen_final = evol.set_index(COL_AÑO)[[\n"
    "    'monto_total', 'num_contratos', 'municipios_activos',\n"
    "    'monto_promedio', 'var_monto_pct'\n"
    "]].copy()\n"
    "resumen_final['monto_total']    = resumen_final['monto_total'].apply(fmt_moneda)\n"
    "resumen_final['monto_promedio'] = resumen_final['monto_promedio'].apply(fmt_moneda)\n"
    "resumen_final['num_contratos']  = resumen_final['num_contratos'].apply(lambda x: f'{x:,.0f}')\n"
    "resumen_final['var_monto_pct']  = resumen_final['var_monto_pct'].apply(\n"
    "    lambda x: f'{x:+.1f}%' if pd.notna(x) else 'Base')\n"
    "display(resumen_final)\n"
    "\n"
    "print('\\nGini por año (desigualdad en distribución de contratos):')\n"
    "for a, g_val in ginis.items():\n"
    "    barra = '|' * int(g_val * 30)\n"
    "    print(f'  {a}: {g_val:.3f} [{barra}]')\n"
    "\n"
    "if 'resumen_cuadrantes' in dir():\n"
    "    print('\\nMunicipios en cuadrante de abandono relativo:')\n"
    "    for r in resumen_cuadrantes:\n"
    "        print(f\"  {r['año']}: {r['municipios_prioritarios']:,} municipios ({r['pct_sobre_total']}%)\")\n"
    "\n"
    "print('\\nFuentes de datos:')\n"
    "print(f'  Gold Mart   : {MART_PATH.relative_to(ROOT)}')\n"
    "print(f'  CNPV 2018   : {SPRINT2_PATH.relative_to(ROOT)}')\n"
    "print(f'  Etnia CNPV  : {ETNIA_PATH.relative_to(ROOT)}')\n"
)

# ─────────────────────────────────────────────────────────────────────────────
# ENSAMBLAR Y ESCRIBIR
# ─────────────────────────────────────────────────────────────────────────────
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "pygments_lexer": "ipython3",
            "version": "3.9.0",
        },
    },
    "cells": cells,
}

out = Path(__file__).parent.parent / "notebooks" / "EDA_SECOP_DANE_Gold_2018_2024.ipynb"
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    json.dump(nb, fh, ensure_ascii=False, indent=1)

print(f"Notebook generado: {out}")
print(f"Celdas: {len(cells)}")
