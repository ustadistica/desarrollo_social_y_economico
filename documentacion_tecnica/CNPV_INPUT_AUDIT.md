# Auditoría de Ingesta CNPV: Inventario de Entradas

**Fecha:** 2026-04-21

Este documento evidencia la inspección real y el descubrimiento de archivos CSV del censo en el disco duro durante la fase de validación.

## Resultados del Descubrimiento Dinámico
La ejecución del `parser_csv_cnpv.py` rastreó con éxito la variable `CNPV_ROOT_DIR` encontrando:

* **Ruta Base Inspeccionada:** `../Datos/CENSO 2018 dep` (Resolución de fallback automática vía `.env` local).
* **Departamentos Detectados:** 33 subcarpetas distintas (los 32 departamentos + Bogotá D.C.).
* **Archivos Totales CSV Detectados:** 165 archivos.
* **Módulos Oficiales Encontrados:** `1VIV`, `2HOG`, `3FALL`, `5PER`, `MGN`. (5 archivos per departamento x 33 departamentos = 165 archivos, sin pérdidas).

### Estructura de Módulos (Detalle por Archivo)
- **1VIV (Viviendas):** 33 archivos leídos e ingestados.
- **2HOG (Hogares):** 33 archivos leídos e ingestados.
- **3FALL (Fallecidos):** 33 archivos leídos e ingestados.
- **5PER (Personas - Clave):** 33 archivos leídos e ingestados.
- **MGN (Marco Geoestadístico):** 33 archivos leídos e ingestados.

## Evaluación de Calidad de Entrada
- **Archivos faltantes:** No se reportaron ausencias departamentales. Todos los módulos principales requeridos para la demografía están presentes.
- **Formato del archivo:** Se evidenció que los CSV del DANE tienen variaciones en su separador (`.` vs `,` vs `;`). El pipeline auto-detecta esta codificación de forma determinística en su nueva versión multi-separador.
- **Doble Conteo del OS:** El sistema previene conteos duplicados en sistemas Windows mediante el uso de resolución absoluta de rutas en un `set` estricto (no diferencia entre `.CSV` y `.csv`).
