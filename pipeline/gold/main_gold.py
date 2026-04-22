"""
Orquestador Principal de la Capa Gold (Business Logic & Datamarts).

Genera el Modelo Estrella y los Cubos Analíticos.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Asegurar importación desde raíz de proyeto
current_dir = os.path.dirname(os.path.abspath(__file__))

from pipeline.config.settings import Settings
import pipeline.gold.schema.create_dimensions as dim_creator
import pipeline.gold.schema.create_facts as fact_creator

def main():
    parser = argparse.ArgumentParser(description="Ejecutar capa Gold (Modelo Estrella y Data Marts)")
    parser.add_argument("--schema", action="store_true", help="Crear dimensiones y hechos (Modelo Estrella)")
    parser.add_argument("--marts", action="store_true", help="Crear Data Marts a partir del Schema")
    parser.add_argument("--all", action="store_true", help="Ejecutar toda la capa Gold")
    
    args = parser.parse_args()
    
    # Si no especifica nada, por defecto hace todo o muestra ayuda
    if not (args.schema or args.marts or args.all):
        parser.print_help()
        return

    settings = Settings()
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format=settings.LOG_FORMAT,
        handlers=[logging.StreamHandler()]
    )
    logger = logging.getLogger("gold_orchestrator")

    logger.info("=" * 60)
    logger.info("INICIANDO INGESTA CAPA GOLD: MODELO ESTRELLA & DATA MARTS")
    logger.info("=" * 60)

    try:
        # Fase 1: Creación del Modelo Estrella
        if args.schema or args.all:
            logger.info("Fase 1: Creando Dimensiones...")
            # NOTA: En la realidad se iteran las funciones pasándoles DataFrames cargados desde Silver
            # dim_creator.create_dim_municipio(...)
            
            logger.info("Fase 1: Creando de Tablas de Hechos...")
            # fact_creator.create_fact_contratacion(...)

        # Fase 2: Creación de Datamarts
        if args.marts or args.all:
            logger.info("Fase 2: Construyendo Data Marts (Social, Económico, Cúbicos)...")
            # import gold.marts.create_datamart_economico as mart_eco
            # mart_eco.build(...)
            
        logger.info("=" * 60)
        logger.info("TRANSFORMACIÓN GOLD FINALIZADA CON ÉXITO")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Falla fatal en construcción Capa Gold: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
