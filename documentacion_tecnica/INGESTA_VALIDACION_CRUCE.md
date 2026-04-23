# Ingesta, Validación y Cruce de Datos — Guía Completa

Documento maestro que explica las tres fases críticas del pipeline ETL: ingesta cruda (Bronze), validación y limpieza (Silver), y cruce dimensional (Gold).

---

## 📁 Estructura de Carpetas y Responsabilidades

### `src/ingesta/`
**Extracción de datos crudos desde fuentes externas (APIs, CSVs).**

```
src/ingesta/
├── run_bronze.py              # Orquestador principal de ingesta
├── bronze/                    # Módulo de carga a Parquet
│   ├── __init__.py
│   ├── ingesta_cnpv.py        # CNPV 2018 (multiarchivo por departamento)
│   ├── ingesta_secop_i.py     # SECOP I (contratos históricos)
│   ├── ingesta_secop_ii.py    # SECOP II (contratos actuales, ~9.6GB)
│   ├── ingesta_emicron.py     # EMICRON (encuesta micronegocios)
│   └── ingesta_proyecciones.py # DANE proyecciones poblacionales
└── extract/                   # Extracción de APIs
    └── sodapy_connector.py    # Conexión a datos.gov.co (Socrata)
```

**Qué ocurre aquí:**
- Conecta a APIs (Socrata/datos.gov.co) o lee CSVs locales
- Convierte a formato Parquet para optimizar lectura posterior
- **Sin validación ni limpieza** — solo persistencia fiel
- Maneja múltiples estructuras (ej. CNPV 2018 distribuido en 33 carpetas)
- Guarda en `datos/bronze/<fuente>/`

**Salidas:**
```
datos/bronze/
├── cnpv/
│   ├── cnpv_2018_antioquia.parquet
│   ├── cnpv_2018_valle.parquet
│   └── ... (33 departamentos)
├── secop_i/
│   └── secop_i_raw.parquet
├── secop_ii/
│   └── secop_ii_sample_raw.parquet  (nota: sample, no full 9.6GB)
├── emicron/
│   └── emicron_raw.parquet
└── proyecciones/
    └── proyecciones_raw.parquet
```

---

### `src/transformacion/`
**Limpieza, validación y agregación a granularidad Municipio-Año.**

```
src/transformacion/
├── run_silver.py              # Orquestador de limpieza
├── run_gold.py                # Orquestador de modelo dimensional
├── silver/
│   ├── cleaners/
│   │   ├── clean_secop_i.py       # Normalizar columnas, parsear moneda, DIVIPOLA
│   │   ├── clean_secop_ii.py      # ⚠️ FIX: regex para moneda colombiana
│   │   ├── clean_cnpv.py          # Agregación CNPV a municipio
│   │   ├── clean_emicron.py       # Expansión con factores fex_c
│   │   └── clean_proyecciones.py  # Agregación DANE a municipio-año
│   └── validadores/
│       └── schema_validation.py   # Pandera contracts
└── gold/
    ├── build_dimensions.py        # dim_territorio, dim_tiempo
    ├── build_facts.py             # fact_contratacion, fact_censo, etc.
    └── build_mart.py              # ⚠️ FIX: joins con granularidad correcta
```

**Qué ocurre aquí:**
- **Silver:** Normaliza columnas reales (con espacios/tildes), parsea formatos especiales (moneda, fechas), mapea DIVIPOLA, agrega a municipio-año
- **Gold:** Construye dimensiones y tablas de hechos, genera el OBT final (One Big Table)

**Salidas:**
```
datos/plata/                    # Silver
├── secop_i/
│   ├── silver_secop_i_agregado.parquet          # municipio-año
│   └── silver_secop_i_transaccional.parquet     # contrato-nivel
├── secop_ii/
│   ├── silver_secop_ii_agregado.parquet
│   └── silver_secop_ii_transaccional.parquet
├── cnpv/
│   └── silver_cnpv_agregado.parquet             # municipio (2018)
├── emicron/
│   └── silver_emicron_agregado.parquet          # depto-año
└── proyecciones/
    └── silver_proyecciones_agregado.parquet     # depto-año

datos/oro/                      # Gold
├── dim_territorio.parquet       # 299 municipios (con DIVIPOLA)
├── dim_tiempo.parquet           # 12 años (2018-2029)
├── fact_contratacion_municipio_anio.parquet       # SECOP I+II unido
├── fact_censo_municipio.parquet                   # CNPV 2018
├── fact_demografia_municipio_anio.parquet         # DANE proyecciones
├── fact_micronegocios_municipio_anio.parquet      # EMICRON expandido
└── marts/
    ├── latest/
    │   └── mart_desarrollo_social_economico_municipio_anio.parquet  # OBT final
    └── version_20260423/
        └── mart_desarrollo_social_economico_municipio_anio.parquet  # versionado
```

---

## 🔍 Validación en Cada Capa

### Bronze Validation
**Archivo:** `documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`

Validaciones automáticas al cargar:
- ✅ Verificación de esquemas (columnas esperadas)
- ✅ Integridad de archivos Parquet
- ✅ Conteo de registros
- ⚠️ Sin limpieza — se persiste fielmente

### Silver Validation
**Archivo:** `documentacion_tecnica/DATA_CONTRACTS.md`

Validaciones en limpieza:
- ✅ Normalización de DIVIPOLA: `astype(str).str.zfill(5)` (debe ser 5 dígitos)
- ✅ Rango de años: 2018-2029 para análisis; 2018-2050 en raw para DANE
- ✅ Ausencia de negativos en montos y población
- ✅ Deduplicación en municipio-año (clave primaria)
- ✅ Nulos en PKs (divipola_key, anio_key): deben ser 0

### Gold Validation
**Archivo:** `documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`

Validaciones en modelo dimensional:
- ✅ Integridad referencial: todas las FK apuntan a dimensiones existentes
- ✅ No hay duplicados en PKs (divipola_key, anio_key)
- ✅ Cobertura poblacional: 100% en `poblacion_total_proyectada`
- ✅ Indicadores derivados: per-cápita sin NaN (excepto donde no hay inversión)
- ✅ Deduplicación SECOP I+II: COUNT(DISTINCT nit) sobre UNION, no SUM

---

## 🐛 Bugs Encontrados y Solucionados

### Bug 1: SECOP II — Valores monetarios 99.6% cero

**Ubicación:** `src/transformacion/silver/cleaners/clean_secop_ii.py` (líneas 47-52)

**Síntoma:**
```
inversion_total_monto: Positivos: 82 | Zeros: 14,656 (99.6%)  ❌
Max value: 999,018 COP (ridículamente bajo)
```

**Causa raíz:**
```python
# CÓDIGO ORIGINAL (FALLIDO)
_MONEDA_RE = re.compile(r"[^\d\-\.]")  # ❌ Mantiene el PUNTO

def _parse_valor(s: pd.Series) -> pd.Series:
    s2 = s.astype(str).str.replace(",", ".", regex=False)
    s2 = s2.str.replace(_MONEDA_RE, "", regex=True)  # Elimina TODO excepto dígito, signo, PUNTO
    s2 = s2.replace("", None)
    return pd.to_numeric(s2, errors="coerce").fillna(0.0)
```

Problema: En formato colombiano `$23.300.213`, el punto es separador de miles, no decimal:
- Input: `$23.300.213`
- Después de reemplazos: `23.300.213` (múltiples puntos)
- `pd.to_numeric("23.300.213")` → `NaN` (no puede parsear múltiples decimales)
- `fillna(0.0)` → `0`

**Solución aplicada:**
```python
# CÓDIGO CORREGIDO
_MONEDA_RE = re.compile(r"[^\d\-]")  # ✅ Sin punto en keep-set

def _parse_valor(s: pd.Series) -> pd.Series:
    """$1.234.567 -> 1234567 (elimina TODO lo no dígito; formato colombiano con punto como miles)."""
    s2 = s.astype(str).str.replace(_MONEDA_RE, "", regex=True).replace("", None)
    return pd.to_numeric(s2, errors="coerce").fillna(0.0)
```

- Input: `$23.300.213`
- Después de reemplazos: `23300213` (solo dígitos)
- `pd.to_numeric("23300213")` → `23300213` ✅
- Resultado: 14,656 → 82 ceros (0.6%), max = 54,853,329,383 COP ✅

**Verificación:**
```python
# Antes
datos/plata/secop_ii/silver_secop_ii_transaccional.parquet
Ceros: 14,683 / 14,738 (99.6%)
Max: 999,018

# Después
datos/plata/secop_ii/silver_secop_ii_transaccional.parquet
Ceros: 82 / 14,738 (0.6%)
Max: 54,853,329,383
```

---

### Bug 2: Mart — Años espurios 2030-2050

**Ubicación:** `src/transformacion/gold/build_mart.py` (líneas 92-124)

**Síntoma:**
```
Mart contenía 6,825 filas (años 2018-2050)
Debería tener ~3,129 filas (años 2018-2029)
33 años en lugar de 12
```

**Causa raíz:**
```python
# CÓDIGO ORIGINAL (FALLIDO)
pares = []
for df_ in (f_cnt, f_mic, f_dem):
    if not df_.empty and "divipola_key" in df_.columns and "anio_key" in df_.columns:
        sub = df_[["divipola_key", "anio_key"]].dropna().copy()
        pares.append(sub)

if pares:
    spine = pd.concat(pares, ignore_index=True).drop_duplicates()  # ❌ Incluye 2030-2050
```

Problema: `fact_demografia` contiene proyecciones DANE hasta 2050, pero el OBT analítico solo debe cubrir 2018-2029 (definido en `dim_tiempo`).

**Solución aplicada:**
```python
# CÓDIGO CORREGIDO
anios_validos = set(dim_tiempo["anio_key"].dropna().astype(int).tolist())  # [2018...2029]

pares = []
for df_ in (f_cnt, f_mic, f_dem):
    if not df_.empty and "divipola_key" in df_.columns and "anio_key" in df_.columns:
        sub = df_[["divipola_key", "anio_key"]].dropna().copy()
        sub["anio_key"] = pd.to_numeric(sub["anio_key"], errors="coerce").astype("Int64")
        sub = sub[sub["anio_key"].isin(anios_validos)]  # ✅ Filtrar a años válidos
        pares.append(sub)
```

**Verificación:**
```
Antes:  6,825 filas, años 2018-2050
Después: 3,129 filas, años 2018-2029 ✅
```

---

### Bug 3: Mart — Per-cápita siempre NaN (Granularidad Municipal vs Departamental)

**Ubicación:** `src/transformacion/gold/build_mart.py` (líneas 139-148)

**Síntoma:**
```
poblacion_total_proyectada: 396 / 3,129 rows populated (12.6%)
indicador_inversion_per_capita: 0 / 3,129 (100% NaN)  ❌
```

**Causa raíz — Mismatch de granularidad:**

| Fuente | Granularidad | Clave DIVIPOLA |
|--------|-------------|----------------|
| `fact_contratacion` | Municipal | `05001` (Medellín), `08001` (Cali) |
| `fact_demografia` | **Departamental** | `05000` (Antioquia), `08000` (Valle) |

```python
# CÓDIGO ORIGINAL (FALLIDO)
df = df.merge(f_dem, on=["divipola_key", "anio_key"], how="left")  # ❌
```

Buscaba coincidencia en `divipola_key` exacto:
- Spine tiene `(05001, 2018)` — Medellín
- `f_dem` tiene `(05000, 2018)` — Antioquia completo
- **Zero intersection** → `poblacion_total_proyectada = NULL` para todas las filas

**Solución aplicada — Lookup Departamental:**
```python
# CÓDIGO CORREGIDO
df["_div_depto"] = df["divipola_key"].str[:2] + "000"  # 05001 → 05000

f_mic_join = f_mic.rename(columns={"divipola_key": "_div_depto"})
f_dem_join = f_dem.rename(columns={"divipola_key": "_div_depto"})

df = df.merge(f_mic_join, on=["_div_depto", "anio_key"], how="left")  # ✅
df = df.merge(f_dem_join, on=["_div_depto", "anio_key"], how="left")  # ✅

df = df.drop(columns=["_div_depto"])
```

Derivar código depto desde municipio y unir por ese:
- Spine: `(05001, 2018)` → derivar `_div_depto = 05000`
- `f_dem`: `_div_depto = 05000`, `anio_key = 2018`
- **Match en (05000, 2018)** ✅ → `poblacion_total_proyectada = 12,000,000`

**Verificación:**
```
Antes:  poblacion_total_proyectada: 396/3,129 (12.6%), per-cápita: 0/3,129 (0%)
Después: poblacion_total_proyectada: 3,129/3,129 (100%), per-cápita: 1,034/3,129 (33%)

Ejemplo Medellín 2018:
  inversion_total_monto = 102,048,303,872 COP
  poblacion_total_proyectada = 6,407,149 personas
  indicador_inversion_per_capita = 15,929 COP/persona ✅
```

---

## 📊 Estado Actual del Pipeline (Post-Fixes)

### Verificación Final de Gold

**Dimensiones:**
- `dim_territorio`: 299 municipios ✅
- `dim_tiempo`: 12 años (2018-2029) ✅

**Tablas de Hechos:**
- `fact_contratacion`: 1,035 filas municipio-año ✅ (SECOP I+II unido sin doble conteo)
- `fact_censo`: 143 filas municipio (CNPV 2018) ✅
- `fact_demografia`: 1,089 filas depto-año (DANE) ✅
- `fact_micronegocios`: 25 filas depto-año (EMICRON 2024) ✅

**OBT Final:**
- `mart_desarrollo_social_economico_municipio_anio.parquet`: 3,129 filas
- Cobertura: 295 territorios, años 2018-2029
- PKs nulas: 0 ✅
- PKs duplicadas: 0 ✅
- Per-cápita: 1,034/3,129 calculados (33% con inversión)

---

## 🚀 Cómo Ejecutar

### Ingesta (Bronze)
```bash
python src/ingesta/run_bronze.py
```
Lee CSVs/APIs, convierte a Parquet → `datos/bronze/`

### Limpieza (Silver)
```bash
python src/transformacion/run_silver.py
```
Normaliza, agrega municipio-año → `datos/plata/`

### Modelo Dimensional (Gold)
```bash
python src/transformacion/run_gold.py
```
Crea dimensiones y hechos, OBT → `datos/oro/`

### Pipeline Completo
```bash
python -m src.run_all  # si existe
```

---

## 📚 Documentación Relacionada

- **Arquitectura Completa:** `documentacion_tecnica/MEDALLION_ARCHITECTURE_GUIDE.md`
- **Validaciones Bronze:** `documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`
- **Contratos de Datos:** `documentacion_tecnica/DATA_CONTRACTS.md`
- **Deduplicación SECOP:** `documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`
- **Auditoría CNPV:** `documentacion_tecnica/CNPV_MASTER_DOCUMENTATION.md`
- **Reconciliación Final:** `documentacion_tecnica/RECONCILIACION_FINAL_FUENTES.md`

---

**Última actualización:** 2026-04-23  
**Estado:** ✅ Todos los bugs corregidos, pipeline funcional  
**Responsable:** Equipo de Datos — Johann Sebastian
