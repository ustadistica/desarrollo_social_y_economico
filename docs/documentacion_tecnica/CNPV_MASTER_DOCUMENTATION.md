# Documentación Maestra: Censo Nacional de Población y Vivienda (CNPV) 2018

Este documento consolida toda la información técnica, operativa y metodológica referente a la integración del Censo 2018 en el proyecto de Desarrollo Social y Económico.

---

## 1. Plan de Ingesta y Preparación
El pipeline asume la existencia de datos del CNPV 2018 en la capa Bronze. Para integrar el componente censal (necesario para métricas base como `poblacion_censo_2018`), se deben seguir estos pasos:

### 1.1 Descarga de Microdatos DANE
1. Acceder al portal ANDA del DANE.
2. Descargar los archivos CSV de **Personas (5PER)** y **Viviendas (1VIV)** por departamento.
3. Descomprimir los archivos.

### 1.2 Preparación del Entorno
1. Crear el directorio: `../Datos/CNPV_2018`
2. Mover los CSVs extraídos allí.
3. Configurar `.env` (opcional si se usa la ruta por defecto):
   ```env
   CNPV_ROOT_DIR="C:\Ruta\A\Los\Datos\CENSO 2018 dep"
   ```

---

## 2. Arquitectura de Ingesta (Multicarpeta)
El parser (`pipeline/bronze/parsers/parser_csv_cnpv.py`) utiliza un algoritmo de crawling dinámico:

1. **Auto-Descubrimiento:** Explora subcarpetas y cataloga archivos por módulo (`1VIV`, `2HOG`, `3FALL`, `5PER`, `MGN`).
2. **Consolidación (Chunking):** Lee los CSVs en chunks de 250k filas, detecta el separador (`,` o `;`) y genera archivos Parquet en `data/bronze/cnpv/`.

---

## 3. Trazabilidad de Módulos
Auditoría de completitud física de archivos originales:

| Módulo | Archivos | Filas Totales (Aprox) | Descripción |
|--------|----------|----------------------|-------------|
| **1VIV** | 33 | 16,080,499 | Viviendas |
| **2HOG** | 33 | 14,252,829 | Hogares |
| **3FALL** | 33 | 242,744 | Fallecidos |
| **5PER** | 33 | **44,164,417** | **Personas (Base Poblacional)** |
| **MGN** | 33 | 16,080,499 | Marco Geoestadístico |

---

## 4. Grano Analítico y Cobertura
### 4.1 Grano
- **Bronze:** Grano Persona (44.1M filas).
- **Silver/Gold:** Grano Municipio-Año (1,122 filas por año).
- La transformación colapsa los microdatos usando `divipola_key` y fija el año en `2018`.

### 4.2 Cobertura Geográfica
- El censo cubre los **1,122 municipios** de Colombia.
- Silver concatena `U_DPTO` (2 dígitos) y `U_MPIO` (3 dígitos) para formar la `divipola_key`.

---

## 5. Reconciliación Poblacional
- **Unidad:** Una fila en `5PER` = Una persona censada.
- **Validación:** No se aplican factores de expansión (FEX) ya que es un censo exhaustivo.
- **Calidad:** El 100% de los registros incluyen información geográfica válida.

---

## 6. Integración en el Modelo Gold (Datamart)
- **Fact Table:** Se genera `fact_censo_municipio.parquet`.
- **Variable Clave:** `poblacion_censo_2018`.
- **Impacto:** Actúa como "Verdad Fundamental" para calibrar proyecciones demográficas. En el OBT, el año 2018 tendrá cobertura total, mientras que otros años mostrarán `NULL` (o valores extrapolados en BI).

---

## 7. Ejecución del Pipeline
```bash
# Ingesta Bronze
socioeco-bronze --source cnpv

# Procesamiento Silver
socioeco-silver --source cnpv

# Construcción Gold
socioeco-gold
```
