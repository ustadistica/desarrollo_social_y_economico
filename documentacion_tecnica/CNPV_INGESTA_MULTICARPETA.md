# Arquitectura de Ingesta Multicarpeta para CNPV 2018

**Fecha:** 2026-04-21

Este documento detalla el diseño y la implementación de la ingesta automatizada del Censo Nacional de Población y Vivienda 2018, resolviendo el desafío de fragmentación física de los datos.

## 1. El Desafío de Origen
Los datos del DANE para el CNPV no se entregan en una tabla plana, sino fragmentados en:
- **33 divisiones territoriales** (32 Departamentos + Bogotá D.C.) en subcarpetas separadas.
- **Múltiples módulos temáticos** por carpeta (`1VIV` viviendas, `2HOG` hogares, `3FALL` fallecidos, `5PER` personas, `MGN` marco geoestadístico).

Depender de una ruta *hardcodeada* o forzar a cada analista a consolidar manualmente cientos de CSVs antes de correr el pipeline rompía la portabilidad.

## 2. Diseño de la Solución (Fase de Descubrimiento)
El parser implementado (`pipeline/bronze/parsers/parser_csv_cnpv.py`) ahora utiliza un algoritmo de *crawling* dinámico en dos fases:

1. **Auto-Descubrimiento:** 
   * Se inicia desde una única ruta base portátil (`CNPV_ROOT_DIR`).
   * Explora todas las subcarpetas de primer nivel ignorando las que no contengan archivos `.CSV`.
   * Registra y cataloga cada archivo detectado emparejándolo automáticamente con un módulo oficial del DANE mediante inspección de *substrings* en el nombre del archivo.
   
2. **Consolidación Vectorizada (Chunking):**
   * Agrupa el inventario de archivos por módulo (Ej. agrupa los 33 CSVs de `5PER`).
   * Lee secuencialmente cada CSV en chunks (250k filas).
   * Detecta dinámicamente si el CSV utiliza `,` o `;` como separador leyendo la primera línea.
   * Apendiza (Append) los datos directamente sobre un único archivo Parquet de salida (`cnpv_5per_raw.parquet`), inyectando metadatos de trazabilidad (`_source_file`, `_checksum_md5`).

## 3. Manejo de Errores y Tolerancia a Fallos
- Si un archivo está corrupto, la traza queda en `logger.error` y el chunk problemático es saltado (`on_bad_lines='skip'`), pero el pipeline **no se detiene**; continúa con el siguiente departamento.
- Si falta el módulo completo, emite un Warning y no genera el Parquet, pero no revienta la ingesta de los demás módulos.
- Se resolvió un error histórico donde Windows duplicaba las lecturas al ser *case-insensitive* usando inferencia estricta de extensiones y *sets* de Python para garantizar un conteo único de las fuentes físicas.

Este diseño bloqueante finaliza la dependencia de rutinas de unificación manuales y democratiza la capa Bronze del Censo para cualquier integrante del equipo.
