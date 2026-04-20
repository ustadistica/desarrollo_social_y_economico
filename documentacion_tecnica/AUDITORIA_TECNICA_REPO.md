# AUDITORÍA TÉCNICA Y DIAGNÓSTICO DEL REPOSITORIO

## 1. Mapa General del Repositorio y Arquitectura Actual
Tras la inspección profunda de los directorios, he identificado que el repositorio convive con **dos pipelines en paralelo**, uno legacy y uno refactorizado parcialmente:

- **Legacy Pipeline (`src/` y cuadernos en `modelo estrella/`):** Contiene los scripts antiguos, entre ellos `cruce_secop_dane.py`. Este esquema utiliza estructuras inmaduras (cruce de SECOP vía Pandas `read_csv`, descargas masivas inestables, etc.).
- **Medallion Pipeline (`ingesta y validacion/`):** Una arquitectura más limpia en vías de desarrollo con capas Bronze (Parquet), Silver y Gold. Usan DuckDB y PyArrow para el manejo de volúmenes "Out-of-Core".

**Diagnóstico sobre la Arquitectura:** El esquema Bronze/Silver/Gold existe de manera funcional a nivel código, pero solo opera nominalmente bien para SECOP II y aspectos de DANE CNPV. Elementos críticos declarados (DANE censos históricos, SECOP I en Silver) aún figuran como "Pendientes" en la capa formativa. Además, no existe un verdadero Modelo Estrella en Gold, sino una colección de "One Big Tables" pre-agregadas (Data Marts como `matriz_brechas_municipal.parquet`).

---

## 2. Inventario Técnico de Datasets y Granularidad

| Fuente | Nivel de Granularidad Original | Año(s) | Claves Candidatas | Variables Relevantes | Uso Recomendado en Proyecto |
| --- | --- | --- | --- | --- | --- |
| **SECOP I / SECOP II** | Proceso de Compra / Contrato individual (millones de registros) | 2018-2024 | `id_contrato`, `id_del_proceso`, `nit_proveedor`, `divipola_municipio` | `monto_contrato`, `fecha_publicacion`, `modalidad_seleccion`, `estado_contrato` | Agregar a nivel municipio-año/sector antes del join contra indicadores sociales. |
| **CNPV (DANE)** | Persona / Hogar (microdatos crudos) agregados lógicamente a Municipio | 2018 | `divipola_municipio` | `ipm_total`, `nbi_total`, `pobreza_monetaria`, `poblacion_total` | Dimensión Demográfica o base poblacional estática para per-cápita. |
| **CENU/EMICRON (DANE)** | Micronegocio / Módulo de Encuesta | 2019-2024 | Id encuestado, `divipola_municipio`, `codigo_ciiu` | `total_micronegocios`, factor expansión, sector económico | Utilizar el **Factor de Expansión** para inflar datos antes de agregar a nivel municipio-año. |
| **Proyecciones Población**| Municipio y Departamento por Año | 2018-2050 | `divipola_municipio`, `Año` | Total población proyectada | Normalizar denominadores en años > 2018. |

---

## 3. Matriz de Evaluación de Joins (Problemas Detectados)

| Archivo / Proceso | Tipo de Join | Llaves de Unión | Diagnóstico de Calidad | Evaluación |
| --- | --- | --- | --- | --- |
| `src/cruce_secop_dane.py` | **LEFT JOIN** | `divipola_municipio` | Toma `secop` (grano contrato) y le cruza `dane_consolidado` (grano municipio). No solo expande innecesariamente los totales sociales, sino que **duplica NBI/IPM por cada contrato** existente. | **INCORRECTO (Inflación Categórica)** |
| `ingesta y validacion/gold/marts/create_datamart_social.py` (función `create_inversion_vs_vulnerabilidad`) | **LEFT JOIN** | `divipola_municipio` | El Df `fact_vulnerabilidad` es cruzado con columnas de SECOP **sin agregarse primero**. Las filas de vulnerabilidad se clonan por cada contrato. Si se llama luego `agg({'poblacion_total': 'sum'})`, **la poblacion municipal se multiplica por la cantidad de contratos**. | **INCORRECTO (Inflación Métrica y Riesgo de Reporte)** |
| `ingesta y validacion/gold/marts/create_datamart_social.py` (función `create_matriz_brechas`) | **LEFT JOIN** | `divipola_municipio` | Hace `_aggregate_inversion_municipal(fact_contratacion)` antes del cruce. | **VÁLIDO** |
| `ingesta y validacion/gold/marts/create_datamart_economico.py` (función `create_matriz_sinergia`) | **OUTER JOIN** | `divipola_municipio` | Cruza las bases pre-agregadas. El problema es metodológico en la pre-agregación: calcula moda de CIIU (`mode()`) y sumatorias (`sum()`) sobre `fact_tejido` (una *encuesta probabilística*), **ignorando ciegamente el factor de expansión**. | **DUDOSO (Join correcto, agregación matemáticamente sesgada e inválida)** |

---

## 4. Riesgos y Fallas Adicionales

1. **Ausencia de Homologación real SECOP I y II:** 
   En la capa Gold actual (`create_fact_contratacion`), las reglas de mapeo sólo mencionan variables nativas de SECOP II (ej. `valor_total_adjudicacion`). Como SECOP I usa columnas distintas (`valor_contrato`, etc.), la integración "integral" está incompleta, tirando silenciosamente los datos históricos en la capa Silver si no coinciden.
2. **"Fallbacks" Poco Confiables en Llaves Geográficas:**
   En algoritmos legacy, el sistema busca iterativamente un field que se llame `codigo_entidad_en_secop`, `municipio_entidad`, o "cayendo" hasta la *primera columna posicional* del dataframe (`df.columns[0]`). Esto puede cruzar llaves como `ID_Contrato` contra Divipola.
3. **Riesgo Metodológico en EMICRON (Secreto Estadístico y Muestra):**
   Cruzar una matriz de micronegocios por geografía requiere expansiones, de lo contrario las capitales siempre dominarán las ponderaciones simplemente porque la muestra original fue más voluminosa allí en encuestas absolutas.
4. **Arquitectura Estrella en Gold no cumple la definición formal:**
   El pipeline Medallion genera tablas como 'matriz_brechas', que son en realidad Datamarts de Sabana Única (OBTs). Falta una `Fact_Territorio_Anual_Gasto` genérica que permita análisis OLAP genuino, separando las Dimensiones (`Dim_Territorio`, `Dim_Tiempo`, `Dim_CIIU`).

---

## 5. Plan de Refactorización y Próximos Pasos Priorizados

**Unidad de Análisis Correcta:**
La unidad de análisis unificadora debe ser **Unidad Geográfica Administrativa (Municipio, vía DIVIPOLA)** y **Corte Temporal (Año)**. Nunca el Contrato ni el Micronegocio particular.

| Prioridad | Etapa | Descripción |
| --- | --- | --- |
| **01 - CRÍTICA** | Consolidación y Descarte | Eliminar o deprecar totalmente `src/cruce_secop_dane.py` para evitar que otros corran un archivo que mutilará estrepitosamente sus números. Todo se debe migrar a `ingesta y validacion/`. |
| **02 - ALTA** | Corrección Estadística (EMICRON) | Refactorizar `_calcular_vocacion_productiva` para multiplicar obligatoriamente las métricas sociales y número de micronegocios por el **Factor de Expansión Mensual/Anual** de la encuesta poblacional base. |
| **03 - ALTA** | Corrección de Agregaciones (SECOP) | Reestructurar `create_inversion_vs_vulnerabilidad` para asegurar que todo cruce de `fact_` hacia dimensiones sociales ocurra **después de agregar por municipio-año** el SECOP, mitigando la explosión masiva de población. |
| **04 - MEDIA** | Homologación Definitiva en Silver | Crear un `clean_secop_unified.py` en la Capa Silver que tome el Parquet de SECOP I y el de SECOP II, y mapee sus casi 60 columnas únicas a un formato consolidado antes de ser `fact_contratacion`. |
| **05 - MEDIA** | Consolidación del Modelo Estrella Real | Desarrollar un modelo Dimensional clásico en `Gold` con una métrica aditiva (`Fact_Municipio_Ano`) que centralice Presupuesto (SECOP), NBI/IPM, y tejido empresarial formal vs. informal. |

**Criterios de Aceptación para avanzar:** NINGÚN cruce debe incrementar el conteo de elementos únicos geográficos u ocasionar que la sumatoria total de población del país en los registros supere los 50 Millones esperados.
