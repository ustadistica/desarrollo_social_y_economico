## \# Proyecto: desarrollo_social_y\_economico

![Logo Universidad Santo
Tomás](https://usantotomas.edu.co/hs-fs/hubfs/social-suggested-images/usantotomas.edu.cohs-fshubfsLogo%20Santoto%20-%20SP%20Bogota%20Horizontal%20blanco-2.png)

## Consultorio de Estadística y Ciencia de Datos

**Universidad Santo Tomás**

**Responsables** - Angela Orjuela Guevara\
- Ingrid Umbacia Ramirez\
- Andres Perez Moreno\
- Alejandra Benedetti Castro\
- Diego Gomez Cortes\
- Maria Jose Galindo Piraban

------------------------------------------------------------------------

## 1. Descripción General

Este repositorio analiza la relación entre la distribución territorial
de la contratación pública (**SECOP II**) y las condiciones
socioeconómicas de la población (**DANE 2018**), para evaluar la equidad
y eficacia del gasto público en Colombia. Integra ambas fuentes,
construye indicadores y visualizaciones (mapas/tableros) y aplica
modelos estadísticos.

**Pregunta de investigación:**\
¿En qué medida la contratación pública registrada en SECOP II contribuye
a reducir las desigualdades socioeconómicas identificadas en los datos
del DANE, y cómo se distribuyen los contratos respecto a la
vulnerabilidad y características de la población en los territorios?

------------------------------------------------------------------------

## 2. Stack Tecnológico

![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)
![Jupyter](https://img.shields.io/badge/jupyter-notebooks-orange.svg)
![Power%20BI](https://img.shields.io/badge/Power%20BI-dashboards-yellow.svg)
![Poetry](https://img.shields.io/badge/poetry-deps%20%26%20envs-blueviolet.svg)

**Lenguajes, entornos y herramientas** - **Python 3.12**: `pandas`,
`numpy`, `scikit-learn`, `statsmodels`, `matplotlib`, `plotly` -
**Jupyter Notebooks** para EDA/modelado - **Power BI** (opcional) para
tableros

**Gestión de dependencias y entorno**\
- **Poetry** (sin pyenv). El proyecto **no** se instala como paquete:
`package-mode = false`.

------------------------------------------------------------------------

## 3. Cómo Empezar (Windows + VS Code)

> Requisitos:\
> - **Python 3.12** (la versión de Microsoft Store funciona)\
> - **Git** y **VS Code** con extensión *Python* y *Jupyter*

1)  **Clonar el repositorio**

``` powershell
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico
```

2)  **Instalar Poetry** (si no lo tienes)

``` powershell
pip install --user poetry
```

3)  **Instalar dependencias del proyecto**\
    \> No es necesario activar scripts (`ExecutionPolicy`) ni usar
    `poetry shell`.

``` powershell
python -m poetry install
```

4)  **Usar el entorno de Poetry** (dos opciones):

**Opción A -- Ejecutar comandos dentro del venv sin activarlo**

``` powershell
python -m poetry run python --version
python -m poetry run jupyter notebook
```

**Opción B -- Registrar el kernel para Jupyter/VS Code (recomendado)**

``` powershell
python -m poetry run python -m ipykernel install --user --name=desarrollo_social_y_economico --display-name "Python (desarrollo_social_y_economico)"
```

Luego, en VS Code: abrir un `.ipynb` → seleccionar kernel **Python
(desarrollo_social_y\_economico)**.

> **Tip:** Si prefieres "activar" el entorno en terminal y tu Windows lo
> permite:
>
> ``` powershell
> python -m poetry env activate
> ```
>
> (Si ves un error de *ExecutionPolicy*, usa la Opción A o registra el
> kernel como arriba.)

------------------------------------------------------------------------

## 4. Estructura del Repositorio (tentativa)

    desarrollo_social_y_economico/
    ├─ datos/
    │  ├─ codigos de descarga de datos            # fuentes originales (DANE, SECOP II)
    │  ├─ procesados/        # datasets limpios/curados
    │  ├─ modelos/           # artefactos de modelos
    │  └─ diccionarios/      # diccionarios de variables / metadatos
    ├─ docs/
    │  ├─ planteamiento/     # cartas, planteamiento, justificación
    │  ├─ analisis/          # informes intermedios
    │  └─ presentaciones/    # slides/posters
    ├─ notebooks/
    │  ├─ 00_exploracion.ipynb
    │  ├─ 01_integracion_datos.ipynb
    │  ├─ 02_modelos.ipynb
    │  └─ 03_visualizaciones.ipynb
    ├─ src/
    │  ├─ __init__.py
    │  ├─ data/
    │  │  ├─ load_dane.py       # carga/etiquetado de Personas 2018
    │  │  └─ load_secop2.py     # extracción SECOP II (API/CSV)
    │  ├─ features/
    │  │  └─ build_features.py  # indicadores / joins territoriales
    │  ├─ models/
    │  │  └─ regressions.py     # especificación/ajuste de modelos
    │  └─ viz/
    │     └─ maps.py            # mapas y gráficos comparativos
    ├─ tests/
    │  └─ test_data_pipelines.py
    ├─ pyproject.toml
    ├─ poetry.lock
    ├─ .gitignore
    └─ README.md

------------------------------------------------------------------------

## 5. Datos y Fuentes

**DANE -- Personas 2018 (Pobreza Monetaria / Desigualdad)**\
- Variables: demográficas, educación, empleo, ingresos, pobreza/GINI\
- Recomendaciones: usar **factores de expansión**; consultar diccionario
de variables\
- Formato: CSV local con documentación oficial del DANE\
- Limitaciones: corte único 2018

**SECOP II -- Contratos Electrónicos (Activos)**\
- Variables: entidad, ubicación (departamento/municipio), sector,
objeto, fechas, estado, valor\
- Acceso: **API SODA (Socrata)** y CSV (Datos Abiertos Colombia)\
- Observaciones: calidad variable; alto volumen → limpiar/filtrar
- La descarga de datos se realizo en  un google colab y los datos quedaron guardados en un folder de google drive de ruta '/content/drive/MyDrive/DatosAPI_Trimestral_Parquet/' en archivos .parquet y un sqcrti para correr diario y actualizar los datos con fecha de publicacion. y descargar agrupado por fecha de publicacion.  con el correo: consultoriadesarrollo03@gmail.com  clave: Consultorio1*

------------------------------------------------------------------------

## 6. Metodología (resumen)

-   **Unidades de análisis**: Departamentos (y, si es posible,
    municipios)\
-   **Cruce territorial**: montos de contratación vs. indicadores
    socioeconómicos\
-   **Desigualdad**: índices (p. ej. *Gini*) y concentración
    territorial\
-   **Modelado**: regresiones (monto contratación \~ condiciones
    socioeconómicas + controles)\
-   **Visualización**: mapas comparativos y tableros (Power BI /
    notebooks)

------------------------------------------------------------------------

## 7. Flujo de Trabajo Sugerido

1.  **Ingesta & Limpieza**: DANE (etiquetas/factores), SECOP II
    (API/CSV; códigos DANE; fechas/NIT/duplicados)\
2.  **Integración**: unir por territorio (y sector cuando aplique)\
3.  **Análisis**: EDA, correlaciones, desigualdad, modelos\
4.  **Resultados**: tablas, figuras, mapas, KPIs de brechas\
5.  **Entrega**: dashboards (Power BI) + notebooks/scripts reproducibles

------------------------------------------------------------------------

## 8. Solución de Problemas (Windows)

-   **`poetry : command not found`**

    ``` powershell
    pip install --user poetry
    python -m poetry --version
    ```

-   **Error `pyproject.toml`** → regenerar lock:

    ``` powershell
    del poetry.lock
    python -m poetry lock
    python -m poetry install
    ```

-   **Kernel no aparece en VS Code** → registrar kernel:

    ``` powershell
    python -m poetry run python -m ipykernel install --user --name=desarrollo_social_y_economico --display-name "Python (desarrollo_social_y_economico)"
    ```

-   **ExecutionPolicy bloquea activate.ps1** → usar
    `python -m poetry run ...`

------------------------------------------------------------------------

## 9. Licencia

MIT.
