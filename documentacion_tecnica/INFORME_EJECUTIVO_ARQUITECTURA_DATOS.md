# 🏛️ Informe Ejecutivo de Arquitectura de Datos: Sinergia Socioeconómica

Este documento integra y detalla el esfuerzo transversal realizado para estructurar y empaquetar el repositorio de análisis gubernamental y socioeconómico. Su objetivo es listar proactivamente todo el ecosistema programado e implementado para alcanzar una analítica de grado Senior.

---

## 1. Fundamentos: Arquitectura Medallion Construida

Se estructuró integralmente el paradigma Medallion (Bronze ➡️ Silver ➡️ Gold) apoyándose en motores *Out-of-core* (PyArrow y DuckDB) para gobernar un volumen de datos que tradicionalmente saturaba la infraestructura local.

### 🥉 Capa Bronze (Persistencia, Linaje e Inmutabilidad)
**Propósito:** Ingesta masiva cruda, sin transformaciones numéricas, garantizando linaje estricto.
*   **Orquestador:** Se estructuró `run_bronze.py` apoyado por un validador orientado al esquema (`bronze_validator.py`).
*   **Decisiones de Diseño Mapeadas:** 
    *   Uso de Compresión en formato Parquet (Snappy) para optimizar IO.
    *   Generación de "Metadatos Mágicos": Toda tabla cuenta con auditoría obligatoria como `_ingestion_timestamp`, método de extracción, huella MD5 unívoca y versión atada.
    *   Flexibilidad Estructural Múltiple: Parsers adaptativos tanto para lectura dividida pesada (SECOP por chunks) como lectura difusa inter-anual tolerante de todos los encuches disparejos de EMICRON sin fracasar.
*   **Auditoría Física y Evidencia:** Capucha de generación automática `BRONZE_VALIDATION_REPORT.md` (Evalúa completitud y cardinalidad volumétrica real de la inyección).

### 🥈 Capa Silver (Homologación, Sanidad y Pre-Agregación Espacial)
**Propósito:** Purificación territorial estricta, engranaje de calendarios y aseguramiento del cruce mediante compresión distributiva.
*   **Orquestador:** Módulo maestro escalonado `run_silver.py`.
*   **Decisiones de Diseño Mapeadas:**
    *   **Identidad Geográfica Indestructible (`divipola_key`):** Truncamiento unificado estricto de identificadores departamentales y municipales (Ej: padding con ceros a la izquierda logrando homogeneidad total en la llave).
    *   **Identidad Temporal Categórica (`anio_key`):** Mapeo de fechas brutas y asimétricas a su representación vigencial estricta (Excluyendo proyecciones futuras irracionales, topando a `2025`).
    *   **Pre-Agregación Semántica:** Las extracciones fueron configuradas para *jamás inyectarse* en granularidades 1:N que promuevan sesgos. Todos los subconjuntos del DANE (CNPV, EMICRON) o compras del SECOP se consolidan internamente devolviendo métricas de grado sumatorio, conteos limpios y la absorción estadísticamente obligatoria del **Factor de Expansión (FEX_C)**.
*   **Auditoría Física y Evidencia:** Generación automática de `SILVER_DATA_QUALITY_REPORT.md` para monitorizar posibles vacíos en las PKs.

### 🥇 Capa Gold (Dimensionalidad Estricta y Visualización Orientada)
**Propósito:** Consolidación de Datamarts para consumo inmediato (zero-compute load) en BI o tableros de control.
*   **Orquestador y Estructura Constelación:** Construido enteramente bajo `run_gold.py`.
*   **Decisiones de Diseño Mapeadas:**
    *   **Construcción de Modelos de Hechos (Facts):** `fact_demografia`, `fact_contratacion` y `fact_micronegocios`.
    *   **Construcción Dimensional Fuerte (Dims):** Tablas de referencia puras `dim_territorio` y `dim_tiempo` con subsegmentación inteligente pre-incorporada (banderas booleanas marcando periodos de `pandemia` y periodos electorales, vitales para justificar picos de contratación municipal).
    *   **Consolidación OBT (One-Big-Table):** Motor de fusión modular que compila la espina vertebral (Left join) integrando en memoria y devolviendo la *Sinergia Socioeconómica Final* (`mart_desarrollo_social_economico_municipio_anio.parquet`). Esta posee el cálculo dinámico de todas las variables derivadas estratégicas como (`inversión_per_capita`, `densidad_micronegocios`).
*   **Auditoría Física y Evidencia:** Generación continua del test `GOLD_VALIDATION_REPORT.md` validando que en estricto rigor toda correlación quede encapsulada 1:1.

---

## 2. Orquestación, Empaquetado y UX Estructural

Se garantizó la portabilidad y la curva de aprendizaje logrando una modernización del stack.

1.  **Refactorización Empaquetada:** Cimentada y convertida a una librería formal resolviendo el histórico del espacio en carpetas antiguas.
2.  **`pyproject.toml`:** Aprovisionamiento claro y transparente garantizando resolución de dependencias como Setuptools, DuckDB y Pyarrow, instanciando la escalabilidad del ecosistema en cualquier S.O mediante `pip install -e .`.
3.  **`Makefile` Interactivo:** Creación de directivas terminales puras y estándar agnósticas (Ej. `make gold` o `make all`) reduciendo el comando CLI a trivialidades absolutas.
4.  **Flujos Seguros y Fallbacks (Graceful Degradation):** Para evitar crasheos fatales, si se omite un documento CSV crudo, todo el pipeline levanta un andamio de esquemas seguros y documentados de tal manera que ninguna capa posterior sufre bloqueos, haciendo del software una pared a prueba de colapsos para demostraciones en la nube o analistas apresurados.
5.  **`run_all.py`**: El mega orquestador *End-to-End* uniendo programáticamente las tres partes en un pipeline de orquestación final.

---

## 3. Resumen Documentativo del Proyecto (Repositorio Técnico)

Para democratizar e independizar a todos los actores del proyecto, deposité una inmensa base de conocimiento permanente ubicada en `/documentacion_tecnica/` y directorios base:

- 📖 **`README.md` (Main)**: Presentación front-end del paradigma entero de desarrollo. Desglose detallado sobre los requerimientos, cómo comenzar de ceros con la data e instalación inmediata.
- 📙 **`RUNBOOK.md`**: Protocolo de acción operativa, mapeo transversal en caso de contingencias, tabla general de soluciones contra problemas transaccionales con librerías o con dependencias.
- 📐 **`DISENO_MODELO_DATOS.md`**: Documento diagramado detallando en Mermaid la trazabilidad matricial completa y cada decisión de granularidad concebida entre DANE/Sincronización.
- 📘 **`README_BRONZE.md` y `README_SILVER.md` y `README_GOLD.md`**: Manifiestos independientes de cada estrato Medallion dictaminando textualmente y programáticamente el límite, responsabilidad y arquitectura impuesta (Desde la asimilación estricta de SECOP, re-estructuración DANE hasta las directrices de OBT).
- 📜 **`DICCIONARIO_GOLD.md`**: Catálogo descriptivo oficial y diccionario riguroso informando la pureza de cada métrica materializada (Hechos Aditivos / Modelos Derivados como Inversión per cápita) documentado específicamente para científicos de datos o ingenieros BI.
- 🧪 **`QA_FINAL.md`**: El dictamen y estado garantizado de QA estructural (Quality Assurance), con los sellos de validación certificando la integridad y la ausencia total de sesgos matriciales pre-entrega.
- 🔄 **`CHANGELOG_TECNICO.md`**: Historial técnico exhaustivo informando la evolución paralela de la madurez analítica desde su origen legacy hasta la producción escalable actual V1.0.

Todo el diseño relacional fue levantado a favor de proveer una integración y una experiencia impecable: robusto funcionalmente, puro estadísticamente y reproducible sistemáticamente. 🚀
