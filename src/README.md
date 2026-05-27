# Módulo `src/` — Pipeline ETL de Datos Socioeconómicos

Núcleo de procesamiento del pipeline que implementa la arquitectura Medallion (Bronze → Silver → Gold).

---

## 📁 Estructura del Módulo

```
src/
├── ingesta/                         # Capa BRONZE: Extracción de datos crudos
│   ├── run_bronze.py                # Orquestador principal de ingesta
│   ├── bronze/                      # Módulo de carga a Parquet
│   │   ├── ingesta_cnpv.py          # CNPV 2018 (33 carpetas por depto)
│   │   ├── ingesta_secop_i.py       # SECOP I (histórico de contratos)
│   │   ├── ingesta_secop_ii.py      # SECOP II (contratos recientes, ~9.6GB)
│   │   ├── parser_csv_emicron.py    # EMICRON (encuesta micronegocios)
│   │   └── ingesta_proyecciones.py  # DANE (proyecciones poblacionales)
│   └── extract/                     # Conectores a APIs
│       └── sodapy_connector.py      # Socrata/datos.gov.co
│
├── transformacion/                  # Capas SILVER y GOLD: Limpieza, validación y modelo dimensional
│   ├── run_silver.py                # Orquestador de limpieza y agregación
│   ├── run_gold.py                  # Orquestador de modelo dimensional y OBT
│   │
│   ├── silver/                      # Capa PLATA: Limpieza y estandarización
│   │   ├── cleaners/                # Limpiadores específicos por fuente
│   │   │   ├── clean_secop_i.py     # Normaliza columnas, parsea moneda, DIVIPOLA
│   │   │   ├── clean_secop_ii.py    # ⚠️ FIX: regex para moneda colombiana
│   │   │   ├── clean_cnpv.py        # Agregación CNPV a municipio
│   │   │   ├── clean_emicron.py     # Expansión con factor_expansion validado
│   │   │   └── clean_proyecciones.py # Agregación DANE a municipio-año
│   │   └── validadores/             # Pandera schema contracts
│   │       └── schema_validation.py
│   │
│   └── gold/                        # Capa ORO: Modelo Dimensional y OBT
│       ├── build_dimensions.py      # dim_territorio (299 municipios)
│       │                            # dim_tiempo (2018-2029)
│       ├── build_facts.py           # fact_contratacion, fact_censo, fact_demografia, fact_micronegocios
│       └── build_mart.py            # ⚠️ FIX: joins con granularidad correcta
│                                    # One Big Table (OBT) final
│
├── modelo/                          # Modelado estadístico y ML
│   ├── descriptivo/                 # Análisis descriptivo y clustering
│   └── predictivo/                  # Modelos de predicción (si aplica)
│
├── visualizacion/                   # Gráficos y mapas reutilizables
│   ├── mapas/                       # Visualización geoespacial
│   └── graficos/                    # Gráficos de series de tiempo, barras, etc.
│
└── config/                          # Configuración global
    ├── settings.py                  # Path raíces, logging, variables de entorno
    └── logging_config.py            # Configuración de loggers
```

---

## 🔄 Flujo de Datos

```
CSV/APIs (datos originales)
    ↓
src/ingesta/bronze/ → BRONZE
    (Parquet crudo, sin transformación)
    ↓
data/bronze/<fuente>/
    ↓
src/transformacion/silver/ → SILVER
    (Limpieza, normalización, agregación municipio-año)
    ↓
data/silver/
    ↓
src/transformacion/gold/ → GOLD
    (Dimensiones, hechos, OBT analítico)
    ↓
data/gold/
  ├── dim_territorio.parquet
  ├── dim_tiempo.parquet
  ├── fact_*.parquet
  └── marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet
```

---

## 🚀 Ejecución

### Opción 1: Ejecutar por capas
```bash
# Ingesta: CSV/APIs → Parquet crudo
python src/ingesta/run_bronze.py

# Limpieza: Estandarización y agregación
python src/transformacion/run_silver.py

# Modelo Dimensional: Dimensiones, hechos, OBT
python src/transformacion/run_gold.py
```

### Opción 2: Pipeline completo (si está disponible)
```bash
python src/run_all.py  # Ejecuta Bronze → Silver → Gold
```

---

## 📊 Salidas Principales

| Capa | Ubicación | Descripción |
|------|-----------|-------------|
| **Bronze** | `data/bronze/<fuente>/` | Datos crudos en Parquet (sin transformación) |
| **Silver** | `data/silver/` | Agregados municipio-año por fuente |
| **Gold** | `data/gold/` | Dimensiones + Facts + OBT analítico |
| **OBT** | `data/gold/marts/latest/` | Tabla final lista para análisis |

---

## 🐛 Bugs Corregidos (Registro Técnico)

### 1. SECOP II: Valores monetarios 99.6% cero
- **Archivo:** `src/transformacion/silver/cleaners/clean_secop_ii.py`
- **Problema:** Regex `[^\d\-\.]` guardaba puntos; formato colombiano `$X.XXX.XXX` → `X.XXX.XXX` → NaN
- **Solución:** Cambiar a `[^\d\-]`, eliminar todos los no-dígitos
- **Resultado:** 99.6% → 0.6% ceros; max 999K → 54.8B COP ✅

### 2. Mart: Años espurios 2030-2050
- **Archivo:** `src/transformacion/gold/build_mart.py` (líneas 92-124)
- **Problema:** `fact_demografia` cubre 2018-2050; spine incluía años fuera del rango analítico
- **Solución:** Filtrar spine a `anios_validos` de `dim_tiempo` (2018-2029)
- **Resultado:** 6,825 filas → 3,129 filas ✅

### 3. Mart: Per-cápita siempre NaN (granularidad mismatch)
- **Archivo:** `src/transformacion/gold/build_mart.py` (líneas 139-148)
- **Problema:** `fact_demografía` (depto XX000) vs `fact_contratacion` (municipio XXXXX) → cero intersección en join
- **Solución:** Conservar indicadores departamentales en códigos `XX000` y no replicarlos en municipios
- **Resultado:** 0/3,129 per-cápita → 1,034/3,129 calculados ✅

---

## 📚 Documentación Relacionada

- **Ingesta, Validación, Cruce (Completa):** [`documentacion_tecnica/INGESTA_VALIDACION_CRUCE.md`](../documentacion_tecnica/INGESTA_VALIDACION_CRUCE.md)
- **Arquitectura Medallion:** [`documentacion_tecnica/MEDALLION_ARCHITECTURE_GUIDE.md`](../documentacion_tecnica/MEDALLION_ARCHITECTURE_GUIDE.md)
- **Validaciones Bronze:** [`documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`](../documentacion_tecnica/BRONZE_VALIDATION_REPORT.md)
- **Data Contracts:** [`documentacion_tecnica/DATA_CONTRACTS.md`](../documentacion_tecnica/DATA_CONTRACTS.md)
- **Deduplicación SECOP:** [`documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`](../documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md)

---

## 🔧 Configuración

Ver `src/config/settings.py` para:
- Rutas raíz (`PROJECT_ROOT`, `DATA_ROOT`, `BRONZE_PATH`, `SILVER_PATH`, `GOLD_PATH`)
- Niveles de log
- Variables de entorno (`.env`)

---

**Última actualización:** 2026-04-23  
**Estado:** ✅ Pipeline funcional, todos los bugs corregidos
