# Sinergia socioeconómica: contratación pública, estructura territorial y economía popular

**Equipo:** Consultorio de Estadística USTA · Observatorio Ustadística 2026-I
**Repositorio:** `desarrollo_social_y_economico`
**Periodo analítico:** 2018-2026

Plataforma analítica reproducible que mide la concentración de la contratación pública territorial en Colombia mediante el Índice Herfindahl-Hirschman (HHI) aplicado a SECOP I y SECOP II, articulada con información social y demográfica del DANE (CNPV 2018, EMICRON, proyecciones de población). El pipeline sigue la arquitectura Medallion (Bronze → Silver → Gold) en Python (Pandas + PyArrow).

---

## 1. Índice de entregables

| Componente | Ruta | Descripción |
|---|---|---|
| **Informe final** | [`docs/INFORME_HHI_DETALLADO.md`](docs/INFORME_HHI_DETALLADO.md) | Informe estadístico completo: portada, resumen, contextualización, objetivos, fuentes, métodos, resultados, discusión, conclusiones, limitaciones, referencias y anexos técnicos. |
| Informe interanual | [`docs/INFORME_HHI_INTERANUAL.md`](docs/INFORME_HHI_INTERANUAL.md) | Documento complementario sobre evolución del HHI. |
| **Dashboard** | [`app/streamlit_app.py`](app/streamlit_app.py) | Aplicación Streamlit con visualizaciones interactivas. |
| **Reporte HTML** | [`artifacts/hhi/hhi_report.html`](artifacts/hhi/hhi_report.html) | Reporte ejecutivo con figuras y tablas. |
| **Presentación** | [`artifacts/presentacion/presentacion.md`](artifacts/presentacion/presentacion.md) | Boceto Marp de 13 diapositivas (exportable a PDF). |
| **Infografía** | [`artifacts/infografia/infografia_hhi.png`](artifacts/infografia/infografia_hhi.png) | Síntesis visual con KPIs y figuras principales. |
| Tabla maestra HHI | [`data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv`](data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv) | 11,792 mercados (municipio × año × orden_entidad). |
| Agregaciones HHI | [`data/hhi_por_anio.csv`](data/hhi_por_anio.csv), [`hhi_por_nivel.csv`](data/hhi_por_nivel.csv), [`hhi_por_departamento.csv`](data/hhi_por_departamento.csv), [`hhi_por_municipio.csv`](data/hhi_por_municipio.csv) | Resúmenes anuales y territoriales. |
| Catálogo de datos | [`data/catalogo.yaml`](data/catalogo.yaml) | Diccionario de fuentes, esquemas y trazabilidad. |
| Indicadores derivados | [`data/indicadores/`](data/indicadores/) | CSVs de indicadores sociales (CNPV), inversión (SECOP) y economía popular (EMICRON). |

---

## 2. Fuentes de datos abiertos

| Fuente | Portal / Entidad | Identificador / Catálogo | Periodo | Fecha consulta |
|---|---|---|---|---|
| SECOP I - Procesos de Compra Pública | Datos Abiertos Colombia / Colombia Compra Eficiente | [`f789-7hwg`](https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-I-Procesos-de-Compra-P-blica/f789-7hwg) | 2018-2026 | 2026-05-27 |
| SECOP II - Contratos Electrónicos | Datos Abiertos Colombia / Colombia Compra Eficiente | [`jbjy-vk9h`](https://www.datos.gov.co/Estad-sticas-Nacionales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h) | 2018-2026 | 2026-05-27 |
| CNPV 2018 - Censo Nacional de Población y Vivienda | DANE - Archivo Nacional de Datos | [Catálogo 643, `DANE-DCD-CNPV-2018`](https://microdatos.dane.gov.co/index.php/catalog/643) | 2018 | 2026-05-27 |
| EMICRON - Encuesta de Micronegocios | DANE - Microdatos | [Catálogo 875 (referencia 2024)](https://microdatos.dane.gov.co/index.php/catalog/study/DANE-DIMPE-EMICRON-2024) | 2019-2024 | 2026-05-27 |
| Proyecciones de población | DANE | [Serie 2018-2050 (CNPV 2018 base)](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/proyecciones-de-poblacion) | 2018-2050 | 2026-05-27 |
| DIVIPOLA | DANE / catálogo interno | [`src/utils/divipola_catalog.py`](src/utils/divipola_catalog.py) | Vigente | — |

El catálogo completo con diccionario por dataset, llaves, esquemas y trazabilidad está en [`data/catalogo.yaml`](data/catalogo.yaml) y [`data/README.md`](data/README.md).

---

## 3. Estructura del repositorio

```text
desarrollo_social_y_economico/
├── README.md                       ← este archivo (índice de entrega)
├── CONTRIBUTING.md                 ← guía de contribución
├── pyproject.toml / Makefile       ← build, dependencias
├── Dockerfile                      ← contenedor reproducible
├── app/
│   └── streamlit_app.py            ← dashboard preliminar
├── artifacts/
│   ├── hhi/                        ← reporte HTML + 3 figuras del informe
│   ├── infografia/                 ← infografía preliminar
│   ├── presentacion/               ← presentación Marp preliminar
│   └── AUDITORIA_ANALISIS_EMICRON.html
├── data/
│   ├── catalogo.yaml               ← diccionario y trazabilidad
│   ├── README.md                   ← guía de la capa de datos
│   ├── bronze/  silver/  gold/     ← capas Medallion (gitignored)
│   ├── indicadores/                ← CSVs de indicadores derivados
│   └── hhi_*.csv                   ← resultados del indicador HHI
├── docs/
│   ├── INFORME_HHI_DETALLADO.md    ← informe final ★
│   ├── INFORME_HHI_INTERANUAL.md
│   ├── guias/                      ← instalación, datos, reportes
│   └── ...                         ← otros documentos técnicos
├── notebooks/                      ← EDA y análisis exploratorios
├── scripts/                        ← scripts reproducibles (HHI, EDA, infografía)
├── src/                            ← código de ingesta, limpieza y features
│   ├── ingesta/                    ← Bronze (parsers Socrata + CSV)
│   ├── transformacion/             ← Silver y Gold
│   ├── features/                   ← indicador HHI
│   ├── validadores/  validate/     ← validaciones de datos
│   └── utils/                      ← DIVIPOLA, helpers
└── tests/                          ← pruebas unitarias y de regresión
```

---

## 4. Reproducción del pipeline

### 4.1 Instalación

```bash
git clone <url> && cd desarrollo_social_y_economico
python -m venv .venv
.venv\Scripts\activate                    # Windows
# source .venv/bin/activate               # Linux/Mac
pip install -e .
```

Guía detallada: [`docs/guias/INSTALACION.md`](docs/guias/INSTALACION.md).

### 4.2 Carpeta de datos crudos

La carpeta `Datos/` con archivos fuente debe ubicarse junto a este repositorio. Ver [`docs/guias/SETUP_DATOS.md`](docs/guias/SETUP_DATOS.md).

### 4.3 Ejecución

```bash
# Pipeline Medallion completo
python -m src.cli all

# Por capa
python -m src.cli bronze
python -m src.cli silver
python -m src.cli gold

# Cálculo HHI desde Silver transaccional
python -m src.features.indicador_hhi_cruce

# Reporte HTML y figuras HHI
python scripts/generar_graficas_hhi.py

# Infografía
python scripts/generar_infografia_hhi.py

# Dashboard
streamlit run app/streamlit_app.py
```

### 4.4 Validación

```bash
python -m pytest tests/ -q
python -m pytest tests/test_indicador_hhi_cruce.py -v
```

---

## 5. Scripts reproducibles destacados

| Script | Propósito |
|---|---|
| [`src/cli`](src/cli/) | Orquestador de capas Medallion. |
| [`src/features/indicador_hhi_cruce.py`](src/features/indicador_hhi_cruce.py) | Cálculo HHI desde Silver transaccional. |
| [`scripts/generar_graficas_hhi.py`](scripts/generar_graficas_hhi.py) | Genera reporte HTML + figuras del informe. |
| [`scripts/generar_infografia_hhi.py`](scripts/generar_infografia_hhi.py) | Genera infografía PNG preliminar. |
| [`scripts/generate_eda_notebook.py`](scripts/generate_eda_notebook.py) | Construye el notebook EDA. |
| [`scripts/indicadores_exploratorios.py`](scripts/indicadores_exploratorios.py) | Exploración de indicadores derivados. |

---

## 6. Resultados clave

- **11,792 mercados** analizados (municipio × año × orden_entidad).
- HHI promedio nacional anual entre **1,040 y 1,484** → concentración baja a moderada.
- Contratación **nacional consistentemente más concentrada** que la territorial.
- Solo **186 mercados (1.58 %)** alcanzan HHI = 10,000; de estos, 19 son monopolios reales (≥2 contratos al mismo NIT).
- Departamentos con mayor concentración en 2026: **Atlántico, Chocó, Magdalena, La Guajira, Boyacá**.

Detalles completos en el informe: [`docs/INFORME_HHI_DETALLADO.md`](docs/INFORME_HHI_DETALLADO.md).

---

## 7. Cumplimiento de los requisitos de entrega

| Requisito del enunciado | Producto en el repo |
|---|---|
| Informe estadístico completo (portada, resumen, contextualización, objetivos, fuentes, tratamiento, métodos, resultados, discusión, conclusiones, recomendaciones, limitaciones, referencias, anexos) | [`docs/INFORME_HHI_DETALLADO.md`](docs/INFORME_HHI_DETALLADO.md) |
| Dashboard / aplicación | [`app/streamlit_app.py`](app/streamlit_app.py) |
| Infografía (versión previa) | [`artifacts/infografia/`](artifacts/infografia/) |
| Presentación (versión previa) | [`artifacts/presentacion/`](artifacts/presentacion/) |
| Repositorio ordenado con código, documentación, README y control de versiones | Estructura descrita en la sección 3 |
| Scripts reproducibles de consulta y procesamiento de datos abiertos | [`src/ingesta/`](src/ingesta/) (parsers Socrata + CSV) y [`scripts/`](scripts/) |
| Conjuntos de datos con diccionario | [`data/catalogo.yaml`](data/catalogo.yaml), [`data/README.md`](data/README.md), sección 13 del informe |
| Citación explícita del catálogo de cada fuente | Sección 2 de este README y sección 3 del informe |
| Trazabilidad de transformaciones | Arquitectura Medallion `Bronze → Silver → Gold` documentada en informe y código |

---

## 8. Licencia y autoría

- **Equipo:** Consultorio de Estadística USTA · Observatorio Ustadística 2026-I.
- **Datos:** propiedad de los publicadores originales (Datos Abiertos Colombia, DANE). Uso académico bajo los términos de cada portal.
- **Código:** ver `pyproject.toml`.
