# DATA CONTRACTS & GOVERNANCE PIPELINE
*Definiciones estrictas de esquemas de datos esperados para prevenir rupturas estructurales entre capas.*

Este archivo consolida las condiciones innegociables para que las transferencias entre la Capa Bronze (Raw Extracción), Capa Silver (Depuración) y Capa Gold (Modelo Estrella) se ejecuten exitosamente. Si se viola el contrato, correrá una "Great Expectation" o un assert bloqueando la fase para proteger el repositorio de corrupciones subyacentes masivas.

---

## 1. Contratos Funcionales Capa SILVER (Homogeneizada)

A esta capa acceden tablas base limpiadas que aún preservan el volumen atómico (granularidad) y el largo formato originario de su recolección.

### 1.1 `silver_secop_unificado.parquet`
**Propósito:** Transaccional contable de procesos adjudicados unificados entre SECOP I y SECOP II.
**Regla de Negocio:** La unificación requiere forzosamente la alineación de llaves con cast de tipos formales idénticos.

| Columna Target (Silver) | Tipo de Dato | Nulabilidad | Validaciones (Assertions/Exceptions) |
| --- | --- | --- | --- |
| `id_contrato` | `STRING` | NOT NULL | Único (Primary Key de nivel transaccional). |
| `origen` | `STRING` | NOT NULL | `IN ('SECOP_I', 'SECOP_II')` |
| `divipola_municipio` | `STRING(5)` | NOT NULL | Debe tener longitud estricta de 5 caracteres (`zfill(5)` aplicado). Omitir NAs imputando `'99999'`. |
| `fecha_publicacion` | `TIMESTAMP` | NOT NULL | `fecha_publicacion <= CURRENT_DATE()`. Si es pre 2000, imputar fecha base de rescate. |
| `monto_contrato` | `FLOAT` | NOT NULL | No puede ser nulo, imputar a `0.0`. Debe ser `>= 0.0`. Rechas negativas contables. |
| `estado_contrato` | `STRING` | NULL | Valores estandarizados a UPPERCASE. |

### 1.2 `silver_emicron_agregado.parquet`
**Propósito:** Agregado departamental-año de micronegocios DANE con expansión muestral validada.
**Regla de Negocio:** La base probabilística se deduplica por unidad muestral antes de agregar. El campo de salida `volumen_micronegocios_exp` se calcula con `SUM(factor_expansion)`.

| Columna Target (Silver) | Tipo de Dato | Nulabilidad | Validaciones (Assertions/Exceptions) |
| --- | --- | --- | --- |
| `divipola_key` | `STRING(5)` | NOT NULL | Código departamental `XX000`. |
| `divipola_depto` | `STRING(2)` | NOT NULL | Código DANE de departamento. |
| `anio_key` | `INTEGER` | NOT NULL | Rango permitido: `>= 2019` AND `<= 2024`. |
| `volumen_micronegocios_exp` | `FLOAT` | NOT NULL | Debe ser `> 0` para años EMICRON con registros. |
| `n_registros_encuesta` | `INTEGER` | NOT NULL | Conteo de unidades muestrales deduplicadas. |
| `_factor_expansion_origen` | `STRING` | NOT NULL | `F_EXP` o archivo/columna de fallback usada. |

---

## 2. Contratos Funcionales Capa GOLD (Dimensional)

En este escalafón los joins deben ser determinísticos (Relaciones `M-to-1`). Es ilícito presentar multiplicidad en el PK.

### 2.1 Tablas de Hechos (Facts)
Los schemas esperados bajo las funciones agregadoras deben cumplir con la unicidad compuesta obligatoria.

#### A. `fact_contratacion_municipio_anio`
| Atributo / Campo | Tipo | Naturaleza | Expectativa / Regla DataContract |
| --- | --- | --- | --- |
| `divipola_key` | `STRING(5)` | Foreign Key | Garantizada pre-existencia en `dim_territorio`. Único en cruce con año. |
| `anio_key` | `INTEGER` | Foreign Key | Garantizada pre-existencia en `dim_tiempo`. |
| `inversion_total_monto` | `FLOAT` | Facture | `SUM(monto_contrato)`. Must be `>= 0`. |
| `cantidad_procesos` | `INTEGER` | Facture | `COUNT(id_contrato)`. Must be `>= 0`. |

#### B. `fact_micronegocios_municipio_anio`
| Atributo / Campo | Tipo | Naturaleza | Expectativa / Regla DataContract |
| --- | --- | --- | --- |
| `divipola_key` | `STRING(5)` | Foreign Key | - |
| `anio_key` | `INTEGER` | Foreign Key | - |
| `volumen_micronegocios_exp`| `FLOAT` | Facture | Requiere que `> 0` para años EMICRON con registros. Resultante de `SUM(factor_expansion)` después de validar/fusionar FEX. |

### 2.2 Datamart Output (Consumo)
**Contrato Supremo para `mart_desarrollo_social_economico_municipio_anio.parquet`**:
1. **Cardinalidad Bloqueada:** El DataMart final no puede tener jamás más filas que el total de vigencias analizables cruzados contra los 1,122 municipios existentes en DIVIPOLA. Por ejemplo: `(2018 al 2024= 7 años) * 1122 = Máximo Teórico de 7,854 Filas`.  Cualquier alteración por sobre esta cota máxima de recuento será considerada un `FAN-OUT ERROR` activando advertencias de validación rojas para romper la pipeline.
2. **Nulabilidad Controlada Lógica:** Zonas rurales sin cobertura en la encuesta EMICRON deberán tener `NULL` explícito o `0.0` controlable en los volúmenes, nunca desechar la fila geográfica; la existencia de Inversión (SECOP) o Pobreza persistirá aunque el DANE no los haya encuestado esporádicamente para el módulo productivo.
3. **Persistencia Final:** Obligatoriamente guardada en Apache Parquet particionado localmente o empaquetado en Snappy, excluyendo cualquier escritura a formato `.csv` para impedir cast implícita nociva de llaves primarias geo-espaciales (Pérdida de padding zero o comas miles).
