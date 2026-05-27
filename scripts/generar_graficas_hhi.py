"""Genera graficas y reporte HTML del indicador HHI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "artifacts" / "hhi"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.features.indicador_hhi_cruce import OUTPUT_NAMES, run


def _load_or_build() -> dict[str, pd.DataFrame]:
    missing = [name for name in OUTPUT_NAMES.values() if not (DATA_DIR / name).exists()]
    if missing:
        print("CSV HHI ausentes; recalculando desde Silver...")
        return run(ROOT, write=True)
    print("Cargando datos HHI...")
    return {
        key: pd.read_csv(DATA_DIR / filename)
        for key, filename in OUTPUT_NAMES.items()
    }


def _save_tendencia(df: pd.DataFrame) -> Path:
    path = OUT_DIR / "hhi_tendencia_anual.png"
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["anio_key"], df["HHI_promedio"], marker="o", linewidth=2.2)
    ax.axhline(1500, color="#E0A800", linestyle="--", linewidth=1)
    ax.axhline(2500, color="#C43D3D", linestyle="--", linewidth=1)
    ax.set_title("HHI promedio por anio")
    ax.set_xlabel("Anio")
    ax.set_ylabel("HHI promedio")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _save_por_nivel(df: pd.DataFrame) -> Path:
    path = OUT_DIR / "hhi_por_nivel.png"
    fig, ax = plt.subplots(figsize=(10, 5))
    for level, part in df.groupby("orden_entidad"):
        part = part.sort_values("anio_key")
        ax.plot(part["anio_key"], part["HHI_promedio"], marker="o", linewidth=2, label=level)
    ax.axhline(1500, color="#E0A800", linestyle="--", linewidth=1)
    ax.axhline(2500, color="#C43D3D", linestyle="--", linewidth=1)
    ax.set_title("HHI promedio por orden de entidad")
    ax.set_xlabel("Anio")
    ax.set_ylabel("HHI promedio")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _save_distribucion(master: pd.DataFrame) -> Path:
    path = OUT_DIR / "hhi_distribucion_municipal.png"
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(master["HHI"], bins=40, color="#4E79A7", edgecolor="white")
    ax.axvline(1500, color="#E0A800", linestyle="--", linewidth=1.2, label="1500")
    ax.axvline(2500, color="#C43D3D", linestyle="--", linewidth=1.2, label="2500")
    ax.set_title("Distribucion HHI municipio-anio-orden")
    ax.set_xlabel("HHI")
    ax.set_ylabel("Mercados")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def _fmt_number(value: float) -> str:
    return f"{value:,.2f}"


def _build_html(outputs: dict[str, pd.DataFrame], figures: list[Path]) -> str:
    yearly = outputs["anio"].copy()
    level = outputs["nivel"].copy()
    master = outputs["master"].copy()

    yearly_table = yearly.to_html(index=False, float_format=_fmt_number)
    level_table = level.to_html(index=False, float_format=_fmt_number)
    top_high = (
        master.sort_values(["anio_key", "HHI"], ascending=[False, False])
        .head(25)
        .to_html(index=False, float_format=_fmt_number)
    )

    fig_tags = "\n".join(
        f'<figure><img src="{fig.name}" alt="{fig.stem}"></figure>' for fig in figures
    )
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Reporte HHI SECOP</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 32px; color: #222; }}
    h1, h2 {{ color: #1f2937; }}
    img {{ max-width: 100%; border: 1px solid #ddd; }}
    table {{ border-collapse: collapse; width: 100%; margin: 16px 0 28px; font-size: 13px; }}
    th, td {{ border: 1px solid #ddd; padding: 6px 8px; text-align: right; }}
    th {{ background: #f3f4f6; }}
    td:first-child, th:first-child {{ text-align: left; }}
    .note {{ background: #f8fafc; border-left: 4px solid #4e79a7; padding: 12px 16px; }}
  </style>
</head>
<body>
  <h1>Reporte HHI SECOP</h1>
  <p class="note">
    Generado el {generated_at}. El calculo usa Silver transaccional SECOP I+II,
    deduplica por <code>id_contrato</code> y calcula el mercado por
    <code>anio_key</code>, <code>divipola_key</code> y <code>orden_entidad</code>.
    Los faltantes de orden quedan como <code>NO_DEFINIDO</code>; no se imputan
    como territoriales.
  </p>
  {fig_tags}
  <h2>Resumen anual</h2>
  {yearly_table}
  <h2>Resumen por orden de entidad</h2>
  {level_table}
  <h2>Mercados con HHI mas alto</h2>
  {top_high}
</body>
</html>
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = _load_or_build()
    print(f"  hhi_por_anio        : {len(outputs['anio']):,} filas")
    print(f"  hhi_por_nivel       : {len(outputs['nivel']):,} filas")
    print(f"  HHI_CRUCE_SECOP_DANE: {len(outputs['master']):,} filas")

    print("Generando figuras...")
    figures = [
        _save_tendencia(outputs["anio"]),
        _save_por_nivel(outputs["nivel"]),
        _save_distribucion(outputs["master"]),
    ]
    for fig in figures:
        print(f"  OK {fig.relative_to(ROOT)}")

    print("Generando reporte HTML...")
    report = OUT_DIR / "hhi_report.html"
    report.write_text(_build_html(outputs, figures), encoding="utf-8")
    print(f"  OK {report.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
