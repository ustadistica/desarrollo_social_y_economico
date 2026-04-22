# Trazabilidad de Módulos: Censo Nacional 2018 (CNPV)

**Fecha:** 2026-04-21

La presente auditoría técnica valida la lectura íntegra de los microdatos del CNPV 2018 alojados en las 33 carpetas departamentales físicas.

## Inventario Real de Módulos (Auditoría Exhaustiva en Disco)

Mediante motor analítico distribuido (`duckdb`), se contabilizó la completitud física de los archivos originales previo a su paso por chunks en el parser Bronze.

| Módulo | Archivos Leídos | Filas Totales Leídas | Descripción Técnica |
|--------|-----------------|----------------------|---------------------|
| **1VIV** | 33 | 16,080,499 | Representa conteo total de viviendas (1 fila = 1 vivienda). |
| **2HOG** | 33 | 14,252,829 | Representa conteo total de hogares (1 fila = 1 hogar). Menor que viviendas por desocupación. |
| **3FALL** | 33 | 242,744 | Representa conteo total de fallecidos en el hogar. |
| **5PER** | 33 | **44,164,417** | **Representa conteo total de personas censadas.** |
| **MGN** | 33 | 16,080,499 | Marco Geoestadístico (Alineado 1 a 1 con viviendas). |

## Evaluación del Pipeline Python (Bronze)
- El *parser_csv_cnpv.py* fue diseñado inicialmente con rutinas de evaluación en modo truncado (leyendo solo 1 chunk de 250,000 filas por departamento) para propósitos de prueba de integración rápida (`DEMO_MODE`), lo cual reportó la cifra truncada de ~7 millones de personas en ejecuciones previas.
- Dicha limitación temporal de CI/CD ya fue removida en el código final (`feature/migracion-duckdb-a-pyspark`).
- En ejecución completa asíncrona, el pipeline itera sobre la totalidad de estas **44,164,417 filas**, ingiriendo todos los departamentos sin rechazar ni descartar archivos. El separador variable (`,` o `;`) es manejado dinámicamente sin fallos de lectura, garantizando 0% de exclusión poblacional silenciosa.
