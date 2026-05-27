"""Genera una infografia preliminar del indicador HHI (versión boceto)."""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "artifacts" / "infografia"


def _load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    anio = pd.read_csv(DATA_DIR / "hhi_por_anio.csv")
    nivel = pd.read_csv(DATA_DIR / "hhi_por_nivel.csv")
    master = pd.read_csv(DATA_DIR / "HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv")
    return anio, nivel, master


def _color_concentracion(hhi: float) -> str:
    if hhi >= 2500:
        return "#C43D3D"
    if hhi >= 1500:
        return "#E0A800"
    return "#4E79A7"


def render(anio: pd.DataFrame, nivel: pd.DataFrame, master: pd.DataFrame) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "infografia_hhi.png"

    fig = plt.figure(figsize=(11, 16))
    fig.patch.set_facecolor("#F7F8FA")

    gs = fig.add_gridspec(
        nrows=6, ncols=2,
        height_ratios=[1.0, 0.5, 2.0, 2.0, 2.0, 1.2],
        hspace=0.7, wspace=0.25,
        left=0.07, right=0.95, top=0.96, bottom=0.04,
    )

    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    ax_title.text(
        0.5, 0.78,
        "Concentración de la contratación pública en Colombia",
        ha="center", va="center", fontsize=22, fontweight="bold", color="#1F2937",
    )
    ax_title.text(
        0.5, 0.42,
        "Índice Herfindahl-Hirschman (HHI) · SECOP I + II · 2018-2026",
        ha="center", va="center", fontsize=14, color="#4E79A7",
    )
    ax_title.text(
        0.5, 0.10,
        "Consultorio de Estadística USTA · Observatorio Ustadistica 2026-I",
        ha="center", va="center", fontsize=10, color="#6B7280", style="italic",
    )

    ax_kpi = fig.add_subplot(gs[1, :])
    ax_kpi.axis("off")
    kpis = [
        ("Mercados analizados", f"{len(master):,}"),
        ("HHI promedio nacional", f"{master['HHI'].mean():,.0f}"),
        ("Años cubiertos", f"{master['anio_key'].nunique()}"),
        ("Mercados con HHI = 10,000", f"{(master['HHI']==10000).sum()} ({(master['HHI']==10000).mean()*100:.2f}%)"),
    ]
    for i, (label, value) in enumerate(kpis):
        x = 0.05 + i * 0.235
        rect = mpatches.FancyBboxPatch(
            (x, 0.05), 0.21, 0.9,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            linewidth=0, facecolor="#FFFFFF", edgecolor="none",
        )
        ax_kpi.add_patch(rect)
        ax_kpi.text(x + 0.105, 0.62, value, ha="center", va="center",
                    fontsize=15, fontweight="bold", color="#1F2937")
        ax_kpi.text(x + 0.105, 0.25, label, ha="center", va="center",
                    fontsize=8.5, color="#6B7280")
    ax_kpi.set_xlim(0, 1)
    ax_kpi.set_ylim(0, 1)

    ax_trend = fig.add_subplot(gs[2, :])
    ax_trend.plot(anio["anio_key"], anio["HHI_promedio"], marker="o",
                  color="#4E79A7", linewidth=2.5, markersize=8, label="HHI promedio")
    ax_trend.plot(anio["anio_key"], anio["HHI_mediana"], marker="s",
                  color="#76B7B2", linewidth=2, markersize=6, label="HHI mediana",
                  linestyle="--")
    ax_trend.axhline(1500, color="#E0A800", linestyle=":", linewidth=1, alpha=0.7)
    ax_trend.axhline(2500, color="#C43D3D", linestyle=":", linewidth=1, alpha=0.7)
    ax_trend.text(anio["anio_key"].max(), 1500, " moderada", va="center",
                  fontsize=8, color="#E0A800")
    ax_trend.text(anio["anio_key"].max(), 2500, " alta", va="center",
                  fontsize=8, color="#C43D3D")
    ax_trend.set_title("Tendencia anual del HHI", fontsize=13, fontweight="bold",
                       color="#1F2937", loc="left")
    ax_trend.set_xlabel("Año")
    ax_trend.set_ylabel("HHI")
    ax_trend.legend(loc="upper left", frameon=False, fontsize=9)
    ax_trend.grid(alpha=0.2)
    ax_trend.set_facecolor("#FFFFFF")
    for spine in ("top", "right"):
        ax_trend.spines[spine].set_visible(False)

    ax_orden = fig.add_subplot(gs[3, 0])
    for orden, part in nivel.groupby("orden_entidad"):
        part = part.sort_values("anio_key")
        ax_orden.plot(part["anio_key"], part["HHI_promedio"], marker="o",
                      linewidth=2, label=orden, markersize=5)
    ax_orden.set_title("HHI por orden de entidad", fontsize=12,
                       fontweight="bold", color="#1F2937", loc="left")
    ax_orden.set_xlabel("Año")
    ax_orden.set_ylabel("HHI promedio")
    ax_orden.legend(loc="upper left", frameon=False, fontsize=8)
    ax_orden.grid(alpha=0.2)
    ax_orden.set_facecolor("#FFFFFF")
    for spine in ("top", "right"):
        ax_orden.spines[spine].set_visible(False)

    ax_dist = fig.add_subplot(gs[3, 1])
    ax_dist.hist(master["HHI"], bins=40, color="#4E79A7",
                 edgecolor="white", alpha=0.85)
    ax_dist.axvline(1500, color="#E0A800", linestyle="--", linewidth=1.2)
    ax_dist.axvline(2500, color="#C43D3D", linestyle="--", linewidth=1.2)
    ax_dist.set_title("Distribución del HHI", fontsize=12,
                      fontweight="bold", color="#1F2937", loc="left")
    ax_dist.set_xlabel("HHI")
    ax_dist.set_ylabel("Mercados")
    ax_dist.grid(axis="y", alpha=0.2)
    ax_dist.set_facecolor("#FFFFFF")
    for spine in ("top", "right"):
        ax_dist.spines[spine].set_visible(False)

    ax_top = fig.add_subplot(gs[4, :])
    ultimo = master["anio_key"].max()
    if "nombre_departamento" in master.columns:
        top_dept = (
            master[master["anio_key"] == ultimo]
            .groupby("nombre_departamento", dropna=True)["HHI"]
            .mean()
            .sort_values(ascending=True)
            .tail(10)
        )
        colors = [_color_concentracion(v) for v in top_dept.values]
        ax_top.barh(top_dept.index, top_dept.values, color=colors, edgecolor="white")
        for i, v in enumerate(top_dept.values):
            ax_top.text(v + 50, i, f"{v:,.0f}", va="center", fontsize=8.5,
                        color="#1F2937")
        ax_top.set_title(f"Top 10 departamentos con mayor HHI promedio ({ultimo})",
                         fontsize=12, fontweight="bold", color="#1F2937", loc="left")
        ax_top.set_xlabel("HHI promedio")
        ax_top.grid(axis="x", alpha=0.2)
        ax_top.set_facecolor("#FFFFFF")
        for spine in ("top", "right"):
            ax_top.spines[spine].set_visible(False)
    else:
        ax_top.axis("off")

    ax_foot = fig.add_subplot(gs[5, :])
    ax_foot.axis("off")
    leyenda = [
        ("Baja (< 1,500)", "#4E79A7"),
        ("Moderada (1,500-2,500)", "#E0A800"),
        ("Alta (≥ 2,500)", "#C43D3D"),
    ]
    for i, (label, color) in enumerate(leyenda):
        ax_foot.add_patch(mpatches.Rectangle(
            (0.08 + i * 0.30, 0.62), 0.025, 0.18, color=color))
        ax_foot.text(0.115 + i * 0.30, 0.71, label, va="center", fontsize=9,
                     color="#1F2937")
    ax_foot.text(
        0.5, 0.30,
        "Fuentes: Datos Abiertos Colombia (SECOP I `f789-7hwg`, SECOP II `jbjy-vk9h`) · DANE (CNPV 2018, EMICRON)\n"
        "Mercado estadístico: anio_key × divipola_key × orden_entidad · Escala HHI 0-10,000",
        ha="center", va="center", fontsize=8.5, color="#6B7280",
    )
    ax_foot.set_xlim(0, 1)
    ax_foot.set_ylim(0, 1)

    fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor())
    plt.close(fig)
    return out_path


def main() -> int:
    try:
        anio, nivel, master = _load_data()
    except FileNotFoundError as exc:
        print(f"ERROR: falta archivo HHI requerido: {exc}", file=sys.stderr)
        print("Genere los CSV primero con:", file=sys.stderr)
        print("  python -m src.features.indicador_hhi_cruce", file=sys.stderr)
        return 1

    out = render(anio, nivel, master)
    print(f"OK {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
