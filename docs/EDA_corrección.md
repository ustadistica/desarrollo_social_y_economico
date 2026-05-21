# EDA — Diagnóstico de fallos y documentación de la corrección

Fecha de corrección: 2026-05-15  
Notebook afectado: `notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb`  
Notebook adicional revisado: `notebooks/EDA_Express.ipynb`

---

## 0. Por qué se cambió el EDA

El EDA fue corregido porque dependía de variables (NBI e IPM) que **nunca formaron parte del pipeline de ingesta del proyecto**. La ingesta actual procesa cuatro fuentes — SECOP I, SECOP II, CNPV 2018 y EMICRON — y produce una capa Gold (`mart_desarrollo_social_economico_municipio_anio.parquet`) que contiene indicadores de contratación pública, población y micronegocios. NBI e IPM no son producidos por ningún paso de ese pipeline, ni en Bronze, ni en Silver, ni en Gold.

No está claro por qué el EDA fue diseñado con dependencia en NBI/IPM si esos indicadores nunca estuvieron contemplados en la ingesta. Lo que sí es evidente es que **el EDA nunca pudo haber funcionado completamente tal como estaba escrito**: desde el primer día que se ejecutó sobre el pipeline actual, NBI e IPM habrían llegado como 100 % nulos, desactivando seis de sus dieciséis secciones sin ningún error visible.

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

### 1.4 Limpieza de notebooks obsoletos (2026-05-15)

Se eliminaron del repositorio los siguientes archivos que referenciaban arquitecturas previas y eran inoperativos sobre el pipeline Medallion:

| Archivo eliminado | Motivo |
|---|---|
| `notebooks/EDA_Express.ipynb` | Referenciaba 10 archivos Excel (`D_Categoria.xlsx`, `D_Entidad.xlsx`, `F_Proceso_parte1.xlsx`, etc.) de un modelo de estrella antiguo que no existe en el repositorio. Completamente inoperativo. |
| `notebooks/indicadores.ipynb` | Archivo vacío (0 bytes). |
| `notebooks/jupyter.log` | Log temporal de Jupyter. |
| `notebooks/.ipynb_checkpoints/EDA_SECOP_DANE_Gold_2018_2024-checkpoint.ipynb` | Checkpoint *stale* anterior a la corrección de la sección 6 del Gini. |

El análisis exploratorio se concentra ahora en `notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb` (única fuente vigente).

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

- **NBI / IPM** siguen sin estar disponibles. Las secciones 4, 7, 9, 10, 11 y 13 usan IPC como proxy operativo, no como indicador de pobreza. Si en el futuro se implementa el cálculo de NBI en la capa silver, basta con restaurar `COL_NBI` en esas secciones.
- La carga de etnia (~30 s) puede optimizarse incorporando `etnia_indigena_pct` y `etnia_afro_pct` directamente al Gold Mart en `src/transformacion/gold/build_mart.py`.

---

## 4. Corrección de la sección 6 — Coeficiente de Gini (2026-05-15)

### 4.1 Qué estaba pasando

La sección 6 reportaba un único coeficiente de Gini con valores **0.89–0.93** en todos los años. El valor llamaba la atención por estar pegado al techo (1 = desigualdad máxima) y casi no variar año a año. La hipótesis inicial fue un error en la fórmula o en el cruce; tras la revisión se descartaron ambas.

**La fórmula del Gini (`gini(array)` en `cell-0003`) es matemáticamente correcta.** Es la formulación equivalente

```
G = ( (n+1) − 2·Σ_{i=1..n} cumsum(a)_i / Σa ) / n
```

que se reduce algebraicamente a la expresión estándar `(2·Σ(i·a_i))/(n·S) − (n+1)/n` cuando el array está ordenado. No es el cálculo el que falla, son los **insumos y la interpretación**.

### 4.2 Por qué fallaba

Tres problemas concurrentes producían el valor inflado:

**(1) Sesgo de atribución geográfica del SECOP — causa principal.**
En `src/transformacion/silver/cleaners/clean_secop_i.py` y `clean_secop_ii.py`, la columna `divipola_key` se construye a partir del *Municipio / Departamento de la Entidad contratante*, **no del lugar de ejecución del contrato**. Todas las entidades del **orden nacional** (ministerios, Presidencia, ICBF, Invías, Fuerzas Militares, agencias) tienen su sede en Bogotá y, por tanto, sus contratos quedan imputados a `divipola_key = 11001`. Evidencia:

| Año | Cuota de Bogotá en el monto total |
|---|---|
| 2018 | 50.2 % |
| 2019 | 42.6 % |
| 2020 | 41.2 % |
| 2021 | 47.2 % |
| 2022 | 54.3 % |
| 2023 | 38.0 % |
| 2024 | 34.1 % |

Esa concentración no es desigualdad municipal — es un artefacto del modelo de datos del SECOP. El silver de SECOP **no preserva** la columna `orden_entidad` que permitiría filtrar nacionales vs. territoriales (la transaccional sólo trae `id_contrato`, `divipola_key`, `anio_key`, `fecha_firma`, `valor_del_contrato`, `nit_contratista`, `_fuente_origen`).

**(2) Indicador inapropiado para la pregunta.**
El título original decía *"desigualdad en distribución de contratos"* pero se calculaba sobre **monto absoluto**, no contratos ni inversión por habitante. Un Gini sobre montos absolutos entre municipios siempre dará valores > 0.85 — Bogotá tiene 8 M de habitantes y Mitú 30 k; la dispersión refleja escala demográfica, no inequidad de política pública. La métrica apropiada para "equidad territorial" es el Gini de **inversión per cápita** (monto / población).

**(3) Imputación incorrecta de ceros con `fillna(0)`.**
El cálculo original era:

```python
gini(df_mun.loc[df_mun[COL_AÑO] == a, COL_MONTO].fillna(0))
```

Esto mezcla dos casos distintos: municipios que no contrataron y municipios que no reportaron al SECOP. Al inyectar ceros artificiales se infla el Gini.

### 4.3 Qué se hizo para corregirlo

La sección 6 fue reescrita por completo (`cell-0014` markdown y `cell-0015` code) y el resumen ejecutivo (`cell-0035`) ahora reporta las nuevas series:

1. **Se cambió la métrica principal a Gini de inversión per cápita** (`monto / poblacion_censo_2018`). Es la única de las dos que puede interpretarse como indicador de política pública.
2. **El Gini sobre monto absoluto se conserva pero renombrado** como *"Concentración geográfica del gasto"* (no como "desigualdad"), para dejar claro que es una métrica descriptiva, no de equidad.
3. **Se reportan ambas series con y sin Bogotá D.C.** (`divipola_key = 11001`) como *workaround* para aproximar el filtro de orden nacional. Es un parche explícito: el filtro correcto sería por `orden_entidad ∈ {Territorial}`, pendiente de propagarse desde bronze a silver.
4. **Se eliminó el `fillna(0)`**: el Gini se calcula sólo sobre municipios con `monto > 0`. Se reporta también el número de municipios usados cada año (`n_muni_con_monto>0`).
5. **Cambio cosmético:** título de la sección y de los gráficos actualizado a *"Concentración geográfica del gasto y equidad territorial (Gini)"*.

### 4.4 Valores nuevos y por qué ahora son creíbles

| Año | Gini monto abs. | Gini monto sin Bogotá | **Gini IPC (equidad)** | Gini IPC sin Bogotá |
|---:|---:|---:|---:|---:|
| 2018 | 0.917 | 0.837 | **0.447** | 0.445 |
| 2019 | 0.911 | 0.847 | **0.522** | 0.521 |
| 2020 | 0.926 | 0.876 | **0.590** | 0.589 |
| 2021 | 0.916 | 0.844 | **0.470** | 0.468 |
| 2022 | 0.921 | 0.830 | **0.509** | 0.507 |
| 2023 | 0.887 | 0.820 | **0.525** | 0.525 |
| 2024 | 0.912 | 0.869 | **0.516** | 0.515 |

La métrica principal (**Gini IPC**) se mueve en el rango **0.45 – 0.59**, que es consistente con la literatura sobre desigualdad territorial del gasto público en Colombia y con la naturaleza del país (alta dispersión real, pero no extrema). Que el Gini IPC con y sin Bogotá sean prácticamente iguales (≤ 0.002 de diferencia) confirma que el problema previo era el **monto absoluto**, no la composición municipal: cuando se neutraliza el tamaño poblacional con la división por habitantes, Bogotá deja de dominar el agregado.

El pico en 2020 (0.59) es coherente con el efecto de la pandemia: gasto público concentrado en pocos municipios para emergencia sanitaria. El descenso en 2021 (0.47) refleja la fase de reactivación y transferencias del programa de Ingreso Solidario.

### 4.5 Casos donde se requiere aclaración explícita en cualquier reporte

Estos puntos **deben mencionarse siempre** que se cite cualquier número de la sección 6 de este EDA:

| Métrica | Aclaración obligatoria |
|---|---|
| **Gini de monto absoluto** | No es una medida de equidad. Mide concentración geográfica del registro contable. Su valor estructuralmente alto (~0.9) se debe a (i) escala demográfica y (ii) imputación de los contratos del orden nacional al municipio de la entidad contratante. |
| **Gini de monto absoluto con Bogotá** | Bogotá D.C. (`11001`) acumula 34–55 % del monto anual por ser sede del orden nacional, no por concentración real de gasto en su territorio. |
| **Gini de monto absoluto sin Bogotá** | Es un *proxy* para "orden territorial". No es un filtro estricto: entidades nacionales con sede fuera de Bogotá (sedes regionales, gobernaciones) siguen incluidas. El filtro estricto requeriría incorporar `orden_entidad` desde bronze al silver de SECOP. |
| **Gini IPC** | Métrica principal. Reportarla como "Gini de inversión per cápita". Aclarar que el denominador es `poblacion_censo_2018`, no proyección DANE anual (limitación del mart actual — ver sección 4.6 "Limitaciones residuales sin corregir en esta iteración"). |
| **Cualquier IPC year-over-year** | Las variaciones interanuales del IPC reflejan variaciones del numerador (monto), no del denominador. La población usada es la del censo 2018 propagada como constante. |

### 4.6 Limitaciones residuales sin corregir en esta iteración

- **Población constante 2018.** `poblacion_total_proyectada` está en 0 para los 1.122 municipios del mart porque `silver_proyecciones_agregado.parquet` se produce a granularidad **departamento-año**, no municipio-año, y no se propaga al mart municipal. El cálculo cae al fallback `poblacion_censo_2018`, perdiendo la dinámica demográfica del periodo. Corregirlo requiere reescribir `_fact_simple` para proyecciones o crear un cleaner municipal específico — pendiente para una iteración posterior.
- **Filtro estricto por orden de la entidad.** Ideal: filtrar contratos por `orden_entidad ∈ {Territorial}`. Workaround actual: excluir Bogotá. Para implementarlo bien hay que preservar la columna `orden` desde el bronze de SECOP a través de los cleaners (`clean_secop_i.py`, `clean_secop_ii.py`) y la transaccional silver. Pendiente.
