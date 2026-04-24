# Informe de avance técnico del proyecto

### 1. Propósito general del trabajo realizado

El trabajo que se ha venido haciendo tuvo como objetivo corregir y profesionalizar el repositorio del proyecto para que el análisis social y económico fuera técnicamente válido, reproducible para todo el equipo y defendible ante revisión académica.

En términos prácticos, no se trató solo de “hacer que corra”, sino de asegurar cinco cosas:

1. que los datos se ingesten de forma correcta;
2. que los cruces entre fuentes no produzcan duplicaciones ni sesgos;
3. que el repositorio pueda ejecutarse en distintos computadores del grupo;
4. que exista una estructura clara por capas para dejar tablas finales listas para análisis;
5. que el producto final tenga una base metodológica consistente.

---

### 2. Problemas iniciales identificados

Al comienzo, el proyecto presentaba varios problemas importantes.

Por un lado, coexistían dos pipelines en paralelo: uno antiguo y uno más nuevo, lo que generaba ambigüedad sobre cuál era el flujo oficial. Además, había cruces incorrectos entre bases que mezclaban distintos niveles de granularidad, por ejemplo contratos individuales con indicadores municipales, lo que inflaba métricas como población, pobreza o inversión.

También había problemas de portabilidad: rutas absolutas de un solo computador, archivos locales, logs versionados, dependencias incompletas y documentación que no coincidía con el código real. Eso implicaba que el proyecto podía funcionar parcialmente en una máquina específica, pero no estaba listo para trabajo colaborativo real en GitHub.

Desde el punto de vista analítico, también había fallas metodológicas. SECOP I y SECOP II no estaban homologados completamente, EMICRON presentaba riesgo de ser tratado como si fuera censo exhaustivo sin considerar adecuadamente los factores de expansión, y la integración del CNPV 2018 estaba incompleta.

---

### 3. Arquitectura adoptada: Bronze, Silver y Gold

Se adoptó una arquitectura por capas, porque es la forma correcta de organizar un proyecto de datos de este tipo.

#### Bronze
La capa Bronze se usa para almacenar los datos crudos, es decir, los archivos tal como llegan desde las fuentes originales, sin transformaciones analíticas fuertes.

**¿Para qué sirve?**  
Sirve para preservar trazabilidad, evitar perder la fuente original y permitir reejecutar el pipeline cuando sea necesario.

#### Silver
La capa Silver se usa para limpiar, normalizar, homologar y agregar los datos a una granularidad analítica coherente.

**¿Para qué sirve?**  
Sirve para transformar datos heterogéneos en tablas consistentes, comparables y listas para ser integradas.

#### Gold
La capa Gold se usa para construir tablas analíticas finales, dimensiones, hechos y marts que el equipo puede usar directamente para sacar indicadores.

**¿Para qué sirve?**  
Sirve para que los integrantes del grupo no tengan que rehacer toda la ingesta y limpieza, sino trabajar sobre tablas ya listas para análisis.

---

### 4. Correcciones de ingeniería realizadas

### 4.1. Limpieza de portabilidad y seguridad

Se eliminaron dependencias específicas del computador original, como rutas absolutas tipo `C:\Users\...`, archivos `.env` locales, logs versionados, binarios, outputs temporales y artefactos de empaquetado innecesarios.

Además, se corrigieron temas de seguridad, incluyendo exposición de tokens o configuraciones sensibles.

**¿Para qué sirve esto?**  
Para que cualquier compañero pueda clonar el repositorio y trabajar sin depender de la estructura local de una sola persona. También mejora seguridad, limpieza del repositorio y control de versiones.

---

### 4.2. Empaquetado del proyecto como paquete Python

Se reorganizó el proyecto para que funcione como paquete Python instalable, con dependencias declaradas correctamente y entrypoints o comandos formales de ejecución.

Se corrigieron imports internos frágiles, hacks de `sys.path`, y se creó una interfaz de ejecución más estable mediante CLI.

**¿Para qué sirve esto?**  
Sirve para que el proyecto no dependa del directorio de trabajo, se instale de forma limpia y pueda ejecutarse de manera controlada en distintos entornos.

---

### 4.3. Unificación del flujo oficial y eliminación de ambigüedad

Se consolidó un solo flujo oficial del pipeline y se dejaron como legacy o históricos los scripts viejos que ya no deben usarse como camino principal.

También se alinearon README, instrucciones al equipo, Makefile y QA con la implementación real.

**¿Para qué sirve esto?**  
Sirve para reducir errores del grupo, evitar que cada persona ejecute algo distinto y asegurar que todos usen la misma arquitectura y los mismos comandos.

---

### 5. Correcciones analíticas y metodológicas

### 5.1. Corrección del cruce con SECOP

Se corrigió la lógica de integración de SECOP para evitar cruzar directamente contratos individuales con tablas sociales agregadas. En su lugar, SECOP se agrega primero al nivel adecuado y luego se integra.

Además, se revisó el conteo de `proveedores_unicos` entre SECOP I y SECOP II para evitar doble conteo de NITs que aparecen en ambas plataformas dentro del mismo municipio-año.

**¿Para qué sirve esto?**  
Sirve para que las métricas de contratación, competencia y concentración de mercado no queden infladas artificialmente ni distorsionadas por duplicaciones.

---

### 5.2. Tratamiento metodológico de EMICRON

EMICRON es una encuesta, no un censo exhaustivo. Por eso se revisó su integración para asegurar que no se estuviera usando como si cada fila representara una observación poblacional directa.

Se documentó el uso del factor de expansión y se corrigió la agregación para que el resultado sea estadísticamente más defendible.

**¿Para qué sirve esto?**  
Sirve para evitar sesgos graves. Si una encuesta se usa como si fuera conteo exhaustivo, las conclusiones sobre tejido empresarial o estructura económica pueden quedar mal interpretadas.

---

### 5.3. Construcción de dimensión territorio

Se reemplazaron nombres sintéticos de territorios por una dimensión territorial basada en catálogo real, con capacidad de ampliación vía archivo oficial.

**¿Para qué sirve esto?**  
Sirve para tener consistencia geográfica, mejorar trazabilidad territorial y permitir análisis más claros y defendibles en municipio, departamento u otros niveles.

---

### 6. Modelo analítico final

Se avanzó en la construcción de una estructura tipo modelo estrella o al menos dimensional, con dimensiones como tiempo y territorio, y tablas de hechos relacionadas con demografía, contratación y micronegocios.

También se construyó un mart final para integrar el componente social y económico en una sola salida analítica.

**¿Para qué sirve esto?**  
Sirve para que el equipo trabaje directamente sobre tablas analíticas finales, sin rehacer cruces complejos. Además, permite una base más estable para tableros, indicadores y análisis comparativos.

---

### 7. Integración del CNPV 2018

Uno de los avances más importantes recientes fue resolver la ingesta multicarpeta del CNPV 2018. El problema no era que el dato no existiera, sino que estaba distribuido en múltiples carpetas por departamento y módulos.

Se implementó una lógica para que el pipeline descubra automáticamente la carpeta base del censo, recorra subcarpetas por departamento e identifique archivos por módulo, usando una variable de entorno configurable para cada integrante del grupo.

En esta parte se trabajó con módulos como vivienda, hogares, personas, fallecidos y manzana, y se dejó Bronze alimentado desde esa estructura distribuida.

**¿Para qué sirve esto?**  
Sirve para que el equipo no tenga que señalar manualmente cientos de archivos, sino solo definir la carpeta raíz del censo y dejar que el pipeline haga el descubrimiento e ingesta automática.

---

### 8. Estado actual del proyecto

A la fecha, el proyecto ha mejorado mucho en términos de ingeniería, reproducibilidad y estructura analítica. Ya se resolvieron temas críticos como portabilidad, empaquetado, documentación, SECOP, EMICRON y la ingesta multicarpeta del CNPV.

Sin embargo, todavía hay una verificación importante en curso: la **reconciliación final del CNPV**. En particular, aún se está validando rigurosamente:

- si el conteo poblacional derivado del módulo de personas (`5PER`) está siendo interpretado correctamente;
- si la cobertura geográfica final del CNPV en Silver y Gold corresponde realmente al nivel territorial esperado;
- si el grano de integración censal es completamente consistente con el grano analítico del proyecto.

Esto significa que el proyecto ya está mucho más maduro y funcional, pero la parte censal todavía requiere una validación final para asegurar que el componente social entre de manera completamente consistente al producto final.

---

### 9. Utilidad académica y técnica de lo realizado

Todo lo que se ha hecho hasta ahora sirve para fortalecer tres dimensiones del proyecto.

#### Rigor técnico
Porque el código ya no depende de una sola máquina, tiene mejor estructura, mejor gestión de dependencias y una arquitectura más profesional.

#### Rigor metodológico
Porque los cruces entre bases dejaron de hacerse de forma ingenua y se empezaron a respetar temas como granularidad, agregación previa, expansión muestral e integración territorial.

#### Utilidad para el equipo
Porque ahora el grupo puede trabajar sobre una base más reproducible, más limpia y con salidas analíticas más claras, en vez de que cada integrante tenga que rehacer todo desde cero.

---

### 10. Conclusión

En síntesis, lo realizado no fue solo una corrección de scripts, sino una reestructuración completa del proyecto en términos de ingeniería de datos, analítica y trabajo colaborativo.

Se pasó de un repositorio con cruces frágiles, problemas de portabilidad y documentación inconsistente, a un pipeline mucho más organizado, con capas Bronze/Silver/Gold, un flujo oficial reproducible, integración más rigurosa de las fuentes y una base más sólida para construir indicadores sociales y económicos.

El punto que todavía se está cerrando de forma estricta es la validación final del CNPV en términos de cobertura poblacional y geográfica. Esa validación es importante porque el objetivo del proyecto no es solo económico, sino también social, y por tanto la entrada censal debe quedar correctamente interpretada y reconciliada antes de dar el cierre definitivo.
