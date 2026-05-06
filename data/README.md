# Cargue, Actualización y Consolidación de Datos del SECOP

##  Contexto del Proyecto

La presente parte del proyecto tiene como objetivo realizar el **cargue, actualización y consolidación histórica** de los datos del **SECOP (Sistema Electrónico para la Contratación Pública de Colombia)**, con el fin de analizar el comportamiento de los procesos de contratación pública a lo largo del tiempo, y asi mantener un registro de los mismos.  

Este trabajo permite identificar **tendencias, volúmenes de contratación** y apoyar la **toma de decisiones** en torno a políticas públicas y desarrollo económico, especialmente relacionadas con la **generación de empleo** y la **gestión de recursos públicos**.

---

##  Fuente de Datos – SECOP

Los datos provienen de la plataforma de **Datos Abiertos del Gobierno de Colombia (Datos.gov.co)**, específicamente del conjunto de datos disponible en la siguiente URL oficial del SECOP:

🔗 [https://www.datos.gov.co/resource/p6dx-8zbt.json](https://www.datos.gov.co/resource/p6dx-8zbt.json)

El SECOP centraliza toda la información sobre los procesos de contratación del Estado colombiano.  
A través de esta plataforma, las entidades públicas registran sus procesos contractuales desde la publicación de los pliegos hasta la adjudicación y ejecución.  

El acceso público a esta información **fomenta la transparencia, la vigilancia ciudadana y la eficiencia** en la gestión pública.

---

##  1. Descarga Trimestral de la Información

Dada la gran cantidad de registros que maneja el SECOP, se diseñó un proceso que permite **descargar la información de forma trimestral**.  

El primer código desarrollado, llamado **`Descarga_de_records_secop`**, se encarga de:

- Conectarse a la API de Datos Abiertos usando la URL del SECOP.  
- Extraer los datos por trimestre (Q1, Q2, Q3 y Q4).  
- Organizar los registros según la columna `fecha_de_publicacion_del`.  
- Guardar cada trimestre como un archivo independiente en formato **.parquet**, dentro de la carpeta:

 **`DatosAPI_Trimestral_Parquet/`**

El uso del formato **Parquet** se debe a su eficiencia en el manejo de grandes volúmenes de datos y su compatibilidad con herramientas de análisis en Python y entornos de Big Data.  
Esto permitió un tratamiento **más ágil, ordenado y escalable** de los datos.

---

##  2. Proceso de Actualización de Datos

Posteriormente, se creó un segundo código llamado **`Actualizacion_de_Datos`**, con el objetivo de mantener los archivos trimestrales **actualizados con la información más reciente** publicada en el SECOP.

Este proceso:

- Identifica la **última fecha de publicación** procesada en los archivos locales.  
- Descarga desde la API todos los registros nuevos desde el día siguiente a esa fecha.  
- Agrega los nuevos datos automáticamente al archivo del trimestre correspondiente.  
- Si no existe el archivo del trimestre, el sistema crea uno nuevo.  

Gracias a este proceso, los archivos trimestrales se mantienen **sincronizados con la fuente oficial**, sin necesidad de volver a descargar toda la base de datos completa.

---

##  3. Validación de Información Faltante

Durante las pruebas iniciales se detectó que, en algunos casos, podían faltar registros debido a **cortes en la descarga o actualizaciones del propio SECOP**.  

Para mitigar este riesgo, se desarrolló una **rutina de validación** que compara los datos descargados localmente con los datos actuales de la API.  

Si el sistema identifica registros que están en la API pero no en los archivos locales, los **agrega automáticamente** para garantizar la **integridad y completitud** de la información.

---

##  4. Consolidación del Histórico General

Una vez creados y validados los archivos trimestrales, se desarrolló un tercer proceso denominado **`Historico_de_Datos`**, cuyo propósito es **unificar toda la información descargada** en un solo archivo histórico consolidado.

Este proceso realiza los siguientes pasos:

1. Lee todos los archivos trimestrales `.parquet` de la carpeta `DatosAPI_Trimestral_Parquet`.  
2. Ordena los trimestres cronológicamente.  
3. Une todos los registros en un solo DataFrame histórico.  
4. Elimina las columnas obsoletas `anio` y `trimestre` que ya no existen en la API.  
5. Excluye los **dos trimestres más recientes** (por ejemplo, Q3 y Q4 de 2025) para permitir su regeneración con datos frescos desde la fuente oficial.  
6. Guarda el archivo final consolidado también en formato `.parquet`.

El sistema compara el total de registros reportados por la API y el total consolidado en el histórico local, lo que permite detectar posibles diferencias o pérdidas de información.

---

##  5. Resultados y Beneficios

Gracias a este sistema automatizado de **extracción, actualización y consolidación**:

- Se cuenta con un histórico completo y limpio de los procesos de contratación del SECOP.  
- Los datos se encuentran estructurados por trimestre, facilitando su análisis temporal.  
- La actualización periódica es eficiente, sin duplicar registros ni perder información.  
- Se habilita una base sólida para futuros análisis de **series de tiempo, contratación pública, transparencia y economía**.

---

##  Estructura de Carpetas

```plaintext
 DatosAPI_Trimestral_Parquet/
 ├── datos_trimestre_2025_Q1_2025-01-01_to_2025-03-31.parquet
 ├── datos_trimestre_2025_Q2_2025-04-01_to_2025-06-30.parquet
 ├── datos_trimestre_2025_Q3_2025-07-01_to_2025-09-30.parquet
 ├── datos_trimestre_2025_Q4_2025-10-01_to_2025-12-31.parquet
 └── historico_consolidado.parquet
