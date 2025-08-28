# Proyecto: desarrollo_social_y_economico
---
![Logo Universidad Santo Tomás](https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png)

## Consultorio de Estadística y Ciencia de Datos  
**Universidad Santo Tomás**

**Responsables**
- Angela Orjuela Guevara
- Ingrid Umbacia Ramirez
- Andres Perez Moreno
- Alejandra Benedetti Castro
- Diego Gomez Cortes
- Maria Jose Galindo Piraban

### 1. Descripción General
Este repositorio contiene el código, datos y documentación del proyecto “desarrollo_social_y_economico”, cuyo objetivo es analizar la relación entre la distribución territorial de la contratación pública (SECOP II) y las condiciones socioeconómicas de la población (DANE), con el fin de evaluar la equidad y eficacia del gasto público en Colombia. El estudio busca responder si los recursos estatales se asignan de manera proporcional a las necesidades sociales o si se concentran en territorios específicos.

Para lograrlo, se integran datos del SECOP II y del DANE 2018, aplicando técnicas estadísticas como índices de desigualdad, correlaciones y modelos de regresión, junto con visualizaciones en mapas comparativos. El proyecto utiliza herramientas como Python/R y Power BI, y aporta insumos relevantes para la discusión sobre desarrollo regional, reducción de desigualdades y transparencia en la gestión pública.

**Descripción del problema**
En Colombia, la contratación pública es uno de los principales mecanismos de inversión social y desarrollo territorial. Sin embargo, persisten dudas sobre si los recursos adjudicados mediante contratos se distribuyen de manera equitativa entre las diferentes regiones del país. Mientras algunas zonas presentan altos niveles de vulnerabilidad socioeconómica, la asignación de recursos podría estar concentrada en territorios con mejores condiciones, lo que amplía las brechas de desigualdad.

El problema radica en la falta de evidencia clara sobre la correspondencia entre la inversión pública y las necesidades reales de la población. Esto dificulta evaluar la eficacia y equidad del gasto estatal, así como su impacto en la reducción de desigualdades regionales y sociales.

**Pregunta de investigación.** ¿En qué medida la contratación pública registrada en SECOP II contribuye a reducir las desigualdades socioeconómicas identificadas en los datos del DANE, y cómo se distribuyen los contratos respecto a la vulnerabilidad y características de la población en los territorios?

**Objetivos específicos (resumen).**
- Caracterizar contratos del SECOP II por ubicación, sector, tipo y monto.  
- Describir indicadores socioeconómicos (ingresos, educación, empleo) por territorio.  
- Integrar ambas fuentes para construir indicadores de correlación/consistencia.  
- Detectar brechas territoriales (alta vulnerabilidad vs. baja inversión).

## Justificación

La contratación pública en Colombia es uno de los principales mecanismos de inversión social y desarrollo territorial. Sin embargo, no siempre se tiene claridad sobre si los recursos se distribuyen de manera equitativa en relación con las necesidades de la población.  

Este proyecto integra datos del **SECOP II** y del **DANE**, con el fin de evaluar la relación entre el gasto público y las condiciones socioeconómicas de los territorios. De esta forma, se busca aportar evidencia para la discusión sobre **equidad regional, desarrollo social y transparencia** en el uso de los recursos estatales.  

### 2. Stack Tecnológico
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg) ![Jupyter](https://img.shields.io/badge/jupyter-notebooks-orange.svg) ![R](https://img.shields.io/badge/R-4.x-blue.svg) ![Power%20BI](https://img.shields.io/badge/Power%20BI-dashboards-yellow.svg) ![Poetry](https://img.shields.io/badge/poetry-deps%20%26%20envs-blueviolet.svg)

## Lenguajes, entornos y herramientas

### Lenguajes y entornos
- **Python 3.12**: análisis estadístico, limpieza de datos y desarrollo de modelos de IA/ML con librerías como `pandas`, `numpy`, `scikit-learn`, `statsmodels`, `matplotlib` y `plotly`.  
- **Jupyter Notebooks**: exploración de datos (EDA), visualizaciones, experimentación y transformación de datos de forma interactiva.  
- **R (4.x)**: análisis estadístico complementario utilizando `tidyverse`, `dplyr` y `ggplot2`. *(RStudio no es requisito).*  

### Gestión de dependencias
- **Poetry**: manejo de paquetes, control de versiones y creación de entornos aislados de desarrollo.  

### Visualización e informes
- **Power BI**: creación de tableros interactivos, tablas comparativas y reportes de indicadores clave.  

### 3. Cómo Empezar

1) **Clonar el repositorio**
```bash
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico
```

2) **Configurar el entorno con Poetry**
```bash
# (opcional) fuerza Python 3.12 si tienes varias versiones instaladas
poetry env use 3.12

# inicializa si aún no existe pyproject.toml (si ya existe, omite este paso)
# poetry init

# instala dependencias del proyecto
poetry install
```

3) **Activar el entorno virtual**
```bash
poetry shell
```


### 4. Estructura tentativa del Repositorio
```
desarrollo_social_y_economico/
├─ datos/
│  ├─ crudos/           # fuentes originales (DANE, SECOP II)
│  ├─ procesados/       # datasets limpios/curados
│  ├─ modelos/          # artefactos de modelos y/o resultados
│  └─ diccionarios/     # diccionarios de variables / metadatos
├─ docs/
│  ├─ planteamiento/    # cartas, planteamiento del problema, justificación
│  ├─ analisis/         # informes y análisis intermedios
│  └─ presentaciones/   # slides/posters
├─ notebooks/
│  ├─ 00_exploracion.ipynb
│  ├─ 01_integracion_datos.ipynb
│  ├─ 02_modelos.ipynb
│  └─ 03_visualizaciones.ipynb
├─ src/
│  ├─ __init__.py
│  ├─ data/
│  │  ├─ load_dane.py      # carga/etiquetado de Personas 2018
│  │  └─ load_secop2.py    # extracción SECOP II (API/CSV)
│  ├─ features/
│  │  └─ build_features.py # construcción de indicadores/joins territoriales
│  ├─ models/
│  │  └─ regressions.py    # especificación/ajuste de modelos
│  └─ viz/
│     └─ maps.py           # mapas y gráficos comparativos
├─ tests/
│  └─ test_data_pipelines.py
├─ pyproject.toml
├─ .gitignore
└─ README.md
```

### 5. Datos y Fuentes

El proyecto integra dos fuentes principales de información: **DANE – Personas 2018** y **SECOP II (Contratos Electrónicos)**. La combinación de estas bases permite analizar la relación entre inversión pública y condiciones socioeconómicas en diferentes territorios de Colombia.


#### DANE – Personas 2018 (Pobreza Monetaria y Desigualdad)
- **Descripción:** Encuesta de hogares y personas con información sociodemográfica y económica representativa a nivel nacional.  
- **Variables clave:**  
  - Demográficas: sexo, edad, composición del hogar.  
  - Educación: nivel educativo alcanzado, asistencia escolar.  
  - Empleo: ocupación, posición laboral, horas trabajadas.  
  - Ingresos: salario, fuentes de ingreso adicionales, transferencias.  
  - Pobreza y desigualdad: variables para cálculo de pobreza monetaria y coeficiente de Gini.  
- **Recomendaciones técnicas:**  
  - Aplicar **factores de expansión** para obtener inferencias poblacionales.  
  - Averiguar el **diccionario de variables** para interpretar los códigos.  
- **Formato y acceso:** disponible en **CSV local**, con documentación oficial en la página del DANE.  
- **Limitaciones:**  
  - Corte único (2018), sin actualización anual directa en este archivo.  
  - No captura dinámicas recientes de desigualdad.  


#### SECOP II – Contratos Electrónicos (ACTIVOS)
- **Descripción:** Plataforma oficial de contratación estatal en Colombia, con información detallada de procesos de compra pública.  
- **Variables clave:**  
  - Datos del contratante: entidad pública, NIT.  
  - Información territorial: ubicación (departamento/municipio).  
  - Contratos: sector, objeto contractual, modalidad, fechas de inicio y fin, estado.  
  - Financieros: valor del contrato, rubro presupuestal, vigencias.  
- **Acceso:**  
  - **API SODA (Socrata)** para consultas dinámicas y reproducibles.  
  - Descarga de archivos en **CSV** desde el portal de Datos Abiertos Colombia.  
- **Actualización:** dataset **vivo en línea**, con actualizaciones periódicas de nuevos contratos.  
- **Limitaciones:**  
  - Posibles inconsistencias en el diligenciamiento por parte de entidades.  
  - Datos muy voluminosos, requieren procesos de limpieza y filtrado para análisis eficiente.  


> Los detalles de pertinencia, calidad de datos, acceso y actualización se consolidan en los documentos de **Planteamiento** y **Análisis Preliminar** dentro de docs/.


### 6. Metodología (Resumen)

La metodología se centra en integrar y analizar datos de contratación pública (SECOP II) junto con información socioeconómica (DANE) para determinar si el gasto público refleja de manera adecuada las necesidades de la población. El enfoque es principalmente cuantitativo, apoyado en indicadores de desigualdad, técnicas de modelado y visualización comparativa.

- **Unidades de análisis:** Departamentos (de ser posible, municipios), permitiendo capturar tanto la visión macro de la inversión pública como las dinámicas locales.
- **Cruce territorial:** vincular montos de contratación con indicadores socioeconómicos (ingresos, educación, empleo), identificando posibles desajustes entre necesidades sociales y asignación de recursos.  
- **Medidas de desigualdad:** aplicación de índices como el *Gini* y concentración de contratos para evaluar la equidad en la distribución territorial de los recursos.  
- **Modelado:** uso de regresiones, considerando el monto de contratación como variable dependiente y las condiciones socioeconómicas como variables explicativas, con el fin de explorar relaciones causales o correlacionales.  
- **Visualización:** elaboración de mapas comparativos (contratos vs. vulnerabilidad) y dashboards que faciliten la interpretación de resultados por parte de distintos públicos (académico, institucional, ciudadano).  
- **Herramientas:** **Python** (limpieza, integración, análisis estadístico y modelado) y, opcionalmente, **Power BI** para visualización interactiva y presentación de resultados.  

### 7. Flujo de Trabajo Sugerido

- **Ingesta & Limpieza**  
   - Cargar DANE Personas 2018, normalizar etiquetas/códigos.  
   - Extraer SECOP II (API/CSV), estandarizar geografía (códigos DANE), validar duplicados/fechas/NIT.  

- **Integración**  
   - Unir bases por territorio y, cuando aplique, por sector económico.  

- **Análisis**  
   - EDA (distribuciones, outliers, sesgos).  
   - Correlaciones, índices de concentración (Gini).  
   - Modelos de regresión (línea base + variaciones con controles).  

- **Resultados**  
   - Tablas, figuras y mapas comparativos.  
   - KPIs de brechas territoriales.  

- **Entrega**  
   - Dashboards y reportes en **Power BI**.  
   - Modelos y scripts documentados en el repositorio.  


