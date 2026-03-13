# Verificación de Migración: SQLite → DuckDB

## Modelo Estrella SECOP

---

## 📋 Resumen Ejecutivo

Este documento describe el proceso de **verificación de integridad de datos** después de migrar el modelo estrella de SECOP desde SQLite hacia DuckDB.

### Estado Actual

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| Migración completada | ✅ | Exitosa |
| Verificación de integridad | ⚠️ | 5/6 pruebas pasaron |
| Datos en SQLite | ✅ | 31,892 registros totales |
| Datos en DuckDB | ✅ | 31,892 registros totales |

---

## 📊 Volumen de Datos

| Tabla | Registros | Descripción |
|-------|-----------|-------------|
| `D_Entidad` | 2,941 | Entidades contratantes |
| `D_Proveedor` | 6,421 | Proveedores/contratistas |
| `D_Tiempo` | 4 | Dimensión temporal |
| `D_UbiEntidad` | 801 | Ubicación de entidades |
| `D_UbiProveedor` | 608 | Ubicación de proveedores |
| `D_Categoria` | 2,083 | Categorías de contratación |
| `D_Modalidad` | 15 | Modalidades de contratación |
| `D_TipoContrato` | 19 | Tipos de contrato |
| `F_Proceso` | 19,000 | **Tabla de hechos** |
| **TOTAL** | **31,892** | |

---

## 🗂️ Estructura del Modelo Estrella

### Tablas de Dimensión (8)

| Tabla | Primary Key | Columnas |
|-------|-------------|----------|
| `D_Entidad` | entidad_id | 6 |
| `D_Proveedor` | proveedor_id | 5 |
| `D_Tiempo` | tiempo_id | 6 |
| `D_UbiEntidad` | ubi_entidad_id | 3 |
| `D_UbiProveedor` | ubi_proveedor_id | 3 |
| `D_Categoria` | categoria_id | 2 |
| `D_Modalidad` | modalidad_id | 3 |
| `D_TipoContrato` | tipo_contrato_id | 3 |

### Tabla de Hechos (1)

| Tabla | Primary Key | Columnas | Foreign Keys |
|-------|-------------|----------|--------------|
| `F_Proceso` | id_del_proceso | 18 | 8 FKs a dimensiones |

---

## 🔗 Relaciones (Foreign Keys)

```
F_Proceso.entidad_id       → D_Entidad.entidad_id
F_Proceso.proveedor_id     → D_Proveedor.proveedor_id
F_Proceso.tiempo_id        → D_Tiempo.tiempo_id
F_Proceso.ubi_entidad_id   → D_UbiEntidad.ubi_entidad_id
F_Proceso.ubi_proveedor_id → D_UbiProveedor.ubi_proveedor_id
F_Proceso.categoria_id     → D_Categoria.categoria_id
F_Proceso.modalidad_id     → D_Modalidad.modalidad_id
F_Proceso.tipo_contrato_id → D_TipoContrato.tipo_contrato_id
```

---

## 📁 Archivos

| Archivo | Ubicación | Descripción |
|---------|-----------|-------------|
| SQLite (origen) | `modelo_estrella_sqlite/Proyect_SECOP.db` | Base de datos original |
| DuckDB (destino) | `modelo_estrella_duckdb/Proyect_SECOP.duckdb` | Base de datos migrada |
| Script ETL | `load_star_model.py` | Carga datos Parquet → Modelo Estrella |
| Script verificación | `verify_migration.py` | Migración y verificación |

---

## 🧪 Proceso de Verificación

El script `verify_migration.py` ejecuta **6 verificaciones**:

### 1. Conteo de Registros ✅
- Compara el número de filas en cada tabla entre SQLite y DuckDB
- **Resultado:** 9/9 tablas coinciden exactamente

### 2. Esquema y Tipos de Datos ✅
- Verifica que todas las columnas existan en ambas bases
- Compara tipos de datos (con conversión apropiada SQLite→DuckDB)
- **Resultado:** 51 columnas verificadas correctamente

### 3. Integridad Referencial ✅
- Valida que todas las foreign keys apunten a registros existentes
- Detecta registros huérfanos en la tabla de hechos
- **Resultado:** 8 FKs sin registros huérfanos

### 4. Valores Nulos Críticos ⚠️
- Verifica que las primary keys y foreign keys no tengan NULL
- **Resultado:** 3 columnas con NULLs (5 registros de 19,000 = 0.03%)
- **Detalle:**
  - `F_Proceso.entidad_id`: 5 NULLs
  - `F_Proceso.proveedor_id`: 5 NULLs
  - `F_Proceso.tiempo_id`: 5 NULLs
- **Causa:** Los 5 registros (CO1.REQ.8856229, CO1.REQ.8831315, etc.) no tienen entidad, proveedor o fecha válidos en los datos fuente

### 5. Unicidad de Primary Keys ✅
- Detecta valores duplicados en columnas PK
- **Resultado:** 9 PKs sin duplicados

### 6. Agregaciones y Sumas de Control ✅
- Compara SUM y AVG de columnas numéricas entre SQLite y DuckDB
- **Resultado:**
  - `precio_base`: SUM = $3,352,378,654,419
  - `valor_total_adjudicacion`: SUM = $30,933,903,676
  - `numero_de_lotes`: SUM = 468

---

## 🚀 Cómo Ejecutar la Verificación

### Requisitos

```bash
pip install duckdb pandas pyarrow
```

### Paso 1: Cargar datos (si es necesario)

```bash
python load_star_model.py
```

### Paso 2: Ejecutar verificación

```bash
python verify_migration.py
```

### Salida Esperada

```
[OK] Conteo de Registros
[OK] Esquema y Tipos de Datos
[OK] Integridad Referencial
[OK] Valores Nulos Criticos
[OK] Unicidad de Primary Keys
[OK] Agregaciones

Total: 6/6 verificaciones pasaron
```

---

## 📊 Resultados de Verificación

| Verificación | Estado | Detalles |
|--------------|--------|----------|
| Conteo de Registros | ✅ | 9/9 tablas coinciden |
| Esquema y Tipos | ✅ | 51 columnas verificadas |
| Integridad Referencial | ✅ | 8 FKs sin huérfanos |
| Valores Nulos | ⚠️ | 5 registros (0.03%) con NULLs en FKs |
| Primary Keys | ✅ | 9 PKs sin duplicados |
| Agregaciones | ✅ | Valores coinciden exactamente |

---

## ⚠️ Hallazgos

### Valores Nulos en Foreign Keys (5 registros)

**Problema:** 5 registros en `F_Proceso` tienen NULL en `entidad_id`, `proveedor_id` y `tiempo_id`.

**Registros afectados:**
- CO1.REQ.8856229
- CO1.REQ.8831315
- CO1.REQ.8867366
- CO1.REQ.8802128
- CO1.REQ.8850315

**Causa probable:** Estos registros no tienen entidad, proveedor o fecha de publicación válidos en los datos fuente del SECOP.

**Impacto:** Mínimo (0.03% del total). Estos registros no se podrán unir con las tablas de dimensión en consultas analíticas.

**Recomendación:**
- Opción A: Excluir estos registros en el ETL si no son críticos
- Opción B: Investigar los datos originales del SECOP para estos IDs de proceso

---

## 🔧 Solución de Problemas

### Error: "No module named 'duckdb'"
```bash
pip install duckdb
```

### Error: "database is locked"
- Cierre cualquier conexión abierta a las bases de datos
- Reinicie el kernel de Jupyter si está usando notebooks

### Error: "table does not exist"
- Ejecute primero el ETL: `python load_star_model.py`
- Luego ejecute la migración: `python verify_migration.py`

---

## 📝 Recomendaciones

1. **Backup:** Mantenga siempre una copia de la base SQLite original
2. **Verificación continua:** Ejecute este script después de cada actualización de datos
3. **Calidad de datos:** Investigar los 5 registros con NULLs si son críticos para el análisis
4. **Automatización:** Considere ejecutar la verificación en un pipeline CI/CD

---

## 📄 Licencia

MIT - Proyecto de Consultoría Universidad Santo Tomás

---

*Última actualización: Marzo 2026*
*Generado automáticamente por verify_migration.py*
