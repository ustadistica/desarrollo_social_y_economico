# Reestructuración del Pipeline de Ingesta - Capa Bronze

## Resumen Ejecutivo

Este documento describe la reestructuración completa del proceso de ingesta y validación de datos siguiendo la arquitectura Medallion (Capa Bronze).

---

1. Nueva Estructura de Carpetas

```
ingesta y validacion/
├── bronze/                          # Módulo de ingesta Bronze
│   ├── main_ingestion.py            # Orquestador principal crudo
│   ├── parsers/                     
│   │   ├── parser_csv_cnpv.py       # CNPV 2018 (Microdatos CSV - Particionado)
│   │   ├── parser_csv_secop.py      # SECOP II (CSV Local)
│   │   └── parser_csv_emicron.py    # EMICRON 2024 (CSV Local)
│   └── validators/                  # Validaciones Bronze
│
├── silver/                          # Módulo de transformación Plata
│   ├── main_transformation.py       # Orquestador de limpieza y agregación
│   ├── cleaners/                    
│   │   ├── clean_cnpv.py            # Agregación out-of-core con DuckDB/PyArrow
│   │   ├── clean_secop.py           # Casting de montos y fechas
│   │   └── clean_emicron.py         # Mapeo de diccionarios DANE
│   └── validators/                  # Validaciones funcionales (integridad)
│
├── config/                          # Configuración global
├── transform/                       # Creación de Dimensiones y Hechos (Estrella)
├── load/                            # Carga
├── validate/                        # Validación final
└── utils/                           # Utilidades
```

---

## 2. Scripts Obsoletos para Eliminar

### 2.1 Root-Level Scripts (Temporales/Un solo uso)

**Ubicación:** `desarrollo_social_y_economico-main (2)/` (raíz)

| Archivo | Propósito Original | Razón para Eliminar |
|---------|-------------------|---------------------|
| `deep_data_check.py` | Análisis de Parquet en bronze | Script de análisis puntual, funcionalidad reemplazada |
| `inspect_db_temp.py` | Copia de carpetas DuckDB | Script temporal de migración |
| `verify_repo_temp_data.py` | Verificación de datos en repo_temp | Script de verificación puntual |
| `copy_binary.py` | Copia de archivo DuckDB | Utilidad temporal |
| `copy_using_python.py` | Copia de carpetas/archivos | Utilidad temporal duplicada |
| `run_copy.py` | Copia de carpetas/archivos | Duplicado de copy_using_python.py |
| `verify_data_content.py` | Verificación de 6 databases | Script de verificación puntual |

### 2.2 Batch/PowerShell Scripts

**Ubicación:** `desarrollo_social_y_economico-main (2)/` (raíz)

| Archivo | Propósito | Razón para Eliminar |
|---------|-----------|---------------------|
| `copy_files.bat` | Copia de archivos | Reemplazado por pipeline Python |
| `copy_files_script.ps1` | Copia PowerShell | Reemplazado por pipeline Python |
| `copy_duckdb.bat` | Copia DuckDB | Reemplazado por pipeline Python |
| `do_copy.bat` | Ejecución de copia | Reemplazado por pipeline Python |
| `do_copy.ps1` | Ejecución PowerShell | Reemplazado por pipeline Python |
| `verify_copy.ps1` | Verificación de copia | Reemplazado por validador Bronze |

### 2.3 Documentación Temporal

**Ubicación:** `desarrollo_social_y_economico-main (2)/` (raíz)

| Archivo | Contenido | Razón para Eliminar |
|---------|-----------|---------------------|
| `CNPV_ARCHIVOS_ESPECIFICOS_DESCARGAR.txt` | Lista de archivos CNPV | Información obsoleta |
| `INFORME_DATOS_REPO_TEMP.txt` | Informe temporal de datos | Temporal |
| `INFORME_ESTADO_DATOS.txt` | Estado de datos | Reemplazado por validador |
| `QUICK_REFERENCE.txt` | Referencia rápida | Obsoleto |
| `GUÍA_DESCARGA_DATOS_DANE.txt` | Guía de descarga | Información en data_sources.yaml |
| `REQUISITOS_DESCARGA_AUTOMATICA.md` | Requisitos | Obsoleto |
| `RESPUESTA_REGISTRO_DANE.md` | Respuesta registro | Temporal |

### 2.4 Directorios Completos

| Directorio | Razón para Eliminar |
|------------|---------------------|
| `repo_temp/` | Copia temporal redundante del repositorio principal |

---

## 3. Scripts a Mantener

### 3.1 Pipeline ETL/ELT Principal

**Ubicación:** `ingesta y validacion/`

| Archivo | Estado | Notas |
|---------|--------|-------|
| `orchestrator.py` | ✅ KEEP | Orquestador principal del pipeline |
| `PIPELINE_ETL_ELT_DISENO.md` | ✅ KEEP | Documentación de diseño |
| `README.md` | ✅ KEEP | Documentación del módulo |
| `requirements.txt` | ✅ KEEP | Dependencias |

### 3.2 Configuración

**Ubicación:** `ingesta y validacion/config/`

| Archivo | Estado | Notas |
|---------|--------|-------|
| `data_sources.yaml` | ✅ KEEP | Catálogo de fuentes de datos |
| `settings.py` | ✅ KEEP | Configuración general |
| `vigencia_config.py` | ✅ KEEP | Configuración de vigencia |

### 3.3 Extractores Existentes

**Ubicación:** `ingesta y validacion/extract/`

| Archivo | Estado | Notas |
|---------|--------|-------|
| `extract_dane_cnpv.py` | ✅ KEEP | Extractor CNPV vía SODA API |
| `extract_dane_cenu.py` | ✅ KEEP | Extractor CENU vía SODA API |
| `extract_secop_ii.py` | ✅ KEEP | Extractor SECOP II (funcional) |
| `extract_terridata.py` | ✅ KEEP | Extractor TerriData |
| `extract_dane_geoportal.py` | ✅ KEEP | Descarga Geoportal DANE |
| `process_manual_downloads.py` | ✅ KEEP | Procesa descargas manuales |

### 3.4 Transformación, Carga y Validación

**Ubicación:** `ingesta y validacion/{transform,load,validate,utils}/`

Todos los archivos en estos directorios se mantienen:
- ✅ `transform/*.py` - Creación de dimensiones y hechos
- ✅ `load/*.py` - Data Marts y cubos analíticos
- ✅ `validate/*.py` - Validación de capas
- ✅ `utils/*.py` - Utilidades

---

## 4. Comandos de Uso del Nuevo Pipeline

### 4.1 Ejecutar Ingesta Completa

```bash
cd "ingesta y validacion/bronze"
python main_ingestion.py --all --validate
```

### 4.2 Ejecutar Ingesta para Fuentes Específicas

```bash
# Solo CNPV
python main_ingestion.py --source cnpv

# CNPV y SECOP II
python main_ingestion.py --sources cnpv secop

# Todas excepto IPM/NBI
python main_ingestion.py --sources cnpv secop emicron
```

### 4.3 Forzar Re-ingesta

```bash
python main_ingestion.py --all --force --validate
```

### 4.4 Listar Fuentes Disponibles

```bash
python main_ingestion.py --list
```

### 4.5 Ejecutar desde la Raíz del Proyecto

```bash
cd desarrollo_social_y_economico-main
python -m ingesta_y_validacion.bronze.main_ingestion --all
```

---

## 5. Especificaciones Técnicas por Fuente

### Fuente 1: CNPV 2018 (DANE)

| Parámetro | Valor |
|-----------|-------|
| **Tipo** | XML Local |
| **Ruta** | `C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\DANE-DCD-CNPV-2018.xml` |
| **Parser** | `parser_xml_cnpv.py` |
| **Librerías** | `lxml`, `pandas` |
| **Validación** | Schema con columnas críticas (divipola, ipm_*, nbi_*) |
| **Output** | `datos/bronze/dane_cnpv/cnpv_2018_YYYYMMDD_HHMMSS_raw.parquet` |

### Fuente 2: SECOP II

| Parámetro | Valor |
|-----------|-------|
| **Tipo** | API JSON (SODA 2.0) |
| **Endpoint** | `https://www.datos.gov.co/resource/287p-52ht.json` |
| **Parser** | `parser_api_secop.py` |
| **Librerías** | `requests`, `pandas` |
| **Características** | Paginación, rate limiting, reintentos con backoff |
| **Output** | `datos/bronze/secop_ii/secop_ii_YYYY-MM-DD_to_YYYY-MM-DD_raw.parquet` |

### Fuente 3: EMICRON 2024

| Parámetro | Valor |
|-----------|-------|
| **Tipo** | CSV Local |
| **Ruta** | `C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\Módulo de características del micronegocio.csv` |
| **Parser** | `parser_csv_emicron.py` |
| **Librerías** | `pandas`, `chardet` |
| **Características** | Detección automática de encoding y separador |
| **Output** | `datos/bronze/emicron/emicron_2024_YYYYMMDD_HHMMSS_raw.parquet` |

### Fuente 4: IPM/NBI (Genérico)

| Parámetro | Valor |
|-----------|-------|
| **Tipo** | Genérico (Excel/CSV/JSON) |
| **Ruta Base** | `C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Datos\` |
| **Parser** | `parser_generic.py` |
| **Librerías** | `pandas`, `openpyxl`, `chardet` |
| **Características** | Detección automática de tipo de archivo |
| **Output** | `datos/bronze/{ipm,nbi}/{source}_YYYYMMDD_HHMMSS_raw.parquet` |

---

## 6. Validaciones de Capa Bronze

Cada ingesta incluye las siguientes validaciones automáticas:

### 6.1 Checks Realizados

| Check | Descripción | Estado Crítico |
|-------|-------------|----------------|
| `row_count` | Conteo de registros | Error si = 0 |
| `column_count` | Conteo de columnas | Error si = 0 |
| `null_check` | Valores nulos en columnas críticas | Error si hay nulos |
| `schema_check` | Coincidencia de schema esperado | Warning si no coincide |
| `duplicate_check` | Registros duplicados | Warning si hay duplicados |
| `statistics` | Estadísticas básicas | Informativo |

### 6.2 Columnas Críticas

Las siguientes columnas NO pueden tener valores nulos:
- `divipola_municipio`
- `divipola_departamento`

### 6.3 Reporte de Validación

Cada fuente genera un archivo `validation_report.txt` en su carpeta Bronze con:
- Estado general (VÁLIDO/INVÁLIDO)
- Resultados de cada check
- Lista de errores y advertencias

---

## 7. Dependencias Requeridas

Agregar al `requirements.txt` o `pyproject.toml`:

```txt
# Core
pandas>=2.0.0
numpy>=1.24.0

# XML Parsing
lxml>=4.9.0

# API Requests
requests>=2.31.0

# Encoding Detection
chardet>=5.0.0

# Excel Support
openpyxl>=3.1.0

# Parquet Support
pyarrow>=12.0.0
```

---

## 8. Comandos para Limpieza del Repositorio

### 8.1 Eliminar Scripts Obsoletos (Windows PowerShell)

```powershell
cd "c:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\desarrolo eco\desarrollo_social_y_economico-main (2)"

# Eliminar scripts Python obsoletos
Remove-Item -Force deep_data_check.py
Remove-Item -Force inspect_db_temp.py
Remove-Item -Force verify_repo_temp_data.py
Remove-Item -Force copy_binary.py
Remove-Item -Force copy_using_python.py
Remove-Item -Force run_copy.py
Remove-Item -Force verify_data_content.py

# Eliminar scripts batch/PowerShell
Remove-Item -Force copy_files.bat
Remove-Item -Force copy_files_script.ps1
Remove-Item -Force copy_duckdb.bat
Remove-Item -Force do_copy.bat
Remove-Item -Force do_copy.ps1
Remove-Item -Force verify_copy.ps1

# Eliminar documentación temporal
Remove-Item -Force CNPV_ARCHIVOS_ESPECIFICOS_DESCARGAR.txt
Remove-Item -Force INFORME_DATOS_REPO_TEMP.txt
Remove-Item -Force INFORME_ESTADO_DATOS.txt
Remove-Item -Force QUICK_REFERENCE.txt
Remove-Item -Force GUÍA_DESCARGA_DATAS_DANE.txt
Remove-Item -Force REQUISITOS_DESCARGA_AUTOMATICA.md
Remove-Item -Force RESPUESTA_REGISTRO_DANE.md

# Eliminar directorio repo_temp
Remove-Item -Recurse -Force repo_temp
```

### 8.2 Verificar Eliminación

```powershell
# Listar archivos restantes en raíz
Get-ChildItem -File

# Deberían quedar solo:
# - copy_files.bat (si se quiere mantener backup)
# - README.md, CONTRIBUTING.md
# - pyproject.toml, poetry.lock
# - .gitignore, Dockerfile
# - verify_migration.py (si es necesario)
```

---

## 9. Trazabilidad de Datos

### 9.1 Metadatos de Ingesta

Cada DataFrame en Bronze incluye:

| Columna | Descripción |
|---------|-------------|
| `_ingestion_timestamp` | Timestamp de ingesta (ISO 8601) |
| `_source` | Nombre de la fuente (ej: `secop_ii`) |
| `_source_version` | Versión de la fuente (ej: `SECOP_II_LATEST`) |
| `_extraction_method` | Método de extracción (ej: `SODA_API`) |
| `_checksum_md5` | Checksum MD5 para integridad |

### 9.2 Estructura de Directorios Bronze

```
datos/bronze/
├── dane_cnpv/
│   ├── ingestion_date=20260322/
│   │   └── cnpv_2018_20260322_143022_raw.parquet
│   └── validation_report.txt
├── secop_ii/
│   ├── ingestion_date=20260322/
│   │   └── secop_ii_2026-03-01_to_2026-03-22_raw.parquet
│   └── validation_report.txt
├── emicron/
│   ├── ingestion_date=20260322/
│   │   └── emicron_2024_20260322_143045_raw.parquet
│   └── validation_report.txt
├── ipm/
│   └── validation_report.txt
└── nbi/
    └── validation_report.txt
```

---

## 10. Próximos Pasos (Capa Silver)

Una vez completada la ingesta Bronze:

1. **Transformación a Capa Silver:**
   - Limpieza de valores nulos
   - Estandarización de tipos de datos
   - Normalización de nombres de columnas
   - Validación de integridad referencial

2. **Creación de Dimensiones:**
   - `dim_municipio` (DIVIPOLA)
   - `dim_tiempo` (fechas)
   - `dim_sector_ciiu` (clasificación económica)
   - `dim_sector_unspsc` (clasificación compras)

3. **Creación de Tablas de Hechos:**
   - `fact_vulnerabilidad` (CNPV + IPM + NBI)
   - `fact_tejido_productivo` (CENU + EMICRON)
   - `fact_contratacion` (SECOP II)

---

## 11. Contacto y Soporte

Para preguntas o issues con el pipeline de ingesta:

- Revisar logs en `ingesta y validacion/bronze/logs/`
- Consultar `validation_report.txt` en cada carpeta Bronze
- Verificar `data_sources.yaml` para configuración de fuentes

---

*Documento generado: 2026-03-22*
*Versión: 1.0*
