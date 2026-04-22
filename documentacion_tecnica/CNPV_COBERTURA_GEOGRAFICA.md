# Cobertura Geográfica CNPV (Reconciliación de Territorios)

**Fecha:** 2026-04-21

La calidad del modelo Estrella recae en que las llaves foráneas territoriales (DIVIPOLA) crucen correctamente. Este documento explica el comportamiento geográfico real del Censo.

## 1. Códigos Territoriales Reales en Bronze
La auditoría con DuckDB sobre el dataset original de `5PER` (44.1 millones de filas) concatenando `LPAD(U_DPTO, 2, '0') || LPAD(U_MPIO, 3, '0')` arrojó exactamente **1,122 códigos únicos**.
* **Interpretación:** El censo trae cobertura total de los 1,122 municipios de Colombia vigentes en 2018.

## 2. Reconciliación en Silver y Gold
- **El caso de los 299 territorios reportados previamente:** El pipeline Gold (`dim_territorio`) reportó 299 territorios en las últimas pruebas porque el parser local en Bronze estaba restringido a leer solo 250k registros por archivo para facilitar pruebas rápidas. Estos 250k de los 33 departamentos alcanzaban a mapear solo una fracción de los municipios (143 municipios censados en esas primeras porciones + 156 agregados propios de la dimensión territorio).
- **Ejecución Completa (Sin Restricciones):** Cuando el script de Ingesta Bronze procesa la totalidad del archivo CSV, Silver agrega exactamente 1,122 filas de `fact_censo` (una por cada municipio). 
- Por lo tanto, `dim_territorio` asimila **la totalidad territorial del país**, cruzando exhaustivamente al nivel municipal y departamental esperado por el proyecto.

## 3. Calidad de la Georreferenciación
- **Nivel del Censo:** Estrictamente **Municipal**.
- No existe "mezcla de niveles" silenciosa en el Censo. El archivo `5PER` tiene tanto departamento (`U_DPTO`) como municipio (`U_MPIO`). Silver SIEMPRE concatena a 5 dígitos (`divipola_key`). Si el analista quiere ver información departamental en el BI, usará el nivel jerárquico de `dim_territorio` agolpando los componentes de los 5 dígitos, pero en el datamart (OBT) todos los 1,122 registros del censo entran por su puerta respectiva de municipio.
