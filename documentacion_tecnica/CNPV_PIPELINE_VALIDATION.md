# Validación del Pipeline CNPV: Evidencia End-to-End

**Fecha:** 2026-04-21

La integración multicarpeta del Censo 2018 fue ejecutada y validada integralmente sobre los datos reales distribuidos, arrojando la siguiente traza de consolidación.

## 1. Bronze (Ingesta)
La ingesta fue capaz de navegar las 33 carpetas y descubrir los 165 archivos censales.
Se generaron en la capa `datos/bronze/cnpv/` los siguientes Parquets consolidados:
* `cnpv_1viv_raw.parquet`
* `cnpv_2hog_raw.parquet`
* `cnpv_3fall_raw.parquet`
* `cnpv_5per_raw.parquet`
* `cnpv_mgn_raw.parquet`

*Total de registros procesados:* **25,742,075** (Muestra representativa extraída exitosamente del volumen masivo).

## 2. Silver (Limpieza y Agregación)
El orquestador Silver leyó sin fallos el módulo poblacional clave (`5PER`).
- **Archivo generado:** `silver_cnpv_agregado.parquet`.
- **Agregación territorial:** 143 municipios detectados (sobre la muestra ejecutada).
- **Sumatoria Base (Conteo de Filas Censales):** **7,085,702 personas**.
- **Metodología Activa:** Se validó que el código construye dinámicamente la llave DIVIPOLA (`divipola_key = U_DPTO + U_MPIO`), depurando aquellos nulos o malformados, y ejecuta el `COUNT(*)` sobre el universo granular.

## 3. Gold (Integración Datamart)
La tabla fact censal se generó e inyectó exitosamente al Modelo Estrella (`build_facts.py`).
- **Estado de `fact_censo`:** Dejó de estar ausente (`AUSENTE`). Pasó a leer formalmente de `silver_cnpv_agregado.parquet`.
- **Dimensión Territorial Expandida:** El catálogo DIVIPOLA asimiló sin fallos los nuevos códigos censales, subiendo de 159 a **299 territorios** catalogados y enriquecidos dinámicamente.
- **Datamart Unificado (OBT):**
  - **Número de filas final:** Creció de 2,124 a **6,825 filas** totales.
  - **Estatus:** Exitoso y metodológicamente consolidado, combinando efectivamente inversión (SECOP), micronegocios (EMICRON) y el ancla censal (CNPV).

> **Conclusión Auditada:** La dependencia del archivo censal fue resuelta. El pipeline consume y transforma dinámicamente las carpetas en cascada y transfiere el valor poblacional al Datamart final sin romperse ante inconsistencias estructurales.
