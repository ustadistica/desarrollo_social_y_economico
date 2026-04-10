# 🏗️ Reestructuración del Pipeline de Ingesta - Capa Bronze

## ✅ Tareas Completadas

Se ha completado la reestructuración completa del proceso de ingesta y validación de datos siguiendo la arquitectura Medallion (Capa Bronze).

---

## 📁 Nueva Estructura de Carpetas

```
ingesta y validacion/
└── bronze/                              # NUEVO MÓDULO
    ├── __init__.py                      # Paquete Bronze
    ├── main_ingestion.py                # 🎯 Orquestador Principal
    ├── README_RESTRUCTURACION.md        # Documentación completa
    │
    ├── parsers/                         # Parsers por fuente
    │   ├── __init__.py
    │   ├── parser_xml_cnpv.py           # CNPV 2018 (XML Local)
    │   ├── parser_api_secop.py          # SECOP II (API JSON)
    │   ├── parser_csv_emicron.py        # EMICRON 2024 (CSV Local)
    │   └── parser_generic.py            # IPM/NBI (Genérico)
    │
    └── validators/                      # Validaciones
        ├── __init__.py
        └── bronze_validator.py          # Validador de esquema
```

---

## 📊 Fuentes de Datos Implementadas

| # | Fuente | Tipo | Parser | Estado |
|---|--------|------|--------|--------|
| 1 | **CNPV 2018** (DANE) | XML Local | `parser_xml_cnpv.py` | ✅ Implementado |
| 2 | **SECOP II** (datos.gov.co) | API JSON | `parser_api_secop.py` | ✅ Implementado |
| 3 | **EMICRON 2024** (DANE) | CSV Local | `parser_csv_emicron.py` | ✅ Implementado |
| 4 | **IPM/NBI** (DANE) | Genérico | `parser_generic.py` | ✅ Implementado |
| 5 | **Proyecciones Censales** (DANE) | CSV Local | `parser_csv_proyecciones.py` | ✅ Implementado |

---

## 🔧 Características Técnicas

### 1. Parser XML (CNPV 2018)
- ✅ Parser eficiente con `lxml` e `iterparse`
- ✅ Procesamiento por chunks para memoria eficiente
- ✅ Detección automática de estructura XML
- ✅ Conversión de tipos de datos inteligente

### 2. Parser API (SECOP II)
- ✅ Conexión con API SODA 2.0
- ✅ Paginación automática (batch_size configurable)
- ✅ Reintentos con backoff exponencial
- ✅ Rate limiting automático
- ✅ Soporte para App Token

### 3. Parser CSV (EMICRON 2024)
- ✅ Detección automática de encoding (chardet)
- ✅ Detección automática de separador
- ✅ Manejo de archivos grandes con chunks
- ✅ Modo permisivo para CSVs problemáticos

### 4. Parser Genérico (IPM/NBI)
- ✅ Soporte multi-formato (Excel, CSV, JSON)
- ✅ Detección automática de tipo de archivo
- ✅ Búsqueda inteligente de archivos
- ✅ Funciones específicas para IPM y NBI

---

## ✅ Validaciones de Capa Bronze

Cada ingesta incluye validaciones automáticas:

| Validación | Descripción | Criticalidad |
|------------|-------------|--------------|
| `row_count` | Conteo de registros | 🔴 Error si = 0 |
| `column_count` | Conteo de columnas | 🔴 Error si = 0 |
| `null_check` | Nulos en columnas críticas | 🔴 Error si hay nulos |
| `schema_check` | Coincidencia de schema | 🟡 Warning si no coincide |
| `duplicate_check` | Registros duplicados | 🟡 Warning si hay duplicados |
| `statistics` | Estadísticas básicas | ℹ️ Informativo |

**Columnas críticas** (no pueden ser nulas):
- `divipola_municipio`
- `divipola_departamento`

---

## 🚀 Comandos de Uso

### Ejecutar ingesta completa
```bash
cd "ingesta y validacion/bronze"
python main_ingestion.py --all --validate
```

### Ejecutar ingesta para fuentes específicas
```bash
# Solo CNPV
python main_ingestion.py --source cnpv

# CNPV y SECOP II
python main_ingestion.py --sources cnpv secop

# Todas excepto IPM/NBI
python main_ingestion.py --sources cnpv secop emicron
```

### Forzar re-ingesta
```bash
python main_ingestion.py --all --force --validate
```

### Listar fuentes disponibles
```bash
python main_ingestion.py --list
```

---

## 🗑️ Limpieza de Scripts Obsoletos

Se ha creado el script `cleanup_obsolete_scripts.py` para eliminar archivos obsoletos:

### Modo simulación (recomendado primero)
```bash
python cleanup_obsolete_scripts.py --dry-run
```

### Ejecutar eliminación real
```bash
python cleanup_obsolete_scripts.py --confirm
```

### Verificar archivos importantes
```bash
python cleanup_obsolete_scripts.py --verify
```

### Archivos a eliminar:
- **Scripts Python temporales**: `deep_data_check.py`, `inspect_db_temp.py`, `verify_repo_temp_data.py`, etc.
- **Scripts Batch/PowerShell**: `copy_files.bat`, `do_copy.ps1`, etc.
- **Documentación temporal**: `*.txt`, `*.md` obsoletos
- **Directorios**: `repo_temp/`

---

## 📝 Metadatos de Trazabilidad

Cada DataFrame en Bronze incluye:

| Columna | Descripción |
|---------|-------------|
| `_ingestion_timestamp` | Timestamp de ingesta (ISO 8601) |
| `_source` | Nombre de la fuente |
| `_source_version` | Versión de la fuente |
| `_extraction_method` | Método de extracción |
| `_checksum_md5` | Checksum para integridad |

---

## 📂 Estructura de Salida

```
datos/bronze/
├── dane_cnpv/
│   ├── ingestion_date=2026-03-22/
│   │   └── cnpv_2018_20260322_143022_raw.parquet
│   └── validation_report.txt
├── secop_ii/
│   ├── ingestion_date=2026-03-22/
│   │   └── secop_ii_2026-03-01_to_2026-03-22_raw.parquet
│   └── validation_report.txt
├── emicron/
│   ├── ingestion_date=2026-03-22/
│   │   └── emicron_2024_20260322_143045_raw.parquet
│   └── validation_report.txt
├── ipm/
│   └── validation_report.txt
└── nbi/
    └── validation_report.txt
```

---

## 📋 Dependencias Requeridas

Agregar a `requirements.txt` o `pyproject.toml`:

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

## 📚 Documentación Adicional

- `ingesta y validacion/bronze/README_RESTRUCTURACION.md` - Documentación completa
- `ingesta y validacion/config/data_sources.yaml` - Catálogo de fuentes
- `ingesta y validacion/bronze/validation_report.txt` - Reportes de validación (generado automáticamente)

---

## 🎯 Próximos Pasos (Capa Silver)

1. **Transformación a Capa Silver**:
   - Limpieza de valores nulos
   - Estandarización de tipos de datos
   - Normalización de nombres de columnas

2. **Creación de Dimensiones**:
   - `dim_municipio` (DIVIPOLA)
   - `dim_tiempo` (fechas)
   - `dim_sector_ciiu` (clasificación económica)
   - `dim_sector_unspsc` (clasificación compras)

3. **Creación de Tablas de Hechos**:
   - `fact_vulnerabilidad` (CNPV + IPM + NBI)
   - `fact_tejido_productivo` (CENU + EMICRON)
   - `fact_contratacion` (SECOP II)

---

## 📞 Soporte

Para issues con el pipeline:
1. Revisar logs en consola
2. Consultar `validation_report.txt` en cada carpeta Bronze
3. Verificar `data_sources.yaml` para configuración

---

*Fecha de implementación: 2026-03-22*  
*Versión del pipeline: 1.0*  
*Arquitectura: Medallion (Bronze Layer)*
