# REPORTE DE VALIDACIÓN Y CARGA - CAPA GOLD

> **Unidad de Integridad:** Granularidad estricta (Municipio-Año).
> Todas las relaciones son One-to-Many entre las Dimensiones y las Fact Tables.

## 1. Dimensiones Estandardizadas (Conformed Dimensions)
- **DIM_TIEMPO**: Estado `success` | Registros Inyectados: 12 | 🔑 Duplicados de PK: 0
- **DIM_TERRITORIO**: Estado `success` | Registros Inyectados: 1,155 | 🔑 Duplicados de PK: 0

## 2. Tablas de Hecho Consolidadas (Fact Tables)
- **FACT_DEMOGRAFIA**: Estado `success` | Registros Consolidados: 1,089 | 🔑 Duplicados de FK-Set: 0
- **FACT_MICRONEGOCIOS**: Estado `success` | Registros Consolidados: 150 | 🔑 Duplicados de FK-Set: 0
- **FACT_CONTRATACION**: Estado `success` | Registros Consolidados: 9,711 | 🔑 Duplicados de FK-Set: 0
- **FACT_CENSO**: Estado `success` | Registros Consolidados: 1,122 | 🔑 Duplicados de FK-Set: 0

## 3. Certificación del Modelo y Datamart Analítico Unificado
- **Estado de Ensamblaje OBT:** `success`
- **Filas del Cubo Final Analítico:** 13,860
- **Integridad Referencial Unívoca:** Se valida la NO duplicación del cruce Mpio-Año: N/A registros solapados.
- **Ruta Simbólica Entregada al Analista:** `data\gold\marts\latest\mart_desarrollo_social_economico_municipio_anio.parquet`
