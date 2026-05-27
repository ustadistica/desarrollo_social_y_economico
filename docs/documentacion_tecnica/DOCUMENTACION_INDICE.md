# Índice de Documentación — Pipeline Socioeconómico

Guía rápida para navegar toda la documentación del proyecto. La estructura está organizada en:
- **Raíz** — Documentos para empezar (instalación, setup)
- **documentacion_tecnica/** — Documentación técnica de datos
- **docs/** — Informes y diagnósticos

---

## 📋 Estructura de Documentación

### **Ingesta, Validación y Cruce (Inicio Recomendado)**

| Documento | Descripción |
|-----------|------------|
| [`../docs/INFORME_TECNICO_INGESTA_CRUCE.md`](../docs/INFORME_TECNICO_INGESTA_CRUCE.md) | **📌 DOCUMENTO MAESTRO.** Ingesta (Bronze) → Validación (Silver) → Cruce (Gold). Incluye: estructura de capas, responsabilidades, bugs corregidos, diccionario Gold integrado, metodología EMICRON. **Comience aquí.** |
| [`../src/README.md`](../src/README.md) | Estructura interna de `src/`. Flujo de datos, salidas principales, bugs corregidos. |
| [`../data/README.md`](../data/README.md) | Contexto de datos SECOP (histórico y actualización). |

---

### **Arquitectura y Diseño**

| Documento | Descripción |
|-----------|------------|
| [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) | Esquemas esperados en cada tabla (Parquet). Clave primaria, tipos de datos, restricciones, validaciones. |
| [`../docs/INFORME_TECNICO_INGESTA_CRUCE.md`](../docs/INFORME_TECNICO_INGESTA_CRUCE.md#diccionario-gold) | Diccionario de columnas de Gold (sección integrada). Dimensiones, tablas de hechos, métricas y descripciones. |

---

### **Validación de Datos**

| Documento | Descripción |
|-----------|------------|
| [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) | Validaciones en cada capa. Esquemas esperados, nulabilidad, restricciones, assertions. |
| [`VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`](VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md) | Deduplicación SECOP I+II. Estrategia COUNT(DISTINCT nit) sobre UNION transaccional. |
| [`RECONCILIACION_CNPV_SECOP_EMICRON.md`](RECONCILIACION_CNPV_SECOP_EMICRON.md) | Auditoría: integración y reconciliación entre todas las fuentes de datos. |

---

### **Documentación por Fuente**

| Documento | Fuente | Descripción |
|-----------|--------|------------|
| [`documentacion_tecnica/CNPV_MASTER_DOCUMENTATION.md`](documentacion_tecnica/CNPV_MASTER_DOCUMENTATION.md) | **CNPV 2018** | Censo de población. Estructura 33 carpetas, agregación a municipio, universo 44M+ registros. |
| [`documentacion_tecnica/EMICRON_METODOLOGIA_FINAL.md`](documentacion_tecnica/EMICRON_METODOLOGIA_FINAL.md) | **EMICRON** | Encuesta micronegocios. Factores de expansión fex_c, agregación depto-año. |
| [`documentacion_tecnica/RECONCILIACION_CNPV_SECOP_EMICRON.md`](documentacion_tecnica/RECONCILIACION_CNPV_SECOP_EMICRON.md) | Múltiples | Cruce y validación de consistencia entre CNPV, SECOP, EMICRON. |

---

### **Informes y Auditoría**

| Documento | Descripción |
|-----------|------------|
| [`CHANGELOG_TECNICO.md`](CHANGELOG_TECNICO.md) | Historial de cambios, versiones, actualizaciones técnicas. |
| [`TECHNICAL_MASTER_AUDIT.md`](TECHNICAL_MASTER_AUDIT.md) | Auditoría comprensiva del pipeline: validaciones, integridad, reconciliación. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Guía para contribuidores: estándares de código, procesos de validación. |

---

### **Reportes Ejecutivos**

| Documento | Descripción |
|-----------|------------|
| [`docs/INFORME_EJECUTIVO_ARQUITECTURA_DATOS.md`](documentacion_tecnica/INFORME_EJECUTIVO_ARQUITECTURA_DATOS.md) | Resumen ejecutivo de arquitectura de datos para stakeholders. |
| [`docs/INFORME_AVANCE_ARQUITECTURA_Y_METODOLOGIA.md`](docs/INFORME_AVANCE_ARQUITECTURA_Y_METODOLOGIA.md) | Avance técnico y metodológico del proyecto. |

---

## 🎯 Cómo Usar Este Índice

### **Si Necesitas Entender el Pipeline Completo:**
1. Lee: [`INGESTA_VALIDACION_CRUCE.md`](documentacion_tecnica/INGESTA_VALIDACION_CRUCE.md) — Documento maestro
2. Consulta: [`DATA_CONTRACTS.md`](documentacion_tecnica/DATA_CONTRACTS.md) — Esquemas y validaciones

### **Si Necesitas Validar Datos:**
1. [`DATA_CONTRACTS.md`](documentacion_tecnica/DATA_CONTRACTS.md) — Esquemas esperados, nulabilidad, restricciones
2. [`VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`](documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md) — Deduplicación SECOP
3. [`RECONCILIACION_CNPV_SECOP_EMICRON.md`](documentacion_tecnica/RECONCILIACION_CNPV_SECOP_EMICRON.md) — Auditoría final

### **Si Necesitas Entender Una Fuente Específica:**
- **CNPV:** [`CNPV_MASTER_DOCUMENTATION.md`](documentacion_tecnica/CNPV_MASTER_DOCUMENTATION.md)
- **EMICRON:** [`EMICRON_METODOLOGIA_FINAL.md`](documentacion_tecnica/EMICRON_METODOLOGIA_FINAL.md)
- **SECOP I+II:** [`VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md`](documentacion_tecnica/VALIDACION_NO_DOBLE_CONTEO_PROVEEDORES.md)

### **Si Necesitas Contextualizar el Proyecto:**
1. [`src/README.md`](src/README.md)
2. [`data/README.md`](data/README.md)

---

## 🐛 Bugs Corregidos (Histórico Rápido)

| Bug | Archivo | Severidad | Resultado |
|-----|---------|-----------|----------|
| SECOP II: moneda 99.6% cero | `clean_secop_ii.py` | 🔴 Crítica | Regex corregida, max 999K → 54.8B COP ✅ |
| Mart: años 2030-2050 espurios | `build_mart.py` | 🟡 Alta | Filtro anios_validos, 6,825 → 3,129 filas ✅ |
| Mart: per-cápita NaN (granularidad) | `build_mart.py` | 🔴 Crítica | Lookup depto, 0 → 1,034 indicadores ✅ |

**Detalles:** Ver [`INGESTA_VALIDACION_CRUCE.md`](documentacion_tecnica/INGESTA_VALIDACION_CRUCE.md) sección "Bugs Encontrados y Solucionados".

---

## 📊 Estado Actual

✅ **Pipeline Operacional**
- Ingesta (Bronze): 100%
- Limpieza (Silver): 100% (con fixes)
- Modelo Dimensional (Gold): 100% (con fixes)
- OBT Analítico: 3,129 filas, 295 territorios, 2018-2029

❌ **Limitaciones Conocidas** (no bugs):
- `dim_territorio`: 299 municipios (falta DIVIPOLA oficial)
- SECOP II: sample (43MB) en lugar de full (9.6GB)
- EMICRON: 25 filas (encuesta limitada)
- CNPV: 143 municipios (solo deptos disponibles)

---

## 🔗 Navegación Rápida

**Carpetas principales:**
- `src/ingesta/` — Extracción de datos
- `src/transformacion/` — Limpieza y modelo dimensional
- `src/modelo/` — Análisis estadístico
- `src/visualizacion/` — Gráficos y mapas
- `data/bronze/`, `data/silver/`, `data/gold/` — Capas de datos

**Documentación:**
- `documentacion_tecnica/` — Documentos técnicos detallados
- `docs/` — Informes ejecutivos
- Root `.md` files — README, CHANGELOG, CONTRIBUTING

---

**Última actualización:** 2026-04-23  
**Responsable:** Johann Sebastian  
**Estado:** 🟢 Actualizado con todos los bugs corregidos
