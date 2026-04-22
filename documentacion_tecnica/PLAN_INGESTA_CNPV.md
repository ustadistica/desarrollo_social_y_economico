# Plan de Ingesta: CNPV 2018 (Censo Nacional de Población y Vivienda)

**Fecha:** 2026-04-21

El pipeline actual asume la existencia de datos del CNPV 2018 en la capa Bronze. Para integrar correctamente el componente censal (necesario para métricas base como `poblacion_censo_2018`), se debe ejecutar el siguiente plan de ingesta utilizando la infraestructura `main_ingestion.py` ya existente.

## 1. Descarga de Microdatos DANE
Los datos del Censo 2018 están anonimizados y distribuidos públicamente por el DANE a través de su portal de microdatos (Archivo Nacional de Datos - ANDA).

**Pasos:**
1. Acceder al portal ANDA del DANE (Censo Nacional de Población y Vivienda 2018).
2. Descargar los archivos CSV correspondientes a **Personas** y **Viviendas** por departamento.
3. Descomprimir los archivos.

## 2. Preparación del Entorno Local
El parser genérico `CSVLocalParser` ya implementado en el pipeline puede ingerir estos archivos directamente a formato Parquet estandarizado.

1. Crear el directorio de recaudo temporal en el entorno local:
   ```bash
   mkdir -p ../Datos/CNPV_2018
   ```
2. Mover todos los archivos CSV extraídos a dicho directorio. No es necesario renombrarlos.

## 3. Ejecución de la Ingesta (Capa Bronze)
Ejecutar el orquestador de ingesta apuntando al directorio temporal. Se asume que el `.env` o la CLI permiten pasar rutas específicas, o utilizando el fallback default de `../Datos/`:

```bash
# Vía CLI oficial
socioeco-bronze --source cnpv
```

El pipeline ejecutará lo siguiente de manera autónoma:
1. `CSVLocalParser` detectará los CSV en el origen.
2. Limpiará cabeceras, tipará las columnas de manera inicial y agregará hashes MD5 para tracking.
3. Volcará el resultado particionado en `datos/bronze/cnpv/`.

## 4. Agregación a Nivel Municipal (Capa Silver)
Una vez en Bronze, el script `pipeline/silver/cleaners/clean_cnpv.py` está diseñado para leer los microdatos y colapsarlos a nivel de Municipio-Año (2018 estático):

```bash
# Ejecutar capa Silver para CNPV
socioeco-silver --source cnpv
```
La lógica internamente realiza:
- Concatenación de `U_DPTO` y `U_MPIO` en `divipola_key` (5 dígitos zero-padded).
- `COUNT(*)` como `poblacion_total_base`.

## 5. Integración Final (Capa Gold)
Cuando Silver ha generado el artefacto `silver_cnpv_agregado.parquet`, correr la etapa Gold inyectará automáticamente este componente al Datamart:

```bash
# Construir OBT final
socioeco-gold
```
En el modelo final (OBT), esta variable se manifestará como `poblacion_censo_2018`, permitiendo comparaciones entre el censo estático y las `poblacion_total_proyectada` por año para control de consistencia.
