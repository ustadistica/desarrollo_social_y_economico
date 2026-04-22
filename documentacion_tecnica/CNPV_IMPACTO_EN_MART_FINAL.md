# Impacto del CNPV en el Mart Final (OBT)

**Fecha:** 2026-04-21

La ingesta y consolidación del CNPV no es "decorativa". Es el ancla poblacional inmutable (Censo base) que habilita las per-cápitas de 2018 para contrastes del modelo socioeconómico. 

## 1. Variables Exclusivas Aportadas al OBT
El OBT final absorbe estrictamente una columna proveniente de `fact_censo`:
* **`poblacion_censo_2018`**: Esta columna es de vital importancia, porque el DANE utiliza el censo de 2018 como la base sobre la que se calculan y calibran las proyecciones interanuales (`fact_demografia` -> `poblacion_total_proyectada`).

## 2. Filas Impactadas en el Datamart (Densidad de Cruce)
Cuando el pipeline genera la One Big Table (`mart_desarrollo_social_economico...`), realiza los cruces `FULL OUTER JOIN` entre territorios. 
* Dado que el censo trae 1,122 municipios, el Datamart de Gold se expande instantáneamente para garantizar una fila por cada año-municipio base.
* Para el filtro específico del `anio_key == 2018`, **el 100% de los 1,122 municipios** contendrá un valor numérico real no-nulo en la variable `poblacion_censo_2018`.
* Para otros años (ej. 2020), la variable censal natural es `NULL` (al ser un evento puntual de un año). El equipo de BI deberá utilizar una función analítica de relleno o ventana (`LAST_VALUE` / `FIRST_VALUE` ignorando nulos en el dashboard) si desean mostrar el valor censal junto con métricas proyectadas en años posteriores, o dejarla exclusiva del año 2018.

## 3. Conclusión de Integración
La integración de CNPV es **Amplia y Fundamental**, no marginal. Si el censo faltara, el OBT dependería exclusivamente de la tabla de proyecciones demográficas que, sin un conteo duro de calibración, carece de ancla observable oficial para 2018 a nivel estrictamente municipal.

**Estado:** Cerrado y verificado. No hay pérdidas estructurales en las ramas del cruce de datos.
