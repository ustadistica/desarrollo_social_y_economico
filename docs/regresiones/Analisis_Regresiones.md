# Análisis de Regresiones: SECOP y Censo DANE

## 1. Descripción del Proyecto

Este proyecto analiza la relación entre la inversión pública municipal
en Colombia (SECOP) y la vulnerabilidad sociodemográfica (DANE, Censo
2018), utilizando modelos econométricos implementados en PySpark.

El objetivo es identificar si la asignación de recursos públicos
responde a condiciones estructurales de pobreza a nivel territorial.

------------------------------------------------------------------------

## 2. Fuentes de Datos

-   SECOP: información de contratación pública (montos y número de
    contratos)
-   DANE: indicadores sociales
    -   Índice de Pobreza Multidimensional (IPM)
    -   Necesidades Básicas Insatisfechas (NBI)

Los datos fueron integrados en un dataset unificado en formato Parquet.

------------------------------------------------------------------------

## 3. Tecnologías y Arquitectura

-   Python\
-   PySpark (Spark SQL y MLlib)\
-   Procesamiento distribuido

El pipeline se ejecuta localmente sobre Spark, permitiendo manejar
grandes volúmenes de datos.

------------------------------------------------------------------------

## 4. Preparación de Datos

El script realiza:

-   Carga del dataset en formato Parquet\
-   Limpieza de datos y manejo de valores nulos\
-   Conversión de variables a formato numérico\
-   Cálculo de variables derivadas:
    -   población estimada\
    -   inversión per cápita\
    -   logaritmo de inversión\
-   Creación de variable binaria de alta inversión (por mediana)

Se construye un vector de características con IPM y NBI para el
modelado.

------------------------------------------------------------------------

## 5. Modelos Implementados

### 5.1 Regresión Lineal (OLS)

Variable dependiente: - Logaritmo de inversión per cápita

Resultados: - R²: 0.003 - IPM no significativo - NBI significativo
(efecto positivo)

Interpretación: La pobreza estructural no explica la asignación de
inversión. Solo las carencias específicas muestran una relación débil.

------------------------------------------------------------------------

### 5.2 Modelo de Conteo (Poisson)

Variable dependiente: - Número de contratos

Resultados: - IPM negativo y significativo - NBI positivo y
significativo

Interpretación: Los municipios más pobres gestionan menos contratos,
mientras que mayores carencias básicas generan mayor actividad
contractual de tipo reactivo.

------------------------------------------------------------------------

### 5.3 Regresión Logística (Logit)

Variable dependiente: - Alta inversión (binaria)

Resultados: - IPM reduce la probabilidad de alta inversión - NBI efecto
positivo débil

Interpretación: Existe una barrera estructural que limita el acceso a
grandes inversiones en territorios con mayor pobreza.

------------------------------------------------------------------------

## 6. Descripción del Código

El script principal incluye:

-   Inicialización de Spark y configuración del entorno (Java y Hadoop)
-   Carga del dataset consolidado
-   Transformaciones de variables clave
-   Construcción del vector de features con `VectorAssembler`
-   Entrenamiento de modelos:
    -   LinearRegression
    -   GeneralizedLinearRegression (Poisson)
    -   LogisticRegression
-   Impresión de coeficientes, métricas y resultados

El flujo ejecuta todo el pipeline de forma secuencial.

------------------------------------------------------------------------

## 7. Ejecución del Proyecto

Requisitos:

-   Python 3.x\
-   Java 11\
-   Apache Spark\
-   Variables de entorno configuradas (JAVA_HOME, HADOOP_HOME)

Ejecución:

``` bash
python main.py
```

------------------------------------------------------------------------

## 8. Conclusiones

Los resultados evidencian:

-   Desconexión entre pobreza estructural e inversión pública\
-   Menor acceso al sistema de contratación en municipios más
    vulnerables\
-   Concentración de inversión en territorios menos pobres

Esto sugiere limitaciones institucionales y técnicas en la asignación de
recursos.

------------------------------------------------------------------------

## 9. Autoría

-   Desarrollo del modelo: Lizeth Villamil\
-   Documentación y análisis: Autor del repositorio
