---
title: "Socioeconomico"
author: "LIZETH DANIELA VILLAMIL GIL"
date: "2026-03-12"
output: html_document
---

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE)
```
# Propuesta de Proyecto: Sinergia Socioeconómica entre el Territorio y el Gasto Público

## 1. Introducción
Este proyecto propone un análisis técnico y objetivo sobre la relación entre la realidad social de Colombia y la ejecución presupuestal del Estado. El objetivo es determinar si la contratación pública actúa como un motor de desarrollo coherente con las necesidades identificadas por las autoridades estadísticas.

## 2. Pilares de Información
Para este análisis, se utilizarán tres fuentes de datos fundamentales:

* **DANE (Censo Nacional de Población y Vivienda):** Provee la base demográfica, el Índice de Pobreza Multidimensional (IPM) y el déficit habitacional.
* **CENU (Censo Económico Nacional Urbano):** La fuente más reciente (2024-2025) que mapea el tejido productivo, los micronegocios y la "Economía Popular".
* **SECOP II:** Plataforma transaccional de la Agencia Nacional de Contratación Pública que permite rastrear el flujo de dinero, los perfiles de contratistas y las modalidades de selección.

---

## 3. Preguntas de Investigación 
Un análisis socioeconómico de alto nivel requiere preguntas que crucen ambas realidades:

1.  **¿Capacidad o Exclusión?**: ¿Existe una correlación entre la baja densidad de empresas locales (según el CENU) y la alta tasa de contratos adjudicados a empresas de otras ciudades en el SECOP II?
2.  **Formalización y Estado**: ¿Qué porcentaje de los micronegocios identificados por el DANE han logrado transitar a ser proveedores del Estado mediante procesos de mínima cuantía?
3.  **Vocación Territorial**: En municipios con vocación agrícola o industrial según el Censo, ¿el gasto público en SECOP II está orientado a fortalecer esos sectores o se desvía hacia servicios administrativos?
4.  **Impacto en Pobreza**: ¿En los municipios donde el DANE reporta un aumento en las Necesidades Básicas Insatisfechas (NBI), se observa un incremento en la contratación de infraestructura social o servicios básicos?

---

## 4. Fuentes y Bases de Datos 
Para un trabajo objetivo, se recomienda extraer datos crudos de las siguientes fuentes:

| Fuente | Dataset / Herramienta | Aplicación |
| :--- | :--- | :--- |
| **DANE** | [Microdatos Anonimizados](https://microdatos.dane.gov.co/) | Análisis profundo de ingresos, empleo y demografía empresarial. |
| **DANE** | [Geoportal](https://geoportal.dane.gov.co/) | Mapas de calor para cruzar ubicación de contratos vs. focos de pobreza. |
| **Portal Datos Abiertos** | [SECOP II - Contratos](https://www.datos.gov.co/) | Tabla maestra con valores, NITs de contratistas y objetos del gasto. |
| **TerriData** | [Indicadores Municipales](https://terridata.dnp.gov.co/) | Comparativa rápida de desempeño socioeconómico por región. |

---

## 4. Otras Posibles Preguntas de Investigación 
1. **Sintonía Territorial:** ¿Coinciden los sectores con mayor inversión en SECOP II con las vocaciones económicas identificadas en el Censo Económico Nacional Urbano (CENU)?
2. **Impacto en la Economía Popular:** ¿Qué porcentaje de contratos de mínima cuantía son adjudicados a micronegocios locales en zonas de alta vulnerabilidad socioeconómica?
3. **Brechas de Género:** ¿Cómo se correlaciona la jefatura de hogar femenina (Censo de Población) con la representación de mujeres como representantes legales en contratos estatales?
4. **Eficiencia en Zonas de Pobreza:** ¿Existe una relación directa entre el Índice de Pobreza Multidimensional (IPM) de un municipio y la modalidad de contratación predominante (Licitación vs. Contratación Directa)?

---

## 6. Directorio de Fuentes y Bases de Datos
A continuación, se presentan los enlaces oficiales a los datasets crudos ("los datos de verdad") para trabajar el proyecto:

### A. Contratación Pública (SECOP II)
* **[SECOP II - Contratos Electrónicos](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Contratos-Electr-nicos-ACTIVOS/p8vk-huva)**
    * **De qué trata:** Es la base de datos maestra con todos los contratos firmados. Incluye nombres de contratistas, NIT, valores, fechas, y el objeto del contrato (código UNSPSC).
    * **Uso técnico:** Ideal para filtrar por municipio y nivel de entidad (Nacional/Territorial).
* **[SECOP II - Ejecución de Contratos](https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Ejecuci-n-Contratos/mfmm-jqmq)**
    * **De qué trata:** Información sobre pagos, actas y el estado real de los recursos.
    * **Uso técnico:** Sirve para ver si el dinero "social" realmente llegó a los beneficiarios o sigue en trámite.

### B. Estadísticas y Censo (DANE)
* **[Archivo Nacional de Datos (ANDA)](https://microdatos.dane.gov.co/index.php/catalog/central)**
    * **De qué trata:** Repositorio de microdatos. Debes buscar el **CENU (Censo Económico)** y la **GEIH (Gran Encuesta Integrada de Hogares)**.
    * **Uso técnico:** Permite descargar archivos en `.csv` o `.dta` para hacer cruces de variables propias.
* **[Censo Nacional de Población y Vivienda (Consulta)](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivienda-2018)**
    * **De qué trata:** Datos sobre quiénes somos y cómo vivimos. Incluye el IPM (Pobreza) por manzana o sector censal.
* **[Geoportal DANE](https://geoportal.dane.gov.co/)**
    * **De qué trata:** Mapas y servicios geográficos.
    * **Uso técnico:** Permite descargar capas (Shapefiles) para ver visualmente dónde están las brechas socioeconómicas.

### C. Indicadores Municipales
* **[TerriData (DNP)](https://terridata.dnp.gov.co/)**
    * **De qué trata:** Compendio de indicadores de salud, educación, economía y finanzas públicas por cada municipio.
    * **Uso técnico:** Es la mejor fuente para tener un "resumen" rápido de un municipio sin procesar microdatos.

---
