# Interpretación de Resultados Econométricos

A continuación se presenta la lectura e interpretación estadística formal para los modelos ejecutados en PySpark sobre la base de datos fusionada (SECOP + DANE 2018).

---

### 1. Modelo de Regresión Lineal (OLS): Inversión Per Cápita
```text
>> Parámetros: IPM (-0.0038), NBI (0.0018)
>> P-values: IPM (0.457), NBI (0.007**)
>> R-cuadrado: 0.003
```
**Interpretación:**
El modelo lineal presenta un coeficiente de determinación ($R^2$) prácticamente nulo (0.3%), lo cual indica que la vulnerabilidad social por sí sola no explica la varianza en la cantidad de dinero público invertido per cápita. 
Sin embargo, analizando las variables individualmente:
*   **Índice de Pobreza Multidimensional (IPM):** No es estadísticamente significativo ($p=0.457$ > 0.05). Matemáticamente, el IPM de un municipio no tiene un impacto lineal predecible sobre el presupuesto per cápita que recibe.
*   **Necesidades Básicas Insatisfechas (NBI):** Resulta **altamente significativo ($p=0.007$)** y con un coeficiente positivo. Esto sugiere empíricamente que, al desglosar por necesidades básicas críticas (como falta de servicios o vivienda), el Estado sí percibe una leve presión para inyectar recursos económicos marginales.

---

### 2. Modelo de Conteo (Poisson GLM): Volumen de Contratación
```text
>> Parámetros: IPM (-4.7689***), NBI (2.7103***)
>> P-values: [0.000, 0.000, 0.000]
```
**Interpretación:**
Este ha sido el modelo metodológicamente más exitoso y robusto de la prueba, ya que todas sus variables son **altamente significativas ($p<0.001$)**. Al estar parametrizado con una función de enlace logarítmica (Poisson), los coeficientes representan cambios en las tasas de aparición (número de contratos).
*   **Efecto Negativo del IPM:** A mayor Pobreza Multidimensional global, la cantidad de contratos tramitados por la jurisdicción cae abruptamente en su escala logarítmica ($\beta = -4.76$). Esto sugiere una trampa burocrática: *los municipios más pobres de manera estructural tienen menos capacidad administrativa para formular, gestionar y adjudicar procesos de SECOP*.
*   **Efecto Positivo del NBI:** De forma contrastante, la elevación de Necesidades Básicas en un municipio estimula positivamente el volumen de contratación ($\beta = 2.71$). Se hipotetiza que esto obedece a un mayor fraccionamiento de contratos pequeños (contratación directa de baja cuantía o emergencias) para intentar suplir carencias inmediatas.

---

### 3. Modelo Logit: Probabilidad de Inversión por encima del Promedio
```text
>> Parámetros: IPM (-0.087*), NBI (0.0489)
```
**Interpretación:**
Este modelo evalúa el cambio en la probabilidad o "Chance" (Odds) de que un municipio logre pertenecer a la "filiación de alta inversión".
*   El **IPM** vuelve a fungir como un obstáculo estructural: por cada aumento en el índice de pobreza, el *log-odds* de recibir alta inversión decrece en $-0.087$. Es decir, empíricamente, **la pobreza extrema reduce la probabilidad matemática de que una región consiga presupuestos sobresalientes por parte del Estado.**
*   El **NBI** presenta un coeficiente positivo pero muy débil.

### Conclusión General para el Observatorio
La evidencia econométrica extraída con PySpark avala fuertemente una tesis de **desigualdad y capacidad institucional:** La verdadera pobreza integral (IPM) aleja a los municipios del sistema SECOP (menos contratos y disminuye la probabilidad de alta inversión) debido presumiblemente a la falta de competencias técnicas territoriales para la estructuración de proyectos estatales.
