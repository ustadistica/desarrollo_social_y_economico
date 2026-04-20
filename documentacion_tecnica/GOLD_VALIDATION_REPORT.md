# REPORTE DE VALIDACIÓN Y CARGA - CAPA GOLD

> **Unidad de Integridad:** Granularidad estricta (Municipio-Año).
> Todas las relaciones son One-to-Many entre las Dimensiones y las Fact Tables.

## 1. Dimensiones Estandardizadas (Conformed Dimensions)
- **DIM_TIEMPO**: Estado `success` | Registros Inyectados: 30 | 🔑 Duplicados de PK: 0
- **DIM_TERRITORIO**: Estado `success` | Registros Inyectados: 0 | 🔑 Duplicados de PK: 0

## 2. Tablas de Hecho Consolidadas (Fact Tables)
- **FACT_DEMOGRAFIA**: Estado `failed_safe` | Registros Consolidados: 0 | 🔑 Duplicados de FK-Set: N/A
- **FACT_MICRONEGOCIOS**: Estado `failed_safe` | Registros Consolidados: 0 | 🔑 Duplicados de FK-Set: N/A
- **FACT_CONTRATACION**: Estado `failed_safe` | Registros Consolidados: 0 | 🔑 Duplicados de FK-Set: N/A

## 3. Certificación del Modelo y Datamart Analítico Unificado
- **Estado de Ensamblaje OBT:** `success`
- **Filas del Cubo Final Analítico:** 0
- **Integridad Referencial Unívoca:** Se valida la NO duplicación del cruce Mpio-Año: 0 registros solapados.
- **Ruta Simbólica Entregada al Analista:** `C:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\Desarrollo social y economico\desarrollo_social_y_economico\datos\oro\marts\latest\mart_desarrollo_social_economico_municipio_anio.parquet`
