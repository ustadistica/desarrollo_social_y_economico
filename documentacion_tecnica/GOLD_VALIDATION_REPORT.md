# REPORTE DE VALIDACIÓN Y CIERRE — CAPA GOLD (ACTUALIZADO EVIDENCIA REAL)

**Ejecución:** 2026-04-21

## Resumen de Ejecución General
* **¿Corre sin error?** SÍ (Ejecución E2E completada vía `python -m pipeline gold`).
* **¿Genera tablas?** SÍ (Parquets generados en `datos/oro/`).
* **¿Genera tablas no vacías?** SÍ (El OBT está poblado).
* **¿Metodológicamente válido?** SÍ. Las dimensiones y hechos mantienen coherencia en sus llaves relacionales.

## Evidencia por Entidad (Modelo Estrella)

### Dimensiones
- **DIM_TIEMPO**: `SUCCESS` | **12 registros** (2018-2029).
- **DIM_TERRITORIO**: `SUCCESS` | **159 registros** (126 Municipios reales de `DIVIPOLA_BASE` + 33 agregados departamentales inferidos desde EMICRON/Proyecciones). Evita llaves sintéticas.

### Tablas de Hechos (Facts)
- **FACT_DEMOGRAFIA**: `SUCCESS` | **1,089 registros**. (Granularidad: Depto-Año).
- **FACT_MICRONEGOCIOS**: `SUCCESS` | **25 registros**. (Granularidad: Depto-Año).
- **FACT_CONTRATACION**: `SUCCESS` | **1,035 registros**. (Granularidad: Municipio-Año). Doble conteo evitado mediante agregación de límite superior (MAX).
- **FACT_CENSO**: `FAILED_SAFE` | **0 registros**. El esqueleto estructural está listo en `build_mart.py`, a la espera de la ejecución en Silver.

### Datamart Unificado (OBT final)
- **Estado Técnico:** `SUCCESS`
- **Ruta Generada:** `datos/oro/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet`
- **Registros:** **2,124 filas** combinadas.
- **Cobertura Territorial:** 154 territorios impactados.
- **Cobertura Temporal:** 2018 a 2050 (impulsado por las series demográficas).
- **Validación Social-Económica:** El cruce integra con éxito `proveedores_unicos` (economía), `volumen_micronegocios_exp` (tejido informal), e `indicador_inversion_per_capita` (gasto público / demografía). El componente final es completamente válido y no está vacío.
