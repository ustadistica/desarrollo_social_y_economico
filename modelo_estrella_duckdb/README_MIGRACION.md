# Migración SQLite → DuckDB: Modelo Estrella SECOP

## 📋 Resumen del Proyecto

Este documento describe el proceso completo de **migración del modelo estrella SECOP** desde SQLite hacia DuckDB, incluyendo la **verificación exhaustiva de integridad de datos** para garantizar que la migración se realizó sin errores.

---

## 🎯 Objetivo

Migrar el modelo dimensional (modelo estrella) de la base de datos de contratación pública SECOP desde **SQLite** hacia **DuckDB**, aprovechando las capacidades analíticas de DuckDB para consultas OLAP más rápidas, manteniendo la integridad completa de los datos.

---

## 📊 Volumen de Datos Migrados

| Tabla | Tipo | Registros | Tamaño Aproximado |
|-------|------|-----------|-------------------|
| `F_Proceso` | Hechos | 19,000 | ~2.5 MB |
| `D_Entidad` | Dimensión | 2,941 | ~200 KB |
| `D_Proveedor` | Dimensión | 6,421 | ~400 KB |
| `D_UbiEntidad` | Dimensión | 801 | ~50 KB |
| `D_UbiProveedor` | Dimensión | 608 | ~40 KB |
| `D_Categoria` | Dimensión | 2,083 | ~150 KB |
| `D_Modalidad` | Dimensión | 15 | ~2 KB |
| `D_TipoContrato` | Dimensión | 19 | ~2 KB |
| `D_Tiempo` | Dimensión | 4 | <1 KB |
| **TOTAL** | | **31,892** | **~3.3 MB** |

---

## 🏗️ Arquitectura del Modelo Estrella

```
                         ┌─────────────────┐
                         │   F_Proceso     │
                         │   (Hechos)      │
                         │  19,000 regs    │
                         └────────┬────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│D_Entidad  │ │D_Proveedor│ │ D_Tiempo  │ │D_UbiEnt.  │ │D_UbiProv. │
│  2,941    │ │  6,421    │ │    4      │ │   801     │ │   608     │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘

        │            │            │            │            │
        ▼            ▼            ▼            ▼            ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│D_Categoria│ │D_Modalidad│ │D_TipoCont.│
│  2,083    │ │    15     │ │    19     │
└───────────┘ └───────────┘ └───────────┘
```

### Foreign Keys (8 relaciones)

```sql
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

## 🔄 Proceso de Migración

### Flujo Completo

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Datos     │     │  ETL        │     │  SQLite     │     │  DuckDB     │
│  Parquet   │ ──► │  (carga)    │ ──► │  (origen)   │ ──► │  (destino)  │
│  (SECOP)   │     │             │     │             │     │             │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                   │                   │
                           │                   │                   │
                           ▼                   ▼                   ▼
                    load_star_model.py   Proyect_SECOP.db   Proyect_SECOP.duckdb
```

### Paso 1: Carga de Datos (ETL)

**Script:** `load_star_model.py`

Este script realiza las siguientes operaciones:

1. **Lectura de datos fuente:** Carga los archivos Parquet (`secop_nuevos1.parquet`, `secop_cambiados1.parquet`)
2. **Limpieza:** Elimina duplicados por `id_del_proceso`
3. **Transformación dimensional:**
   - Extrae dimensiones únicas (entidades, proveedores, ubicaciones, etc.)
   - Genera IDs secuenciales para cada dimensión
   - Crea la tabla de hechos con las foreign keys mapeadas
4. **Carga:** Guarda las 9 tablas en SQLite

**Ejecución:**
```bash
python load_star_model.py
```

### Paso 2: Migración y Verificación

**Script:** `verify_migration.py`

Este script realiza:

1. **Migración:** Copia todas las tablas de SQLite a DuckDB
2. **6 verificaciones de integridad:**
   - Conteo de registros
   - Esquema y tipos de datos
   - Integridad referencial (foreign keys)
   - Valores nulos críticos
   - Unicidad de primary keys
   - Agregaciones y sumas de control

**Ejecución:**
```bash
python verify_migration.py
```

---

## ✅ Resultados de la Verificación

### Resumen

| Verificación | Estado | Detalles |
|--------------|--------|----------|
| 1. Conteo de Registros | ✅ **PASS** | 9/9 tablas coinciden exactamente |
| 2. Esquema y Tipos | ✅ **PASS** | 51 columnas verificadas |
| 3. Integridad Referencial | ✅ **PASS** | 8 FKs sin huérfanos |
| 4. Valores Nulos | ⚠️ **WARN** | 5 registros (0.03%) con NULLs |
| 5. Primary Keys | ✅ **PASS** | 9 PKs sin duplicados |
| 6. Agregaciones | ✅ **PASS** | Sumas coinciden exactamente |

**Calificación:** 5/6 pruebas pasaron (99.97% integridad)

### Detalle de Verificaciones

#### 1. Conteo de Registros ✅

```
Tabla              SQLite      DuckDB     Estado
--------------------------------------------------
D_Entidad           2,941       2,941     ✓
D_Proveedor         6,421       6,421     ✓
D_Tiempo                4           4     ✓
D_UbiEntidad          801         801     ✓
D_UbiProveedor        608         608     ✓
D_Categoria         2,083       2,083     ✓
D_Modalidad            15          15     ✓
D_TipoContrato         19          19     ✓
F_Proceso          19,000      19,000     ✓
```

#### 2. Esquema y Tipos de Datos ✅

Todas las 51 columnas en las 9 tablas fueron verificadas con tipos compatibles:

| Tipo SQLite | Tipo DuckDB | Estado |
|-------------|-------------|--------|
| INTEGER | BIGINT/INTEGER | ✓ |
| TEXT | VARCHAR/TEXT | ✓ |
| REAL | DOUBLE | ✓ |
| DATE | DATE | ✓ |

#### 3. Integridad Referencial ✅

Las 8 foreign keys fueron validadas sin registros huérfanos:

```
FK                                      Huérfanos    Estado
------------------------------------------------------------
F_Proceso.entidad_id → D_Entidad              0      ✓
F_Proceso.proveedor_id → D_Proveedor          0      ✓
F_Proceso.tiempo_id → D_Tiempo                0      ✓
F_Proceso.ubi_entidad_id → D_UbiEntidad       0      ✓
F_Proceso.ubi_proveedor_id → D_UbiProveedor   0      ✓
F_Proceso.categoria_id → D_Categoria          0      ✓
F_Proceso.modalidad_id → D_Modalidad          0      ✓
F_Proceso.tipo_contrato_id → D_TipoContrato   0      ✓
```

#### 4. Valores Nulos Críticos ⚠️

```
Columna                        NULLs    Estado
----------------------------------------------
D_Entidad.entidad_id               0    ✓
D_Proveedor.proveedor_id           0    ✓
D_Tiempo.tiempo_id                 0    ✓
F_Proceso.id_del_proceso           0    ✓
F_Proceso.entidad_id               5    ⚠️
F_Proceso.proveedor_id             5    ⚠️
F_Proceso.tiempo_id                5    ⚠️
```

**Análisis:** Los 5 registros con NULLs corresponden a procesos del SECOP que no tienen entidad, proveedor o fecha válidos en los datos originales. Esto representa el 0.03% del total (5 de 19,000).

**Registros afectados:**
- CO1.REQ.8856229
- CO1.REQ.8831315
- CO1.REQ.8867366
- CO1.REQ.8802128
- CO1.REQ.8850315

#### 5. Unicidad de Primary Keys ✅

```
Tabla.Columna               Duplicados    Estado
------------------------------------------------
D_Entidad.entidad_id               0      ✓
D_Proveedor.proveedor_id           0      ✓
D_Tiempo.tiempo_id                 0      ✓
D_UbiEntidad.ubi_entidad_id        0      ✓
D_UbiProveedor.ubi_proveedor_id    0      ✓
D_Categoria.categoria_id           0      ✓
D_Modalidad.modalidad_id           0      ✓
D_TipoContrato.tipo_contrato_id    0      ✓
F_Proceso.id_del_proceso           0      ✓
```

#### 6. Agregaciones y Sumas de Control ✅

```
Columna                        SQLite            DuckDB            Estado
------------------------------------------------------------------------
F_Proceso.precio_base     3,352,378,654,419   3,352,378,654,419    ✓
F_Proceso.valor_total        30,933,903,676      30,933,903,676    ✓
F_Proceso.numero_de_lotes             468                 468    ✓
```

---

## 📁 Estructura de Archivos

```
desarrollo_social_y_economico-main/
│
├── modelo_estrella_sqlite/
│   └── Proyect_SECOP.db          # Base de datos SQLite (origen)
│
├── modelo_estrella_duckdb/
│   ├── Proyect_SECOP.duckdb      # Base de datos DuckDB (destino)
│   └── README_VERIFICACION.md    # Documentación de verificación
│
├── datos/
│   ├── secop_nuevos1.parquet     # Datos fuente SECOP
│   └── secop_cambiados1.parquet  # Datos actualizados SECOP
│
├── load_star_model.py            # Script ETL (Parquet → SQLite)
├── verify_migration.py           # Migración + Verificación
├── pyproject.toml                # Dependencias (incluye duckdb)
└── README.md                     # README principal actualizado
```

---

## 🛠️ Requisitos Técnicos

### Dependencias

```toml
[tool.poetry.dependencies]
python = "3.12.*"
pandas = "^2.2.2"
duckdb = "^1.0.0"
pyarrow = "^23.0.0"
```

### Instalación

```bash
# Instalar dependencias
pip install duckdb pandas pyarrow

# O con Poetry
python -m poetry install
```

---

## 🚀 Guía de Uso

### Paso 1: Cargar Datos (si es necesario)

Si actualiza los archivos Parquet en la carpeta `datos/`, ejecute:

```bash
python load_star_model.py
```

**Salida esperada:**
```
ETL: Carga de Datos SECOP al Modelo Estrella
============================================================

=== CARGANDO DATOS PARQUET ===
  secop_nuevos1.parquet: 19,188 registros
  secop_cambiados1.parquet: 76 registros
  TOTAL: 19,264 registros
  Despues de eliminar duplicados: 19,000 registros

=== CREANDO TABLAS DE DIMENSION ===
  D_Tiempo: 4 registros
  D_Entidad: 2,941 registros
  ...

ETL COMPLETADO EXITOSAMENTE
```

### Paso 2: Migrar y Verificar

```bash
python verify_migration.py
```

**Salida esperada:**
```
MIGRACION Y VERIFICACION: SQLite -> DuckDB
============================================================

INSPECCION DE BASE DE DATOS SQLite
  D_Entidad: 2,941 registros
  D_Proveedor: 6,421 registros
  ...

MIGRACION: SQLite -> DuckDB
  D_Entidad: 2,941 registros migrados
  ...

VERIFICACION 1: CONTEO DE REGISTROS
  [OK] Todas las tablas coinciden

VERIFICACION 2: ESQUEMA Y TIPOS DE DATOS
  [OK] Esquemas coinciden

...

Total: 6/6 verificaciones pasaron
¡MIGRACION Y VERIFICACION COMPLETADAS EXITOSAMENTE!
```

---

## 📈 Beneficios de la Migración a DuckDB

| Característica | SQLite | DuckDB |
|----------------|--------|--------|
| **Propósito** | Base de datos transaccional | Base de datos analítica (OLAP) |
| **Consultas columnares** | No | ✅ Sí |
| **Parquet nativo** | No | ✅ Sí |
| **Consultas complejas** | Lento | ✅ Rápido |
| **Agregaciones** | Regular | ✅ Optimizado |
| **Integración Python** | Buena | ✅ Excelente |

### Ejemplo de Consulta en DuckDB

```python
import duckdb

conn = duckdb.connect('modelo_estrella_duckdb/Proyect_SECOP.duckdb')

# Consulta analítica compleja
query = """
SELECT
    e.departamento_entidad,
    COUNT(f.id_del_proceso) as total_procesos,
    SUM(f.valor_total_adjudicacion) as valor_total
FROM F_Proceso f
JOIN D_Entidad e ON f.entidad_id = e.entidad_id
JOIN D_Tiempo t ON f.tiempo_id = t.tiempo_id
WHERE t.año = 2024
GROUP BY e.departamento_entidad
ORDER BY valor_total DESC
"""

resultado = conn.execute(query).fetchdf()
print(resultado)
```

---

## ⚠️ Consideraciones y Limitaciones

### Valores Nulos en Foreign Keys

**Problema:** 5 registros (0.03%) tienen NULLs en `entidad_id`, `proveedor_id`, y `tiempo_id`.

**Causa:** Los datos originales del SECOP para estos procesos no tienen entidad, proveedor o fecha de publicación válidos.

**Impacto:** Estos registros no se podrán unir con las tablas de dimensión en consultas analíticas.

**Soluciones posibles:**
1. **Excluir en consultas:** Usar `WHERE entidad_id IS NOT NULL`
2. **Investigar origen:** Revisar los datos crudos del SECOP para estos IDs
3. **Aceptar como límite:** El impacto es mínimo (0.03%)

### Fechas en D_Tiempo

La tabla `D_Tiempo` solo tiene 4 registros porque los datos Parquet cargados cubren un rango limitado de fechas. Para un modelo completo, se recomienda:

1. Cargar más datos históricos del SECOP
2. Ejecutar nuevamente `load_star_model.py`
3. Verificar con `verify_migration.py`

---

## 📊 Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| Integridad de Registros | 100% | ✅ |
| Integridad de Esquema | 100% | ✅ |
| Integridad Referencial | 100% | ✅ |
| Primary Keys Únicas | 100% | ✅ |
| Integridad de Agregaciones | 100% | ✅ |
| Valores Nulos Críticos | 99.97% | ⚠️ |
| **CALIDAD TOTAL** | **99.97%** | ✅ |

---

## 📝 Recomendaciones

1. **Backup:** Mantener copia de seguridad de `Proyect_SECOP.db` (SQLite)
2. **Verificación continua:** Ejecutar `verify_migration.py` después de cada actualización
3. **Monitoreo:** Registrar cualquier discrepancia encontrada
4. **Automatización:** Integrar la verificación en un pipeline CI/CD
5. **Documentación:** Actualizar este README con cambios futuros

---

## 👥 Autores

**Consultorio de Estadística y Ciencia de Datos**
Universidad Santo Tomás

- Angela Orjuela Guevara
- Ingrid Umbacia Ramirez
- Andres Perez Moreno
- Alejandra Benedetti Castro
- Diego Gomez Cortes
- Maria Jose Galindo Piraban

---

## 📄 Licencia

MIT License - Proyecto de Consultoría Universidad Santo Tomás

---

*Fecha de última actualización: Marzo 2026*

*Versión del documento: 1.0*
