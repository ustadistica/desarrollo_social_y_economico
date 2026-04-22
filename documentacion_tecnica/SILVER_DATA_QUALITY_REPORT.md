# REPORTE DE CALIDAD Y VALIDACIÓN — CAPA SILVER (ACTUALIZADO EVIDENCIA REAL)

**Ejecución:** 2026-04-21

## Resumen de Ejecución General
* **¿Corre sin error?** SÍ (Ejecución E2E completada vía `python -m pipeline silver`).
* **¿Genera tablas?** SÍ (Parquets generados en `datos/silver`).
* **¿Genera tablas no vacías?** SÍ (Excepto CNPV por diseño).

## Evidencia por Fuente

### 1. SECOP I
- **Estado Técnico:** `SUCCESS`
- **Artefacto:** `silver_secop_i_agregado.parquet` (y transaccional)
- **Registros:** 821 filas (agregadas por Municipio-Año).
- **Cobertura:** 16,228 contratos crudos procesados.
- **Calificación Metodológica:** Válido.

### 2. SECOP II
- **Estado Técnico:** `SUCCESS`
- **Artefacto:** `silver_secop_ii_agregado.parquet` (y transaccional)
- **Registros:** 462 filas (agregadas por Municipio-Año).
- **Cobertura:** 14,738 contratos crudos procesados.
- **Calificación Metodológica:** Válido.

### 3. EMICRON
- **Estado Técnico:** `SUCCESS`
- **Artefacto:** `silver_emicron_agregado.parquet`
- **Registros:** 25 filas (Agregados departamentales).
- **Cobertura:** Volumen expandido total = 5,297,252 micronegocios estimados.
- **Calificación Metodológica:** Válido (Uso de `F_EXP`).

### 4. PROYECCIONES POBLACIONALES
- **Estado Técnico:** `SUCCESS`
- **Artefacto:** `silver_proyecciones_agregado.parquet`
- **Registros:** 1,089 filas.
- **Cobertura:** 33 departamentos, horizonte 2018-2050.
- **Calificación Metodológica:** Válido.

### 5. CNPV (Censo 2018)
- **Estado Técnico:** `FAILED_SAFE` (Falta de datos en Bronze).
- **Artefacto Esperado:** `silver_cnpv_agregado.parquet`
- **Registros:** 0
- **Pendiente Oficial:** (Nivel Medio) Equipo de datos debe inyectar microdatos en `datos/bronze/cnpv/` según `PLAN_INGESTA_CNPV.md`.
