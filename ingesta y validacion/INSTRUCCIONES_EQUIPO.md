# Guía de Colaboración Integral - Equipo de Data Engineering 🚀

¡Hola equipo! Nuestro pipeline de Ingesta y Validación ha sido refactorizado desde cero hacia una arquitectura **Medallion End-to-End** (Bronze -> Silver -> Gold). Nuestro objetivo es procesar Gigabytes de información cruda local y transformarla en modelos estadísticos instantáneos a través de la magia de Python, DuckDB y Parquet.

Para evitar el famoso problema de *"En mi máquina sí funciona"*, hemos estructurado este manual. **Por favor lee todo antes de programar.**

---

## 🛠️ 1. Preparación del Entorno Virtual (Poetry)

El proyecto global usa **Poetry** para controlar las librerías fuertemente anidadas (fastapi, duckdb, pandas, pyarrow). 

1. Sitúate en la raíz del proyecto global (`desarrollo_social_y_economico-main`).
2. Instala las dependencias y activa el entorno:
   ```bash
   poetry install
   poetry shell
   ```
*(Asegúrate de ver `(desarrollo_social-...)` a la izquierda de tu terminal).*

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
2. **[Silver Layer]**: Levanta DuckDB sin usar tu RAM entera para escanear simultáneamente los mega-parquets. Mapea la divipola y junta a los 49 Millones de Colombianos en estadisticas agregadas instantáneas.
3. **[Gold Layer]**: Instancia el modelo tipo Estrella en la base de datos local `observatorio_desarrollo.duckdb`.

---

## 💻 5. Y para el equipo de Back / Front... ¿Qué hacen?

Si tú eres un compañero que está haciendo los tableros analíticos o la API REST, y **no necesitas modelar** los datos crudos del censo... ¡Ignora todo lo anterior!
1. Pídele al ingeniero de datos que te envíe el archivo binario final compilado llamado `observatorio_desarrollo.duckdb`.
2. Reemplaza el de tu repositorio con ese.
3. Continúa trabajando en tu capa web con los tableros ultra rápidos leyendo el modelo estrella, sin gastar giga-bytes de espacio en tu disco.
