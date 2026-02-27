# Observatorio de Desarrollo Social y Economico

> **Ustadistica** -- Consultoria e Investigacion . Universidad Santo Tomas . 2026-I

Observatorio de desarrollo social (SECOP II + DANE) y economico. Analisis de equidad en contratacion publica vs. vulnerabilidad territorial.

## Fuentes de Datos

SECOP II (contratacion publica), DANE Censo 2018 (condiciones socioeconomicas) -- datos.gov.co

Consultar [`datos/catalogo.yaml`](datos/catalogo.yaml) para los identificadores Socrata y metadatos de cada dataset.

## Preguntas de Investigacion

- La contratacion publica se distribuye proporcionalmente a la vulnerabilidad territorial?
- Existe autocorrelacion espacial (Moran's I) en la distribucion de la inversion publica?
- Que municipios presentan mayor brecha entre vulnerabilidad socioeconomica e inversion per capita?
- Cual es el indice de concentracion de contratos (Gini/HHI) por departamento?

## Estructura del Proyecto

```
desarrollo_social_y_economico/
|-- README.md                    # Este archivo
|-- CONTRIBUTING.md              # Guia de contribucion y Git Flow
|-- pyproject.toml               # Poetry (dependencias + metadata)
|-- Dockerfile                   # Contenedor reproducible
|-- .github/
|   +-- workflows/
|       +-- etl_update.yml       # GitHub Actions para ingesta periodica
|-- src/
|   |-- ingesta/                 # Scripts de extraccion (sodapy)
|   |-- transformacion/          # Limpieza, normalizacion, joins
|   |-- modelo/                  # Modelo estrella / modelado estadistico
|   +-- visualizacion/           # Funciones de graficos reutilizables
|-- notebooks/
|   |-- 01_eda.ipynb
|   |-- 02_analisis.ipynb
|   +-- 03_modelado.ipynb
|-- app/
|   +-- streamlit_app.py         # Dashboard interactivo
|-- datos/
|   |-- raw/                     # Datos crudos (gitignored si pesados)
|   |-- processed/               # Datos limpios
|   +-- catalogo.yaml            # Metadatos de cada dataset
|-- docs/                        # Informes y documentacion
|-- tests/                       # Tests automatizados
|-- artifacts/                   # Artefactos generados (metricas, reportes)
+-- models/                      # Modelos serializados
```

## Instalacion

```bash
# Clonar el repositorio
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico

# Instalar dependencias con Poetry
pip install poetry
poetry install

# Ejecutar pipeline de ingesta
poetry run python -m src.ingesta.main

# Ejecutar pipeline de transformacion
poetry run python -m src.transformacion.main

# Lanzar dashboard
poetry run streamlit run app/streamlit_app.py
```

## Cronograma -- CRISP-DM

### Sprint 1 (Sem 1-2)

Definir alcance de ambos subproyectos (social + economico). Migrar modelo estrella de SQLite a DuckDB. Estructura monorepo: `social/`, `economico/`, `shared/`.

### Sprint 2 (Sem 3-4)

Cruce SECOP II con indicadores DANE (IPM, NBI, servicios publicos). Indicadores derivados: inversion per capita, concentracion de contratos.

### Sprint 3 (Sem 5-7)

Regresion espacial, Moran's I, clustering municipal. Dashboard Streamlit open-source (reemplazo de Power BI).

### Sprint 4 (Sem 8)

Informe final de ambos subproyectos. Dashboard desplegado en Streamlit Cloud.


## Equipo

| Rol | GitHub |
|-----|--------|
| Lider modelado R -- Social | [@carolinasc0328-png](https://github.com/carolinasc0328-png) |
| Analisis + viz -- Social | [@chechitoooo](https://github.com/chechitoooo) |
| Por perfilar -- Castano Vergara -- Social | (por confirmar) |
| Lider de proyecto -- Economico | [@LizethVillamil](https://github.com/LizethVillamil) |
| Modelado + analisis -- Economico | [@johannsebastian19877-png](https://github.com/johannsebastian19877-png) |

**Director:** [@Izainea](https://github.com/Izainea)

## Metodologia

- **Framework analitico:** CRISP-DM
- **Gestion de proyecto:** Sprints de 2 semanas con Kanban (GitHub Projects)
- **Control de versiones:** Git Flow (`main` / `develop` / `feature/*`)
- **Estandar operativo:** Big 4 (governance formal, auditoria cruzada, mejora continua)

Consultar [CONTRIBUTING.md](CONTRIBUTING.md) para la guia completa de contribucion.

## Stack Tecnologico

| Capa | Herramientas |
|------|-------------|
| Ingesta | sodapy, pandas, requests |
| Almacen | DuckDB (modelo estrella) |
| Analisis | pandas, scikit-learn, statsmodels |
| Visualizacion | matplotlib, seaborn, plotly, folium |
| Dashboard | Streamlit |
| Reproducibilidad | Poetry, Docker, GitHub Actions |
| Testing | pytest, pandera |

---

> *"Si no esta en el README, el proyecto no existe."* -- Ustadistica 2026-I
