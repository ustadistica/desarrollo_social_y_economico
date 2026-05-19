# Análisis Exploratorio del Desempeño Económico del Micronegocio Colombiano
## EMICRON 2019-2024 — DANE

> **Proyecto:** Desarrollo Social y Económico — Universidad Santo Tomás  
> **Fecha:** Mayo 2026  
> **Fuente:** Encuesta de Micronegocios (EMICRON) — DANE  
> **Pipeline:** Bronze → Silver → Gold — Arquitectura Medallion

---

## 1. Resumen Ejecutivo

El presente informe presenta los resultados del análisis exploratorio del desempeño económico de los micronegocios colombianos utilizando datos de la Encuesta de Micronegocios (EMICRON) del DANE para el período 2019-2024. Se procesaron **496.274 registros** de 25 departamentos del país, integrando los módulos de ventas, costos e identificación mediante la arquitectura de datos Medallion.

| Indicador | Valor |
|---|---|
| Registros procesados (6 años) | 496.274 |
| Micronegocios con actividad económica | 92.2% |
| Micronegocios rentables | 90.8% |
| Ingreso mediano mensual | $1.200.000 COP |
| Margen de utilidad mediano | 69.2% |
| Prima de formalización | +151.9% más ingreso si registrado |
| Departamentos cubiertos | 25 |
| Años analizados | 2019 — 2024 |

---

## 2. Metodología

### 2.1 Fuente de Datos

| Elemento | Descripción |
|---|---|
| Fuente | EMICRON 2019-2024 — DANE (Bronze layer) |
| Módulos usados | Ventas/Ingresos, Costos/Gastos, Identificación y Clasificación Económica |
| Llave de cruce | DIRECTORIO + SECUENCIA_ENCUESTA + SECUENCIA_P |
| Ponderación | Factor de expansión `F_EXP` — media ponderada `wmean()` en todos los indicadores |
| Variables clave | `VENTAS_MES_ANTERIOR`, `COSTOS_MES_ANTERIOR`, `P3031` (tipo persona), `P3000` (registro mercantil) |
| Cobertura geográfica | 25 departamentos con representación estadística departamental |

### 2.2 Indicadores Calculados

| Indicador | Fórmula | Tipo |
|---|---|---|
| Ingreso promedio ponderado | `wmean(VENTAS_MES_ANTERIOR, F_EXP)` | Continuo (COP) |
| Utilidad mensual | `VENTAS_MES_ANTERIOR − COSTOS_MES_ANTERIOR` | Continuo (COP) |
| Margen de utilidad | `(UTILIDAD / VENTAS) × 100` | Porcentaje |
| % Negocios rentables | `UTILIDAD > 0` | Binario / Proporción |
| Índice de formalización | `P3000 = 1` (Registrado en Cámara de Comercio) | Binario |

> **Nota metodológica:** Todos los indicadores se calculan aplicando el factor de expansión `F_EXP`, lo que permite obtener estimaciones representativas de la población total de micronegocios en cada departamento.

---

## 3. Estadísticas Descriptivas Generales

| Estadístico | Ingresos (COP) | Costos (COP) | Utilidad (COP) | Margen (%) |
|---|---|---|---|---|
| **Registros** | 496.274 | 496.274 | 496.274 | 457.791 |
| **Media** | $2.446.538 | $1.128.772 | $1.317.766 | 61.0% |
| **Desv. Estándar** | $8.102.909 | $5.704.849 | $4.527.400 | 252.0% |
| **Mínimo** | $0 | $0 | -$435.000.000 | -67.400% |
| **Percentil 10** | $89.930 | $0 | $25.000 | 29% |
| **Percentil 25** | $433.333 | $20.000 | $250.000 | 47% |
| **Mediana (50%)** | $1.000.000 | $230.000 | $700.000 | 69% |
| **Percentil 75** | $2.200.000 | $800.000 | $1.420.000 | 92% |
| **Percentil 90** | $5.000.000 | $2.000.000 | $2.900.000 | 100% |
| **Máximo** | $1.200.000.000 | $743.000.000 | $900.000.000 | 100% |

**Indicadores clave:**
- Negocios activos (ventas > 0): **92.2%**
- Negocios rentables: **90.8%**
- Ingreso mediano mensual: **$1.200.000 COP**
- Costo mediano mensual: **$281.250 COP**
- Utilidad mediana mensual: **$772.000 COP**
- Margen de utilidad mediano: **69.2%**

**Interpretación:**
- **Alta desigualdad interna:** La desviación estándar de ingresos ($8.1M) es más de 3 veces la media ($2.4M), evidenciando una distribución extremadamente heterogénea entre micronegocios.
- **Sesgo pronunciado:** La media de ingresos ($2.4M) duplica la mediana ($1.0M), confirmando que pocos negocios con ingresos altos elevan el promedio sin representar la realidad del micronegocio típico.
- **Costos bajos:** La mediana de costos ($230.000) refleja que la mayoría opera con estructura de costos mínima — principalmente trabajo familiar sin insumos costosos.
- **Implicación metodológica:** Dado el sesgo pronunciado, la **mediana** es el estadístico más apropiado para describir el micronegocio típico colombiano.

---

## 4. Figura 1 — Distribución de Ingresos, Costos y Utilidad

![Figura 1 — Distribución de Ingresos, Costos y Utilidad](../src/visualizacion/fig1_distribucion.png)

*Histogramas de ingresos, costos y utilidad mensual. Línea roja = mediana | Línea naranja = media. EMICRON 2019-2024, DANE.*

**Interpretación:**
- **Ingresos:** Fuertemente sesgados a la derecha. La concentración está entre $0 y $2M/mes, con cola larga hacia valores altos. La mediana ($1.0M) está muy por debajo de la media ($2.4M), confirmando que pocos micronegocios con ingresos altos distorsionan el promedio.
- **Costos:** Aún más concentrados en valores bajos. La mediana de costos ($230.000) refleja que la mayoría opera con estructura de costos mínima — principalmente trabajo familiar.
- **Utilidad:** La mayor parte de observaciones se ubica entre $0 y $1.5M positivo. La línea del punto de equilibrio (utilidad = 0) muestra que la mayoría opera en terreno positivo, confirmando el 90.8% de negocios rentables.

---

## 5. Figura 2 — Evolución Temporal 2019-2024

![Figura 2 — Evolución Temporal](../src/visualizacion/fig2_evolucion_temporal.png)

*Evolución de ingresos, costos, utilidad y % rentables. Zona gris = período pandemia COVID-19 (2020-2021). EMICRON 2019-2024, DANE.*

**Interpretación:**
- **Ingresos y costos:** Tendencia creciente sostenida de 2019 a 2024, con caída visible en 2020-2021 por el COVID-19. Los costos crecen a menor ritmo, preservando el margen.
- **Utilidad promedio:** Positiva en todos los años. La caída en 2020-2021 es clara. La recuperación desde 2022 supera los niveles pre-pandemia, evidenciando resiliencia del sector.
- **Margen de utilidad mediano:** Se mantiene por encima del 60% en todo el período, con leve reducción en 2020-2021.
- **% Micronegocios rentables:** Estable por encima del 88% en todos los años. La pandemia redujo marginalmente este porcentaje sin cambios dramáticos.
- **Conclusión:** El sector demostró alta resiliencia ante el choque pandémico, con recuperación completa hacia 2022-2024.

---

## 6. Figura 3 — Desempeño Económico por Departamento

![Figura 3 — Desempeño por Departamento](../src/visualizacion/fig3_departamentos.png)

*Ingreso promedio mensual ponderado y margen de utilidad mediano por departamento. EMICRON 2019-2024, DANE.*

| Ranking | Departamento (Ingreso) | Departamento (Margen) |
|---|---|---|
| 🥇 1° | Boyacá | Caldas |
| 🥈 2° | Bogotá D.C. | Risaralda |
| 🥉 3° | San Andrés | San Andrés |

**Mediana nacional de margen: 70.0%**

**Interpretación:**
- **Liderazgo en ingresos:** Boyacá, Bogotá D.C. y San Andrés encabezan el ranking, reflejando mayor capacidad productiva en estas regiones.
- **Liderazgo en margen:** Caldas, Risaralda y San Andrés tienen los márgenes más altos. El Eje Cafetero destaca por eficiencia en la relación ingresos-costos.
- **Disociación ingreso-margen:** No existe correlación perfecta entre mayor ingreso y mayor margen, sugiriendo estructuras de costos más complejas en departamentos de mayor ingreso.
- **Heterogeneidad territorial:** La variación entre el departamento de mayor y menor ingreso evidencia la necesidad de políticas territoriales diferenciadas.

---

## 7. Figura 4 — Formalización y Tipo de Persona

![Figura 4 — Formalización](../src/visualizacion/fig4_formalizacion.png)

*Ingreso promedio por registro mercantil, distribución por tipo de persona e ingreso cruzado. EMICRON 2019-2024, DANE.*

| Categoría | Ingreso Promedio Ponderado | Diferencia |
|---|---|---|
| **Registrado** (con Cámara de Comercio) | **$5.940.000 COP/mes** | +151.9% |
| **No registrado** (informal) | $2.360.000 COP/mes | — |

**Interpretación:**
- **Prima de formalización:** Los micronegocios registrados ganan **$5.94M/mes** vs **$2.36M** los no registrados. La diferencia del **151.9%** es el hallazgo más robusto del análisis.
- **Distribución por tipo de persona:** Las personas jurídicas presentan mayor dispersión de ingresos — existen tanto micronegocios jurídicos muy exitosos como con dificultades.
- **Cruce tipo × formalización:** En ambos tipos de persona, los registrados tienen ingresos significativamente mayores. La brecha es más pronunciada en personas jurídicas.
- **Implicación de política:** Programas de formalización empresarial podrían tener alto retorno en términos de mejora del ingreso para los microempresarios colombianos.

---

## 8. Figura 5 — Ingreso vs Margen por Departamento

![Figura 5 — Scatter Ingreso vs Margen](../src/visualizacion/fig5_scatter_deptos.png)

*Relación entre ingreso promedio y margen de utilidad por departamento. Tamaño del punto = volumen de micronegocios. EMICRON 2019-2024, DANE.*

**Interpretación:**
- **Cuatro perfiles departamentales:** Los cuadrantes identifican: (1) alto ingreso y alto margen — más competitivos, (2) alto ingreso y bajo margen — eficientes en escala pero con costos altos, (3) bajo ingreso y alto margen — pequeños pero eficientes, (4) bajo ingreso y bajo margen — más vulnerables.
- **Relación no lineal:** No existe correlación lineal clara entre ingreso y margen. Mayores ingresos no garantizan mayor rentabilidad relativa.
- **Priorización territorial:** Los departamentos del cuadrante inferior izquierdo requieren intervención prioritaria, mientras los del cuadrante superior derecho pueden servir como casos de éxito replicables.

---

## 9. Hallazgos Principales

1. **Alta actividad económica:** El 92.2% reportó ventas positivas y el 90.8% opera con utilidad positiva, indicando un sector altamente activo aunque con ingresos bajos.
2. **Desigualdad interna pronunciada:** La media ($2.4M) duplica la mediana ($1.0M). El micronegocio típico gana $1.0M/mes.
3. **Resiliencia ante el COVID-19:** La recuperación fue completa hacia 2022 y los niveles 2023-2024 superan los pre-pandemia.
4. **Heterogeneidad territorial:** Boyacá, Bogotá D.C. y San Andrés lideran en ingresos. Caldas y Risaralda en margen.
5. **Prima de formalización del 151.9%:** Los registrados ganan $5.94M/mes vs $2.36M de los informales — hallazgo más robusto con mayor implicación de política pública.
6. **Margen mediano alto (69.2%):** Aunque los ingresos son bajos, los costos también lo son, sugiriendo viabilidad económica del sector.

---

## 10. Conclusiones

### 10.1 Viabilidad económica
Los micronegocios colombianos son económicamente viables — más del 90% opera con utilidad positiva. Sin embargo, la escala de ingresos es insuficiente para generar bienestar significativo para los hogares dependientes de este sector.

### 10.2 Formalización como palanca de desarrollo
La diferencia del 151.9% en ingresos entre formalizados e informales es el argumento más sólido para promover programas de formalización empresarial como estrategia de reducción de brechas económicas.

### 10.3 Resiliencia sectorial
El sector demostró capacidad de recuperación ante el COVID-19, con retorno completo a tendencias pre-pandemia hacia 2022.

### 10.4 Brechas territoriales
La heterogeneidad inter-departamental es significativa. Se requieren intervenciones territorialmente diferenciadas que atiendan las particularidades de cada región.

---

## 11. Limitaciones

- EMICRON no tiene cobertura municipal — el análisis es a nivel departamental.
- Los datos de formalización (`P3031`, `P3000`) solo están disponibles en algunos años de la encuesta.
- Los ingresos reportados pueden subestimar la realidad por subdeclaración en negocios informales.
- La relación entre formalización e ingresos es correlacional, no necesariamente causal.
- La cobertura EMICRON excluye departamentos con baja densidad poblacional.

---

## Archivos Relacionados

| Archivo | Descripción |
|---|---|
| `notebooks/ANALISIS_INDICADOR_EMICRON.ipynb` | Notebook completo con código y gráficas |
| `src/visualizacion/fig1_distribucion.png` | Distribución de ingresos, costos y utilidad |
| `src/visualizacion/fig2_evolucion_temporal.png` | Evolución temporal 2019-2024 |
| `src/visualizacion/fig3_departamentos.png` | Desempeño por departamento |
| `src/visualizacion/fig4_formalizacion.png` | Análisis por formalización y tipo de persona |
| `src/visualizacion/fig5_scatter_deptos.png` | Scatter ingreso vs margen por departamento |

---

*Análisis elaborado con datos del DANE — EMICRON 2019-2024*  
*Pipeline de datos: Bronze → Silver → Gold — Arquitectura Medallion*  
*Proyecto: Desarrollo Social y Económico — Universidad Santo Tomás | Mayo 2026*
