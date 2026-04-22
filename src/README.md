# Documentación del Pipeline ETL/ELT: Sinergia Socioeconómica

Este documento es la guía maestra para la ejecución, configuración y diseño técnico del pipeline de datos.

---

## 1. Estructura del Módulo `pipeline/`

```text
pipeline/
├── bronze/                     # Capa BRONCE (Ingesta cruda)
│   ├── main_ingestion.py       # Orquestador de ingesta
│   ├── parsers/                # Parser por fuente (CNPV, SECOP, EMICRON, etc.)
│   └── validators/             # Validación de esquemas Bronze
├── silver/                     # Capa PLATA (Limpieza y Agregación)
│   ├── main_transformation.py  # Orquestador de limpieza
│   └── cleaners/               # Limpiadores específicos
├── gold/                       # Capa ORO (Modelo Dimensional)
│   ├── build_dimensions.py     # Construcción de dim_territorio, dim_tiempo
│   ├── build_facts.py          # Construcción de fact_contratacion, fact_censo, etc.
│   └── build_mart.py           # Generación del OBT final
├── config/                     # Configuración (settings.py, .env)
├── utils/                      # Utilidades de sistema, loggers y Spark/Arrow
└── cli.py                      # Interfaz de Línea de Comandos (CLI)
```

---

## 2. Guía de Inicio Rápido (Runbook)

### 2.1 Requisitos Previos
1. **Instalación:** `pip install -e .` (desde la raíz).
2. **Configuración de Datos:** Coloque sus archivos en `../Datos/` o configure el archivo `.env`.

### 2.2 Comandos de Ejecución (CLI)
El sistema expone entrypoints oficiales para facilitar la ejecución:

```bash
# Ejecutar todo el flujo (Bronze -> Silver -> Gold)
socioeco-pipeline

# Ejecutar capas específicas
socioeco-bronze
socioeco-silver
socioeco-gold
```

O mediante el módulo de Python: `python -m pipeline all`.

---

## 3. Diseño Técnico y Estrategia

### 3.1 Capas Medallion
- **Bronze:** Ingesta fiel de CSVs a Parquet. Maneja múltiples separadores y estructuras multicarpeta (especialmente para CNPV).
- **Silver:** Limpieza de texto, estandarización de DIVIPOLA y agregación al grano **Municipio-Año**.
- **Gold:** Modelo Estrella que une las fuentes mediante dimensiones conformadas (`dim_territorio` y `dim_tiempo`).

### 3.2 Estrategia por Fuente
- **SECOP I/II:** Agregación de montos adjudicados por municipio ejecutor.
- **CNPV 2018:** Censo universal de población (44M+ registros) reducido a totales municipales.
- **EMICRON:** Encuesta de micronegocios expandida mediante factores de expansión (`fex_c`).

---

## 4. Configuración del Entorno (.env)

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `DATA_PATH` | Ruta raíz de datos | `../Datos/` |
| `CNPV_ROOT_DIR` | Directorio del Censo | `../Datos/CENSO 2018 dep` |
| `LOG_LEVEL` | Nivel de log | `INFO` |

---

## 5. Salidas Reales del Pipeline

- **Bronze:** `datos/bronze/`
- **Silver:** `datos/plata/`
- **Gold:** `datos/oro/`
- **OBT Final:** `datos/oro/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet`

> **Nota:** La arquitectura está diseñada para ser agnóstica al volumen, utilizando DuckDB para procesar gigabytes de datos sin desbordar la memoria RAM.
