# 🥉 Capa Bronze - Ingestión Raw (Inmutable)

La arquitectura de la capa Bronze ha sido refactorizada para asegurar desacoplamiento, reproducibilidad y escalabilidad multi-año bajo un enfoque Parquet-First.

## Principios de Diseño
1. **Inmutabilidad:** Los datos extraídos en esta capa representan la verdad absoluta y original proveniente del DANE o de la agencia de compras públicas. **NO sufren conversiones de unidades locales ni transformaciones matemáticas.**
2. **Columnas de Trazabilidad:** Todo registro persistido debe incluir:
   - `_ingestion_timestamp`: Fecha ISO de escritura
   - `_source`: Origen lógico de la fuente.
   - `_source_version`: Versión o año atado al módulo.
   - `_extraction_method`: Parser utilizado.
   - `_checksum_md5`: Hash estático para detección de corrupción.
3. **Persistencia Optimizada:** Todo se codifica sin indexación en Apache Parquet comprimido con codificador Snappy, facilitando el procesamiento Out-of-Core en la Capa Silver.

## Modularidad de Fuentes
El módulo está segmentado para permitir descargas masivas tolerantes a fallos (Chunking de 250,000 registros para datasets de >10GB como SECOP):

| Fuente | Naturaleza | Organización en Carpeta | Agregación Mínima |
| --- | --- | --- | --- |
| **SECOP I** | Archivo Histórico Pesado | `bronze/secop_i/` | Único Parquet Multi-chunk |
| **SECOP II** | Dataset en Crecimiento Vivo | `bronze/secop_ii/ingestion_date=...` | Acumulativo |
| **EMICRON**| Encuesta Jerárquica | `bronze/emicron/<año>/emicron_<modulo>.parquet` | Particionamiento por Año y Módulo |
| **CNPV** | Censo Poblacional | `bronze/cnpv/` | Único |
| **PPED** | Proyecciones | `bronze/proyecciones/` | Único |

## Comando Único de Ejecución
Se ha implementado un punto de entrada global exento de conflictos de paquetes Python en la raíz del proyecto.
Para regenerar toda la capa Bronze, ejecuta:
```bash
python run_bronze.py
```
*(El script autodetectará la configuración en `.env` o usará recolección de fallback si los CSVs se localizan en la carpeta relativa `../Datos/`)*.
