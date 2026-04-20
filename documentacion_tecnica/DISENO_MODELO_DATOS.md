# DISEÑO TÉCNICO Y FUNCIONAL DEL MODELO DE DATOS
*Rol: Senior Data/Analytics Engineer & Data Architect*

## 1. Unidad de Análisis Principal Recomendada
**Granularidad Integradora:** `Municipio - Año`
**Justificación:** Las bases de datos que originan este proyecto son operativamente disonantes: el SECOP es transaccional y continuo (grano: Contrato); EMICRON es probabilístico y anual (grano: Micronegocio Muestral); y el CNPV es estructural y se da en un punto del tiempo (grano: Geografía/Hogar). La única manera estadísticamente válida y analíticamente escalable de integrarlas sin causar inflación matricial (multiplicar los NBI por cada contrato) o sub-representación es agrupar o "rodar" (*roll-up*) el nivel de detalle hacia su intersección espacio-temporal más atómica que comparten todas: **el Municipio en su respectiva vigencia Anual**.

---

## 2. Arquitectura Objetivo (Medallion Data Architecture)

```mermaid
graph TD
    %% Capas
    subgraph BRONZE [Capa Bronze: Datos Crudos]
        A1[SECOP I y II - CSVs] -->|Parser Chunks| B1(secop_raw.parquet)
        A2[EMICRON 2019-2024] -->|Parser Recursive| B2(emicron_raw.parquet)
        A3[CNPV y Proyecciones] -->|Parser Direct| B3(demografia_raw.parquet)
    end

    subgraph SILVER [Capa Silver: Depurados, Homogeneizados y Pre-Agregados]
        B1 -->|Agrupación Contratación a Municipio-Año| S1(silver_secop_agregado.parquet)
        B2 -->|Búsqueda espacial, Sum fex_c a Municipio-Año| S2(silver_emicron_agregado.parquet)
        B3 -->|Cálculo denominadores a Municipio-Año| S3(silver_proyecciones_agregadas.parquet)
    end

    subgraph GOLD [Capa Gold: Modelo Estrella Unificador]
        S1 -->|Carga directa (Grano OBT)| F1(fact_contratacion_municipio_anio)
        S2 -->|Carga directa (Grano OBT)| F2(fact_micronegocios_municipio_anio)
        S3 -->|Carga directa (Grano OBT)| F3(fact_demografia_municipio_anio)
        
        DIM1(dim_territorio) -.-> F1 & F2 & F3
        DIM2(dim_tiempo) -.-> F1 & F2 & F3
    end
    
    subgraph DATAMARTS [Consumo Analítico]
        F1 & F2 & F3 -->|INNER JOIN (por divipola y año)| M1((mart_sinergia_socioeconomica.parquet))
    end
```

---

## 3. Modelo Dimensional Constelación (Estrella Múltiple)

El esquema a implementar en la Base de Datos Analítica (o persistido en Parquet vía DuckDB) debe separar estrictamente los Hechos de las Dimensiones conforeign keys estandarizadas.

### 3.1. Dimensiones Compartidas (Conformed Dimensions)

#### `dim_tiempo`
* **Grano:** 1 fila = 1 Año.
* **Llave Primaria (PK):** `anio_key` (ej. 2018, 2019).
* **Columnas obligatorias:** `anio_key` (int), `es_año_electoral` (boolean), `es_pandemia` (boolean), `periodo_presidencial` (string).
* **Propósito:** Filtros longitudinales unificados para cruzar fact tables sin ambigüedades.

#### `dim_territorio`
* **Grano:** 1 fila = 1 Municipio.
* **Llave Primaria (PK):** `divipola_key` (string de 5 caracteres con zero-padding).
* **Columnas obligatorias:** `divipola_key`, `nombre_municipio`, `divipola_departamento`, `nombre_departamento`, `region_geografica`, `categoria_municipal` (1 a 6 si existe, o Especial).
* **Restricción:** El Maestro Divipola debe tener exactamente los 1,122 municipios oficiales del país. NINGÚN `fact` debe generar filas divipola inexistentes.

---

### 3.2. Tablas de Hechos (Facts)

Para mantener aislamiento y reproducibilidad independiente de las lógicas métricas:

#### `fact_demografia_municipio_anio`
* **Grano:** 1 fila = 1 Municipio por 1 Año.
* **Llaves (FK):** `divipola_key`, `anio_key`.
* **Columnas obligatorias (Facts):** `poblacion_total_proyectada` (float), `ipm_absoluto` (float), `nbi_absoluto` (float), `déficit_vivienda`_volumen (int).
* **Regla de Agregación:** Para IPM/NBI (2018 base censal) el atributo asume constancia temporal salvo que se disponga de series anualizadas del DANE. La población *sí* muta iterativamente usando `silver_proyecciones_demograficas`.

#### `fact_micronegocios_municipio_anio`
* **Grano:** 1 fila = 1 Municipio por 1 Año (para aquellos municipios captados en la muestra).
* **Llaves (FK):** `divipola_key`, `anio_key`.
* **Columnas obligatorias (Facts):** `volumen_micronegocios_exp` (float), `formalizados_exp` (float), `empleo_total_generado_exp` (float).
* **Regla de Agregación Obligatoria:** Todos los conteos sobre EMICRON **deben** multiplicarse previamente a nivel fila individual por `fex_c` (Factor de Expansión) y luego sumarse al amarrarlos a `(divipola, anio)`. 

#### `fact_contratacion_municipio_anio`
* **Grano:** 1 fila = 1 Municipio ejecutor por 1 Año.
* **Llaves (FK):** `divipola_key`, `anio_key`.
* **Columnas obligatorias (Facts):** `inversion_total_monto` (float), `cantidad_procesos_adjudicados` (int), `proveedores_unicos` (int, Count Distinct sobre nit), `inversion_economia_popular` (float - condicionado por cuantía).
* **Regla de Agregación Obligatoria:** Agregar la capa Silver de SECOP agrupando por `divipola_key` y el año extraído de `fecha_publicacion`.

---

## 4. Datamart Analítico de Consumo (El "Entregable de Equipo")

En lugar de delegarle a científicos de datos junior la responsabilidad de unir las Fact Tables con las Dimensiones, el orquestador generará un artefacto final listo para la explotación visual.

### `mart_desarrollo_social_economico_municipio_anio.parquet` (One-Big-Table)
* **Composición:** Operación `LEFT JOIN` con pivot base `dim_territorio` cruzado vectorialmente al producto cartesiano de `dim_tiempo` filtrado a histórico activo.
* **Indicadores Derivados (Calculados On-the-Fly durante la inyección):**
  - `inversion_per_capita` = `fact_contratacion.inversion_total_monto / fact_demografia.poblacion_total_proyectada`
  - `tasa_formalidad_micron` = `fact_micronegocios.formalizados_exp / fact_micronegocios.volumen_micronegocios_exp`
  - `brecha_gasto_pobreza` = Normalización Z-score de `inversion_per_capita` versus `ipm`.

---

## 5. Estrés, Versionado y Entrega a Analistas

**5.1 Versionado y Persistencia de la Capa Oro:**
No se reconstruirá el universo de Parquets cada vez que se ejecute un cuaderno en Jupyter. El orquestador generará su salida estructurada en una carpeta llamada `datos/gold/marts/version=<YYYYMMDD>/`. Un symlink lógico llamado `datos/gold/marts/latest/` se actualizará con cada iteración que pase las pruebas de unit-testing de Data Quality.

**5.2 Consumo de los Analistas:**
La instrucción oficial para el resto del grupo será: 
> "No es necesario correr extractores ni ejecutar joins. Abran `analitica.ipynb` y carguen de forma directa `pd.read_parquet('datos/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet')`."

**5.3 Validaciones y Supuestos Aceptados:**
* **Supuesto validado:** El cruce a nivel Municipio-Año aísla efectivamente las cardinalidades (One-to-One), acabando matemáticamente con la posibilidad metodológica de sobre inflar NBI (la población de Bogotá no aumentará mágicamente si se dan 40,000 contratos adicionales).
* **Supuesto faltante (amarrado):** Si existe asimetría de divipolas mal digitadas en el SECOP I (códigos a 4 dígitos), se les antepondrá un pad '0' en la capa de Bronze a Silver para homologar en clave. Si una Divipola no existe en `dim_territorio`, el gasto público debe derivarse a una fila `99999 - Municipio No Definido` para no purgar montos macroeconómicos del radar.
