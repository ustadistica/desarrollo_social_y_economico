# Guión de exposición

**Proyecto:** Sinergia socioeconómica — concentración de la contratación pública en Colombia (HHI)
**Equipo:** Consultorio de Estadística USTA · Observatorio Ustadística 2026-I
**Modalidad:** exposición para dos presentadores
**Duración estimada:** 12-15 minutos

## Distribución de roles

- **Presentador 1 (P1):** abre, presenta el problema, las fuentes de datos, el modelo dimensional y el cruce.
- **Presentador 2 (P2):** desarrolla el indicador HHI, los resultados con datos reales, los hallazgos y las limitaciones.

Ambos cierran la exposición.

---

## 1. Apertura (≈ 1 minuto)

**P1:** Buenos días. Somos parte del Consultorio de Estadística de la Universidad Santo Tomás, en el marco del Observatorio Ustadística. Hoy les vamos a presentar el proyecto *Sinergia socioeconómica*, que analiza la concentración de la contratación pública en Colombia entre 2018 y 2026, articulando datos abiertos de Colombia Compra Eficiente con información social y demográfica del DANE.

**P2:** La pregunta central que nos hicimos es muy concreta: cuando el Estado contrata, ¿el valor que paga se reparte entre muchos proveedores o se concentra en pocos? Esa pregunta tiene implicaciones en competencia, eficiencia del gasto y riesgo de captura de rentas. Para responderla usamos el Índice Herfindahl-Hirschman, conocido como HHI, que es un estándar internacional para medir concentración de mercado. Pero antes de hablar del indicador, necesitan entender de dónde vienen los datos.

---

## 2. ¿Por qué hablar primero de las bases de datos? (≈ 1 minuto)

**P1:** Un indicador como el HHI no se entiende sin entender la materia prima. Si la materia prima está mal medida o mal cruzada, el indicador miente. Por eso vamos a empezar por las fuentes: qué portales usamos, qué registran, qué miden y por qué cada una nos sirve para construir la pregunta del HHI.

La idea es que ustedes salgan de esta presentación pudiendo responder tres cosas: primero, qué información alimenta el indicador; segundo, cómo se integró esa información para que sea comparable; y tercero, qué significan los números del HHI cuando los leamos al final.

---

## 3. Las fuentes de datos abiertos (≈ 3 minutos)

**P1:** Usamos cinco fuentes oficiales, todas con descarga pública. Las voy a presentar en orden de importancia para el HHI.

### 3.1 SECOP I — Procesos de Compra Pública

**P1:** SECOP I es el sistema más antiguo de Colombia Compra Eficiente. Lo administra la entidad Colombia Compra Eficiente y se publica en el portal Datos Abiertos Colombia con el identificador `f789-7hwg`. Es un sistema heredado donde se registraban los procesos de contratación pública del Estado: licitaciones, contratación directa, mínima cuantía, todo. Cada fila es un proceso o contrato firmado por una entidad pública con un proveedor, con su monto, su fecha, el municipio de la entidad contratante y el NIT del contratista.

En cifras, materializamos **más de 6.3 millones de filas** de SECOP I, cubriendo el periodo 2018 a 2026.

**P2:** Esta es la base más grande del proyecto. Sin ella no hay HHI porque es donde están los contratos del Estado en la mayoría de municipios del país, especialmente los pequeños.

### 3.2 SECOP II — Contratos Electrónicos

**P1:** SECOP II es el sistema moderno que reemplazó a SECOP I a partir de 2017-2018 con un proceso de transición gradual. Mismo emisor —Colombia Compra Eficiente— mismo portal Datos Abiertos Colombia, identificador `jbjy-vk9h`. La diferencia técnica es que SECOP II es transaccional electrónico: las entidades ejecutan todo el proceso en línea, desde la convocatoria hasta la firma. Por eso trae información más rica y trazable.

Materializamos **5.6 millones de filas** de SECOP II.

**P2:** Por la transición entre los dos sistemas, un mismo contrato a veces aparece en ambas plataformas. Tuvimos que diseñar una deduplicación específica para no inflar los conteos. Más adelante les explico cómo.

### 3.3 CNPV 2018 — Censo Nacional de Población y Vivienda

**P1:** El Censo de Población y Vivienda del 2018 es el del DANE, accesible vía el Archivo Nacional de Datos en el catálogo 643, con identificador `DANE-DCD-CNPV-2018`. Es la radiografía demográfica oficial del país, con cobertura municipal completa.

Para nuestro proyecto, el CNPV cumple dos funciones: nos da los nombres oficiales de los 1,122 municipios catalogados, y nos provee la población base de referencia que se usa para indicadores per cápita en otros productos del observatorio.

**P2:** Es importante aclarar que el CNPV **no entra directamente en la fórmula del HHI**. El HHI mide concentración de valor adjudicado entre proveedores; no necesita variables sociales. El censo entra al modelo dimensional para enriquecer geográficamente los resultados.

### 3.4 EMICRON — Encuesta de Micronegocios

**P1:** EMICRON es la Encuesta de Micronegocios del DANE, también en el catálogo de microdatos del DANE; la referencia 2024 está en el catálogo 875. Esta encuesta mide la economía popular: micronegocios con menos de diez trabajadores, lo que en el lenguaje del Plan Nacional de Desarrollo se llama *economía popular y comunitaria*. La granularidad es **departamental**, no municipal, porque es una encuesta muestral, no un censo.

**P2:** Igual que el censo, EMICRON no entra en la fórmula del HHI pero sí en el contexto. Nos permite caracterizar la estructura económica local que rodea a la contratación pública.

### 3.5 Proyecciones de población

**P1:** Las proyecciones del DANE basadas en el censo de 2018 cubren de 2018 a 2050. Nos sirven para indicadores per cápita en el horizonte completo del análisis, no solo en el año censal.

**P2:** Y como con CNPV y EMICRON: alimentan el contexto, no la fórmula HHI.

---

## 4. Resumen útil: ¿qué hace cada base? (≈ 1 minuto)

**P1:** Para que no se pierdan, hagamos un mapa mental rápido. De las cinco bases, **dos son protagonistas del HHI**: SECOP I y SECOP II, porque registran los contratos públicos. Las otras tres —CNPV, EMICRON y proyecciones DANE— son **contextuales**: enriquecen el análisis con nombres de municipios, departamentos, regiones, población y entorno económico, pero no entran en el cálculo del indicador.

**P2:** Dicho de otra forma: el HHI se calcula 100 % con SECOP. El cruce con DANE da el contexto para interpretarlo.

---

## 5. Cómo construimos el modelo dimensional (≈ 3 minutos)

**P1:** Las cinco bases vienen en formatos diferentes, con codificaciones diferentes, con granularidades diferentes y con nombres distintos para los mismos municipios. Tuvimos que homogenizarlas para poder cruzarlas. Lo hicimos con una **arquitectura Medallion**, que tiene tres capas: Bronce, Plata y Oro.

### 5.1 Capa Bronce

**P1:** La capa Bronce es la ingesta cruda. Tomamos los CSV oficiales descargados manualmente de los portales —SECOP de Datos Abiertos Colombia, y los del DANE desde los catálogos de microdatos— y los convertimos a un formato llamado Parquet, que es columnar y comprimido, sin transformar el contenido. Lo importante de esta capa es que conserva la copia fiel del dato original, con metadatos de trazabilidad: cuándo se ingestó, cuál fue la fuente, qué versión, un hash de integridad. Si en cualquier momento alguien duda de un número, podemos rastrearlo hasta el dato crudo en Bronce.

**P2:** En cifras: la capa Bronce de SECOP I son más de 6.3 millones de filas con 84 columnas; la de SECOP II son 5.6 millones de filas con 89 columnas; el módulo de personas del CNPV son **más de 44 millones de filas**, una por cada persona censada en 2018.

### 5.2 Capa Plata

**P1:** La capa Plata es donde limpiamos. Aquí pasan tres cosas críticas para el HHI. Primera: tipificamos los datos. Los montos en SECOP vienen como texto con signos de pesos, puntos y comas; los convertimos a números reales. Segunda: estandarizamos el código geográfico, el DIVIPOLA. El DIVIPOLA es el código de cinco dígitos que el DANE asigna a cada municipio; los dos primeros son el departamento, los tres siguientes el municipio. Es nuestra **llave de cruce** entre todas las bases.

**P2:** Esto último fue un trabajo grande, porque SECOP I no trae el código DIVIPOLA directamente: trae el nombre del municipio en texto libre. Entonces hubo que mapear nombre a código usando un catálogo embebido con los 1,102 municipios de Colombia, con normalización de tildes, mayúsculas y variantes ortográficas. Sin esa estandarización, el cruce con DANE habría sido imposible.

**P1:** Tercera transformación en Plata: deduplicamos. Si un contrato aparece en SECOP I y SECOP II, lo contamos una sola vez. La regla es: si el `id_contrato` se repite entre plataformas, nos quedamos con la primera ocurrencia. Esto evita inflar artificialmente la inversión total.

**P2:** Cifras de la capa Plata: SECOP I transaccional limpio queda en 5.4 millones de filas; SECOP II en 4 millones. La diferencia con Bronce se debe a contratos con DIVIPOLA inválido, montos en cero o años fuera del rango 2018-2026, que se descartan por calidad.

### 5.3 Capa Oro

**P1:** La capa Oro es el modelo dimensional propiamente dicho. Aquí construimos dos tipos de tablas: **dimensiones**, que describen entidades estables, y **hechos**, que registran eventos cuantificables.

Las dimensiones son dos:

- **`dim_tiempo`**: una fila por año entre 2018 y 2029, con atributos como si fue año electoral o si fue año de pandemia.
- **`dim_territorio`**: una fila por cada código DIVIPOLA, con nombre del municipio, nombre del departamento, código departamental y región.

Los hechos son cuatro:

- **`fact_contratacion_municipio_anio`**: la unión deduplicada de SECOP I y SECOP II por municipio y año. Aquí registramos el número de procesos, la inversión total y el número de proveedores únicos.
- **`fact_censo_municipio`**: la población base CNPV 2018, propagada a todos los años porque el censo es un *snapshot* fijo.
- **`fact_micronegocios_municipio_anio`**: el volumen expandido de micronegocios EMICRON por departamento-año.
- **`fact_demografia_municipio_anio`**: las proyecciones de población DANE por departamento-año.

**P2:** Y todos esos hechos y dimensiones se integran en una tabla final que llamamos el *mart*, o tabla analítica única. Tiene **13,860 filas**, cubre 1,155 códigos DIVIPOLA y 2018-2029. Es la tabla que un analista o el dashboard consume directamente.

---

## 6. ¿Por qué este modelo es útil? (≈ 1 minuto)

**P1:** Tres razones prácticas. Primera: **trazabilidad**. Si alguien cuestiona un número del HHI, podemos rastrear desde el resultado hasta el contrato individual en SECOP. Segunda: **reproducibilidad**. Cualquier persona del equipo regenera todo el pipeline con un comando: `python -m src.cli all`. Tercera: **separación de responsabilidades**. Los cambios en la limpieza no afectan los cálculos del indicador, los cambios en el indicador no afectan la ingesta. Esto hace que el proyecto sea mantenible incluso si rotamos el equipo.

---

## 7. ¿Qué es el HHI y por qué lo usamos? (≈ 2 minutos)

**P2:** Ahora sí, el indicador. El Índice Herfindahl-Hirschman, o HHI, es una medida estándar de concentración de mercado. Lo usan las autoridades de competencia en Estados Unidos, en la Unión Europea y en muchos otros países para decidir, por ejemplo, si una fusión empresarial reduce demasiado la competencia.

La fórmula es muy simple: en un mercado dado, calculamos la participación porcentual de cada actor, la elevamos al cuadrado y sumamos. El resultado queda en una escala de 0 a 10,000.

- Si en un mercado hay **muchos proveedores con participaciones pequeñas**, el HHI es bajo. La interpretación es competencia alta.
- Si **un solo proveedor concentra todo**, el HHI llega al máximo de 10,000. Esto es un monopolio.
- Entre esos extremos, la convención internacional es: **menor a 1,500 es concentración baja; entre 1,500 y 2,500 es moderada; mayor o igual a 2,500 es alta**.

**P1:** Nosotros aplicamos esta fórmula a la contratación pública. Para cada municipio, cada año y cada orden de entidad —nacional, territorial, otro, no definido—, calculamos qué porcentaje del valor total fue a cada proveedor único, identificado por su NIT, y sumamos los cuadrados de esas participaciones.

**P2:** La unidad de análisis es un **mercado**: municipio × año × orden de entidad. Calculamos HHI para 11,792 mercados en total entre 2018 y 2026.

---

## 8. Resultados con datos reales (≈ 3 minutos)

### 8.1 Tendencia anual nacional

**P2:** El primer resultado es la evolución del HHI promedio nacional año a año.

- En 2018, el HHI promedio fue **1,221.87** con mediana 669.
- En 2020 bajó a **1,040.57**, el mínimo de la serie. Esto coincide con la pandemia: hubo más contratos pequeños de emergencia distribuidos entre más proveedores.
- En 2023 subió a **1,483.89**, el máximo intermedio.
- En 2025 llegó a **1,484.07**, prácticamente empatado con 2023.
- En 2026 está en **1,422.50** con el dato disponible al corte de mayo.

**P1:** Estos valores están todos en la banda de concentración **baja a moderada**, según la convención internacional. Eso significa que la contratación pública colombiana, en su conjunto, **no presenta monopolización generalizada**. Pero el promedio esconde matices, y es ahí donde está la información interesante.

### 8.2 Diferencia entre orden nacional y orden territorial

**P2:** La segmentación por orden de entidad muestra una diferencia consistente y muy importante.

- En 2018, el HHI promedio del **orden nacional** fue **2,145.84**; el territorial fue **1,047.54**.
- En 2025, el nacional fue **2,809.30**; el territorial **1,147.46**.
- En 2026, el nacional fue **2,189.69**; el territorial **1,237.99**.

El nacional siempre concentra más, y a veces casi triplica al territorial.

**P1:** ¿Por qué? La razón estructural es que la contratación del orden nacional incluye ministerios, agencias, Invías, ICBF, Fuerzas Militares, entidades grandes que firman pocos contratos pero de gran magnitud, con proveedores especializados. El orden territorial son alcaldías, hospitales municipales, instituciones educativas; muchos más contratos, más fragmentados, con mayor pluralidad de proveedores locales.

**P2:** Esto tiene una implicación de política pública: cualquier diagnóstico de competencia en la contratación tiene que separar los dos órdenes. Mezclarlos esconde el problema.

### 8.3 Departamentos con mayor concentración en 2026

**P2:** Por departamento, en el último año disponible, los cinco con mayor HHI promedio son:

- **Atlántico** con HHI promedio **2,824.15** sobre 31 mercados.
- **Chocó** con **2,695.77** sobre 19 mercados.
- **Magdalena** con **2,053.98** sobre 34 mercados.
- **La Guajira** con **1,885.03** sobre 20 mercados.
- **Boyacá** con **1,816.14** sobre 143 mercados.

Y del otro lado, los menos concentrados son **Guainía** con 495, **Quindío** con 518 y **Amazonas** con 629.

**P1:** La lectura aquí requiere prudencia. Atlántico, Chocó y Magdalena en la parte alta de la tabla no significan automáticamente que haya algo irregular. Puede haber explicaciones estructurales: pocos proveedores con capacidad técnica para ciertos tipos de obra, o contratos grandes que dominan el agregado del año. El HHI sirve para identificar **dónde mirar**, no para concluir directamente.

### 8.4 Los casos extremos: HHI = 10,000

**P2:** Un dato que llama la atención: el HHI máximo posible es 10,000 y aparece en algunos mercados. ¿Significa que tenemos cientos de monopolios? La respuesta es no, y vale la pena detallarla.

De los 11,792 mercados, solo **186 alcanzan HHI = 10,000**. Eso es **1.58 %**, menos del 2 % del total. Y de esos 186:

- **167** tienen exactamente un contrato y un proveedor. Matemáticamente la única participación es 100 % y el HHI da 10,000 por construcción. No es informativo.
- **19** son **monopolios reales**: tienen varios contratos pero todos fueron al mismo NIT.
- **Cero** tienen más de un proveedor con HHI = 10,000, lo que confirma que la fórmula está bien implementada.

**P1:** Es decir: la cantidad de mercados con un único proveedor real es muy pequeña en términos absolutos —19 casos en nueve años— y la aparición del HHI máximo no es un error de cálculo ni de ingesta, sino la consecuencia natural de mercados muy pequeños donde un solo contrato satura la fórmula. Esos casos los marcamos para revisión cualitativa, no como alarma automática.

---

## 9. Hallazgos clave (≈ 1 minuto)

**P1:** Resumimos los cuatro hallazgos principales.

1. La concentración promedio de la contratación pública colombiana entre 2018 y 2026 se mantiene en la banda **baja a moderada**, con HHI promedio entre **1,040 y 1,484**.
2. El **orden nacional concentra de forma sistemática más que el territorial**: en algunos años casi tres veces más. Cualquier análisis serio debe separar los dos órdenes.
3. Existen **focos territoriales** —Atlántico, Chocó, Magdalena, La Guajira— con HHI departamental superior a 1,800 en 2026 que ameritan análisis caso a caso.
4. Los mercados con HHI = 10,000 son apenas **1.58 %** del total y, en su mayoría, son artefactos de mercados pequeños, no monopolios estructurales.

---

## 10. Limitaciones que hay que decir explícitamente (≈ 1 minuto)

**P2:** Tres limitaciones importantes que el público debe conocer para leer los números con cuidado.

**Primera:** El municipio que registramos en SECOP es el de la **entidad contratante, no el del lugar de ejecución del contrato**. Por eso Bogotá concentra entre 34 % y 55 % del monto anual: muchas entidades nacionales tienen sede en Bogotá aunque ejecuten contratos en todo el país. Nosotros mitigamos este sesgo segmentando por orden de entidad, pero la advertencia siempre debe ir explícita.

**Segunda:** El HHI **mide concentración del valor adjudicado, no calidad de la competencia**. No sabemos cuántos oferentes hubo en cada proceso, ni si la convocatoria fue plural. Para esas preguntas hace falta otra información, complementaria al HHI.

**P1:** **Tercera:** Los datos de fuentes con secreto estadístico, como el CNPV o EMICRON, **no se pueden cruzar a nivel persona** con la información de proveedores SECOP. Trabajamos siempre con agregaciones territoriales —municipio o departamento— por mandato de la Ley 79 de 1993. Esto es una restricción legal, no una limitación técnica.

---

## 11. Cierre conjunto (≈ 1 minuto)

**P1:** En síntesis: tomamos cinco fuentes oficiales de datos abiertos, las integramos en una arquitectura reproducible de tres capas, construimos un modelo dimensional con dos dimensiones y cuatro tablas de hechos, y calculamos un indicador internacional de concentración aplicado a 11,792 mercados colombianos entre 2018 y 2026.

**P2:** El indicador HHI nos permite afirmar con datos que la contratación pública nacional no está monopolizada en términos generales, que el orden nacional concentra más que el territorial, y que hay focos puntuales que merecen revisión específica. El proyecto deja como producto un informe estadístico completo, un dashboard interactivo, una infografía, esta presentación, y la base de datos con su diccionario disponible para análisis posteriores.

**P1:** Todo el repositorio está versionado, documentado y es reproducible. Gracias por su atención. Quedamos atentos a sus preguntas.

---

## Anexo: tabla resumen de datos para apoyo visual

### Tabla A. Volumen ingestado

| Capa y fuente | Filas | Cobertura |
|---|---:|---|
| Bronze SECOP I | 6,354,773 | 2018-2026 |
| Bronze SECOP II | 5,599,845 | 2018-2026 |
| Bronze CNPV personas | 44,164,417 | 2018 |
| Silver SECOP I transaccional | 5,456,438 | 2018-2026 |
| Silver SECOP II transaccional | 4,026,650 | 2018-2026 |
| Gold mart | 13,860 | 2018-2029 |
| Tabla maestra HHI | 11,792 | 2018-2026 |

### Tabla B. HHI promedio anual

| Año | HHI promedio | HHI mediana | Mercados |
|---:|---:|---:|---:|
| 2018 | 1,221.87 | 669.65 | 1,258 |
| 2019 | 1,405.88 | 792.15 | 1,273 |
| 2020 | 1,040.57 | 460.45 | 1,296 |
| 2021 | 1,121.26 | 582.21 | 1,313 |
| 2022 | 1,373.02 | 667.29 | 1,361 |
| 2023 | 1,483.89 | 768.95 | 1,321 |
| 2024 | 1,114.10 | 515.55 | 1,324 |
| 2025 | 1,484.07 | 680.59 | 1,354 |
| 2026 | 1,422.50 | 701.35 | 1,292 |

### Tabla C. HHI por orden de entidad (2026)

| Orden | HHI promedio | Mediana | Mercados |
|---|---:|---:|---:|
| NACIONAL | 2,189.69 | 774.96 | 179 |
| TERRITORIAL | 1,237.99 | 679.92 | 1,067 |

### Tabla D. Top departamentos por HHI promedio (2026)

| Departamento | HHI promedio | Mercados |
|---|---:|---:|
| Atlántico | 2,824.15 | 31 |
| Chocó | 2,695.77 | 19 |
| Magdalena | 2,053.98 | 34 |
| La Guajira | 1,885.03 | 20 |
| Boyacá | 1,816.14 | 143 |

### Tabla E. Mercados con HHI = 10,000

| Tipo | Mercados |
|---|---:|
| 1 contrato, 1 proveedor | 167 |
| ≥ 2 contratos, 1 solo proveedor (monopolio real) | 19 |
| HHI = 10,000 con varios proveedores (imposible — bug check) | 0 |
| **Total** | **186 (1.58 % de 11,792)** |
