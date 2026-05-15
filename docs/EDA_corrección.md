# EDA — Diagnóstico de fallos y documentación de la corrección

Fecha de corrección: 2026-05-15  
Notebook afectado: `notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb`  
Notebook adicional revisado: `notebooks/EDA_Express.ipynb`

---

## 0. Por qué se cambió el EDA

El EDA fue corregido porque dependía de variables (NBI e IPM) que **nunca formaron parte del pipeline de ingesta del proyecto**. La ingesta actual procesa cuatro fuentes — SECOP I, SECOP II, CNPV 2018 y EMICRON — y produce una capa Gold (`mart_desarrollo_social_economico_municipio_anio.parquet`) que contiene indicadores de contratación pública, población y micronegocios. NBI e IPM no son producidos por ningún paso de ese pipeline, ni en Bronze, ni en Silver, ni en Gold.

No está claro por qué el EDA fue diseñado con dependencia en NBI/IPM si esos indicadores nunca estuvieron contemplados en la ingesta. Una posibilidad es que el notebook se escribiera en paralelo a un proceso de enriquecimiento externo que luego no se completó o que quedó fuera del pipeline definitivo. Lo que sí es evidente es que **el EDA nunca pudo haber funcionado completamente tal como estaba escrito**: desde el primer día que se ejecutó sobre el pipeline actual, NBI e IPM habrían llegado como 100 % nulos, desactivando seis de sus dieciséis secciones sin ningún error visible.

La corrección elimina esa dependencia huérfana y reemplaza NBI/IPM por `indicador_inversion_per_capita`, un indicador que sí produce el pipeline y que permite análisis de equidad territorial coherentes con los datos disponibles.

---

## 1. Estado anterior del EDA — Por qué no funcionaba

### 1.1 Archivos referenciados que no existían

El notebook cargaba tres fuentes de datos. Una funcionaba; dos no existían en el repositorio:

| Variable en el código | Ruta esperada | ¿Existe? | Impacto |
|---|---|---|---|
| `MART_PATH` | `data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet` | ✅ Sí | Ninguno |
| `SPRINT2_PATH` | `data/cruce_secop_dane_sprint2.parquet` | ❌ No | NBI e IPM → 100 % nulos |
| `ETNIA_PATH` | `data/etnia_checkpoint.parquet` | ❌ No | Etnia → 100 % nula |

Estos dos archivos eran checkpoints intermedios generados por un pipeline anterior (diseño "Sprint 2") que fue reemplazado por la arquitectura Medallion (Bronze → Silver → Gold). Al migrar, los archivos no fueron recreados ni eliminados del código del EDA.

### 1.2 Consecuencias en el notebook

Debido a que el notebook cargaba `SPRINT2_PATH` y `ETNIA_PATH` dentro de bloques `try/except`, no lanzaba errores al ejecutarse: simplemente imprimía advertencias y seguía. Pero las columnas clave llegaban todas como `NaN`:

```
ADVERTENCIA: No se pudo cargar Sprint2
ADVERTENCIA: No se pudo cargar Etnia

Nulos en variables clave:
  nbi_pct:   7,854 (100.0 %)
  ipm_total: 7,854 (100.0 %)
```

Esto causaba que **6 de las 16 secciones** del EDA quedaran silenciosamente desactivadas por sus propios guards de seguridad (`if not df_mun[COL_NBI].isna().all()`):

| Sección | Título original | Estado |
|---|---|---|
| 4 | Distribución de vulnerabilidad social (NBI e IPM) | Desactivada |
| 7 | Relación inversión–vulnerabilidad (NBI vs log Monto) | Desactivada |
| 9 | Cuadrantes de abandono relativo por año | Desactivada |
| 10 | Municipios críticos — Alta pobreza, cero contratos | Desactivada |
| 11 | Ticket promedio por cuartil de NBI y año | Desactivada |
| 13 | Alta vulnerabilidad vs. inversión recibida | Desactivada |

El EDA aparentaba ejecutarse correctamente, pero producía menos de dos tercios del análisis previsto.

### 1.3 Por qué `cruce_secop_dane_sprint2.parquet` ya no existe

El archivo contenía NBI (Necesidades Básicas Insatisfechas) e IPM (Índice de Pobreza Multidimensional) a nivel municipal, cruzados con SECOP. Era la salida de un proceso de integración ad hoc. Con la migración al pipeline Medallion, ese proceso fue eliminado. La capa Silver actual de CNPV (`silver_cnpv_agregado.parquet`) solo produce conteo de población, no indicadores de pobreza:

```python
# src/transformacion/silver/cleaners/clean_cnpv.py (línea 76)
dfs.append(df_part[["divipola_key"]])  # solo columna geográfica
```

Para recalcular NBI/IPM se requeriría un cruce complejo entre `cnpv_1viv_raw` (materiales/servicios de vivienda), `cnpv_2hog_raw` (hacinamiento) y `cnpv_5per_raw` (asistencia escolar), que aún no está implementado en el pipeline.

### 1.4 Estado de EDA_Express.ipynb

Este notebook es **completamente inoperativo**. Referencia 10 archivos Excel de un modelo de estrella antiguo que no existe en el repositorio:

```python
archivos = {
    "categoria":    "D_Categoria.xlsx",   # no existe
    "entidad":      "D_Entidad.xlsx",      # no existe
    "modalidad":    "D_Modalidad.xlsx",    # no existe
    "proveedor":    "D_Proveedor.xlsx",    # no existe
    "tiempo":       "D_Tiempo.xlsx",       # no existe
    "tipocontrato": "D_TipoContrato.xlsx", # no existe
    "ubientidad":   "D_UbiEntidad.xlsx",   # no existe
    "ubiproveedor": "D_UbiProveedor.xlsx", # no existe
    "fact_1":       "F_Proceso_parte1.xlsx", # no existe
    "fact_2":       "F_Proceso_parte2.xlsx", # no existe
}
```

Corresponde a la arquitectura de datos más antigua del proyecto (antes del pipeline Medallion). No se corrigió en esta iteración; está pendiente reescribirlo o eliminarlo.

---

## 2. Corrección aplicada al EDA principal

La corrección se realizó en dos fases.

### 2.1 Fase 1 — Actualización de fuentes de datos

Se actualizaron las celdas de configuración y carga (`cell-0003` y `cell-0005`):

**Antes:**
```python
MART_PATH    = ROOT / 'data' / 'gold' / 'marts' / 'latest' / 'mart_...parquet'
SPRINT2_PATH = ROOT / 'data' / 'cruce_secop_dane_sprint2.parquet'   # no existe
ETNIA_PATH   = ROOT / 'data' / 'etnia_checkpoint.parquet'           # no existe
```

**Después:**
```python
MART_PATH      = ROOT / 'data' / 'gold' / 'marts' / 'latest' / 'mart_...parquet'
CNPV_5PER_PATH = ROOT / 'data' / 'bronze' / 'cnpv' / 'cnpv_5per_raw.parquet'
```

**Etnia:** ahora se calcula on-the-fly desde el bronze CNPV usando la columna `PA1_GRP_ETNIC` (lectura columnar de 3 columnas sobre el archivo de 2.4 GB — aproximadamente 30 segundos). Los valores 1 (Indígena) y 5 (Afrodescendiente) se agregan por municipio para producir `etnia_indigena_pct` y `etnia_afro_pct`.

**NBI / IPM:** se declara un DataFrame vacío con las columnas correctas (`nbi_pct`, `miseria_pct`, `ipm_total`) para que los guards de las secciones 4, 7, 9, 10, 11, 13 detecten los datos como ausentes y puedan reactivarse con la nueva variable (ver Fase 2).

### 2.2 Fase 2 — Plan B: reemplazo de NBI por inversión per cápita

Dado que NBI/IPM no están disponibles en el pipeline actual y agregar nuevas bases de datos no era una opción, se optó por usar `indicador_inversion_per_capita` (ya disponible en el Gold Mart) como proxy de equidad territorial.

**Fundamento metodológico:** un municipio con baja inversión per cápita recibe proporcionalmente menos recursos públicos en relación a su población, lo cual es una aproximación operativa válida —aunque no equivalente— a una medida de necesidad insatisfecha.

Las 6 secciones desactivadas se reescribieron completas:

#### Sección 4 — Distribución de la inversión per cápita por año
- **Antes:** boxplots de NBI e IPM por año (inoperativo).
- **Después:** boxplots de `indicador_inversion_per_capita` por año + histogramas superpuestos en escala log10. Permite ver cómo se distribuye la inversión por persona en cada corte anual y si la dispersión aumenta o disminuye.

#### Sección 7 — Inversión per cápita vs tamaño poblacional
- **Antes:** scatter NBI vs log(monto) por año (inoperativo).
- **Después:** scatter log10(población proyectada) vs inversión per cápita por año, con tendencia lineal y correlación de Pearson. Responde si los municipios grandes reciben más o menos inversión por habitante.

#### Sección 9 — Cuadrantes de inversión territorial
- **Antes:** cuadrantes NBI-monto, cuadrante rojo = alto NBI + bajo monto (inoperativo).
- **Después:** cuadrantes IPC-monto en escala log-log. Cuadrante rojo = IPC ≤ mediana Y monto ≤ mediana. Identifica municipios con poco recurso tanto en términos absolutos como per cápita.

#### Sección 10 — Municipios críticos
- **Antes:** municipios con NBI > P75 y cero contratos (inoperativo).
- **Después:** municipios con IPC ≤ P25 y cero contratos. Lista los más poblados sin ningún contrato adjudicado y con la inversión per cápita más baja del año.

#### Sección 11 — Ticket promedio por cuartil
- **Antes:** ticket promedio agrupado por cuartil de NBI (inoperativo).
- **Después:** ticket promedio agrupado por cuartil de `indicador_inversion_per_capita`. Analiza si los municipios con más inversión per cápita tienden a tener contratos de mayor valor unitario.

#### Sección 13 — Concentración del monto
- **Antes:** % del monto total que va a municipios con alta vulnerabilidad (NBI ≥ mediana) (inoperativo).
- **Después:** % del monto total que va a municipios con baja IPC (≤ mediana). Responde si la mitad más rezagada en inversión per cápita recibe más o menos de la mitad del monto total.

---

## 3. Estado final del notebook

Tras la corrección, el EDA tiene **16 secciones** todas activas y funcionales:

| Sección | Contenido | Fuente de datos |
|---|---|---|
| 0 | Configuración | — |
| 1 | Carga e inspección inicial | Gold Mart + CNPV bronze |
| 2 | Evolución temporal de la contratación 2018–2024 | Gold Mart |
| 3 | Distribución del monto por año (histogramas log) | Gold Mart |
| 4 | Distribución de la inversión per cápita por año | Gold Mart |
| 5 | Concentración — Top 15 municipios por año | Gold Mart |
| 6 | Coeficiente de Gini | Gold Mart |
| 7 | IPC vs tamaño poblacional (scatter + correlación) | Gold Mart |
| 8 | Análisis por departamento y región geográfica | Gold Mart |
| 9 | Cuadrantes de inversión territorial (IPC × monto) | Gold Mart |
| 10 | Municipios críticos (IPC ≤ P25 y 0 contratos) | Gold Mart |
| 11 | Ticket promedio por cuartil de IPC | Gold Mart |
| 12 | Matrices de correlación anuales | Gold Mart + CNPV bronze |
| 13 | % del monto hacia municipios de baja IPC | Gold Mart |
| 14 | Micronegocios y Economía Popular (EMICRON) | Gold Mart |
| 15 | Contexto histórico — pandemia y ciclos electorales | Gold Mart |
| 16 | Resumen ejecutivo | Gold Mart |

### Fuentes de datos activas

| Fuente | Ruta | Uso |
|---|---|---|
| Gold Mart | `data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet` | Fuente principal (SECOP + población + micronegocios) |
| CNPV bronze personas | `data/bronze/cnpv/cnpv_5per_raw.parquet` | Etnia por municipio (`PA1_GRP_ETNIC`) |

### Limitaciones conocidas

- **NBI / IPM** siguen sin estar disponibles. Las secciones 4, 7, 9, 10, 11 y 13 usan IPC como proxy operativo, no como indicador de pobreza. Si en el futuro se implementa el cálculo de NBI en la capa silver, basta con actualizar `SPRINT2_PATH` y restaurar `COL_NBI` en esas secciones.
- **EDA_Express.ipynb** permanece inoperativo. Requiere reescritura completa apuntando al Gold Mart.
- La carga de etnia (~30 s) puede optimizarse incorporando `etnia_indigena_pct` y `etnia_afro_pct` directamente al Gold Mart en `src/transformacion/gold/build_mart.py`.
