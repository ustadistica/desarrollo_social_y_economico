# Reconciliación Final de Fuentes (Socioeconómicas y Contratación)

**Fecha:** 2026-04-21

La presente matriz detalla el ciclo de vida completo de cada fuente de datos, desde su ingesta en formato raw (Bronze) hasta su disponibilidad analítica en el Datamart unificado (OBT), aclarando exactamente qué nivel de granularidad aporta y bajo qué indicadores.

| Fuente | Entrada Silver | Artefacto Gold (Fact) | Variables Aportadas al OBT | ¿Integra el OBT final? | Granularidad Real |
|--------|----------------|-----------------------|----------------------------|------------------------|-------------------|
| **SECOP I** | `clean_secop_i.py` | `fact_contratacion` | `inversion_total_monto`, `cantidad_procesos_adjudicados`, `proveedores_unicos` (MAX combinado) | **SÍ** | Municipio - Año |
| **SECOP II** | `clean_secop_ii.py` | `fact_contratacion` | (Se fusiona con SECOP I asumiendo sumas paramétricas y máximos de NITs) | **SÍ** | Municipio - Año |
| **Proyecciones (DANE)** | `clean_proyecciones.py` | `fact_demografia` | `poblacion_total_proyectada` | **SÍ** | Departamento - Año |
| **EMICRON (DANE)** | `clean_emicron.py` | `fact_micronegocios` | `volumen_micronegocios_exp` | **SÍ** | Departamento - Año |
| **CNPV (Censo 2018)** | `clean_cnpv.py` | `fact_censo` | `poblacion_censo_2018` | **SÍ (Esquema)** | Municipio (Estático) |

## Análisis de Integración (Social + Económico)

El **Datamart Final (OBT)** sí logra integrar funcional y metodológicamente los dos frentes del proyecto, generando una verdadera visión transversal de desarrollo:

1. **Variables Económicas:** Incorpora la presión de gasto público (`inversion_total_monto`) y la participación empresarial local (`proveedores_unicos`) mediante las dos plataformas de SECOP.
2. **Variables Sociales y Estructurales:** Proporciona un marco demográfico a través de `fact_demografia` (proyecciones año a año) e incluye una aproximación a la vocación y madurez del tejido informal a través del conteo expandido (`volumen_micronegocios_exp` de EMICRON).
3. **Indicadores Derivados:** La unión permite cruzar mundos creando métricas valiosas no presentes en orígenes crudos:
   - `indicador_inversion_per_capita`: Inversión total en contratos (SECOP) / Población Proyectada.
   - `indicador_densidad_micronegocios`: Volumen estadístico de micronegocios (EMICRON) / Población Proyectada.

## Pendientes Identificados

- **CNPV (Censo de Población y Vivienda 2018):** 
  - **Estado:** Pendiente de ejecución física de descarga.
  - **Severidad:** Media (A nivel infraestructura, todo el modelo Gold y la query de unificación la tiene mapeada y produce un `fact_censo` esqueleto nulo sin romper nada).
  - **Acción a tomar:** Descargar microdatos del ANDA según lo delimitado en `PLAN_INGESTA_CNPV.md` y volver a disparar el pipeline.
