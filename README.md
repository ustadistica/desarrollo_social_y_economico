# Sinergia Socioeconómica - Plataforma Analítica (Medallion Architecture)

Este es el repositorio refactorizado para el análisis avanzado de Sinergia Socioeconómica, el Gasto Público (SECOP) y el ecosistema de Micronegocios (EMICRON). Todo el código obsoleto y propenso a sesgos estadísticos fue sustituido por un pipeline analítico validado bajo la **Arquitectura Medallion (Bronze/Silver/Gold)**.

## ¿Por qué esta arquitectura? (Propósito)
La ingesta manual o usar cuadernos con múltiples Joins de `pandas` provoca "Out-of-Memory" errors y fallas metodológicas críticas (como inflar NBI por no agrupar). Este repositorio ahora funciona como paquete de recolección unificado con `pyarrow` y `duckdb`:
1. **BRONZE:** Ingiere la data cruda DANE/SECOP sin tocarla, fraccionada eficientemente en Parquet. Añade rastreo de hash y timestamp.
2. **SILVER:** Unifica los vocabularios. Aquí ocurre toda la agrupación poblacional rigurosa, mapeos de `fex_c` reales y reducción estructural pre-calculando el cruce a granularidad estricta `Municipio - Año`.
3. **GOLD:** Enlaza matemáticamente la constelación. Se fabrican las Tablas de Dimensiones conformadas (Tiempo/Territorio) y se arroja un datamart (OBT) listo, que computa KPIs derivados (`inversion_per_capita`) vectorizadamente para visualización PowerBI.

## ¿Dónde están los outputs finales?
**No es necesario correr extractores ni ejecutar joins a mano**. Para analistas visuales, solo necesitan usar el resultado final consumible en:
📌 `datos/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet`

> *También puedes leer los reportes automáticos en la carpeta `/documentacion_tecnica/` para entender el modelo y diccionario de variables en cada fase.*

---

## 🚀 ¿Cómo usar o re-ejecutar el pipeline? (Setup y RUNBOOK)
Todo el sistema está estructurado como paquete estándar Python. Puedes encontrar instrucciones paso a paso detalladas en el archivo [RUNBOOK.md](./RUNBOOK.md).

### 1. Instalación Rápida
Abre tu consola en esta carpeta y ejecuta:
```bash
pip install -e .
```
*(Se usarán las dependencias del archivo `pyproject.toml` que garantizan DuckDB, PyArrow, etc.)*

### 2. Ejecutar el Pipeline Estandarizado (End-to-End)
Si tienes un entorno Mac/Linux o PowerShell puedes usar nuestro Makefile, o directamente Python:
```bash
python run_all.py
```
*También es posible ejecutar las capas inviduales si buscas actualizar solo una fase particular (`python run_bronze.py`, `python run_silver.py`).*
