# DOCUMENTACIÓN DE EJECUCIÓN - ETAPAS 2 Y 3

**Etapas Ejecutadas:** 
- 02 - Corrección Estadística (EMICRON)
- 03 - Corrección de Agregaciones (SECOP)
**Fecha de Ejecución:** 2026-04-20

## 1. Validación Previa
De acuerdo a las directrices, se validaron previamente las contradicciones entre la granularidad documentada de EMICRON (microdatos) y los métodos descriptivos de `.mode()` y `.sum()` empleados en la agregación territorial en `ingesta y validacion/gold/marts/create_datamart_economico.py`. Se confirmó que la inexistencia de factores de expansión (`fex_c`) representaba una violación crítica al diseño de encuestas del DANE. Por la otra vía, se verificó también el riesgo de inflación poblacional diagnosticado en la Etapa 3 respecto al script `create_datamart_social.py`.

## 2. Acciones Realizadas

### Etapa 2: Corrección Estadística (EMICRON - Data Mart Económico)
- **Modificación Técnica:** Se refactorizó la función `_calcular_vocacion_productiva` del archivo `ingesta y validacion/gold/marts/create_datamart_economico.py`.
- **Justificación Metodológica:** Para evitar que las ciudades principales lideren siempre la clasificación por simple volumen de recolección de muestras, se detectó y multiplicó explícitamente cualquier métrica (como `economia_popular_unidades` o `total_micronegocios`) por la columna `fex_c` (Factor de Expansión).
- **Control de Modalidad CIIU:** Se rediseñó el cálculo de sector predominante (`codigo_ciiu.mode()`) y se transformó en una función custom `weighted_mode()` que determina la vocación económica de un municipio sumando el peso real (`fex_c`) que tiene un CIIU particular frente a otro.

### Etapa 3: Corrección de Agregaciones (SECOP - Data Mart Social)
- **Modificación Técnica:** Se rediseñó íntegramente de la línea 216 a la 265 del archivo `ingesta y validacion/gold/marts/create_datamart_social.py` (función `create_inversion_vs_vulnerabilidad`).
- **Justificación Metodológica:** Para prevenir la expansión perniciosa discutida exhaustivamente. El dataframe base `fact_contratacion` (que posee un grano transaccional) ahora se agrega localmente por `divipola_municipio` y el año de publicación *antes* del `merge(how='left')` con `fact_vulnerabilidad`. 
- **Verificación Cardinal:** Gracias a esto, cada municipio mantendrá siempre una sola fila representativa por año independientemente de si el estado adjudicó 10 o 5,000 contratos a sus proveedores locales, garantizando que sumatorias posteriores a nivel departamental resulten en cifras poblacionales inalteradas.

## 3. Evidencias Verificables
Los cambios son rastreables vía diff en el sistema de versionado nativo del repositorio en los dos archivos vitales de Datamarts, blindando por fin la calidad estadística de las capas oro del modelo de Medallion.

---
**Estado Etapas 2 y 3:** ✅ COMPLETADAS METODOLÓGICAMENTE.
