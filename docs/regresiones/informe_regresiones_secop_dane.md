# Informe de Regresiones: Cruce SECOP y Censo DANE

El objetivo de este análisis dentro del **Observatorio de Desarrollo Social y Económico** consistió en evaluar la relación entre la inversión pública municipal (SECOP) y la vulnerabilidad sociodemográfica medida a través del Índice de Pobreza Multidimensional (IPM) y las Necesidades Básicas Insatisfechas (NBI).

Para esto, se implementó una arquitectura de *Machine Learning* sobre **PySpark** con modelos lineales generalizados, buscando comprender la desigualdad territorial y las fallas del sistema de contratación estatal o su respuesta solidaria.

---

## 1. Regresión Lineal (MCO / OLS)
**Variable Dependiente:** *Logaritmo de la Inversión Per Cápita* (Continua).

> [!NOTE]
> **Justificación Metodológica:**
> Debido a que la cantidad de dinero que invierte el Estado es una variable fuertemente asimétrica (pocos reciben mucho y muchos poco), se transformó logarítmicamente ($log(1+x)$). El MCO es el modelo fundacional adecuado para responder la pregunta lineal: *"¿Varía estadísticamente el monto per cápita asignado según los niveles de pobreza?"*.

### Interpretación de Resultados (PySpark OLS)
```text
>> Parámetros: IPM (-0.0038), NBI (0.0018)
>> P-values: IPM (0.457), NBI (0.007**)
>> R-cuadrado: 0.003
```
*   **Bondad de Ajuste:** El modelo presenta un coeficiente de determinación nulo ($R^2=0.3\%$), evidenciando que la vulnerabilidad social no explica sustancialmente la dispersión en los presupuestos públicos a nivel nacional.
*   **Significancia:** El IPM **no** resulta significativo ($p=0.457$), lo cual es llamativo ya que significa que las asignaciones presupuestales masivas son indiferentes a la pobreza extrema macro de los municipios. No obstante, el NBI sí resulta significativo ($p=0.007$), denotando que la falta puntual de vivienda o servicios (NBI) sí correlaciona débilmente con inyecciones de presupuesto directo.

---

## 2. Modelo de Conteo (Poisson GLM)
**Variable Dependiente:** *Número total de contratos adjudicados por municipio* (Conteo).

> [!TIP]
> **Justificación Metodológica:**
> Al modelar el número de veces que se firman contratos, no podemos aplicar un modelo continuo (como OLS), ya que no existen los "contratos negativos". Se aplicó la regresión de **Poisson** porque evalúa la "tasa matemática de ocurrencia", ideal para descubrir la fluidez e hiper-suscripción burocrática del mercado SECOP.

### Interpretación de Resultados (PySpark Poisson)
```text
>> Parámetros: IPM (-4.7689***), NBI (2.7103***)
>> P-values: [0.000, 0.000, 0.000]
```
*   Este fue el modelo más exitoso, con todos los coeficientes resultando **altamente significativos** ($p<0.001$).
*   **Efecto del IPM (Trampa Burocrática):** A mayor Pobreza Multidimensional global, la cantidad de contratos adjudicados cae abismalmente ($\beta = -4.76$). Refleja empíricamente que los municipios con pobreza crítica estructural tramitan sustancialmente **menos** contratos de SECOP, derivado presuntamente de fallas técnicas territoriales para formular proyectos con el Estado o abandono del sector privado.
*   **Efecto del NBI:** Inversamente, frente a carencias puntuales de Necesidades Básicas (NBI), la cantidad de contratos sube ($\beta = 2.71$). Se hipotetiza que se trata de contratación pequeña/directa y paliativa a corto plazo (ayudas inmediatas o suministros locales básicos).

---

## 3. Modelo de Regresión Logística (Logit)
**Variable Dependiente:** *Alta Inversión Gubernamental* (Binaria: 1 = Superior a la Mediana, 0 = Inferior a la Mediana).

> [!IMPORTANT]
> **Justificación Metodológica:**
> Esta regresión mide la concentración estocástica del SECOP aislando probabilísticamente los montos mediante un clasificador binario (Logit). En lugar de predecir montos crudos, predice la **probabilidad de éxito** u *Odds Ratio* de que una región logre atraer o captar financiamiento sobresaliente respecto de sus pares nacionales dependiendo de sus métricas de pobreza.

### Interpretación de Resultados (PySpark Logit)
```text
>> Parámetros: IPM (-0.087*), NBI (0.0489)
>> P-values: Significativo en IPM (~0.037)
```
*   **Preferencia Institucional Estructural:** Por cada incremento porcentual en el IPM, el *Log-Odds* municipal de recibir alta inversión disminuye en $-0.087$. Es decir, empíricamente se reafirman las barreras de concentración financiera: las zonas históricamente más pobres y vulnerables experimentan sistemáticas reducciones (o caídas en probabilidad estadística) para acceder a intervenciones económicas supra-mayoritarias por parte del Gobierno Central o presupuestos territoriales.

---

### Conclusión General para el Observatorio
La evidencia extraída a través del Data Engineering en PySpark testifica grandes brechas de exclusión. Aunque el NBI puede estimular compras emergentes menores, la verdadera y compleja **pobreza integral municipal (IPM)** actúa como un lastre estructural, alejando al territorio del ecosistema de Contratación Estatal (menos contratos totales y menos probabilidad de inversiones gigantes per cápita). Esto apalanca la necesidad de descentralizar la burocracia técnica y apoderar a los municipios empobrecidos para estructurar proyectos.
