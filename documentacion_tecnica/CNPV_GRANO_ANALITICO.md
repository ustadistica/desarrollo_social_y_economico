# Grano Analítico CNPV y Consistencia de Proyecto

**Fecha:** 2026-04-21

Este documento certifica que el grano del Censo no colisiona con el del modelo general y está estandarizado.

## 1. Grano Oficial del Proyecto
La arquitectura Medallion para Desarrollo Social y Económico establece el **Datamart Final (OBT)** con el grano: `(Municipio, Año)`. 
Por lo tanto, la llave primaria conceptual del modelo estrella es `(divipola_key, anio_key)`.

## 2. Grano en Ingesta (Bronze CNPV)
El dataset original en `5PER` tiene grano **Persona**. Cada fila representa a un individuo encuestado.
* **Geografía Original:** Departamento (`U_DPTO`) y Municipio (`U_MPIO`).
* **Temporalidad Original:** Carece de columna explícita `AÑO`, ya que el censo representa exclusivamente la foto poblacional de `2018`.

## 3. Grano Transformado (Silver y Gold CNPV)
En el módulo `pipeline/silver/cleaners/clean_cnpv.py`, la transformación efectúa:
```python
df["divipola_key"] = df["__d"] + df["__m"] # Forzando a 5 dgitos zero-padded
df["anio_key"] = 2018
df_agrupado = df.groupby("divipola_key").size().reset_index(name="poblacion_total_base")
```

- **Grano Final de Silver y `fact_censo`:** `(Municipio, Año)`. Específicamente, `(Municipio, 2018)`.
- **Integración con Gold:** Al coincidir el grano del censo con la convención del Datamart final, la integración a través de un simple `LEFT JOIN` utilizando `dim_territorio` y `dim_tiempo` fluye perfectamente sin generar productos cartesianos (explosión de filas).

## Conclusión sobre Grano
**El Censo (CNPV) es el componente de mayor alineación analítica del proyecto.** Entra puro a nivel de `Municipio` a la tabla final (a diferencia de EMICRON que entra como agregado `Departamental` o las Proyecciones que se modelan inter-temporalmente). Su valor en 2018 actúa como la *Verdad Fundamental (Ground Truth)* que el OBT distribuye para calibrar indicadores.
