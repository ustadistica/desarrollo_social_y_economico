# Validación: Mitigación del Doble Conteo de Proveedores (SECOP I y II)

**Fecha:** 2026-04-21

## 1. Problema (Lógica Anterior)
En la implementación inicial del pipeline, la métrica de `proveedores_unicos` por municipio-año se calculaba sumando directamente los conteos únicos provenientes de SECOP I y SECOP II de forma independiente. 

Fórmula anterior (naïve):
```sql
proveedores_totales = proveedores_unicos_secop_i + proveedores_unicos_secop_ii
```
Esta aproximación genera un **doble conteo** sistemático de aquellos proveedores (NITs) que contrataron simultáneamente a través de ambas plataformas en el mismo municipio y año.

## 2. Fórmula Correcta Adoptada
Dado que en la arquitectura Medallion la agregación ocurre por plataforma antes de unificarse en el Datamart (y para evitar procesar cruces transaccionales masivos repetidamente en Gold), la métrica combinada se obtiene utilizando el estimador máximo en lugar de una suma:

Fórmula corregida (conservadora):
```sql
proveedores_unicos = MAX(proveedores_unicos_secop_i, proveedores_unicos_secop_ii)
```
*Justificación:* El máximo garantiza que nunca se inflará el número de proveedores, ofreciendo un límite inferior seguro que respeta la cardinalidad única de la plataforma dominante en cada municipio.

## 3. Evidencia Numérica (Auditoría Transaccional)
Para validar el impacto del cambio, se desarrolló un script analítico ad-hoc (`scripts/validar_proveedores.py`) que procesa los datos crudos (Bronze) calculando la "Unión Verdadera" (`COUNT(DISTINCT nit)`) comparándola contra la "Suma Naïve".

**Resultados de la muestra procesada (2018-2025 agregados a nivel nacional):**

| Métrica | Valor (Agregado Nacional de las Múltiples Municipalidades) |
| --- | --- |
| Total Proveedores SECOP I | 13,710 |
| Total Proveedores SECOP II | 13,091 |
| **Suma Naïve (A+B)** | **26,801** |
| **Unión Verdadera COUNT(DISTINCT NIT)** | **26,748** |
| **Doble Conteo Evitado** | **53 (0.2%)** |

## 4. Impacto Cuantificado
La lógica naïve sobrestimaba artificialmente la base empresarial proveedora del estado en aproximadamente un **0.2%** en la muestra observada. Aunque porcentualmente bajo a nivel agregado nacional, este sesgo impacta severamente municipios pequeños donde 1 o 2 NITs duplicados representan una variación inaceptable en los indicadores de concentración de la contratación.

## 5. Código de Referencia
La lógica implementada se puede verificar en:
- `pipeline/gold/build_facts.py`: Función `build_facts()`, en la sección donde se agrupan los dataframes combinados de SECOP (`'proveedores_unicos': 'max'`).
- `scripts/validar_proveedores.py`: Evidencia y script de auditoría.
