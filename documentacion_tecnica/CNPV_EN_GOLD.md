# Integración del CNPV 2018 en el Modelo Gold (Datamart)

**Fecha:** 2026-04-21

La presente sección describe técnicamente cómo el Censo Nacional de Población y Vivienda converge en el producto analítico final.

## 1. Tabla Fact de Destino
El CNPV no crea un fact aislado, sino que conforma el artefacto `fact_censo_municipio.parquet` dentro de la capa Gold (`build_facts.py`). 

## 2. Granularidad
La granularidad de la ingesta base del CNPV se redujo intencionalmente de *nivel-persona* a **Municipio-Año**.
* **Municipio:** Mapeado bajo `divipola_key` a 5 dígitos (con fallback si el municipio originario no estaba en el catálogo primario de `dim_territorio`).
* **Año:** Estático a `2018` ya que el censo es un evento puntual.

## 3. Variables Aportadas
Actualmente, el pipeline consolida el módulo de personas (`5PER`) para extraer la métrica base:
* **`poblacion_censo_2018`** (Equivalente a la columna `poblacion_total_base` de Silver).

*(Nota técnica: En futuras iteraciones del modelo se pueden incorporar déficit cuantitativo/cualitativo desde el módulo de viviendas `1VIV` de forma plug-and-play).*

## 4. Relación con Proyecciones Demográficas
El DataMart Analítico (`OBT`) hace un `LEFT JOIN` con `fact_censo` usando como pivote `dim_territorio`.
Dado que el censo solo reporta para `2018`, esta variable es tratada como un indicador de **"línea base"**. El frontend de analítica (BI) puede contrastar `poblacion_censo_2018` contra `poblacion_total_proyectada` (proveniente de DANE-Proyecciones) para medir el error poblacional intercensal.

El Gold ya no arroja una tabla censal silenciosa en ceros, demostrando el end-to-end de un archivo físico del DANE hasta el indicador unificado.
