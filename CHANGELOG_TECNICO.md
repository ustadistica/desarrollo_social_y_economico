# 📝 CHANGELOG TÉCNICO

Bitácora de refactorización y resolución de conflictos metodológicos reportados durante la auditoría. Todos los compromisos técnicos están implementados y empaquetados en v1.0.

### 🛑 `[DEPRECATED / BLOCKED]` - Interacciones Prohibidas
* **Falla Crítica de Cardinalidad / Inflación Matricial (`cruce_secop_dane.py`):**
  - Existía un código anticuado y académicamente tóxico en `src/cruce_secop_dane.py`. Hacía `JOIN` directo (N:N) entre SECOP (Contratos) y DANE geográfico. Causaba una inflación astronómica en la métrica Nacional inflando estadísticas absolutas.
  - *Acción Tomada:* Eliminado por completo su uso de ejecución, aislado a nivel histórico, reemplazado a fuerza por la **Capa Silver (`clean_secop.py`)** con agregación espacial preventiva obligatoria.
  
* **Falla de Sesgo Muestral en Micronegocios (`create_datamart_economico.py` legacy):**
  - Se operaba EMICRON sin aplicar los Factores de Expansión (FEX_C), tratando unidades muestrales como censo absoluto, lo cual sesgaba la información masivamente sobre zonas urbanas perdiendo validez legal.
  - *Acción Tomada:* Removido y reimplementado en el nuevo Gold DWH y Capa Silver, usando queries estrictamente ponderados para el DANE.

### 🏗️ `[REFACTOR]` - Migración de Arquitectura Medallion y Empaquetado
* **Nomenclatura Corregida:**
  - Se renombró el directorio subyacente de `ingesta y validacion` (potencialmente fatal por sintaxis espaciada) al paquete formal instalable `pipeline/` integrándolo en el nuevo `pyproject.toml`.
  - **Estrategia Desacoplada a Componentes:**
    - `run_bronze.py`: Asignado a parser de persistencia.
    - `run_silver.py`: Asignado como responsable de confluir, agrupar, normalizar DIVIPOLAS (padding 0) y resolver anomalías antes del modelo relacional.
    - `run_gold.py`: Asignado a compilar el esqueleto estrella, construir el datamart unificador (OBT) `mart_desarrollo_social_economico_municipio_anio` bajo `datos/gold/marts/latest/`.

### ✨ `[FEATURE]` - Automatización de CI / Documentación y Logging
* Aprobados los mecanismos de *Graceful degradation* que blindan cada iteración en el Pipeline emitiendo Reportes Auditables de su fallo y protegiendo el sistema (Si Bronze no encuentra SECOP en CSVs por error del analista, genera archivo vacío seguro para Silver, impidiendo quiebres o *stacktraces* mortales y registrando FAILED en el `BRONZE_VALIDATION_REPORT`).
* Implementados un Makefile robusto para terminales agnósticas, y wrappers en Python estandarizados para ejecución atómica (`run_all.py`).
