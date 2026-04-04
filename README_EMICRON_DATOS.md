# 📊 Guía de Uso: Base de Datos EMICRON 2024

**Para:** Equipo de Análisis y Modelado Económico  
**Asunto:** Procesamiento y Cruce de Microdatos de la Encuesta de Micronegocios (EMICRON 2024)

---

## 🚀 1. Carga de los Datos (Ya automatizado)

El pipeline de ingesta ha sido actualizado para procesar automáticamente los microdatos crudos.  
**No es necesario configurar rutas absolutas individuales.** El sistema está diseñado para portabilidad.

### ¿Cómo configurarlo en tu computador local?

1. Crea una carpeta llamada `Datos` justo al lado de la carpeta raíz del repositorio `desarrollo_social_y_economico`, es decir, una carpeta "hermana" del proyecto.
2. Dentro de esa carpeta `Datos`, pega la carpeta completa llamada `EMICRON 2024` tal como fue descargada (conteniendo las 12 carpetas de los distintos módulos: *Modulo_Caracteristicas_Micronegocios*, *Modulo_TIC*, *Modulo_Inclusion_Financiera*, etc.).
3. Tu estructura de archivos deberá verse así:
    ```
    Contrato o Universidad/
    ├── Datos/
    │   └── EMICRON 2024/
    │       ├── BDATOS-EMICRON-Modulo_Caracteristicas_Micronegocios-2024/
    │       ├── BDATOS-EMICRON-Modulo_Identificacion-2024/
    │       └── ... (demás carpetas)
    └── desarrollo_social_y_economico/
        ├── ingesta y validacion/
        ├── config/
        └── (archivos del repositorio)
    ```

El `settings.py` está programado para buscar automáticamente esta estructura (`../Datos/EMICRON 2024`).

### ¿Qué hace el Pipeline de Ingesta (Bronce)?

- Entra a la carpeta de `EMICRON 2024`.
- Recupera todos los archivos **.csv** dentro de las subcarpetas.
- Los codifica y formatea de forma segura sin romper los registros.
- Guarda los archivos en la capa `bronze/emicron` unificándolos bajo el prefijo del módulo y guardándolos como archivos `.parquet` listos para ser consumidos y cruzados en la capa *Silver* (Plata).

---

## ⚠️ 2. ADVERTENCIAS TÉCNICAS SOBRE LOS CRUCES (Para el equipo)

Se nos ha pedido que los microdatos se pongan a su disposición en la Capa Bronce tal cual vienen del DANE. A la hora de hacer las transformaciones y limpiarlos en la capa de Plata, **tengan en cuenta obligatoriamente las siguientes advertencias estadísticas**:

> [!CAUTION]
> **Falta de DIVIPOLA Municipal (Secreto Estadístico)**
> Los microdatos de EMICRON **no incluyen el código DIVIPOLA a nivel municipio** (5 dígitos) que sí tenemos en SECOP. DANE omite estos datos para preservar el anonimato ya que la encuesta por su diseño muestral no es representativa en todos los municipios de Colombia, principalmente está diseñada para tener representatividad **Departamental** y en las 24 principales ciudades.
> Solo van a encontrar la variable `COD_DEPTO` (Código de Departamento a 2 dígitos) o el `AREA`. 

### ¿Cómo deben proceder con los Cruces en Plata y Oro?

Debido a que ustedes diseñaron un `Modelo Estrella` donde la dimensión principal usa el `divipola_municipio`:

1. **Agrupación a Nivel Departamental:** Recomendamos cruzar los datos de EMICRON agregando la información de contratos SECOP a nivel **departamental**. Extrayendo los dos primeros dígitos de la DIVIPOLA en SECOP, o mapeándolo contra el `COD_DEPTO` de la tabla `dim_ubicacion`.
2. **Uso Indispensable del Factor de Expansión (`F_EXP`):** No pueden contar las filas (registros) directamente como si fueran el número de micronegocios de Colombia. EMICRON es una muestra estadística. Para obtener los valores reales de la "Economía Popular" de un departamento, cada fila debe multiplicarse por la variable ponderadora **`F_EXP`**.
3. **Cruce entre Módulos de la misma encuesta:** Para cruzar, por ejemplo, el *Módulo de Identificación* con el *Módulo de TIC*, **deben usar y agrupar por las 3 llaves únicas** de la encuesta:
    - `DIRECTORIO`
    - `SECUENCIA_P`
    - `SECUENCIA_ENCUESTA`

Cualquier duda adicional, pueden referirse a la Metodología DANE. El trabajo de agregación de esta capa les corresponde en `silver/cleaners/clean_emicron.py`. ¡Feliz tabulación cruzada!
