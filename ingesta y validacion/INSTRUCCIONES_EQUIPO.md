# Guía de Colaboración Integral - Equipo de Data Engineering 🚀

¡Hola equipo! Nuestro pipeline de Ingesta y Validación ha sido refactorizado desde cero hacia una arquitectura **Medallion End-to-End** (Bronze -> Silver -> Gold). Nuestro objetivo es procesar Gigabytes de información cruda local y transformarla en modelos estadísticos instantáneos a través de la magia de Python, PySpark y Parquet.

Para evitar el famoso problema de *"En mi máquina sí funciona"*, hemos estructurado este manual. **Por favor lee todo antes de programar.**

---

## 🛠️ 1. Preparación del Entorno Virtual (Poetry)

El proyecto global usa **Poetry** para controlar las librerías fuertemente anidadas (fastapi, pyspark, pandas, pyarrow). 

1. Sitúate en la raíz del proyecto global (`desarrollo_social_y_economico-main`).
2. Instala las dependencias y activa el entorno:
   ```bash
   poetry install
   poetry shell
   ```
*(Asegúrate de ver `(desarrollo_social-...)` a la izquierda de tu terminal).*

---

## ☕ 1.5. Instalación de Java (Requisito para PySpark)

PySpark requiere Java (OpenJDK 17) para ejecutar el motor distribuido localmente. Hemos incluido un script automático para que no debas configurarlo manualmente.
1. Abre una terminal de **PowerShell** como Administrador.
2. Navega a la carpeta `ingesta y validacion/`.
3. Ejecuta el archivo: `.\setup_java.ps1`
*(Nota: Si te da un error de permisos de ejecución en Windows, corre primero: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`)*.
4. Una vez terminado, **cierra tu terminal y VSCode** y vuelve a abrirlos para que detecte correctamente el nuevo `JAVA_HOME`.

> ⚠️ **IMPORTANTE - Compatibilidad Python**: PySpark 3.5.x tiene una incompatibilidad conocida con **Python 3.12 en Windows** (los workers de Python crashean). Se recomienda usar **Python 3.11.x** para ejecutar el pipeline localmente en Windows. Si tu equipo usa Python 3.12, considerar ejecutar en WSL2 (Linux) o en un contenedor Docker.

---

## 📥 2. Descarga de Datos Crudos (Requisito Indispensable)

Dado que estamos procesando microdatos reales masivos (como los 6GB del Censo), **el repositorio de Git NO CONTIENE LOS DATOS CRUDOS**. Todo analista de datos debe descargar e indexar los documentos en sus propias máquinas.

1. **Censo Nacional de Población y Vivienda (CNPV 2018)**
   - Descarga la base completa (busca el ZIP con las 33 carpetas departamentales CSV).
   - Guárdalas en una carpeta local de uso analítico. 
   - *(Ejemplo: `C:\Proyectos\Datos\CENSO 2018 dep\`)*.
   
2. **SECOP II (Contratos Electrónicos) / EMICRON**
   - Extrae los consolidados CSV directos desde el portal de datos abiertos de Colombia.
   - Guárdalos en tu carpeta analítica.
   - *(Ejemplo: `C:\Proyectos\Datos\SECOP_II.csv`)*.

---

## 🛡️ 3. Configuración del `Archivo Secreto` (.env)

Las rutas de programación estáticas en Windows han sido erradicadas. Ahora, cada uno le dice al Pipeline de Ingesta en dónde puso sus descargas gracias a sus **Variables de Entorno**.

1. Ingresa a la carpeta `ingesta y validacion/`.
2. Localiza el archivo llamado **`.env.example`**.
3. **Cópialo y renómbralo a `.env`** (debe quedar exactamente como `.env`).
4. Abre tu nuevo `.env` y pega las rutas exactas de los archivos crudos que descargaste en el **Paso 2**:
```env
CNPV_CSV_DIR="C:\Proyectos\Datos\CENSO 2018 dep"
SECOP_CSV_PATH="C:\Proyectos\Datos\SECOP_II.csv"
```
> **Nota de Seguridad**: Al llamarlo `.env`, el archivo será **ignorado por Git** por defecto. Tus rutas locales nunca serán subidas a la rama compartida del equipo ni sobrescribirán las configuraciones de otro ingeniero. 💖

---

## 🏃🏽 4. Ejecutar la Transformación Big Data (ELT Completo)

Si ya descargaste los CSVs y le dijiste a tu archivo apuntador `.env` en dónde están, procesarlos todos cuesta literalmente un comando.

Dentro de `ingesta y validacion/`, ejecuta:
```bash
python run_pipeline.py --all
```

### ¿Qué está ocurriendo detrás de escenas?
1. **[Bronze Layer]**: El orquestador extrae tus pesados CSVs y usa `pyarrow` para generar sub-bloques optimizados `.parquet` en tu computadora.
2. **[Silver Layer]**: Levanta un clúster local de **PySpark** sin saturar tu RAM para procesar de forma "Out-of-Core" los mega-parquets. Mapea la divipola y junta a los 49 Millones de Colombianos en métricas agregadas instantáneas.
3. **[Gold Layer]**: Instancia el Data Mart final y guarda tu Modelo Estrella en la carpeta particionada `modelo_estrella_pyspark/` como un lago nativo preparado para BI.

---

## 💻 5. Y para el equipo de BI / Tableros... ¿Qué hacen?

Si tú eres un compañero que está diseñando tableros analíticos... ¡Ignora todo el pipeline!
1. Pídele al ingeniero de datos que te envíe la carpeta final compilada llamada `modelo_estrella_pyspark/` (o mejor, léela desde el S3/DataLake).
2. Conecta tu PowerBI, Metabase o Jupyter Notebook directamente a esa carpeta particionada.
3. Trabaja en la capa de visualización con velocidades turbo leyendo un formato columnar, y sin malgastar espacio en disco.
