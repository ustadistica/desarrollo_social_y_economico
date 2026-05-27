"""
CLI formal del pipeline socioeco_pipeline.

Entrypoints definidos en pyproject.toml [project.scripts]:
  socioeco-bronze   → src.cli:cmd_bronze
  socioeco-silver   → src.cli:cmd_silver
  socioeco-gold     → src.cli:cmd_gold
  socioeco-pipeline → src.cli:cmd_all

Uso directo:
  python -m src.cli bronze
  python -m src.cli silver
  python -m src.cli gold
  python -m src.cli all
"""

import sys
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("socioeco_pipeline")


def _setup_settings():
    """Carga la configuración centralizada."""
    from src.config.settings import get_settings
    return get_settings()


def _run_bronze(sources=None):
    """Ejecuta la capa Bronze (ingesta cruda a Parquet)."""
    logger.info("=" * 60)
    logger.info("CAPA BRONZE — Ingesta")
    logger.info("=" * 60)

    from src.config.settings import get_settings
    from src.ingesta.bronze.main_ingestion import IngestionOrchestrator
    from src.ingesta.bronze.validators.bronze_validator import generate_validation_report
    from pathlib import Path

    settings = get_settings()
    orchestrator = IngestionOrchestrator(bronze_path=settings.BRONZE_PATH)
    resultados = orchestrator.run_ingestion(sources=sources, force=True, validate=True)

    logger.info(f"Total: {resultados['summary']['total']} | "
                f"OK: {resultados['summary']['success']} | "
                f"Fallos: {resultados['summary']['failed']}")

    # Generar reporte de validación
    base_dir = Path(__file__).resolve().parent.parent
    report_path = base_dir / "documentacion_tecnica" / "BRONZE_VALIDATION_REPORT.md"
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORTE DE VALIDACIÓN - CAPA BRONZE (AUTO-GENERADO)\n\n")
        val_count = 0
        for name, source_res in resultados["sources"].items():
            val_data = source_res.get("validation")
            if val_data:
                val_count += 1
                reporte_str = generate_validation_report(val_data)
                f.write(f"## {name.upper()}\n```text\n{reporte_str}\n```\n\n")
        if val_count == 0:
            f.write("*(No se encontraron datos validados)*\n")

    logger.info(f"Reporte: {report_path.relative_to(base_dir)}")
    return resultados


def _run_silver(sources=None):
    """Ejecuta la capa Silver (limpieza, estandarización, agregación)."""
    logger.info("=" * 60)
    logger.info("CAPA SILVER — Limpieza y Homologación")
    logger.info("=" * 60)

    from src.config.settings import get_settings
    from src.transformacion.silver.cleaners.clean_cnpv import clean_cnpv_data
    from src.transformacion.silver.cleaners.clean_emicron import clean_emicron_data
    from src.transformacion.silver.cleaners.clean_secop_i import clean_secop_i_data
    from src.transformacion.silver.cleaners.clean_secop_ii import clean_secop_ii_data
    from src.transformacion.silver.cleaners.clean_proyecciones import clean_proyecciones_data
    from pathlib import Path

    settings = get_settings()
    bronze_base = settings.BRONZE_PATH
    silver_base = settings.SILVER_PATH
    silver_base.mkdir(parents=True, exist_ok=True)

    # Cada cleaner escribe en rutas canonicas dentro de data/silver:
    # silver_<fuente>_agregado.parquet y, cuando aplica, transaccionales.
    def _run(name, cleaner_fn):
        src_bronze = bronze_base / name
        try:
            return cleaner_fn(src_bronze, silver_base, settings)
        except Exception as e:
            logger.error(f"  {name}: FALLO -- {e}")
            return {"status": "failed", "error": str(e)}

    results = {}
    cleaners = [
        ("cnpv", clean_cnpv_data),
        ("emicron", clean_emicron_data),
        ("secop_i", clean_secop_i_data),
        ("secop_ii", clean_secop_ii_data),
        ("proyecciones", clean_proyecciones_data),
    ]

    for name, fn in cleaners:
        results[name] = _run(name, fn)
        logger.info(f"  {name}: {results[name].get('status', 'unknown')}")

    # Generar reporte
    base_dir = Path(__file__).resolve().parent.parent
    report_path = base_dir / "documentacion_tecnica" / "SILVER_DATA_QUALITY_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORTE DE CALIDAD — CAPA SILVER\n\n")
        for name, outcome in results.items():
            f.write(f"## {name.upper()}\n**Estado:** {outcome.get('status', 'failed').upper()}\n\n")
            if outcome.get("status") == "success":
                f.write(f"- Registros: {outcome.get('registros', 0):,}\n")
                if outcome.get("duplicados") is not None:
                    f.write(f"- Duplicados llave territorial-anual: {outcome.get('duplicados'):,}\n")
                nulls = outcome.get("nulls") or {}
                if nulls:
                    nulls_text = ", ".join(f"{col}={value:,}" for col, value in nulls.items())
                    f.write(f"- Nulos de llaves críticas: {nulls_text}\n")
                fallback_events = outcome.get("factores_fallback") or []
                if fallback_events:
                    f.write("- Factores fallback EMICRON aplicados:\n")
                    for event in fallback_events:
                        source_name = Path(str(event.get("source", ""))).name
                        f.write(
                            "  - "
                            f"anio={event.get('anio')}, "
                            f"columna={event.get('factor_col')}, "
                            f"fuente={source_name}, "
                            f"filas={event.get('filas', 0):,}, "
                            f"suma_factor={event.get('suma_factor', 0):,.2f}\n"
                        )
                if outcome.get("reglas_aplicadas"):
                    f.write(f"- Reglas aplicadas: {outcome['reglas_aplicadas']}\n")
            else:
                f.write(f"❌ {outcome.get('error', 'Error desconocido')}\n")
            f.write("\n---\n")

    logger.info(f"Reporte: {report_path.relative_to(base_dir)}")
    return results


def _run_gold():
    """Ejecuta la capa Gold (modelo estrella, datamarts)."""
    logger.info("=" * 60)
    logger.info("CAPA GOLD — Modelo Estrella")
    logger.info("=" * 60)

    from src.config.settings import get_settings
    from src.transformacion.gold.build_dimensions import build_dim_tiempo, build_dim_territorio
    from src.transformacion.gold.build_facts import build_facts
    from src.transformacion.gold.build_mart import build_datamart
    from pathlib import Path

    settings = get_settings()
    silver_base = settings.SILVER_PATH
    gold_base = settings.GOLD_PATH
    gold_base.mkdir(parents=True, exist_ok=True)

    dims = {}
    dims["dim_tiempo"] = build_dim_tiempo(gold_base)
    dims["dim_territorio"] = build_dim_territorio(silver_base, gold_base)

    facts = build_facts(silver_base, gold_base)
    mart = build_datamart(gold_base)

    # Generar reporte
    base_dir = Path(__file__).resolve().parent.parent
    report_path = base_dir / "documentacion_tecnica" / "GOLD_VALIDATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# REPORTE DE VALIDACIÓN — CAPA GOLD\n\n")
        f.write("## Dimensiones\n")
        for k, res in dims.items():
            f.write(f"- **{k.upper()}**: `{res.get('status', 'ERROR')}` | {res.get('registros', 0):,} registros\n")
        f.write("\n## Hechos\n")
        for k, res in facts.items():
            f.write(f"- **{k.upper()}**: `{res.get('status', 'ERROR')}` | {res.get('registros', 0):,} registros\n")
        f.write("\n## Datamart\n")
        f.write(f"- Estado: `{mart.get('status', 'ERROR')}` | {mart.get('registros', 0):,} filas\n")
        if "archivo_latest" in mart:
            f.write(f"- Ruta: `{mart['archivo_latest']}`\n")

    logger.info(f"Reporte: {report_path.relative_to(base_dir)}")
    return {"dims": dims, "facts": facts, "mart": mart}


# ─── Entrypoints para pyproject.toml [project.scripts] ─────────────────

def cmd_bronze():
    """Entrypoint: socioeco-bronze"""
    parser = argparse.ArgumentParser(description="Ejecutar capa Bronze")
    parser.add_argument("sources", nargs="*", help="Fuentes específicas (opcional)")
    args = parser.parse_args()
    _run_bronze(sources=args.sources or None)


def cmd_silver():
    """Entrypoint: socioeco-silver"""
    _run_silver()


def cmd_gold():
    """Entrypoint: socioeco-gold"""
    _run_gold()


def cmd_all():
    """Entrypoint: socioeco-pipeline (end-to-end)"""
    parser = argparse.ArgumentParser(description="Ejecutar pipeline completo (Bronze > Silver > Gold)")
    parser.add_argument("sources", nargs="*", help="Fuentes para Bronze (opcional)")
    args = parser.parse_args()

    logger.info("==========================================================")
    logger.info("       PIPELINE END-TO-END  (Medallion Architecture)       ")
    logger.info("==========================================================")

    _run_bronze(sources=args.sources or None)
    _run_silver()
    _run_gold()

    logger.info("[OK] PIPELINE COMPLETADO. Data lista en data/gold/marts/latest/")


# ─── Soporte para `python -m src.cli` ──────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="socioeco_pipeline -- CLI del Pipeline Medallion",
        usage="python -m src.cli {bronze,silver,gold,all} [opciones]",
    )
    parser.add_argument(
        "layer",
        choices=["bronze", "silver", "gold", "all"],
        help="Capa a ejecutar",
    )
    parser.add_argument("extra", nargs="*", help="Argumentos adicionales")

    args = parser.parse_args()

    if args.layer == "bronze":
        _run_bronze(sources=args.extra or None)
    elif args.layer == "silver":
        _run_silver()
    elif args.layer == "gold":
        _run_gold()
    elif args.layer == "all":
        _run_bronze(sources=args.extra or None)
        _run_silver()
        _run_gold()
        logger.info("✅ PIPELINE COMPLETADO.")


if __name__ == "__main__":
    main()
