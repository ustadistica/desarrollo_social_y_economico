# REPORTE DE CALIDAD — CAPA SILVER

## CNPV
**Estado:** SUCCESS

- Registros: 1,122
- Duplicados llave territorial-anual: 0
- Nulos de llaves críticas: divipola_key=0, anio_key=0
- Reglas aplicadas: Construccion DIVIPOLA = U_DPTO(2) + U_MPIO(3). Conteo de registros censados por municipio. anio_key=2018 fijo.

---
## EMICRON
**Estado:** SUCCESS

- Registros: 150
- Duplicados llave territorial-anual: 0
- Nulos de llaves críticas: divipola_key=0, anio_key=0
- Factores fallback EMICRON aplicados:
  - anio=2019, columna=fex_c, fuente=emicron_fex_proyecciones_cnpv_2018_2019_2019_raw.parquet, filas=25, suma_factor=6,025,575.23
  - anio=2020, columna=fex_c, fuente=emicron_fex_proyecciones_cnpv_2018_2020_2020_raw.parquet, filas=25, suma_factor=5,631,123.07
- Reglas aplicadas: Uso exclusivo del modulo autoritativo para evitar multiplicar unidades muestrales. Deduplicacion por (DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio). SUM(factor_expansion) -> volumen expandido de micronegocios por depto-anio; factor_expansion usa F_EXP valido o fallback fex_c/FEX_C/fex_micro_dpto fusionado desde archivos de factores.

---
## SECOP_I
**Estado:** SUCCESS

- Registros: 9,031
- Duplicados llave territorial-anual: 0
- Nulos de llaves críticas: divipola_key=0, anio_key=0
- Reglas aplicadas: Normalizacion nombres de columnas reales (UID, Cuantia Contrato, Fecha de Firma del Contrato, Identificacion del Contratista). DIVIPOLA desde divipola_key_mapped o lookup Municipio+Departamento. Limpieza de formato moneda colombiano. NIT a solo digitos. Agregado con COUNT(DISTINCT nit) intra-plataforma y output transaccional para union posterior con SECOP II.

---
## SECOP_II
**Estado:** SUCCESS

- Registros: 4,711
- Duplicados llave territorial-anual: 0
- Nulos de llaves críticas: divipola_key=0, anio_key=0
- Reglas aplicadas: Normalizacion nombres reales (ID Contrato, Fecha de Firma, Valor del Contrato, Documento Proveedor). DIVIPOLA desde divipola_key_mapped o lookup Departamento+Ciudad. NIT a solo digitos. Output transaccional para union posterior sin doble conteo.

---
## PROYECCIONES
**Estado:** SUCCESS

- Registros: 1,089
- Duplicados llave territorial-anual: 0
- Nulos de llaves críticas: divipola_key=0, anio_key=0
- Reglas aplicadas: Filtrado por AREA='Total'. Limpieza de formato numerico (separador de miles). Agregacion a departamento-anio.

---
