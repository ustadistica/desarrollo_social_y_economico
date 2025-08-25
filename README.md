# Proyecto: desarrollo_social_y_economico
---
![Logo Universidad Santo Tomás](https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png)

## Consultorio de Estadística y Ciencia de Datos  
**Universidad Santo Tomás**

### 1. Descripción General
Este repositorio contiene el código, datos y documentación del proyecto **“desarrollo_social_y_economico”**, cuyo objetivo es analizar la relación entre la distribución territorial de la contratación pública (SECOP II) y las condiciones socioeconómicas de la población (DANE), para evaluar la equidad y eficacia del gasto público en Colombia.

**Pregunta de investigación.** ¿En qué medida la contratación pública registrada en SECOP II contribuye a reducir las desigualdades socioeconómicas identificadas en los datos del DANE, y cómo se distribuyen los contratos respecto a la vulnerabilidad y características de la población en los territorios?

**Objetivos específicos (resumen).**
- Caracterizar contratos del SECOP II por ubicación, sector, tipo y monto.  
- Describir indicadores socioeconómicos (ingresos, educación, empleo) por territorio.  
- Integrar ambas fuentes para construir indicadores de correlación/consistencia.  
- Detectar brechas territoriales (alta vulnerabilidad vs. baja inversión).

### 2. Stack Tecnológico
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
- **Lenguaje:** Python  
- **Versión:** 3.12  
- **Gestor de dependencias:** Poetry

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

**DANE – Personas 2018 (Pobreza Monetaria y Desigualdad).**  
- Variables sociodemográficas y económicas de personas y hogares (sexo, edad, educación, ocupación, ingresos, factores de expansión).  
- Recomendaciones: aplicar factores de expansión para inferencias y apoyarse en el diccionario de variables para interpretar códigos (p. ej., P6020, P6040).  
- Acceso: CSV local y documentación oficial.  
- Limitación principal: corte único 2018 (sin actualización continua en el archivo).  

**SECOP II – Contratos Electrónicos (ACTIVOS).**  
- Fuente de contratos de compra pública (entidad, NIT, ubicación, fechas, sector, etc.).  
- Acceso: API SODA (Socrata) o descarga CSV desde Datos Abiertos.  
- Actualización periódica (dataset vivo en línea).  

> Los detalles de pertinencia, calidad de datos, acceso y actualización se consolidan en los documentos de **Planteamiento** y **Análisis Preliminar** dentro de `docs/`.  

### 6. Metodología (Resumen)
- **Unidades de análisis:** Departamentos (y, de ser posible, municipios).  
- **Cruce territorial:** vincular montos de contratación con indicadores socioeconómicos.  
- **Medidas de desigualdad:** índices tipo Gini/concentración de contratos.  
- **Modelado:** regresiones con monto de contratación como variable dependiente y condiciones socioeconómicas como explicativas.  
- **Visualización:** mapas comparativos (contratos vs. vulnerabilidad), dashboards.  
- **Herramientas:** Python (limpieza, integración, modelado) y, opcionalmente, Power BI para visualización interactiva.

### 7. Flujo de Trabajo Sugerido
1. **Ingesta & Limpieza**  
   - Cargar DANE Personas 2018 y normalizar etiquetas/códigos.  
   - Extraer SECOP II (API/CSV), estandarizar geografía (códigos DANE), validar duplicados/fechas/NIT.  
2. **Integración**  
   - Unir por territorio y, cuando aplique, por sector económico.  
3. **Análisis**  
   - EDA (distribuciones, outliers, sesgos), correlaciones, índices de concentración.  
   - Modelos (línea base y variaciones con controles).  
4. **Resultados**  
   - Tablas/figuras reproducibles, mapas y KPIs de brechas.  
5. **Entrega**  
   - Visualizaciones y modelos finales  en powerbi y 

