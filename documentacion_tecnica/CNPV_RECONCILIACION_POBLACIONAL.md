# Reconciliación Poblacional: Módulo 5PER (CNPV 2018)

**Fecha:** 2026-04-21

Este documento certifica estadísticamente la pertinencia del cálculo poblacional generado a partir de los datos masivos del CNPV.

## 1. Unidad de Observación (`5PER`)
A diferencia de EMICRON (donde una fila representa un micronegocio encuestado y debe expandirse estadísticamente con `F_EXP`), el CNPV es un censo exhaustivo universal. 
- En el módulo `5PER`, **una (1) fila = una (1) persona efectivamente censada**.
- La base *no contiene factor de expansión de muestreo probabilístico* (`FEX`), por lo que su agregación directa mediante el conteo de la llave geográfica es metodológicamente válida.

## 2. Reconciliación del Conteo Bruto vs. Agregado Silver
- **Conteo Físico Real:** 44,164,417 personas registradas en las fuentes locales.
- **Diferencia Previa Reportada (7,085,702):** Este número no obedeció a descartes silenciosos ni nulos lógicos, sino a un truncamiento artificial (`chunk_size=250k`) impuesto en el script de carga asíncrona local para validaciones rápidas de arquitectura (CI/CD).
- Tras retirar dicho truncamiento, la instrucción de Silver `df.groupby("divipola_key").size()` opera sobre el *DataFrame* completo.
- No existen filtros condicionales adicionales que excluyan personas en `clean_cnpv.py` (no se omite a nadie por edad o sexo, ya que la meta del OBT es la población total).

## 3. Manejo de Nulos y Llaves
La única exclusión posible en Silver (líneas de depuración geográfica) ocurre si una persona no reporta `U_DPTO` ni `U_MPIO`. La auditoría confirma que el 100% de los 44 millones de registros del `5PER` incluyen al menos el departamento y el municipio validos; no hay pérdidas sistémicas.
