# 🏆 Capa Gold - Modelo Estrella y Datamarts (BI-Ready)

La capa Gold constituye el producto final consolidado de analítica. Está blindada a nivel arquitectónico para proveer acceso instantáneo ("zero-compute" requerido por parte del usuario final) a las entidades relacionales que rigen el proyecto de **Sinergia Socioeconómica**.

## Modelo Dimensional Implementado

El DWH fue estructurado mediante un **Modelo Constelación Espacio-Temporal** soportado en Parquet.
El grano fundamental es la intersección `(divipola_key, anio_key)`. Las tablas se dividen en:

1. **Dimensiones Conformadas (`dim_territorio`, `dim_tiempo`)**: Otorgan la uniformidad de filtro (Slicing & Dicing) para impedir asimetría al comparar indicadores de gasto entre distintos marcos de tiempo.
2. **Tablas de Hechos (Facts)**: Contienen la pre-agregación aditiva generada impecablemente por la Capa Silver. Todo hecho (`fact_contratacion`, `fact_micronegocios`, `fact_demografia`) posee la pareja de foreign keys espaciales y la garantía de que **nunca inflará el join** si uno de los indicadores llegase a unificarse o faltar matemáticamente.

## El Artefacto Funcional: El OBT (One-Big-Table)
Dado que para científicos de datos en Python realizar constantes cruces incrementa el gasto de RAM local y fragmenta la lógica de indicadores derivados, el pipeline genera como producto cumbre de la capa Gold el **`mart_desarrollo_social_economico_municipio_anio.parquet`**.
Este Mart implementa todos los ratios derivados (ej. `indicador_inversion_per_capita`) mediante vectorización. 

## Ejecución del Pipeline:
```bash
python run_gold.py
```
*(Al finalizar, el reporte certificado será inyectado en la carpeta actual indicando cualquier infracción referencial).*
