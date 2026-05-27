# Reconciliación — CNPV + SECOP I/II + EMICRON + Proyecciones

Documento operativo que describe, para cada fuente, cómo entra al modelo estrella Gold y cómo se evita doble conteo o confusión de granularidades.

Fecha: 2026-04-21

## 1. Mapa de fuentes y responsabilidades

| Fuente | Naturaleza | Granularidad nativa | Granularidad en Mart | Rol en el modelo |
|---|---|---|---|---|
| **CNPV 2018** | Censo poblacional DANE | Municipio (snapshot 2018) | Atributo fijo por `divipola_key` | Baseline poblacional para trazabilidad histórica |
| **SECOP I** | Contratación pública (plataforma legacy) | Contrato | Municipio-año | Componente económico |
| **SECOP II** | Contratación pública (plataforma actual) | Contrato | Municipio-año | Componente económico (complementa a SECOP I) |
| **EMICRON** | Encuesta muestral DANE | Unidad de negocio (departamento) | Departamento-año (replicado a `XX000`) | Componente económico (estructura microempresarial) |
| **Proyecciones DANE** | Proyecciones poblacionales | Departamento-año | Departamento-año (replicado a `XX000`) | Componente social (denominador per cápita) |

## 2. Flujo Silver → Gold por fuente

### 2.1 CNPV 2018
1. Silver: [pipeline/silver/cleaners/clean_cnpv.py](../pipeline/silver/cleaners/clean_cnpv.py) lee microdatos CNPV Bronze, construye `divipola_key = U_DPTO(2)+U_MPIO(3)`, agrega `COUNT(*) → poblacion_total_base`, fija `anio_key=2018`.
2. Gold (fact): [pipeline/gold/build_facts.py](../pipeline/gold/build_facts.py) → `fact_censo_municipio.parquet` con schema `(divipola_key, anio_key=2018, poblacion_total_base)`.
3. Gold (Mart): broadcast **solo por `divipola_key`** como `poblacion_censo_2018`. No se une por `anio_key`.

Estado actual: Bronze **vacío** para CNPV → `fact_censo = failed_safe` → `poblacion_censo_2018 = 0` en Mart. Es un vacío honesto, no silencioso.

### 2.2 SECOP I
1. Silver: [pipeline/silver/cleaners/clean_secop_i.py](../pipeline/silver/cleaners/clean_secop_i.py) normaliza CSV oficial:
   - `UID` → `id_contrato`
   - `Cuantia Contrato` (formato `$1.234.567`) → `valor_del_contrato` (int)
   - `Fecha de Firma del Contrato` → `fecha_firma`
   - `Identificacion del Contratista` → `nit_contratista` (solo dígitos)
   - `Municipio Entidad` + `Departamento Entidad` → lookup DIVIPOLA vía `_norm` contra `DIVIPOLA_COMPLETO`.
   - Si el parser ya había inyectado `divipola_key_mapped`, se usa directo.
2. Produce **dos outputs**:
   - `silver_secop_i_agregado.parquet`: municipio-año con `cantidad_procesos_adjudicados`, `inversion_total_monto`, `proveedores_unicos` (distintos intra SECOP I).
   - `silver_secop_i_transaccional.parquet`: granularidad contrato, homologado con SECOP II vía `_fuente_origen='SECOP_I'`.
3. Filtros de calidad: `divipola_key` válido (5 dígitos), `anio_key ∈ [2018, 2030]`.

### 2.3 SECOP II
Idéntico patrón, distintos nombres originales:
- `ID Contrato` → `id_contrato`
- `Valor del Contrato` → `valor_del_contrato`
- `Fecha de Firma` → `fecha_firma`
- `Documento Proveedor` → `nit_contratista`
- `Departamento` + `Ciudad` → lookup DIVIPOLA.

Produce `silver_secop_ii_agregado.parquet` + `silver_secop_ii_transaccional.parquet` con `_fuente_origen='SECOP_II'`.

### 2.4 SECOP I + II → `fact_contratacion_municipio_anio`
En [pipeline/gold/build_facts.py](../pipeline/gold/build_facts.py):
```
secop_i_txn  ─┐
              ├─→ UNION (concat) → groupby(divipola_key, anio_key) →
secop_ii_txn ─┘   cantidad_procesos_adjudicados = nunique(id_contrato)
                  inversion_total_monto         = sum(valor_del_contrato)
                  proveedores_unicos            = nunique(nit_contratista)
```
La UNION sobre transaccionales garantiza que un proveedor con NITs repetidos en ambas plataformas se cuente **una sola vez**. Ver `VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md` para el detalle y evidencia.

### 2.5 EMICRON
1. Silver: [pipeline/silver/cleaners/clean_emicron.py](../pipeline/silver/cleaners/clean_emicron.py)
   - Clasifica archivos Bronze por nombre de módulo.
   - Usa **solo** el módulo `identificacion`/`caracteristicas`.
   - Deduplica por `(DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, _emicron_year)`.
   - Deriva año desde `_source_version='EMICRON_YYYY'` (prioridad 1).
   - Agrega `SUM(factor_expansion)` por `(COD_DEPTO, anio)`, marca `divipola_key = <cod_depto>000`.
   - `factor_expansion` usa `F_EXP` cuando viene valido; si un anio queda con `F_EXP = 0`, fusiona los archivos separados de factores (`fex_c`/`FEX_C`, con `fex_micro_dpto` como respaldo) por `(DIRECTORIO, SECUENCIA_P, SECUENCIA_ENCUESTA, anio)`.
2. Gold: `fact_micronegocios_municipio_anio.parquet` con schema `(divipola_key, anio_key, volumen_micronegocios_exp)`.
3. Mart: `merge` por `(divipola_key, anio_key)`. Solo aplica al código departamental `XX000`; ningún municipio específico recibe `volumen_micronegocios_exp` (coherente con la representatividad de la encuesta).

### 2.6 Proyecciones DANE
1. Silver: [pipeline/silver/cleaners/clean_proyecciones.py](../pipeline/silver/cleaners/clean_proyecciones.py) normaliza proyecciones departamentales 2018-2050.
2. Gold: `fact_demografia_municipio_anio.parquet` con `divipola_key=<dpto>000`, `anio_key`, `poblacion_total_proyectada`.
3. Mart: merge por `(divipola_key, anio_key)`. Usa misma convención `XX000` que EMICRON.

## 3. Convención de granularidad mixta departamento/municipio

El Mart final tiene granularidad **municipio-año**, pero coexisten facts departamentales (EMICRON, proyecciones) y municipales (SECOP, CNPV). La convención es:

- **Facts departamentales** viven exclusivamente en `divipola_key = XX000`.
- **Facts municipales** viven en `divipola_key` específico del municipio (p. ej. `11001` Bogotá).
- El Mart **no** hace broadcast automático de dpto → municipios. El analista decide:
  - Consulta puntual municipal: filtra `divipola_key != 'XX000'`.
  - Indicadores per cápita departamentales: filtra `divipola_key LIKE '%000'`.
  - Comparación mixta: une explícitamente `divipola_key[:2]` contra el registro `XX000`.

Esta convención se documenta en `dim_territorio.fuente_nombre` (`'construido_agregado_depto'` marca las filas `XX000`) y en el Mart mediante el flag `tiene_componente_economico`.

## 4. Reconciliación temporal

| Año | CNPV | SECOP I | SECOP II | EMICRON | Proyecciones | Cobertura en Mart |
|-----|------|---------|----------|---------|--------------|-------------------|
| 2018 | ✅ (snapshot) | Parcial | Parcial | — | ✅ | Todas las fuentes disponibles |
| 2019 | (broadcast) | ✅ | ✅ | ✅ | ✅ | Completa |
| 2020 | (broadcast) | ✅ | ✅ | ✅ | ✅ | Completa (flag pandemia) |
| 2021 | (broadcast) | ✅ | ✅ | ✅ | ✅ | Completa (flag pandemia) |
| 2022 | (broadcast) | ✅ | ✅ | ✅ | ✅ | Completa (flag electoral) |
| 2023 | (broadcast) | ✅ | ✅ | ✅ | ✅ | Completa |
| 2024 | (broadcast) | ✅ (parcial) | ✅ (parcial) | ✅ | ✅ | Parcial (corpus SECOP en ingesta) |
| 2025+ | (broadcast) | — | — | — | ✅ | Solo demografía proyectada |

La spine del Mart descarta años sin ningún fact real, así que aunque `dim_tiempo` cubra 2018-2029, el Mart efectivamente genera filas solo donde hay datos. Esto evita el cartesiano vacío.

## 5. Pendientes documentados

- **Ingesta CNPV**: bloqueante para `fact_censo`. Sin esto, `poblacion_censo_2018` es 0 en todo el Mart. Requiere descargar microdatos CNPV 2018 del portal DANE y correr el parser Bronze correspondiente.
- **Catálogo DIVIPOLA completo**: el catálogo actual trae 126 municipios. Cerca del 84% del universo municipal cae en `silver_sin_catalogar` y el Mart los mantiene por código pero sin nombre legible. Recomendación: integrar DIVIPOLA oficial del DANE (1 122 municipios) como fuente externa canónica.
- **Corpus SECOP completo**: la ingesta actual procesa muestras de 100 k filas. El corpus real es ~10 GB por plataforma. Una vez ingestado el total, los números crecerán pero la metodología no cambia.
- **Deduplicación cross-plataforma a nivel contrato**: un mismo contrato físico puede existir en SECOP I (legacy) y SECOP II (migrado). Actualmente se homologa el NIT pero no el `id_contrato`. Si el cliente reporta `cantidad_procesos_adjudicados` inflado, habrá que aplicar reglas adicionales (p. ej. ventana temporal + mismo NIT + mismo valor).
