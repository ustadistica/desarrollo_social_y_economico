# Arquitectura de Datos - Ingesta y Validación (Pipeline Medallion)

Pipeline ETL/ELT refactorizado para el proyecto "Sinergia Socioeconómica entre el Territorio y el Gasto Público". Este submódulo adopta los estándares de la **Arquitectura Medallion** respaldada por **DuckDB** y formato **Parquet** para soportar *Big Data* de forma nativa.

## 🏗️ Estructura del Pipeline End-to-End

El sistema está organizado en tres capas independientes y escalables:

```
ingesta y validacion/
├── bronze/                     # Capa BRONCE (Extracción Cruda)
│   ├── main_ingestion.py       # Orquestador de ingesta a Parquet
│   ├── parsers/                # Parser por fuente (CNPV, SECOP I, SECOP II, EMICRON, etc.)
│   │   ├── parser_csv_cnpv.py
│   │   ├── parser_csv_secop_i.py    ← SECOP I
│   │   ├── parser_csv_secop.py      ← SECOP II (chunks)
│   │   ├── parser_csv_emicron.py    ← EMICRON multi-año (2019-2024)
│   │   └── parser_csv_proyecciones.py
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
│   ├── settings.py             # Configuración centralizada con resolución por glob
│   └── data_sources.yaml       # Catálogo de fuentes de datos
├── utils/                      # Catálogos (DIVIPOLA, CIIU) compartidos
├── run_pipeline.py             # ORQUESTADOR MAESTRO (El botón mágico)
├── .env.example                # Plantilla de configuración para el equipo
└── INSTRUCCIONES_EQUIPO.md     # Guía detallada de setup de entorno
```

## 🚀 Cómo Ejecutar el Pipeline

### Pipeline completo (Bronze → Silver → Gold)

```bash
# Ejecutar todo el ELT
python run_pipeline.py --all

# Forzar sobreescritura de datos
python run_pipeline.py --all --force
```

### Solo capa Bronze (Ingesta)

```bash
# Ingestar todas las fuentes habilitadas
python main_ingestion.py --all

# Ingestar una fuente específica
python main_ingestion.py --source secop_i
python main_ingestion.py --source secop_ii
python main_ingestion.py --source cnpv

# Forzar re-ingesta de SECOP I y II
python main_ingestion.py --sources secop_i secop_ii --force

# Listar todas las fuentes disponibles
python main_ingestion.py --list
```

### Flujo de Datos Interno:
1. **Bronze**: Lee archivos desde el OS (configurados en `.env` o auto-detectados en `../Datos/`), los carga en memoria por fragmentos (chunks de 250K filas) y los convierte en `archivos_raw.parquet`.
2. **Silver**: Ingresa a esos Parquets optimizados, reduce los ~50 Millones de datos del DANE (Personas) agrupándolos geográficamente en milisegundos con *DuckDB* y ajusta los formatos en `archivos_agregados.parquet`.
3. **Gold**: Crea todas las tablas del modelo estrella e inserta los Datamarts en el archivo maestro local de DuckDB (`observatorio_desarrollo.duckdb`).

## 🗄️ Fuentes Soportadas

| Fuente | Entidad | Tamaño Aprox. | Capa Bronze | Capa Silver | Capa Gold (DuckDB) |
|--------|---------|---------------|-------------|-------------|---------------------|
| **Censo (CNPV 2018)** | DANE | ~6 GB | ✅ Parquet particionado | ✅ Agregado Poblacional out-of-core | ✅ Dim_Municipio |
| **SECOP I (Procesos)** | CCE | ~10.5 GB | ✅ Parquet por chunks | 🔜 Pendiente | 🔜 Pendiente |
| **SECOP II (Contratos)** | CCE | ~9.6 GB | ✅ Parquet por chunks | ✅ Casteos monetarios y de fechas | ✅ Hechos Contratación |
| **EMICRON 2019-2024** | DANE | ~70 CSVs (~30 MB) | ✅ Parquet por año y módulo | ✅ Mapas corregidos códigos DANE | ✅ Hechos Tejido |
| **Proyecciones Censales** | DANE | ~140 KB | ✅ Parquet crudo | ✅ Integrado | ✅ Dim_Poblacion |

> La ingesta de **EMICRON** descubre automáticamente las carpetas `EMICRON 2019`, `EMICRON 2020`, ..., `EMICRON 2024` y procesa recursivamente **todos los módulos** (TIC, identificación, ventas, micronegocios, etc.) de cada año. Los Parquets se organizan en `datos/bronze/emicron/<año>/`.

## 📂 Portabilidad y Trabajo en Equipo

El pipeline está diseñado para que **cualquier miembro del equipo** pueda ejecutarlo sin modificar código:

### Opción A: Automática (recomendada)
Coloca todos los datos crudos en una carpeta `Datos/` al **mismo nivel** que el repositorio clonado:

```
📁 TuCarpetaDeProyecto/
├── 📁 Datos/                                    ← Tus archivos aquí
│   ├── SECOP_I_-_Procesos_de_Compra_Pública_*.csv
│   ├── SECOP_II_-_Contratos_Electrónicos_*.csv
│   ├── PPED-AreaDep-2018-2050_VP.csv
│   ├── 📁 CENSO 2018 dep/
│   ├── 📁 EMICRON 2019/
│   ├── 📁 EMICRON 2020/
│   ├── 📁 EMICRON 2021/
│   ├── 📁 EMICRON 2022/
│   ├── 📁 EMICRON 2023/
│   └── 📁 EMICRON 2024/
└── 📁 desarrollo_social_y_economico/            ← Este repositorio
```

El `settings.py` buscará automáticamente los archivos usando **glob patterns**, sin importar la fecha del sufijo en el nombre del archivo.

### Opción B: Configuración manual (.env)
Si tus datos están en otra ubicación:
1. Copia `.env.example` → `.env`
2. Edita las rutas con tus ubicaciones reales
3. El archivo `.env` es ignorado por Git (seguro para compartir el repo)

## 🔧 Dependencias

Para instrucciones detalladas de cómo levantar el proyecto localmente junto al equipo, lee el archivo **`INSTRUCCIONES_EQUIPO.md`**. En resumen:
- Uso de `poetry` para control de librerías.
- `duckdb` y `pyarrow` instalados para la manipulación analítica colosal.
- Uso de un archivo oculto `.env` personal para delimitar la carpeta raíz de las bases de datos.
