# Arquitectura de Datos - Ingesta y Validación (Pipeline Medallion)

Pipeline ETL/ELT refactorizado para el proyecto "Sinergia Socioeconómica entre el Territorio y el Gasto Público". Este submódulo adopta los estándares de la **Arquitectura Medallion** respaldada por **DuckDB** y formato **Parquet** para soportar *Big Data* de forma nativa.

## 🏗️ Estructura del Pipenine End-to-End

El antiguo sistema acoplado ha evolucionado a tres capas independientes y escalables:

```
ingesta y validacion/
├── bronze/                     # Capa BRONCE (Extracción Cruda)
│   ├── main_ingestion.py       # Descargador y convertidor a Parquet
│   ├── parsers/                # Lógica adaptada por fuente (CSV Censo, API Secop, etc)
│   └── validators/             # Auditoría de completitud del esquema original
│
├── silver/                     # Capa PLATA (Limpieza y Agregación Masiva)
│   ├── main_transformation.py  # Orquestador intermedio
│   ├── cleaners/               # DuckDB Group-bys, estandarización DIVIPOLA y Casting
│   └── validators/             # Control de nulos y lógicas estadísticas
│
├── gold/                       # Capa ORO (Modelado Dimensional y Datamarts)
│   ├── main_gold.py            # Orquestador final
│   ├── schema/                 # Creación del Modelo Estrella (Dimensiones y Hechos)
│   └── marts/                  # Cubos OLAP y Datamarts (Social, Económico)
│
├── config/                     # Variables de entorno y rutas (settings.py)
├── utils/                      # Catálogos (DIVIPOLA, CIIU) compartidos
├── run_pipeline.py             # ORQUESTADOR MAESTRO (El botón mágico)
└── INSTRUCCIONES_EQUIPO.md     # Guía detallada de setup de entorno
```

## 🚀 Cómo Ejecutar el Pipeline

En lugar de llamar scripts individuales, el proyecto se unificó en un orquestador que ejecuta la cadena de dependencias en cadena.

```bash
# Ejecutar todo el ELT (Bronze -> Silver -> Gold)
python run_pipeline.py --all

# Forzar sobreescritura de datos
python run_pipeline.py --all --force
```

### Flujo de Datos Interno:
1. **Bronze**: Lee archivos desde el OS (en tu `.env`), los sube en memoria por fragmentos y los transforma en múltiples `archivos_raw.parquet`.
2. **Silver**: Ingresa a esos Parquets optimizados, reduce los ~50 Millones de datos del DANE (Personas) agrupándolos geográficamente en milisegundos con *DuckDB* y ajusta los formatos en `archivos_agregados.parquet`.
3. **Gold**: Crea todas las tablas del modelo estrella e inserta los Datamarts en el archivo maestro local de DuckDB (`observatorio_desarrollo.duckdb`).

## 🗄️ Fuentes Soportadas (Fase Actual)

| Fuente | Entidad | Capa Bronze | Capa Silver | Capa Gold (DuckDB) |
|--------|---------|-------------|-------------|--------------------|
| **Censo (CNPV 2018)** | DANE | ✅ Archivos de 6GB a Parquet particionado | ✅ Agregado Poblacional out-of-core | ✅ Integrado a Dim_Municipio |
| **EMICRON (2024)** | DANE | ✅ Parquet estructurado | ✅ Mapas corregidos de códigos DANE | ✅ Integrado Hechos Tejido |
| **SECOP II** | CCE | ✅ Parquet masivo histórico | ✅ Casteos monetarios y de fechas | ✅ Hechos de Contratación |

## 🔧 Dependencias

Para instrucciones detalladas de cómo levantar el proyecto localmente junto al equipo, lee el archivo **`INSTRUCCIONES_EQUIPO.md`**. En resumen:
- Uso de `poetry` para control de librerías.
- `duckdb` y `pyarrow` instalados para la manipulación analítica colosal.
- Uso del un archivo oculto `.env` personal para delimitar la carpeta raíz de las bases de datos.
