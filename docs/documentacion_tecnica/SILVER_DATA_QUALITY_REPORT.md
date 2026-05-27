# REPORTE DE CALIDAD DE DATOS - CAPA SILVER

> Este reporte audita el proceso de transformación, homologación y agregación espacial (grano: Municipio-Año).

## Fuente: CNPV
**Estado:** SUCCESS

- **Archivo generado:** `silver_cnpv_agregado.parquet`
- **Registros consolidados (Grano Municipio-Año):** 1,122
- **Completitud (Nulls en variables clave):** {'divipola_key': 0, 'anio_key': 0}
- **Unicidad (PK):** 0 duplicados.
- **Reglas Aplicadas:** Construccion DIVIPOLA = U_DPTO(2) + U_MPIO(3). Conteo de registros censados por municipio. anio_key=2018 fijo.

---
## Fuente: EMICRON
**Estado:** SUCCESS

- **Archivo generado:** `silver_emicron_agregado.parquet`
- **Registros consolidados (Grano Municipio-Año):** 150
- **Completitud (Nulls en variables clave):** {'divipola_key': 0, 'anio_key': 0}
- **Unicidad (PK):** 0 duplicados.
- **Factores fallback EMICRON aplicados:** 2019 usa `fex_c` desde `emicron_fex_proyecciones_cnpv_2018_2019_2019_raw.parquet` (25 filas, suma 6,025,575.23); 2020 usa `fex_c` desde `emicron_fex_proyecciones_cnpv_2018_2020_2020_raw.parquet` (25 filas, suma 5,631,123.07).
- **Reglas Aplicadas:** Uso exclusivo del modulo autoritativo para evitar multiplicar unidades muestrales. Deduplicacion por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio). SUM(factor_expansion) -> volumen expandido de micronegocios por depto-anio; factor_expansion usa F_EXP valido o fallback fex_c/FEX_C/fex_micro_dpto fusionado desde archivos de factores.

---
## Fuente: SECOP_I
**Estado:** SUCCESS

- **Archivo generado:** ``
- **Registros consolidados (Grano Municipio-Año):** 9,031
- **Completitud (Nulls en variables clave):** {'divipola_key': 0, 'anio_key': 0}
- **Unicidad (PK):** 0 duplicados.
- **Reglas Aplicadas:** Normalizacion nombres de columnas reales (UID, Cuantia Contrato, Fecha de Firma del Contrato, Identificacion del Contratista). DIVIPOLA desde divipola_key_mapped o lookup Municipio+Departamento. Limpieza de formato moneda colombiano. NIT a solo digitos. Agregado con COUNT(DISTINCT nit) intra-plataforma y output transaccional para union posterior con SECOP II.

---
## Fuente: SECOP_II
**Estado:** SUCCESS

- **Archivo generado:** ``
- **Registros consolidados (Grano Municipio-Año):** 4,711
- **Completitud (Nulls en variables clave):** {'divipola_key': 0, 'anio_key': 0}
- **Unicidad (PK):** 0 duplicados.
- **Reglas Aplicadas:** Normalizacion nombres reales (ID Contrato, Fecha de Firma, Valor del Contrato, Documento Proveedor). DIVIPOLA desde divipola_key_mapped o lookup Departamento+Ciudad. NIT a solo digitos. Output transaccional para union posterior sin doble conteo.

---
## Fuente: PROYECCIONES
**Estado:** SUCCESS

- **Archivo generado:** `silver_proyecciones_agregado.parquet`
- **Registros consolidados (Grano Municipio-Año):** 1,089
- **Completitud (Nulls en variables clave):** {'divipola_key': 0, 'anio_key': 0}
- **Unicidad (PK):** 0 duplicados.
- **Reglas Aplicadas:** Filtrado por AREA='Total'. Limpieza de formato numérico (separador de miles). Agregación a departamento-año.

---
