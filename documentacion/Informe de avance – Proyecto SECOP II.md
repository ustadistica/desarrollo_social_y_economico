# Informe de avance – Proyecto SECOP II

## 1. Contexto general del proyecto

El repositorio `desarrollo_social_y_economico` corresponde al proyecto del **Consultorio de Estadística y Ciencia de Datos** de la **Universidad Santo Tomás**, cuyo objetivo inicial era analizar la relación entre:

- La **distribución territorial de la contratación pública** registrada en **SECOP II**, y  
- Las **condiciones socioeconómicas** de la población a partir de los **microdatos de Personas 2018 del DANE**.

La **pregunta central planteada al inicio** fue:

> ¿En qué medida la contratación pública registrada en SECOP II contribuye a reducir las desigualdades socioeconómicas identificadas en los datos del DANE, y cómo se distribuyen los contratos respecto a la vulnerabilidad y características de la población en los territorios?

Sin embargo, conforme se avanzó en el trabajo, la idea de cruzar información de contratos públicos (montos, sectores, entidades, territorio) con indicadores socioeconómicos (pobreza, educación, empleo, desigualdad del ingreso) **no se alcanzó a implementar en esta fase**.

Por ello, la pregunta se **reestructuró** y se ajustó al alcance real del trabajo, centrado únicamente en SECOP II:

> **Nueva pregunta de trabajo:**  
> ¿Cómo se distribuye territorial y sectorialmente la contratación pública registrada en SECOP II y qué patrones de concentración y brechas entre entidades y territorios se identifican a partir del modelo estrella construido para la base de datos?

---

## 2. Procesos adelantados

### 2.1. Definición del entorno tecnológico y flujo de trabajo

En el `README` se documenta un **stack tecnológico claro**, basado en:

- **Python 3.12** con librerías de ciencia de datos:
  - `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `plotly`.
- Uso de **Jupyter Notebooks** para exploración, integración y modelado.
- Gestión de dependencias con **Poetry**, incluyendo:
  - Instrucciones de instalación.
  - Creación del entorno.
  - Registro del kernel para VS Code.

También se propone un **flujo de trabajo estándar**:

1. **Ingesta y limpieza de datos** (SECOP II).
2. **Integración territorial** de las fuentes (dentro de SECOP II).
3. **Análisis exploratorio**, desigualdad y modelos estadísticos básicos.
4. **Construcción de resultados** (tablas, figuras, mapas).

Esto deja el proyecto con una **ruta de trabajo bien definida** para cualquier integrante del equipo.

---

### 2.2. Gestión y descarga de datos

Se ha avanzado en la **automatización de la descarga y almacenamiento de datos de SECOP II**:

- Uso de la **API SODA (Socrata)** y descargas en formato **CSV** desde Datos Abiertos Colombia.
- Almacenamiento de los datos en:
  - Archivos **Parquet**, y
  - Una base **SQLite**, organizada en una carpeta de Google Drive dedicada al proyecto,
    con la idea de permitir **actualizaciones periódicas** (por fecha de publicación).

Esto muestra que, como equipo, no solo se descargaron los datos, sino que se dejaron **lineamientos de uso estadístico responsable** y una base técnica para mantener los datos actualizados.

---

### 2.3. Diseño metodológico y unidades de análisis

El diseño metodológico se orienta a **describir y analizar** la **distribución territorial y sectorial** de la contratación pública registrada en SECOP II, a partir de la construcción de una **base analítica organizada en un modelo de datos tipo estrella** y su implementación en una base **SQLite**.

El enfoque es **cuantitativo, descriptivo y exploratorio**, con énfasis en la identificación de **patrones de concentración** y **brechas entre territorios y sectores** dentro del propio universo de contratos observados.

#### 2.3.1. Unidades de análisis

Las **unidades de análisis** son:

- **Contratos individuales** registrados en SECOP II  
  Constituyen la **tabla de hechos** del modelo estrella.

- **Territorios**  
  - Departamentos y, cuando la calidad de la información lo permite, municipios.  
  - Asociados a cada contrato mediante los campos de ubicación disponibles en SECOP II.

- **Entidades contratantes** (dimensión institucional)  
  - Permiten analizar la **concentración de la contratación** por tipo de entidad y nivel institucional.

- **Sectores y categorías de gasto** (dimensión temática)  
  - Derivadas de las clasificaciones presentes en SECOP II:
    - Sector.
    - Tipo de bien/servicio.
    - Modalidad de contratación, entre otras.

- **Tiempo**  
  - Año y, si es posible, mes de publicación o adjudicación.  
  - Permite observar la **evolución de la contratación** en el periodo cubierto por la base consolidada.

#### 2.3.2. Bloques metodológicos

Metodológicamente, el trabajo se estructura en **cuatro bloques**:

1. **Modelado y organización de datos**
   - Definición de la **tabla de hechos de contratos**:
     - Monto del contrato.
     - Fecha.
     - Estado.
     - Identificadores clave.
   - Construcción de **tablas de dimensiones** para:
     - Territorio.
     - Entidad.
     - Sector.
     - Tiempo.
   - Implementación del **modelo estrella** en una base de datos **SQLite**, a partir de los archivos descargados y depurados de SECOP II.

2. **Generación de indicadores agregados**
   - Cálculo de:
     - **Montos totales** y
     - **Número de contratos**
     por territorio, sector, entidad y año.
   - Obtención de **participaciones relativas**:
     - Porcentaje del monto total de contratación nacional que concentra cada territorio o sector.
   - Identificación de **territorios y entidades con mayor y menor volumen de contratación**.

3. **Análisis de concentración y brechas internas de la contratación**
   - Cálculo de indicadores de **concentración**:
     - Por ejemplo, proporción del monto acumulado en los principales territorios o entidades.
   - Comparación de territorios en función de:
     - Su **peso relativo** en el total de contratación.
     - Su **especialización sectorial** (sectores predominantes en cada territorio).
   - Identificación de **patrones de desigualdad interna** de la contratación:
     - Territorios muy favorecidos frente a otros con baja participación en el monto total contratado.

4. **Sistematización de resultados y elaboración de insumos para visualización**
   - Generación de **tablas y resúmenes** que puedan ser utilizados en informes y presentaciones:
     - Por ejemplo, ranking de departamentos por monto contratado.
   - Preparación de insumos para futuras **visualizaciones y tableros de control**.

---

### 2.4. Construcción del modelo estrella y base SQLite

A partir de los datos descargados y depurados de SECOP II se diseñó e implementó un **modelo de datos tipo estrella** para organizar la información de contratación pública en una estructura analítica que facilite consultas agregadas por **territorio, entidad, sector y tiempo**.

Este modelo se materializó en una base de datos **SQLite**, pensada como un **“mini data warehouse” de contratación**.

#### 2.4.1. Componentes del modelo

En términos lógicos, el modelo se organiza alrededor de una **tabla de hechos de contratos**, complementada por varias **tablas de dimensiones**:

- **Tabla de hechos `hecho_contrato`**  
  Contiene un registro por contrato (o por ítem relevante de contrato), incluyendo:
  - Identificador del contrato.
  - Monto del contrato (valor total).
  - Fechas clave (publicación, adjudicación, inicio, fin, cuando están disponibles).
  - Estado del contrato.
  - Claves foráneas hacia las dimensiones de territorio, entidad, sector/proceso y tiempo.

- **Dimensión de territorio `dim_territorio`**  
  Recoge la información geográfica asociada a los contratos:
  - Departamento y, cuando es posible, municipio.
  - Códigos estandarizados (por ejemplo, códigos DANE cuando la calidad del dato lo permite).  
  Esta dimensión permite construir **indicadores agregados por territorio** y comparar el **peso relativo de la contratación** entre diferentes regiones.

- **Dimensión de entidad `dim_entidad`**  
  Describe a la entidad contratante:
  - Nombre de la entidad.
  - Nivel (nacional, departamental, municipal, etc.).
  - Tipo de entidad (ministerio, establecimiento público, empresa industrial y comercial, etc.).  
  Esta dimensión facilita el análisis de **concentración de la contratación** por tipo y nivel institucional.

- **Dimensión de sector/proceso `dim_sector_proceso`**  
  Contiene la categorización temática y procedimental de los contratos:
  - Sector o categoría de gasto.
  - Modalidad de contratación.
  - Tipo de bien o servicio.  
  Esta dimensión permite explorar **qué sectores concentran mayores montos** y cómo se distribuyen las **modalidades de contratación**.

- **Dimensión de tiempo `dim_tiempo`**  
  Organiza la información temporal de los contratos:
  - Año, mes y día.
  - Posibles jerarquías (año → trimestre → mes).  
  Esta dimensión habilita la construcción de **series de tiempo simples** y la observación de **cambios en la contratación** a lo largo del periodo cubierto por los datos.

#### 2.4.2. Proceso técnico

El proceso técnico siguió, de forma general, los siguientes pasos:

1. **Extracción y normalización de SECOP II**
   - Descarga de los contratos mediante **API/CSV** y almacenamiento en formatos adecuados (por ejemplo, archivos **Parquet**).
   - Limpieza básica:
     - Estandarización de tipos de datos.
     - Manejo de valores faltantes.
     - Depuración de registros inconsistentes.

2. **Construcción de tablas de staging**
   - Creación de tablas intermedias donde se:
     - Normalizan nombres de entidades.
     - Estandarizan códigos territoriales.
     - Organizan categorías de sector.
   - Revisión de duplicados y definición de **llaves primarias**.

3. **Población del modelo estrella en SQLite**
   - Carga de las dimensiones:
     - `dim_territorio`
     - `dim_entidad`
     - `dim_sector_proceso`
     - `dim_tiempo`
   - Carga de la tabla de hechos `hecho_contrato`, asignando claves foráneas a cada contrato según su:
     - Territorio.
     - Entidad.
     - Sector.
     - Tiempo.
   - Verificación de **integridad referencial**:
     - Comprobación de que todas las claves foráneas tengan correspondencia en las dimensiones.

4. **Definición de vistas y consultas analíticas básicas**
   - Creación de consultas para obtener:
     - Montos agregados.
     - Número de contratos agregados.
     por territorio, sector, entidad y año.
   - Preparación de vistas que pueden ser consumidas desde:
     - Notebooks.
     - Herramientas de BI.

Con esta arquitectura, el proyecto logra transformar la **información cruda de SECOP II** en una **base analítica estructurada**, optimizada para responder preguntas sobre **distribución y concentración de la contratación pública** sin necesidad de re–procesar archivos planos cada vez.

---

## 3. Resultados y productos generados (foco SECOP II)

Aunque la pregunta original del proyecto incluía la integración con datos socioeconómicos externos, en esta fase el trabajo se concentró en **construir infraestructura y capacidades analíticas sobre SECOP II**.

Los principales resultados son:

### 3.1. Infraestructura de datos de contratación

- Un **modelo estrella conceptual y lógico** que organiza la contratación pública en torno a contratos (hechos) y sus dimensiones clave:
  - Territorio.
  - Entidad.
  - Sector.
  - Tiempo.

- Una **base de datos SQLite** que materializa este modelo y permite:
  - Consultas rápidas por:
    - Departamento.
    - Sector.
    - Entidad.
    - Año.
  - Exportación sencilla de **subconjuntos de datos** para análisis específicos:
    - Por ejemplo, solo un conjunto de departamentos o un periodo determinado.

### 3.2. Ordenamiento del trabajo en un repositorio reproducible

Se cuenta con un **repositorio en GitHub** que documenta:

- La **descripción general del proyecto** y la justificación del enfoque en contratación pública.
- El **stack tecnológico** (Python, Jupyter, Poetry) y las instrucciones para **reproducir el entorno**.
- Una **estructura tentativa de carpetas** para:
  - Datos.
  - Documentación.
  - Notebooks.  
  Esta estructura guía la organización futura del trabajo.

Además, se incluyen **documentos de apoyo**, como:

- El **Informe de Consultoría**.
- El texto de **“Desigualdades territoriales y contratación estatal”**.

Estos documentos sistematizan:

- La **motivación y relevancia** de estudiar la contratación pública desde una perspectiva territorial.
- Los **avances logrados** en la estructuración de SECOP II y las posibilidades que abre el modelo estrella.

### 3.3. Capacidad instalada para análisis posteriores

Como resultado del trabajo con SECOP II, el equipo deja instalada una **capacidad importante**:

- La base analítica permite, con relativamente poco esfuerzo adicional, construir:
  - **Rankings de departamentos** por monto de contratación.
  - **Comparaciones entre entidades** en términos de volumen contratado.
  - **Distribuciones sectoriales** de la contratación por territorio.

- El diseño **modular** del modelo estrella hace posible **incorporar nuevas fuentes de datos** (por ejemplo, indicadores socioeconómicos) en fases posteriores, sin necesidad de rediseñar todo el esquema.

---

## 4. Limitaciones y trabajo futuro

Pese a estos avances, el proyecto presenta **limitaciones importantes** que condicionan el alcance de las conclusiones.

### 4.1. Limitaciones

#### 4.1.1. No se integraron los microdatos del DANE

La principal limitación es que, por restricciones de tiempo y complejidad técnica, **no se llegó a efectuar el cruce** entre la base de contratación (SECOP II) y los indicadores socioeconómicos de **DANE Personas 2018**.

En consecuencia:

- No se puede afirmar empíricamente **cómo se relaciona la contratación** con:
  - Pobreza.
  - Desigualdad.
  - Vulnerabilidad de la población.
- La pregunta original sobre la **contribución de la contratación a la reducción de desigualdades territoriales** queda planteada, pero **no resuelta** en esta fase.

#### 4.1.2. Enfoque descriptivo interno a SECOP II

Los análisis posibles con la infraestructura actual se limitan a **comparaciones internas dentro de SECOP II**:

- Quién contrata más.
- Dónde se concentra el monto contratado.
- Qué sectores absorben mayor gasto, etc.

Estas comparaciones son **útiles**, pero:

- No permiten **conclusiones causales**.
- No permiten una evaluación completa de **equidad territorial**.

#### 4.1.3. Cobertura y calidad de los datos de SECOP II

SECOP II es una fuente administrativa con:

- Variaciones en **calidad de registro** entre entidades.
- Posibles diferencias en la forma de diligenciar campos de:
  - Territorio.
  - Sector.
  - Objeto del contrato.

Esto puede introducir **sesgos** en el análisis de concentración territorial o sectorial.

---

### 4.2. Trabajo futuro

A partir de lo logrado, se identifican varias **líneas de trabajo**:

#### 4.2.1. Integración con indicadores socioeconómicos (DANE y otras fuentes)

- Vincular los territorios de `dim_territorio` con bases oficiales de indicadores:
  - Pobreza.
  - Desigualdad.
  - Educación.
  - Salud, etc.
- Construir **indicadores conjuntos**, por ejemplo:
  - Monto contratado per cápita.
  - Contratación en territorios con alta pobreza.
  - Relación entre contratación y brechas territoriales.

#### 4.2.2. Profundización en análisis de concentración y desigualdad dentro de SECOP II

- Calcular medidas de **concentración**:
  - Índices tipo Pareto.
  - Participación acumulada de los principales territorios o entidades.
- Analizar la **especialización sectorial** de la contratación en cada territorio.

#### 4.2.3. Desarrollo de tableros de control y visualizaciones

- Conectar la base SQLite con herramientas de **BI** (por ejemplo, Power BI) para crear **dashboards interactivos**.
- Implementar **mapas y gráficos** que permitan a usuarios no técnicos explorar la **distribución territorial de la contratación**.

#### 4.2.4. Fortalecimiento de la documentación y automatización

- Incorporar al repositorio los **notebooks de exploración** y las **consultas principales**.
- Documentar **scripts de actualización periódica** de SECOP II para mantener la base analítica al día.

---
