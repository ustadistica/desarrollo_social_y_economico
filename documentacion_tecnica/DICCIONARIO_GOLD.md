# 📖 Diccionario de Datos - Capa Gold

Este diccionario documenta el listado maestro de columnas que se materializa tras la ejecución de la arquitectura analítica.

---

## 1. Dimensiones (Slicer / Filtros)

### Tabla: `dim_tiempo`
| Columna | Tipo | Llave | Descripción |
|---------|------|-------|-------------|
| `anio_key` | INT | **PK** | Año calendario transaccional (vigencia fiscal o estadística). |
| `es_año_electoral_presidencial` | BOOLEAN | | Indica si en ese año hubo elecciones mayores ejecutivas en el modelo temporal de Colombia (True para 2018, 2022, 2026). |
| `es_año_electoral_regional` | BOOLEAN | | Indica si hubo elecciones de alcaldes/gobernadores ese mismo año. |
| `es_pandemia` | BOOLEAN | | Flag temporal estática para variables anómalas (2020, 2021). |

### Tabla: `dim_territorio`
| Columna | Tipo | Llave | Descripción |
|---------|------|-------|-------------|
| `divipola_key` | STRING | **PK** | Código DANE único municipal de 5 dígitos (Zero-padded a izquierda). |
| `nombre_municipio_referencia` | STRING | | Valor default descriptivo o extraído canónicamente del SECOP. |
| `divipola_departamento` | STRING | | Código DANE departamental jerárquico extraído de los primeros 2 dígitos de la PK. |

---

## 2. Tablas de Hechos (Facts)

### Tabla: `fact_contratacion_municipio_anio`
*(Grano: Agrupación alzada Mpio-Año del SECOP I y II)*
| Columna | Tipo | Llave | Descripción |
|---------|------|-------|-------------|
| `divipola_key` | STRING | FK | Match exacto con dimensión territorio. |
| `anio_key` | INT | FK | Match exacto con tiempo. |
| `inversion_total_monto` | FLOAT | | **Métrica Aditiva:** Sumatoria bruta total de `valor_del_contrato` publicados en la respectiva vigencia y unidad de gasto. |
| `cantidad_procesos_adjudicados` | INT | | **Métrica Aditiva:** Equivalencia de contratos o procesos adjudicados en la zona. |
| `proveedores_unicos` | INT | | Conteo distintivo (`COUNT DISTINCT`) de identificadores fiscales o NITs atados a los procesos. |

### Tabla: `fact_micronegocios_municipio_anio`
*(Grano: Mpio-Año proyectado desde Muestra EMICRON)*
| Columna | Tipo | Llave | Descripción |
|---------|------|-------|-------------|
| `divipola_key` | STRING | FK | Match geográfico DANE. |
| `anio_key` | INT | FK | Año estadístico. |
| `volumen_micronegocios_exp` | FLOAT | | **Métrica Agregada Ponderada:** Sumatoria integral del factor de expansión probabilístico `fex_c` validando población muestral ajustada sobre dicho sector territorial en ese año, sin necesidad de usar ratios en bruto. |

### Tabla: `fact_demografia_municipio_anio`
*(Grano: Mpio-Año derivado de DPMP Base censal y proyección)*
| Columna | Tipo | Llave | Descripción |
|---------|------|-------|-------------|
| `divipola_key` | STRING | FK | Match territorial. |
| `anio_key` | INT | FK | Match tiempo proyecciones. |
| `poblacion_total_proyectada` | FLOAT | | **Métrica Semi-Aditiva:** Población total. Sirve predominantemente de base o denominador estricto para per-capitas. |

---

## 3. Data Mart Final Analítico (OBT: One-Big-Table)
### Tabla: `mart_desarrollo_social_economico_municipio_anio`
*(Grano: 1 fila = 1 Municipio por 1 Único Año donde hubo al menos presencia transversal)*

Mantiene una conjunción `LEFT JOIN` con todas las métricas de Facts y descriptores de Dimensión listados estáticamente. Mapeo derivado exclusivo de la OBT:

| Fórmula / Variables Derivadas Vectorizadas | Lógica Analítica |
|--------------------------------------------|--------------------|
| `indicador_inversion_per_capita` | `(inversion_total_monto) / NULLIF(poblacion_total_proyectada, 1)` <br> Demuestra intensidad de gasto público real controlando por tamaño pob. |
| `indicador_densidad_micronegocios`| `volumen_micronegocios_exp / NULLIF(poblacion_total_proyectada, 1)` <br> Representa penetración/arraigo popular per cápita del municipio en cuestión en la economía microscópica |
