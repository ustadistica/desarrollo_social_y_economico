# Justificación Metodológica de los Modelos de Regresión

En el marco del **Observatorio de Desarrollo Social y Económico**, el cruce de datos masivos entre el sistema de contratación pública (SECOP) y los indicadores sociodemográficos del DANE (Censo 2018, IPM, NBI) plantea el desafío de modelar fenómenos heterogéneos. 

Para lograr un análisis robusto y estadísticamente riguroso, se definió una arquitectura de *Machine Learning* basada en tres enfoques de regresión (implementados a través de la librería `pyspark.ml` para procesamiento distribuido). Cada modelo obedece a la naturaleza matemática de la variable respuesta (variable dependiente) que se busca explicar.

A continuación, se detalla la justificación técnica y teórica de la elección de cada modelo:

---

### 1. Modelo de Regresión Lineal (MCO / OLS)
**Variable Dependiente:** *Logaritmo de la Inversión Per Cápita* (Continua).

> [!NOTE]
> **Justificación Técnica:**
> La inversión de dinero público es una variable continua estrictamente positiva pero con una **asimetría muy pronunciada (sesgo a la derecha)**, debido a que pocos municipios concentran montos exorbitantes de recursos frente a una inmensa mayoría con presupuestos bajos.
>
> Al aplicar una transformación logarítmica ($log(1 + x)$), se normaliza la varianza del gasto de SECOP. El modelo de **Mínimos Cuadrados Ordinarios (OLS)** es el estándar de oro fundacional de la econometría moderna, permitiéndonos contestar la pregunta de manera lineal: *"¿Aumenta el volumen per cápita distribuido por el estado si el Índice de Pobreza Multidimensional de la región sube un punto porcentual?"*

---

### 2. Modelo de Regresión de Conteo (Poisson GLM)
**Variable Dependiente:** *Número total de contratos adjudicados* (Discreta de conteo).

> [!TIP]
> **Justificación Técnica:**
> El número de contratos tramitados en un municipio NO es una cantidad continua, es un valor entero ($0, 1, 2, 30, ...$). 
> Aplicar regresiones lineales tradicionales a *datos de conteo* genera errores metodológicos graves (como predecir que un municipio tiene "-2 contratos"). Por este motivo, se optó por un **Modelo Lineal Generalizado (GLM)** bajo la distribución de **Poisson**. 
>
> Este enfoque asume la medición analítica de "tasas de ocurrencia" o volumen institucional de contratación asociado con la vulnerabilidad social (NBI e IPM), ideal para identificar si la tracción burocrática se estanca en zonas desfavorecidas o por el contrario, fomenta la hiper-suscripción de proyectos menores.

---

### 3. Modelo de Regresión Logística (Logit)
**Variable Dependiente:** *Alta Inversión Gubernamental* (Binaria: 1 = Sí, 0 = No).

> [!IMPORTANT]
> **Justificación Técnica:**
> Muchas problemáticas estructurales sociodemográficas resultan más certeras al predecirse en forma probabilística que determinística. Para comprender esquemas de focalización y concentración, se sintetizó la inversión per cápita en una **variable categórica dicotómica** (donde 1 indica que el municipio recibe inversión económica superior a la mediana nacional, y 0 que no lo logra).
> 
> La regresión Logística (**Logit**) fue la seleccionada porque su función matemática (sigmoide) fuerza estocásticamente las salidas entre 0% y 100%. Así, el modelo nos permite aislar "cuál es la probabilidad matemática o el cambio en chance (*Odds Ratio*) de que una región disfrute de alta inversión debido solamente a un punto adicional en su índice NBI (Necesidades Básicas Insatisfechas)".
