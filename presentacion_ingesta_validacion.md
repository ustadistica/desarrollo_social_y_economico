# Presentación: Fase de Ingesta y Validación de Datos

---

## 1. Introducción y Objetivo Principal

**Proyecto:** Sinergia Socioeconómica entre el Territorio y el Gasto Público.

**Objetivo Inicial:** Construir un motor de datos escalable, automatizable y auditable que permita cruzar la realidad demográfica de Colombia con la ejecución del gasto público, superando las limitaciones de desempeño y heterogeneidad de las fuentes de datos (DANE, SECOP, TerriData).

---

## 2. Nuestra Arquitectura: El Modelo Medallón

Para la construcción de este pipeline de datos, descartamos desde el inicio los tradicionales procesos ETL monolíticos y adoptamos lo que se conoce como la **Arquitectura Medallón**.

El motivo principal de esta decisión radica en que nuestra fase de ingesta depende de múltiples APIs públicas e institucionales que muchas veces son inestables, presentan tiempos de inactividad o imponen límites estrictos de velocidad de descarga (Rate Limits). En un diseño monolítico tradicional, un fallo técnico durante la última etapa de limpieza o transformación nos habría forzado a interrumpir todo y empezar a descargar gigabytes de información nuevamente desde cero. 

Al implementar el enfoque Medallón, garantizamos que el proceso esté completamente desacoplado y modulado, obteniendo lo que llamamos **idempotencia** o reprocesabilidad aislada:
*   **Capa Bronce (Raw):** Extraemos y almacenamos los datos totalmente crudos, idénticos a como los entrega la fuente del gobierno. Son inmutables.
*   **Capa Plata (Cleaned):** Tomamos esos datos inmutables y realizamos la estandarización masiva: limpieza Unicode, corrección de variables, casteos e imputaciones.
*   **Capa Oro (Curated):** Finalmente, estructuramos y subimos los datos limpios en un Modelo de Estrella (Hechos y Dimensiones) configurando los Datamarts listos para reportes analíticos de Business Intelligence (BI).

---

## 3. Decisiones Técnicas: Stack y Formatos de Almacenamiento

El núcleo de todo el procesamiento analítico se cimentó sobre tres decisiones tecnológicas fundamentales: **Python** (como orquestador), **PySpark** (motor analítico de grandes volúmenes) y **Parquet** (como formato de Data Lake temporal y final).

Cualquier proyecto básico suele iniciar descargando inmensas hojas de Excel o archivos CSV, pero cambiamos ese paradigma por verdaderas herramientas de ingeniería de datos para mitigar tres fallos masivos en potencia:

1.  **Parquet vs CSV:** En lugar de manipular archivos de texto estructurado como el Censo de Población del DANE (que pesa más de 6GB de manera individual), convertimos la captura a formato columnar `.parquet`. Esto aplica compresión masiva (achicando la base casi al 75%) y permite lecturas selectivas inmediatas de columnas, volviéndose ideal para trabajar con Big Data.
2.  **PySpark vs Pandas:** Lidiar con más de 50 millones de registros poblacionales usando la popular librería `Pandas` en un entorno local nos garantizaba colapsos y asfixias por insuficiencia de memoria RAM ("Out-of-Memory"). A su vez, basar nuestro sistema en motores temporales limitaba nuestra capacidad de crecer hacia clústeres reales. Por eso migramos nuestra arquitectura a **PySpark**; el estándar de la industria en computación distribuida, que nos permite procesar transformaciones masivas de manera "Out-of-Core" (fuera de memoria) localmente, y abre la puerta de escalar inmediatamente a ecosistemas multi-nodo en la nube (como Databricks o AWS EMR) para cargas de nivel corporativo en el futuro.

---

## 4. Evolución de la Ingesta (Capa Bronce)

Durante el acoplamiento a la capa Bronce, estandarizamos no solo *qué* datos pedir sino el *cómo* pedirlos al DANE, al SECOP II o a los sistemas API de TerriData. No es recomendable hacer extracciones de fuerza bruta en ecosistemas vulnerables.

Para la ingesta masiva de los contratos de **SECOP II**, implementamos un diseño de extracción por lotes iterados (batches) que incorpora identificadores autorizados por el gobierno (*App Tokens* de la API Socrata SODA), blindándonos así contra bloqueos por velocidad de saturación.

A nivel de persistencia de datos, implementamos que todos los insumos vírgenes (Bronze) sean obligatoriamente versionados en carpetas con sellos temporales (`ingestion_date`). Esta fue una medida preventiva para protegernos empíricamente de **modificaciones retrospectivas invisibles** o "Shadow Updates" por parte del gobierno, lo cual nos confiere un control de trazabilidad estadístico férreo del estado histórico y la fecha de la base procesada.

---

## 5. Agrupación y Estandarización Total (Capa Plata)

En la transición a la capa Plata, mitigamos quirúrgicamente los dos grandes problemas históricos de los análisis en ecosistemas nacionales: **las discrepancias toponímicas** y **las imprecisiones monetarias flotantes**.

*   **Identificador Geográfico Único y Universal:** Fue evidente que instituciones diferentes rotulan los municipios a discreción propia (p. ej. "Bogotá D.C.", "BOGOTA", "SANTÁFE DE BOGOTÁ"). Utilizar texto o nombres regionales para unificar y unir tablas (Joins) se traduce en la pérdida de la mitad de los registros en un análisis real a nivel estatal. Como medida de contención y solución absoluta, impusimos la normalización y emparejamiento usando únicamente el código **DIVIPOLA** (5 dígitos).
*   **Precisión Contable Absoluta:** Ajustamos todo monto presupuestal desde formatos flotantes imprecisos y comunes de la CPU (`float64`) hacia el casting de precisión estricto (`Decimal128`). Cuando la investigación cruza la ejecución presupuestal de billones de pesos agregados a nivel país, las discrepancias por puntos flotantes dejan de ser residuales y se vuelven problemas de cuadre.
*   **Reglamento del Secreto Estadístico:** Protegimos los factores de individualización corporativos realizando enmascaramientos vía Funciones Hash sobre identificaciones (NITs) en favor de proteger la moral investigativa del modelo de ciencia de datos a distribuir.

---

## 6. Generación Analítica Estructurada (Capa Oro)

Terminada la higiene y depuración, es justamente en esta tercera etapa donde materializamos la unión entre el mundo económico del Contratista, la Población Territorial del DANE y los polígonos del Territorio, modelando conceptualmente nuestra base como un flamante **Esquema de Estrella**.

Rechazamos aprovisionar o instalar gestores robustos y tradicionales como PostgreSQL por costos en la nube, latencia, y las dependencias manuales. En vez de ello, integramos de manera centralizada el Modelo Dimensional (Tablas de Hechos y Dimensiones compartidas) usando PySpark para persistirlo como un sistema de Datamarts altamente optimizado en formato nativo **Parquet Particionado** (`modelo_estrella_pyspark/`).

Este enfoque es de grado analítico directo: el observatorio pesa menos, es altamente transferible, y sus vistas internas en lenguaje SQL agilizan métricas tales como la Autocorrelación Espacial Económica para el resto de equipos de Inteligencia de Negocios (BI).

---

## 7. Automatización Predictiva y Orquestación Lineal

Finalmente, la entrega técnica del código no podía culminar resintiendo lo anterior con cargas de operaciones manuales.

Acoples, dependencias rotas, y ejecuciones a destiempo en scripts desarticulados fueron eliminados, diseñando un sistema orquestador automatizado ([orchestrator.py](file:///c:/Users/user/Documents/001%20Uni/Octavo/CONSULTORIA/desarrolo%20eco/desarrollo_social_y_economico-main%20%282%29/desarrollo_social_y_economico-main/ingesta%20y%20validacion/orchestrator.py) y [run_pipeline.py](file:///c:/Users/user/Documents/001%20Uni/Octavo/CONSULTORIA/desarrolo%20eco/desarrollo_social_y_economico-main%20%282%29/desarrollo_social_y_economico-main/ingesta%20y%20validacion/run_pipeline.py)). La innovación acá permite que tras accionar un único comando parametrizado lineal (`--all`), el algoritmo decide, en cadena preestablecida de validaciones de calidad, las tareas de limpieza, recolección en Bronce, depuración analítica de null limits en Plata, y la construcción relacional analítica de matrices en nuestro Gold, reportando cada eventualidad de anomalía si llega a presentarse.

Elevamos una prueba funcional a todo un pipeline de ingeniería productivo estandarizado de la industria para nuestra aplicación investigativa de Big Data.
