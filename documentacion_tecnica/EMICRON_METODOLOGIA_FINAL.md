# Metodología Final: Agregación de Encuesta de Micronegocios (EMICRON)

**Fecha:** 2026-04-21

La encuesta EMICRON, a diferencia del Censo Nacional de Población y Vivienda (CNPV), es una encuesta de tipo muestral. Tratar sus registros crudos de forma exhaustiva (como un censo poblacional) arrojaría un conteo subestimado de los micronegocios del país, dado que cada registro encuestado representa a múltiples negocios en la realidad (diseño muestral).

## 1. Identificación del Factor de Expansión
En la capa Silver, el pipeline no realiza conteos simples de filas (`COUNT(*)`). En su lugar, identifica dinámicamente la columna que provee el factor de expansión censal.

* **Variable principal buscada:** `F_EXP` (Factor de Expansión), con fallbacks a `FEX_C` o derivaciones.
* **Manejo de nulos:** Se aplica una imputación a `1.0` en caso de errores de lectura numéricos para evitar pérdida silenciosa de registros, aunque en datos estándar del DANE esta variable siempre viene poblada en formato *float*.

## 2. Granularidad y Limitación Geográfica
La encuesta EMICRON proporciona inferencia estadística representativa **a nivel departamental**, no municipal. 

* La variable geográfica presente en los microdatos es `COD_DEPTO` (2 dígitos). No existe ni `U_MPIO` ni `DIVIPOLA_MUNICIPIO`.
* **Solución adoptada (Fallback Analítico):** Para que EMICRON pueda cruzarse en el modelo estrella (cuya columna base temporal y territorial exige llaves a nivel municipal de 5 dígitos), la llave sintética se construye añadiendo ceros:
  `divipola_key = COD_DEPTO + '000'`
* Esto indica claramente en las herramientas de BI que la métrica de micronegocios representa el agregado de todo el departamento, mapeado a una entidad "regional" dentro de la Dimensión Territorio (`Agregado Depto XX`).

## 3. Fórmula de Agregación Implementada
La agregación (realizada en `clean_emicron.py`) agrupa los datos válidos por `(COD_DEPTO, anio_key)` y aplica la suma sobre el factor de expansión.

```sql
-- Conceptualización de la lógica implementada
SELECT 
    (COD_DEPTO || '000') AS divipola_key,
    anio_key,
    SUM(F_EXP) AS volumen_micronegocios_exp
FROM emicron_raw
GROUP BY 1, 2
```

## 4. Indicadores en la Capa Gold (Datamart)
La tabla final `mart_desarrollo_social_economico_municipio_anio.parquet` toma esta estimación (`volumen_micronegocios_exp`) para generar indicadores secundarios ponderados:
* **`indicador_densidad_micronegocios`**: Se divide el volumen expandido de micronegocios sobre la proyección poblacional total (`poblacion_total_proyectada`).

## 5. Limitaciones Conocidas
- Al estar los datos de EMICRON a nivel departamental, la tabla de hechos final (`fact_micronegocios`) solo tiene registros para las "cabeceras/agregados departamentales". 
- Cualquier cruce directo a nivel municipal exacto producirá un valor nulo para EMICRON, debiendo los analistas usar un `rollup` o `window_function` a nivel departamento en el frontend BI si desean distribuir esta métrica a los municipios internos.
