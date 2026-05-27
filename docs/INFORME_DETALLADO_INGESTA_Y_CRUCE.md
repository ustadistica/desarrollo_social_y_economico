# INFORME TÉCNICO EXHAUSTIVO — INGESTA Y CRUCE DE DATOS
## Observatorio de Desarrollo Socioeconómico
**Fecha:** 2026-05-19 | **Propósito:** Transferencia de conocimiento completa
**Rama activa:** `feature/migracion-duckdb-a-pyspark`
**Última ejecución del datamart:** `data/gold/marts/version_20260507/`

---

## 1. CONTEXTO DEL PROYECTO

El proyecto construye un **Observatorio de Desarrollo Socioeconómico** que cruza datos de contratación pública (SECOP I y II) con indicadores sociales del DANE (censo, pobreza, micronegocios) para analizar desigualdades territoriales en Colombia. El período analítico es 2018–2024, con granularidad a nivel de municipio (código DIVIPOLA de 5 dígitos).

---

## 2. ARQUITECTURA: MEDALLION (BRONZE → SILVER → GOLD)

Se eligió la **Medallion Architecture** (también llamada Multi-Hop) por las siguientes razones:

| Capa | Propósito | Formato | Ubicación |
|------|-----------|---------|-----------|
| **Bronze** | Datos crudos, sin transformar. Copia fiel del CSV original | Parquet (Snappy) | `data/bronze/` |
| **Silver** | Datos limpios, tipados, estandarizados geográficamente, agregados a grano Municipio-Año | Parquet | `data/silver/` |
| **Gold** | Modelo Estrella (dimensiones + hechos) + Datamart analítico (OBT) | Parquet | `data/gold/` |

### ¿Por qué Medallion y no otra arquitectura?
1. **Trazabilidad**: Si un indicador parece incorrecto, se puede rastrear hasta el dato crudo en Bronze.
2. **Idempotencia**: Cada capa se puede regenerar desde la anterior sin efectos colaterales.
3. **Separación de responsabilidades**: Los parsers de Bronze no limpian datos; los cleaners de Silver no modelan dimensiones.
4. **Reproducibilidad**: Cualquier miembro del equipo puede regenerar todo el pipeline con `python -m src.cli all`.

### ¿Por qué Parquet y no CSV/SQLite/PostgreSQL?
- **Compresión columnar**: Los CSV de SECOP pesan ~10 GB; en Parquet con Snappy ocupan ~1-2 GB.
- **Tipos preservados**: CSV pierde información de tipos; Parquet preserva `int32`, `float64`, `string`, etc.
- **Lectura parcial**: Se pueden leer solo las columnas necesarias sin cargar todo el archivo.
- **Sin servidor**: No requiere instalar PostgreSQL ni configurar conexiones.

---

## 3. STACK TECNOLÓGICO FINAL

| Componente | Tecnología | Justificación |
|------------|-----------|---------------|
| Lectura CSV masiva | `pandas.read_csv` con chunks | Maneja archivos de 10 GB en máquinas con 8 GB RAM |
| Escritura Parquet | `pyarrow.parquet.ParquetWriter` | Escritura streaming chunk-a-chunk sin acumular en RAM |
| Estandarización geográfica | Catálogo DIVIPOLA embebido | Sin dependencia de API externa para mapear municipios |
| Detección de encoding | `chardet` | EMICRON viene en latin-1, SECOP en UTF-8; detección automática |
| Orquestación | Python puro (clases Orchestrator) | Sin dependencia de Airflow/Prefect para un proyecto académico |
| Modelo Estrella / Silver / Gold | pandas + PyArrow | Suficiente para ~2M filas; sin JVM requerido |
| Motor analítico opcional | PySpark con auto-fallback a PyArrow | Probado en la rama `feature/migracion-duckdb-a-pyspark` (ver §3.1) |

> **Nota importante**: Toda la ingesta se realiza exclusivamente desde **archivos CSV locales** descargados manualmente. No se utiliza ninguna API en el pipeline.

### 3.1 Motor analítico dual (PySpark ↔ PyArrow)

A partir de la rama `feature/migracion-duckdb-a-pyspark` se reintrodujo PySpark como motor analítico **opcional** mediante el módulo `src/utils/spark_session.py`. La estrategia es:

1. Al primer uso, el módulo intenta crear una `SparkSession` real (master `local[*]`, 4 GB driver/executor) y ejecuta un cálculo mínimo de prueba.
2. Si la prueba pasa, queda `_engine = "pyspark"` y todas las funciones públicas (`query_parquet`, `write_parquet`) usan Spark.
3. Si la prueba falla (Java ausente, Python 3.12 + Windows, etc.), cae automáticamente a `_engine = "pyarrow"` usando `pyarrow.dataset` + pandas. La API externa no cambia.

> **Nota histórica**: El pipeline arrancó con PySpark, se simplificó a pandas + DuckDB, después se purgó DuckDB para quedarse solo con pandas + PyArrow, y ahora se está evaluando la reintroducción de PySpark como motor escalable opcional sin perder la portabilidad ofrecida por PyArrow. Las capas Bronze, Silver y Gold actuales siguen funcionando 100 % con pandas + PyArrow; PySpark es aditivo.

---

## 4. FUENTES DE DATOS

### 4.1 SECOP I — Procesos de Compra Pública
- **Origen**: [datos.gov.co](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-I-Procesos-de-Compra-P-blica/f789-7hwg)
- **Método de obtención**: Descarga manual del CSV completo (~10 GB)
- **Período**: 2018–2024
- **Campos clave**: `UID`, `Anno Firma Contrato`, `NIT de la Entidad`, `Cuantia Contrato`, `Municipio de Obtencion`, `Modalidad de Contratacion`, `Nombre Grupo`, `Nombre Familia`
- **Particularidad crítica**: NO contiene código DIVIPOLA directamente. El campo `Municipio de Obtencion` es texto libre (nombre del municipio). El mapeo a DIVIPOLA se hace en Silver por fuzzy matching contra el catálogo DIVIPOLA.

### 4.2 SECOP II — Contratos Electrónicos
- **Origen**: [datos.gov.co](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h) — Descarga masiva CSV
- **Método de obtención**: Descarga manual del CSV completo (~9.6 GB) desde datos.gov.co
- **Período**: 2018–2024
- **Campos clave**: `id_contrato`, `fecha_publicacion`, `monto_contrato`, `divipola_municipio`, `codigo_unspsc`, `nit_proveedor`, `modalidad_seleccion`
- **Ventaja sobre SECOP I**: YA contiene `divipola_municipio` como código numérico, no requiere mapeo por nombre.

### 4.3 CNPV 2018 — Censo Nacional de Población y Vivienda
- **Origen**: Microdatos del DANE (descarga manual desde ANDA)
- **Estructura en disco**: Carpetas por departamento, cada una con CSVs por módulo (1VIV, 2HOG, 3FALL, 5PER, MGN)
- **Separador**: Punto y coma (`;`) en la mayoría de archivos
- **Variables**: IPM, NBI, déficit habitacional, composición étnica, población
- **Restricción legal**: Datos anonimizados por secreto estadístico. NO se puede cruzar NIT de proveedores SECOP con personas del censo. Solo se permiten agregaciones geográficas por DIVIPOLA.

### 4.4 EMICRON — Encuesta de Micronegocios
- **Origen**: DANE — Encuesta muestral
- **Período**: 2019–2024 (6 años, ~11-14 módulos por año)
- **Estructura**: Carpeta `EMICRON YYYY/` con subcarpetas por módulo (TIC, ventas, identificación, etc.)
- **Encodings mixtos**: Algunos archivos en UTF-8, otros en latin-1/cp1252
- **Granularidad**: DEPARTAMENTAL (no municipal). Se usa código `XX000` para representar el agregado departamental.

### 4.5 Proyecciones Censales DANE
- **Origen**: DANE — Proyecciones de población 2018–2050
- **Método de obtención**: Descarga manual del CSV
- **Formato**: CSV con separador punto y coma
- **Granularidad**: Área y Departamento

### 4.6 Otros (CENU, TerriData, Geoportal)
Definidos en `data_sources.yaml` como catálogo declarativo de referencia. Estos datasets fueron evaluados durante la fase de diseño pero **toda la ingesta se realiza exclusivamente desde archivos CSV descargados manualmente**.

---

## 5. CAPA BRONZE — INGESTA DETALLADA

### 5.1 Punto de entrada
```
python src/ingesta/run_bronze.py [fuente1 fuente2 ...]
# o bien:
python -m src.cli bronze
```

### 5.2 Orquestador: `IngestionOrchestrator`
**Archivo**: `src/ingesta/bronze/main_ingestion.py`

El orquestador mantiene un diccionario `SOURCES_CONFIG` con 5 fuentes:

```python
SOURCES_CONFIG = {
    "cnpv":          { "parser": parse_cnpv_csv },
    "secop_i":       { "parser": parse_secop_i_csv },
    "secop_ii":      { "parser": parse_secop_csv },
    "emicron":       { "parser": parse_emicron_csv },
    "proyecciones":  { "parser": parse_proyecciones_csv },
}
```

Para cada fuente, el orquestador:
1. Verifica si existen datos previos (skip si ya hay `.parquet` y no se usa `--force`)
2. Ejecuta el parser correspondiente
3. Ejecuta validación post-ingesta (`bronze_validator.py`)
4. Genera reporte de validación en `documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`

### 5.3 Parser SECOP II (`parser_csv_secop.py`)

**Estrategia de lectura por chunks con PyArrow streaming**:

```python
for i, chunk in enumerate(pd.read_csv(
    input_path,
    chunksize=250_000,      # 250K filas por lote
    sep=",",
    dtype=str,              # TODO como string en Bronze
    keep_default_na=False,  # No interpretar "NA" como nulo
    low_memory=False,
    encoding="utf-8",
    on_bad_lines="warn",    # No abortar por líneas malformadas
)):
    chunk["_ingestion_timestamp"] = datetime.now().isoformat()
    chunk["_source"] = "secop_ii_csv"
    chunk["_checksum_md5"] = pd.util.hash_pandas_object(chunk).astype(str)
    
    table = pa.Table.from_pandas(chunk)
    if writer is None:
        writer = pq.ParquetWriter(parquet_file, table.schema, compression="snappy")
    writer.write_table(table)
```

**¿Por qué `dtype=str`?** En Bronze, todo se lee como string crudo. La tipificación se hace en Silver. Esto evita que pandas interprete montos como `float` y pierda precisión, o que interprete NITs como enteros y les quite ceros a la izquierda.

**¿Por qué `keep_default_na=False`?** Algunos campos legítimamente contienen la cadena "NA" (ej: estado del contrato). Sin este flag, pandas los convertiría a `NaN`.

**¿Por qué `on_bad_lines="warn"`?** Los CSV de SECOP ocasionalmente tienen líneas con comillas desbalanceadas. En lugar de abortar la ingesta completa, se salta la línea y se emite advertencia.

### 5.4 Parser SECOP I (`parser_csv_secop_i.py`)
Idéntico al de SECOP II en estructura. La diferencia está en la ruta de entrada (`SECOP_I_CSV_PATH`) y los metadatos de trazabilidad.

### 5.5 Parser CNPV (`parser_csv_cnpv.py`)

El CNPV tiene una estructura jerárquica: carpetas por departamento, archivos por módulo censal.

**Fase 1 — Descubrimiento (crawling)**:
```python
CNPV_MODULES = ["1VIV", "2HOG", "3FALL", "5PER", "MGN"]

for dpto_dir in input_path.iterdir():
    for file_path in dpto_dir.glob("*.[cC][sS][vV]"):
        for module in CNPV_MODULES:
            if module in file_path.name.upper():
                inventario[module].append(file_path)
```

**Fase 2 — Ingesta por módulo**: Cada módulo genera un Parquet independiente (`cnpv_1viv_raw.parquet`, `cnpv_2hog_raw.parquet`, etc.). Se detecta automáticamente si el separador es `;` o `,` leyendo la primera línea.

### 5.6 Parser EMICRON (`parser_csv_emicron.py`)

El más complejo de los parsers por la heterogeneidad de los datos:

1. **Descubrimiento multi-año**: Busca carpetas `EMICRON YYYY` en el directorio base
2. **Detección de encoding**: Usa `chardet` con muestra de 100KB por archivo
3. **Detección de separador**: Analiza las primeras 10 líneas para determinar `,`, `;`, `\t` o `|`
4. **Nombres seguros**: Convierte nombres de archivo con acentos/espacios a snake_case para el Parquet de salida

### 5.7 Metadatos de trazabilidad (Bronze)

Cada registro en Bronze incluye estas columnas de auditoría:
- `_ingestion_timestamp`: Momento exacto de la ingesta
- `_source`: Identificador de la fuente (`secop_ii_csv`, `dane_cnpv`, etc.)
- `_source_version`: Versión del dataset
- `_extraction_method`: Método usado (`CSV_LOCAL_PARSER`)
- `_checksum_md5`: Hash de integridad por fila o por lote

---

## 6. CONFIGURACIÓN Y RESOLUCIÓN DE RUTAS

### 6.1 Archivo `settings.py`

La configuración centralizada (`src/config/settings.py`) resuelve rutas de CSVs fuente con esta estrategia de búsqueda:

```python
candidate_paths = [
    PROJECT_ROOT / "Datos",           # Dentro del proyecto
    PROJECT_ROOT.parent / "Datos",    # Un nivel arriba
    PROJECT_ROOT.parent.parent / "Datos",  # Dos niveles (CONSULTORIA/Datos)
]
```

Para SECOP I y II, usa glob patterns para no depender del nombre exacto del archivo (que incluye fecha de descarga):
```python
SECOP_I_CSV_PATH = _resolve_glob_path(datos_folder, "SECOP_I_-_Procesos_de_Compra*.*csv")
SECOP_CSV_PATH = _resolve_glob_path(datos_folder, "SECOP_II_-_Contratos_Electr*.*csv")
```

### 6.2 Variables de entorno (`.env`)

Se pueden sobreescribir todas las rutas vía `.env`:
- `SECOP_CSV_PATH`, `SECOP_I_CSV_PATH`, `CNPV_ROOT_DIR`, `EMICRON_CSV_PATH`, `PROYECCIONES_CENSO_PATH`
- `NULL_THRESHOLD_WARNING` (0.5), `NULL_THRESHOLD_BLOCKING` (0.9)

### 6.3 Validador previo de configuración

Antes de correr Bronze por primera vez, se recomienda ejecutar el validador:

```bash
python -m src.validadores.verificar_datos
```

Este script (introducido el 2026-04-23 para resolver un problema recurrente de compañeros que clonaban el repo y la ingesta fallaba con *"No hay datos de SECOP II en Bronze"*) verifica que:
- Exista la carpeta `Datos/` en alguna de las tres ubicaciones candidatas (proyecto, padre, abuelo).
- Estén presentes los subdirectorios `CENSO 2018 dep/`, `EMICRON 2024/`.
- Existan los CSV de SECOP I, SECOP II y proyecciones (`PPED-AreaDep-2018-2050_VP.csv`).

Si el validador imprime ✅ en todas las fuentes, la ingesta debería pasar. Si imprime ⚠ con el listado de rutas que se buscaron, hay que mover la carpeta `Datos/` o configurar el `.env` con rutas explícitas. Documentación complementaria: `INSTALACION_COMPAÑEROS.md` y `SETUP_DATOS.md`.

---

## 7. CAPA SILVER — LIMPIEZA, ESTANDARIZACIÓN Y AGREGACIÓN

### 7.1 Punto de entrada
```bash
python src/transformacion/run_silver.py
# o bien:
python -m src.cli silver
```

### 7.2 Orquestador Silver

**Archivo**: `src/transformacion/silver/main_transformation.py`

La clase `TransformationOrchestrator` ejecuta un "cleaner" específico por fuente. Cada cleaner:
1. Lee los Parquet crudos de Bronze
2. Aplica limpieza de texto (normalización Unicode NFKC, eliminación de caracteres de control)
3. Estandariza nombres de columnas a `snake_case`
4. Aplica tipificación (montos a `float64`, DIVIPOLA a `string` con `zfill(5)`, fechas a `datetime`)
5. Estandariza geográficamente (mapeo a código DIVIPOLA de 5 dígitos)
6. Agrega a granularidad **Municipio-Año** (o Departamento-Año para EMICRON/Proyecciones)
7. Escribe el resultado en `data/silver/silver_<fuente>_agregado.parquet`

### 7.3 Módulos de transformación compartidos

#### `transform/clean_text.py`
- **Normalización Unicode**: `unicodedata.normalize('NFKC', text)` — convierte caracteres compatibles a su forma canónica
- **Eliminación de caracteres de control**: `re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', '', text)`
- **Estandarización de caso**: Soporte para `upper`, `lower`, `title`, `sentence`
- **Snake case para columnas**: CamelCase → snake_case, espacios → guiones bajos

#### `transform/standardize_geo.py` — Estandarización geográfica DIVIPOLA

Este es uno de los módulos más críticos del pipeline. Resuelve el problema fundamental de que **SECOP I no tiene código DIVIPOLA** sino nombres de municipio en texto libre.

**Catálogo DIVIPOLA embebido**: Se mantiene un diccionario Python con los 1,102 municipios de Colombia. Cada entrada tiene:
```python
'05001': {
    'nombre': 'Medellín',
    'departamento': 'Antioquia',
    'divipola_dep': '05'
}
```

**Mapeo inverso por nombre normalizado**:
```python
def _normalize_municipio_name(nombre):
    nombre = nombre.lower()
    nombre = unicodedata.normalize('NFD', nombre)
    nombre = re.sub(r'[^\w\s]', '', nombre)
    return nombre.strip()
```

Se generan variantes automáticas: "Bogotá D.C." → ["bogota dc", "bogota", "bogota d.c."].

**¿Por qué un catálogo embebido y no una API?**
- **Reproducibilidad offline**: El pipeline funciona sin conexión a internet
- **Velocidad**: No hay latencia de red para mapear 2 millones de registros
- **Determinismo**: El mismo código siempre produce el mismo resultado
- **Fallback a CSV**: Si existe `data/bronze/divipola/divipola_oficial.csv`, se carga dinámicamente

#### `transform/type_cast.py` — Tipificación para capa Silver

Define el esquema `PLATA_SCHEMA` con tipos PyArrow optimizados:

| Campo | Tipo | Razón |
|-------|------|-------|
| `divipola_municipio` | `string[pyarrow]` | Preservar ceros a la izquierda (ej: "05001") |
| `monto_contrato` | `float64[pyarrow]` | Precisión decimal para montos en pesos colombianos |
| `ipm_total` | `float32[pyarrow]` | Indicadores de 0 a 1, float32 es suficiente |
| `total_micronegocios` | `int32[pyarrow]` | Conteos enteros |
| `es_economia_popular` | `bool[pyarrow]` | Banderas binarias |

### 7.4 Cleaner SECOP I (`clean_secop_i.py`)

1. Lee todos los Parquet bajo `data/bronze/secop_i/` (recursivo)
2. Resuelve nombres reales de columnas (con tildes/espacios) vía un índice normalizado (`_norm`): `UID`, `Fecha de Firma del Contrato`, `Cuantia Contrato`, `Identificacion del Contratista`, `Departamento Entidad`, `Municipio Entidad`.
3. **Resolución de `divipola_key` por prioridad**:
   1. `DIVIPOLA_KEY_MAPPED` (si el parser de Bronze ya lo inyectó)
   2. `CODIGO_MUNICIPIO_ENTIDAD`
   3. Lookup `(_norm(departamento), _norm(municipio))` contra `DIVIPOLA_COMPLETO` con alias para Bogotá D.C. (`BOGOTA_D_C` ↔ `BOGOTA`).
4. Limpieza monetaria colombiana: `"$1.234.567,89"` → `1234567` eliminando todo carácter no dígito.
5. Extrae el año desde `fecha_firma` (intenta `DD/MM/YYYY` y luego ISO).
6. NIT de contratista: solo dígitos, preservado como string para `COUNT(DISTINCT)` en Gold.
7. **Filtros de calidad** antes de agregar:
   - `divipola_key` debe coincidir con `^\d{5}$`
   - `anio_key` no nulo y en rango `[2018, 2030]`
8. Genera dos salidas:
   - `silver_secop_i_transaccional.parquet` (grano contrato; insumo del cruce sin doble conteo)
   - `silver_secop_i_agregado.parquet` (grano municipio-año con `COUNT(DISTINCT nit)` intra-plataforma)

### 7.5 Cleaner SECOP II (`clean_secop_ii.py`)

Mismo patrón que SECOP I, pero con nombres reales propios:
1. Lee `data/bronze/secop_ii/*.parquet` recursivamente.
2. Resuelve `id_contrato` (`ID Contrato` / `Referencia del Contrato`), `Fecha de Firma`, `Valor del Contrato`, `Documento Proveedor`.
3. **`divipola_key` por prioridad**: `DIVIPOLA_KEY_MAPPED` → `COD_MUNICIPIO` / `CODIGO_MUNICIPIO` → lookup `Departamento + Ciudad` con alias para Bogotá. Importante: `Codigo Entidad` **no** es DIVIPOLA en SECOP II (es NIT de la entidad), por eso no se usa.
4. Aplica los mismos filtros de calidad (`^\d{5}$`, año 2018–2030) y produce transaccional + agregado análogos a SECOP I.

### 7.5.1 ⚠ Sesgo crítico de atribución geográfica (SECOP I y II)

> **Advertencia obligatoria al usar cualquier indicador territorial derivado de SECOP**

En los cleaners de SECOP I y SECOP II, la `divipola_key` se construye a partir de `Municipio Entidad + Departamento Entidad` (o sus equivalentes en SECOP II `Ciudad + Departamento`). Es decir: **el municipio del contrato es el municipio de la entidad contratante, no el municipio donde se ejecuta el contrato**.

Esto produce un sesgo sistemático en favor de Bogotá D.C. (`11001`):

| Año | Cuota de Bogotá en monto total |
|---:|---:|
| 2018 | 50.2 % |
| 2019 | 42.6 % |
| 2020 | 41.2 % |
| 2021 | 47.2 % |
| 2022 | 54.3 % |
| 2023 | 38.0 % |
| 2024 | 34.1 % |

La razón es estructural: todas las entidades del **orden nacional** (Presidencia, ministerios, ICBF, Invías, Fuerzas Militares, agencias) tienen sede en Bogotá; SECOP registra `Municipio Entidad = "BOGOTA D.C."` para todas ellas y, en consecuencia, esos contratos quedan imputados a `11001` aunque se ejecuten en cualquier otro municipio del país.

**Workaround actual**: en análisis EDA se reportan series "con Bogotá" y "sin Bogotá" para aproximar el filtro de orden territorial. No es un filtro estricto — entidades nacionales con sedes regionales siguen incluidas.

**Solución correcta (pendiente)**: preservar la columna `orden_entidad` desde el Bronze hasta la transaccional Silver, y filtrar por `orden_entidad ∈ {Territorial}`. El esquema transaccional actual solo conserva `id_contrato, divipola_key, anio_key, fecha_firma, valor_del_contrato, nit_contratista, _fuente_origen`, por lo que esta corrección requiere modificar los cleaners SECOP. Ver §15 ítem 6.

### 7.6 Cleaner CNPV (`clean_cnpv.py`)

**Corrección 2026-05-19** — Versiones anteriores de este informe afirmaban que el cleaner extraía IPM total, IPM por dimensión, NBI y déficit habitacional. La revisión del código (verificada en el documento [EDA_corrección.md](docs/EDA_corrección.md) §1.3) confirma que **eso no es cierto**:

1. Lee los Parquet por módulo (viviendas, hogares, personas, MGN).
2. **Solo emite la columna geográfica `divipola_key`** (`clean_cnpv.py:76`: `dfs.append(df_part[["divipola_key"]])`).
3. Agrega a nivel municipio como conteo de población base (`poblacion_total_base`) — equivale a `COUNT(*)` sobre el módulo de personas por municipio.
4. Genera `silver_cnpv_agregado.parquet` con `anio_key = 2018`.

**Consecuencia**: NBI, IPM y déficit habitacional **no existen en el pipeline Medallion actual**. Cualquier análisis que los requiera (p. ej. cuadrantes pobreza × inversión en EDAs) debe o bien usar `indicador_inversion_per_capita` como proxy de equidad, o bien implementar un cleaner CNPV extendido que cruce `cnpv_1viv_raw` (materiales/servicios de vivienda), `cnpv_2hog_raw` (hacinamiento) y `cnpv_5per_raw` (asistencia escolar) para reconstruir los componentes del IPM. Pendiente.

**Etnia (no implementada en Silver)**: La columna `PA1_GRP_ETNIC` del Bronze (`cnpv_5per_raw.parquet`, ~2.4 GB) sí permite reconstruir `etnia_indigena_pct` y `etnia_afro_pct` por municipio. El EDA principal lo hace on-the-fly (~30 s con lectura columnar). Si se requiere de forma recurrente, debería incorporarse al mart desde Silver para evitar recomputar.

### 7.7 Cleaner EMICRON (`clean_emicron.py`)

1. Lee todos los Parquet por año (2019–2024)
2. Identifica variables de micronegocios, ventas, empleo
3. Construye `factor_expansion`: usa `F_EXP` cuando viene válido y, si un año queda en cero, fusiona los archivos separados de factores (`fex_c`/`FEX_C`; `fex_micro_dpto` como respaldo) por `(DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, año)`
4. Agrega a nivel **departamental** (no municipal — la EMICRON es encuesta muestral)
5. El código DIVIPOLA para departamentos usa formato `XX000` (ej: "05000" para Antioquia)
6. Genera `silver_emicron_agregado.parquet`

### 7.8 Cleaner Proyecciones (`clean_proyecciones.py`)

1. Lee `proyecciones_censo_raw.parquet`
2. Identifica columnas de año y población
3. Genera serie temporal de población por departamento
4. Escribe `silver_proyecciones_agregado.parquet`

> **Limitación crítica para el cruce**: la salida queda a granularidad **departamento-año** (códigos `XX000`). No se desagrega a municipio. Por eso `fact_demografia_municipio_anio.parquet` solo tiene valores no nulos en los códigos `XX000`, y en el mart la columna `poblacion_total_proyectada` queda en 0 para los 1.122 municipios reales. El cálculo de `indicador_inversion_per_capita` cae al fallback `poblacion_censo_2018` (constante 2018) y por tanto **no captura la dinámica demográfica 2018–2024**. Para corregirlo hace falta o un cleaner municipal de proyecciones DANE, o reescribir `_fact_simple` para que abra el código departamental a sus municipios usando el censo 2018 como peso. Pendiente.

---

## 8. CRUCE DE DATOS — LA LÓGICA CENTRAL

### 8.1 Concepto del cruce

El cruce une datos de **contratación pública** (SECOP I + II) con **indicadores socioeconómicos** (DANE) para responder preguntas como: *¿Los municipios con mayor pobreza multidimensional reciben menos inversión pública per cápita?*

### 8.2 Llave de cruce: `divipola_municipio` (5 dígitos)

**Decisión crítica**: Se eligió el código DIVIPOLA del DANE como llave única de cruce porque:
- Es el estándar oficial del DANE para identificar municipios
- Es numérico y no ambiguo (a diferencia de nombres de municipio que tienen homónimos: "Armenia" existe en Antioquia y en Quindío)
- Tiene exactamente 5 dígitos: los 2 primeros identifican el departamento, los 3 últimos el municipio
- Se estandariza con `str.zfill(5)` para garantizar ceros a la izquierda

### 8.3 Tipos de join utilizados

| Join | Tablas | Tipo | Justificación |
|------|--------|------|---------------|
| SECOP I + SECOP II → fact_contratacion | UNION + GROUP BY | Unión vertical + agregación | Un mismo NIT puede aparecer en ambas plataformas; se usa COUNT(DISTINCT nit) para no inflar proveedores |
| fact_contratacion + dim_territorio | LEFT JOIN on divipola_key | Left | No perder contratos aunque el municipio no esté en catálogo |
| fact_contratacion + dim_tiempo | LEFT JOIN on anio_key | Left | Enriquecer con atributos temporales (año electoral, pandemia) |
| fact_censo (CNPV) → mart | LEFT JOIN on divipola_key (sin año) | Left broadcast | El censo 2018 es snapshot fijo que se propaga a todos los años |
| fact_micronegocios + mart | LEFT JOIN on divipola_key, anio_key | Left | EMICRON es departamental; solo el agregado XX000 tiene valor |
| fact_demografia + mart | LEFT JOIN on divipola_key, anio_key | Left | Proyecciones DANE departamentales |

### 8.4 El problema del doble conteo SECOP I vs SECOP II

**Archivo clave**: `src/transformacion/gold/build_facts.py`, función `_build_fact_contratacion()`

SECOP I y SECOP II son plataformas distintas de Colombia Compra Eficiente, pero un mismo proveedor (NIT) puede tener contratos en ambas. Si simplemente se suman los `proveedores_unicos` de cada plataforma, se infla el conteo.

**Solución implementada (camino preferido — verificado en código)**:
1. Concatena `silver_secop_i_transaccional.parquet` y `silver_secop_ii_transaccional.parquet`.
2. Descarta filas con `divipola_key` o `anio_key` nulos.
3. **Deduplica por `id_contrato`** (`drop_duplicates(keep="first")`) para que un contrato presente en ambas plataformas no infle `inversion_total_monto`.
4. Agrupa por `(divipola_key, anio_key)` con:
   - `cantidad_procesos_adjudicados = nunique(id_contrato)`
   - `inversion_total_monto = sum(valor_del_contrato)`
   - `proveedores_unicos = nunique(nit_contratista)` — un NIT en ambas plataformas cuenta UNA sola vez.
5. Marca la fila con `_metodo_proveedores = "COUNT(DISTINCT nit) sobre union transaccional (correcto)"` y `_fuentes` con los archivos consumidos.

**Fallback (si no hay transaccionales)**: UNION de los dos `*_agregado.parquet`, suma de procesos e inversión, pero `MAX(proveedores_unicos)` como estimador conservador. Se marca con `_metodo_proveedores = "MAX sobre agregados (fallback conservador, NO correcto)"` y devuelve `status = "success_fallback"` para que el reporte Gold lo distinga.

### 8.5 Restricciones legales del cruce

El DANE opera bajo **secreto estadístico** (Ley 79 de 1993). Esto implica:
- **NO** se puede cruzar NIT de proveedores SECOP directamente con microdatos censales del DANE
- Solo se permiten **agregaciones geográficas** (nivel municipio o departamento)
- El cruce es siempre SECOP(municipio) ↔ DANE(municipio), nunca SECOP(proveedor) ↔ DANE(persona)

---

## 9. CAPA GOLD — MODELO ESTRELLA Y DATAMART

### 9.1 Punto de entrada
```bash
python src/transformacion/run_gold.py
# o bien:
python -m src.cli gold
```

### 9.2 Dimensiones

#### `dim_tiempo` (`build_dim_tiempo()`)
- Años 2018–2029
- Atributos: `es_anio_electoral_presidencial`, `es_anio_electoral_regional`, `es_pandemia`
- PK: `anio_key`

#### `dim_territorio` (`build_dim_territorio()`)
1. **Base**: Catálogo DIVIPOLA oficial (1,102 municipios)
2. **Enriquecimiento**: Escanea todos los Parquet de Silver buscando `divipola_key` que no estén en catálogo
3. Para códigos tipo `XX000`: marca como "Agregado departamental"
4. Para municipios no catalogados: marca como "Municipio sin catalogar" con nombre del departamento
5. PK: `divipola_key`

### 9.3 Tablas de hechos

| Fact | Fuente Silver | Grano | Campos principales |
|------|---------------|-------|-------------------|
| `fact_contratacion` | SECOP I + II transaccionales | municipio-año | procesos, inversión, proveedores únicos |
| `fact_censo` | CNPV 2018 | municipio (año fijo 2018) | población base |
| `fact_micronegocios` | EMICRON | departamento-año | volumen expandido |
| `fact_demografia` | Proyecciones DANE | departamento-año | población proyectada |

### 9.4 Datamart analítico (OBT)

**Archivo**: `src/transformacion/gold/build_mart.py`

El OBT (One Big Table) es la tabla final que consume el analista o el dashboard. Se construye así:

1. **Spine**: Solo pares `(divipola_key, anio_key)` que aparecen en al menos un fact real (no producto cartesiano), **acotados al rango de `dim_tiempo` (2018–2029)**. Aunque `fact_demografia` trae proyecciones DANE hasta 2050, el mart analítico solo materializa el horizonte de la dimensión tiempo.
2. **Inclusión adicional de filas solo-censo**: Para todos los municipios con datos en `fact_censo` se cruzan con los años existentes en el spine (o con todos los años de `dim_tiempo` si el spine está vacío). Esto evita perder municipios donde solo hay dato censal pero no contratación.
3. **Join dim_territorio**: LEFT JOIN por `divipola_key`
4. **Join dim_tiempo**: LEFT JOIN por `anio_key`
5. **Join fact_contratacion**: LEFT JOIN por `(divipola_key, anio_key)`
6. **Join fact_micronegocios**: LEFT JOIN por `(divipola_key, anio_key)` — solo aplica para códigos `XX000`
7. **Join fact_demografia**: LEFT JOIN por `(divipola_key, anio_key)` — igual, departamental
8. **Broadcast fact_censo**: LEFT JOIN solo por `divipola_key` (sin año) para propagar dato censal 2018 como `poblacion_censo_2018`.

**Indicadores derivados**:
- `indicador_inversion_per_capita = inversion_total_monto / poblacion`
- `indicador_densidad_micronegocios = volumen_micronegocios_exp / poblacion`

Donde `poblacion` toma `poblacion_censo_2018` cuando es > 0 y cae a `poblacion_total_proyectada` en otros casos (sirve a agregados departamentales que no tienen censo municipal).

**Flags de trazabilidad** (nuevos respecto a la versión 2026-05-11 del informe):
- `tiene_componente_social = (poblacion_total_proyectada > 0) | (poblacion_censo_2018 > 0)`
- `tiene_componente_economico = (inversion_total_monto > 0) | (volumen_micronegocios_exp > 0)`

**Versionamiento**: Se genera una copia versionada (`marts/version_YYYYMMDD/`) y una copia `latest/`. Estado actual: la última versión persistida es `marts/version_20260507/` y `marts/latest/` apunta al mismo Parquet.

---

## 10. EJECUCIÓN END-TO-END

```bash
# Opción 1: CLI formal
python -m src.cli all

# Opción 2: Capa por capa
python -m src.cli bronze          # Ingesta
python -m src.cli silver          # Limpieza
python -m src.cli gold            # Modelo Estrella

# Opción 3: Scripts individuales
python src/ingesta/run_bronze.py
python src/transformacion/run_silver.py
python src/transformacion/run_gold.py
```

### Prerequisitos
1. Python 3.10+ con dependencias: `pip install -e .` o `poetry install`
2. Carpeta `Datos/` con los CSVs fuente (SECOP I, SECOP II, CNPV, EMICRON, Proyecciones)
3. Archivo `.env` con rutas (o usar las rutas por defecto)

---

## 11. VALIDACIÓN Y CALIDAD DE DATOS

### Validación Bronze (`bronze_validator.py`)
- Verifica existencia de archivos Parquet
- Cuenta registros y columnas
- Detecta nulos excesivos (umbral configurable: 50% warning, 90% blocking)
- Genera reporte automático en `documentacion_tecnica/BRONZE_VALIDATION_REPORT.md`

### Validación Silver (`run_silver.py`)
- Verifica completitud de claves primarias
- Detecta duplicados en PK `(divipola_key, anio_key)`
- Genera `documentacion_tecnica/SILVER_DATA_QUALITY_REPORT.md`

### Validación Gold (`run_gold.py`)
- Valida integridad referencial entre facts y dimensiones
- Verifica NO duplicación en FK-set
- Genera `documentacion_tecnica/GOLD_VALIDATION_REPORT.md`

---

## 12. DECISIONES TÉCNICAS CLAVE Y SUS ALTERNATIVAS

| Decisión | Alternativa rechazada | Razón del rechazo |
|----------|----------------------|-------------------|
| Pandas + PyArrow (default) | DuckDB | Dependencia extra sin beneficio claro; eliminado en refactorización previa |
| PySpark opcional con fallback PyArrow | "PySpark obligatorio" o "PySpark eliminado del todo" | El módulo `spark_session.py` permite escalar si hay JVM, sin romper entornos sin Java — la decisión final sobre adoptarlo se toma al cerrar la rama `feature/migracion-duckdb-a-pyspark` |
| CSV local (descarga manual) | Conexión directa a APIs en tiempo real | Dependencia de red, límites de registros, no reproducible offline |
| Parquet con Snappy | CSV plano | Compresión 5x, tipos preservados, lectura columnar |
| Catálogo DIVIPOLA embebido | Geocodificación vía API | Reproducibilidad offline, velocidad, determinismo |
| LEFT JOIN (preservar SECOP) | INNER JOIN | No perder contratos de municipios sin datos DANE |
| COUNT(DISTINCT nit) sobre UNION | SUM de proveedores por plataforma | Evitar doble conteo de NITs presentes en SECOP I y II |
| Spine basada en facts reales | Producto cartesiano territorio×tiempo | Evitar 13K+ filas vacías sin información real |
| Censo como broadcast (sin año) | Censo como fact con año | CNPV 2018 es snapshot fijo; no varía por año |

---

## 13. MAPA DE ARCHIVOS RELEVANTES

```
src/
├── cli.py                           # Entrypoints formales del pipeline
├── orchestrator.py                  # Orquestador general
├── config/
│   ├── settings.py                  # Configuración centralizada (rutas, umbrales)
│   ├── data_sources.yaml            # Catálogo declarativo de fuentes
│   └── vigencia_config.py           # Configuración de actualización automática
├── ingesta/
│   ├── run_bronze.py                # Runner de capa Bronze
│   └── bronze/
│       ├── main_ingestion.py        # Orquestador de ingesta Bronze
│       ├── parsers/
│       │   ├── parser_csv_secop.py      # Parser SECOP II
│       │   ├── parser_csv_secop_i.py    # Parser SECOP I
│       │   ├── parser_csv_cnpv.py       # Parser CNPV (multi-depto, multi-módulo)
│       │   ├── parser_csv_emicron.py    # Parser EMICRON (multi-año, auto-detect)
│       │   └── parser_csv_proyecciones.py # Parser Proyecciones Censales
│       └── validators/
│           └── bronze_validator.py  # Validación post-ingesta
├── transformacion/
│   ├── run_silver.py                # Runner de capa Silver
│   ├── run_gold.py                  # Runner de capa Gold
│   ├── silver/
│   │   ├── main_transformation.py   # Orquestador Silver
│   │   └── cleaners/
│   │       ├── clean_cnpv.py, clean_secop_i.py, clean_secop_ii.py
│   │       └── clean_emicron.py, clean_proyecciones.py
│   ├── gold/
│   │   ├── build_dimensions.py      # dim_tiempo, dim_territorio
│   │   ├── build_facts.py           # fact_contratacion (anti-doble-conteo)
│   │   └── build_mart.py            # Datamart OBT final
│   └── transform/
│       ├── clean_text.py            # Normalización Unicode, snake_case
│       ├── standardize_geo.py       # Mapeo DIVIPOLA con variantes y fuzzy matching
│       └── type_cast.py             # Tipificación PyArrow para capa Silver
└── utils/
    ├── divipola_catalog.py          # Catálogo DIVIPOLA completo (1,102 municipios)
    ├── ciiu_unspsc_mapping.py       # Mapeo CIIU ↔ UNSPSC
    ├── spark_session.py             # Motor dual PySpark↔PyArrow (rama feature/migracion-duckdb-a-pyspark)
    └── logger.py                    # Logger del pipeline
```

---

## 14. FLUJO DE DATOS COMPLETO (DIAGRAMA)

```
CSV SECOP I (~10 GB)   → parser_csv_secop_i  → bronze/secop_i/*.parquet
CSV SECOP II (~9.6 GB) → parser_csv_secop    → bronze/secop_ii/*.parquet
Carpetas CNPV          → parser_csv_cnpv     → bronze/cnpv/*.parquet
Carpetas EMICRON       → parser_csv_emicron  → bronze/emicron/**/*.parquet
CSV Proyecciones       → parser_csv_proyecc. → bronze/proyecciones/*.parquet
        |
        v (Silver: limpieza + estandarización geográfica + agregación)
        |
silver/secop_i/silver_secop_i_{transaccional|agregado}.parquet
silver/secop_ii/silver_secop_ii_{transaccional|agregado}.parquet
silver/cnpv/silver_cnpv_agregado.parquet
data/silver/silver_emicron_agregado.parquet
silver/proyecciones/silver_proyecciones_agregado.parquet
        |
        v (Gold: modelo estrella + mart)
        |
gold/dim_tiempo.parquet
gold/dim_territorio.parquet
gold/fact_contratacion_municipio_anio.parquet  <- UNION(SECOP I + II)
gold/fact_censo_municipio.parquet              <- CNPV 2018
gold/fact_micronegocios_municipio_anio.parquet <- EMICRON
gold/fact_demografia_municipio_anio.parquet    <- Proyecciones
        |
        v (Mart: tabla final para análisis)
        |
gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet
```

---

## 15. PROBLEMAS CONOCIDOS Y LIMITACIONES

1. **Catálogo DIVIPOLA incompleto en `standardize_geo.py`**: El diccionario embebido solo tiene ~200 municipios (Antioquia y Valle). El catálogo completo está en `utils/divipola_catalog.py` con fallback a CSV.

2. **EMICRON es muestral, no censal**: Los datos de micronegocios son estimaciones expandidas con factores de expansión, no conteos exactos. La granularidad es departamental, no municipal.

3. **SECOP I sin DIVIPOLA directo**: El mapeo por nombre de municipio puede fallar para nombres ambiguos o con errores de digitación en el CSV original. Los alias actuales solo cubren Bogotá D.C.; otros homónimos (p. ej. "Armenia") se resuelven correctamente porque el lookup requiere `(departamento, municipio)` y no solo nombre suelto.

4. **`main_gold.py` es un stub**: El archivo `src/transformacion/gold/main_gold.py` y los módulos `gold/schema/` y `gold/marts/create_datamart_*.py` están vacíos / esqueleto. La capa Gold real corre a través del CLI (`src/cli.py::_run_gold`) que invoca directamente `build_dim_tiempo`, `build_dim_territorio`, `build_facts` y `build_datamart`. Si se ejecuta `python src/transformacion/gold/main_gold.py --all` no produce datamarts; usar siempre `python -m src.cli gold` o `python src/transformacion/run_gold.py`.

5. **PySpark requiere Java**: El motor dual (§3.1) intenta crear `SparkSession` con `local[*]` y 4 GB driver/executor. En entornos sin JDK, la prueba falla automáticamente y el código sigue con PyArrow. Para forzar PyArrow se puede simplemente no instalar `pyspark` en el entorno.

6. **Sesgo crítico de atribución geográfica en SECOP** *(documentado a fondo en §7.5.1)*: `divipola_key` representa el municipio de la *entidad contratante*, no del lugar de ejecución. Bogotá D.C. acumula 34–55 % del monto anual por ser sede del orden nacional. Cualquier estadístico territorial sobre SECOP (Gini, ranking municipal, inversión por departamento) debe reportarse con la aclaración explícita, y preferiblemente con doble serie *con/sin Bogotá* hasta que se preserve `orden_entidad` desde Bronze.

7. **CNPV no calcula NBI ni IPM** *(documentado en §7.6)*: Versiones previas del informe afirmaban que el cleaner producía estos indicadores; la verificación de código demostró que `clean_cnpv.py` solo emite `divipola_key`. Cualquier análisis o tablero que dependa de NBI/IPM municipal debe (a) ser deshabilitado, (b) usar `indicador_inversion_per_capita` como proxy de equidad, o (c) esperar a la implementación de un cleaner CNPV extendido.

8. **`poblacion_total_proyectada` es 0 en el mart municipal** *(documentado en §7.8)*: las proyecciones DANE están a granularidad departamento-año y no se reparten a municipios. Los indicadores per cápita usan `poblacion_censo_2018` propagada como constante; las variaciones interanuales reflejan el numerador (monto), no cambios demográficos. Aclarar siempre en cualquier reporte que cite IPC.

9. **`fillna(0)` en agregados de contratación**: el cleaner SECOP genera `proveedores_unicos = 0` para municipios sin contratos en un año dado. Al calcular medidas de concentración (Gini, HHI) hay que filtrar `monto > 0` antes, o se inflan artificialmente los indicadores de desigualdad (problema histórico de la sección 6 del EDA — ver [EDA_corrección.md](docs/EDA_corrección.md) §4.2).

---

## 16. CAMBIOS DESDE LA VERSIÓN 2026-05-11 DEL INFORME

| Área | Cambio |
|------|--------|
| Motor analítico | Se reintrodujo PySpark como motor opcional con auto-fallback a PyArrow en `src/utils/spark_session.py` (rama `feature/migracion-duckdb-a-pyspark`) |
| Cleaners SECOP | Se documentaron filtros de calidad explícitos (`divipola_key` regex `^\d{5}$`, `anio_key` ∈ [2018, 2030]) y la resolución de DIVIPOLA por prioridad (mapped → cod_municipio → lookup con alias Bogotá) |
| **Corrección §7.6 CNPV** | Se quitó la afirmación falsa de que el cleaner CNPV extrae IPM/NBI/déficit. En realidad solo emite `divipola_key` y un conteo poblacional; los indicadores de pobreza no existen en el pipeline (verificado en código y documentado en [EDA_corrección.md](docs/EDA_corrección.md)) |
| **Nuevo §7.5.1 — Sesgo SECOP** | `divipola_key` representa la sede de la entidad contratante, no la ejecución. Bogotá acumula 34–55 % del monto anual. Documentado con la cuota anual y el workaround "sin Bogotá" |
| **§7.8 Proyecciones** | Documentado explícitamente que la granularidad es depto-año y que `poblacion_total_proyectada` queda en 0 en el mart municipal; los IPC del mart usan censo 2018 constante |
| **§6.3 Validador** | Documentado `python -m src.validadores.verificar_datos` (introducido el 2026-04-23 — ver [DIAGNOSTICO_PROBLEMA_INGESTA.md](docs/DIAGNOSTICO_PROBLEMA_INGESTA.md)) para chequear la carpeta `Datos/` antes de correr Bronze |
| Datamart | Se documentaron los flags `tiene_componente_social` / `tiene_componente_economico` y la inclusión adicional de filas solo-censo en el spine |
| Versionado del mart | Última versión persistida: `data/gold/marts/version_20260507/` |
| Stub Gold | `main_gold.py`, `gold/schema/*` y `gold/marts/create_datamart_*.py` son esqueletos; el flujo real corre por `src/cli.py::_run_gold` |
| EDA / HHI / Gini | Limpieza de scripts legacy de HHI y reescritura completa del cálculo de Gini (sec. 6 del EDA): la métrica reportable queda definida como Gini de inversión per cápita (0.45–0.59, plausible). Se descarta el cálculo sobre montos totales, se elimina `fillna(0)` y se reporta `n_muni_ipc`. Ver [EDA_corrección.md](docs/EDA_corrección.md) §4 |
| **Nuevos ítems §15 (6–9)** | Sesgo SECOP, ausencia de NBI/IPM, población constante 2018, y `fillna(0)` en agregados — cuatro caveats obligatorios para cualquier indicador territorial derivado del mart |

---

**Fin del informe técnico.**
*Actualizado el 2026-05-19 basado en revisión del repositorio en la rama `feature/migracion-duckdb-a-pyspark`.*
*Versión anterior: 2026-05-11.*
