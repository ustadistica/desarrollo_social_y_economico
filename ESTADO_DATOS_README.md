# Estado del Proyecto - Datos Observatorio de Desarrollo Socioeconómico

**Fecha:** 20 de marzo de 2026  
**Versión:** 1.0

---

## 📊 Resumen Ejecutivo

### Estado de las 6 Bases de Datos Requeridas

| # | Base de Datos | Estado | Registros | Observación |
|---|---------------|--------|-----------|-------------|
| 1 | **SECOP II** | ✅ COMPLETO | 19,188 | Datos reales disponibles |
| 2 | **CNPV (DANE)** | ⚠️ MOCK | 5 | Solo datos de prueba |
| 3 | **CENU (DANE)** | ⚠️ MOCK | 5 | Solo datos de prueba |
| 4 | **IPM (DANE)** | ❌ FALTANTE | 0 | Requiere descarga manual |
| 5 | **NBI (DANE)** | ❌ FALTANTE | 0 | Requiere descarga manual |
| 6 | **EMICRON (DANE)** | ❌ FALTANTE | 0 | Requiere descarga manual |

---

## 🔍 Análisis Detallado

### 1. ✅ SECOP II - Contratación Pública (COMPLETO)

**Ubicación:**  
`datos/bronze/secop_ii/ingestion_date=2026-03-20/secop_data.parquet`

**Características:**
- 19,188 registros reales
- 58-59 columnas
- Fuente: datos.gov.co (API SODA)
- Vigencia: Última disponible

**Columnas principales:**
- `entidad`, `nit_entidad`, `departamento_entidad`, `ciudad_entidad`
- `id_del_proceso`, `referencia_del_proceso`
- `nombre_del_procedimiento`, `descripcion_del_procedimiento`
- `fase`, `fecha_de_publicacion`, `precio_base`
- `modalidad_de_contratacion`, `proveedores_invitados`

**Acción:** ✅ Ninguna requerida - Datos listos para uso

---

### 2. ⚠️ CNPV (DANE) - Datos Mock

**Ubicación:**  
`datos/bronze/dane_cnpv/ingestion_date=2026-03-20/cnpv_data.parquet`

**Problema:**
- Solo 5 registros (municipios de ejemplo)
- Fuente: "Mock Server" (datos de prueba)
- No son datos reales del DANE

**Columnas disponibles (esquema correcto):**
- `municipio`, `divipola_municipio`
- `ipm`, `nbi`, `poblacion`
- `pobreza_monetaria`, `deficit_habitacional_cuantitativo`
- `anio`, `_ingestion_timestamp`, `_source`

**Acción requerida:** 📥 Descargar datos reales (ver instrucciones abajo)

---

### 3. ⚠️ CENU (DANE) - Datos Mock

**Ubicación:**  
`datos/bronze/dane_cenu/ingestion_date=2026-03-20/cenu_data.parquet`

**Problema:**
- Solo 5 registros (municipios de ejemplo)
- Fuente: "Mock Server" (datos de prueba)

**Columnas disponibles (esquema correcto):**
- `municipio`, `divipola_municipio`
- `total_micronegocios`, `economia_popular_unidades`
- `codigo_ciiu`, `anio`

**Acción requerida:** 📥 Descargar datos reales

---

### 4-6. ❌ IPM, NBI, EMICRON - No Encontrados

Estas tres bases de datos **NO existen** como archivos independientes en el proyecto.

**Nota:** Los campos `ipm` y `nbi` existen como columnas dentro de CNPV (mock), y `total_micronegocios` existe en CENU (mock), pero son datos de prueba.

**Acción requerida:** 📥 Descargar desde portales oficiales

---

## 📥 Instrucciones de Descarga

### Opción A: Descarga Manual (RECOMENDADA)

#### Paso 1: Crear carpetas de destino

```bash
cd "c:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\desarrolo eco\desarrollo_social_y_economico-main (2)\desarrollo_social_y_economico-main\datos\bronze"

mkdir dane_cnpv\raw
mkdir dane_ipm\raw
mkdir dane_nbi\raw
mkdir dane_emicron\raw
mkdir dane_cenu\raw
```

#### Paso 2: Descargar archivos desde los portales

**1. CNPV / IPM / NBI:**

URL: https://www.datos.gov.co/

Buscar:
- "Índice de Pobreza Multidimensional IPM municipal DANE"
- "Necesidades Básicas Insatisfechas NBI municipal"
- "Censo Nacional Población Vivienda 2018 indicadores"

**2. EMICRON / CENU:**

URL: https://www.dane.gov.co/

Ruta:
- Estadísticas → Empresas → EMICRON/CENU
- O buscar: "Encuesta de Micronegocios DANE"

**3. Alternativa - Microdatos DANE (registro requerido):**

URL: https://microdatos.dane.gov.co/
- Crear cuenta gratuita
- Solicitar acceso a microdatos
- Descargar en formato CSV o Excel

#### Paso 3: Guardar archivos

Guardar los archivos descargados en las carpetas `raw` creadas:

```
datos/bronze/dane_cnpv/raw/cnpv_2018.xlsx
datos/bronze/dane_ipm/raw/ipm_municipal.xlsx
datos/bronze/dane_nbi/raw/nbi_municipal.xlsx
datos/bronze/dane_emicron/raw/emicron_2024.xlsx
datos/bronze/dane_cenu/raw/cenu_2024.xlsx
```

#### Paso 4: Ejecutar script de procesamiento

```bash
cd "c:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\desarrolo eco\desarrollo_social_y_economico-main (2)"

.venv\Scripts\python.exe "desarrollo_social_y_economico-main\ingesta y validacion\extract\process_manual_downloads.py"
```

---

### Opción B: Intentar Descarga vía API (AVANZADA)

Los scripts de descarga automática están creados pero la API de datos.gov.co está retornando error 403 (Forbidden).

**Scripts disponibles:**
- `download_dane_massive.py` - Descarga masiva vía API SODA

**Ejecutar:**
```bash
cd "c:\Users\user\Documents\001 Uni\Octavo\CONSULTORIA\desarrolo eco\desarrollo_social_y_economico-main (2)\desarrollo_social_y_economico-main"

.venv\Scripts\python.exe "ingesta y validacion\extract\download_dane_massive.py" --force
```

**Problema actual:** Error 403 - Requiere autenticación OAuth2 o los IDs de dataset no son públicos.

---

## 🗂️ Estructura de Archivos del Proyecto

```
desarrollo_social_y_economico-main/
├── datos/
│   ├── bronze/
│   │   ├── secop_ii/              ✅ COMPLETO (19,188 registros)
│   │   │   └── ingestion_date=2026-03-20/
│   │   │       └── secop_data.parquet
│   │   ├── dane_cnpv/             ⚠️ MOCK (5 registros)
│   │   │   └── ingestion_date=2026-03-20/
│   │   │       └── cnpv_data.parquet
│   │   ├── dane_cenu/             ⚠️ MOCK (5 registros)
│   │   │   └── ingestion_date=2026-03-20/
│   │   │       └── cenu_data.parquet
│   │   ├── dane_ipm/              ❌ VACÍO
│   │   ├── dane_nbi/              ❌ VACÍO
│   │   └── dane_emicron/          ❌ VACÍO
│   ├── plata/                     ✅ DATOS DERIVADOS (demo)
│   └── oro/                       ✅ DATAMARTS (demo)
├── ingesta y validacion/
│   ├── extract/
│   │   ├── extract_secop_ii.py    ✅ FUNCIONANDO
│   │   ├── extract_dane_cnpv.py   ⚠️ REQUIERE API REAL
│   │   ├── extract_dane_cenu.py   ⚠️ REQUIERE API REAL
│   │   ├── download_dane_massive.py  🆕 DESCARGA MASIVA
│   │   └── process_manual_downloads.py  🆕 PROCESA MANUALES
│   └── config/
│       ├── settings.py            ✅ ACTUALIZADO CON API KEY
│       └── vigencia_config.py     ✅ CONFIGURADO
└── ...
```

---

## 📋 Próximos Pasos

### Inmediatos (Esta Semana)

- [ ] **Descargar CNPV real** desde datos.gov.co o microdatos.dane.gov.co
- [ ] **Descargar IPM** como base independiente
- [ ] **Descargar NBI** como base independiente
- [ ] **Descargar EMICRON/CENU** completo
- [ ] **Ejecutar process_manual_downloads.py**

### Corto Plazo (2 Semanas)

- [ ] Validar calidad de datos descargados
- [ ] Re-ejecutar pipeline ETL completo
- [ ] Verificar que las capas Plata y Oro se actualicen con datos reales
- [ ] Generar reportes de calidad

### Mediano Plazo (1 Mes)

- [ ] Configurar actualización automática mensual (SECOP II)
- [ ] Configurar actualización trimestral (CENU/EMICRON)
- [ ] Documentar procesos de mantenimiento

---

## 🔧 Scripts Disponibles

### Para Descarga y Procesamiento

| Script | Función | Estado |
|--------|---------|--------|
| `extract_secop_ii.py` | Descarga SECOP II vía API | ✅ Funcionando |
| `download_dane_massive.py` | Descarga masiva DANE | ⚠️ Error 403 |
| `process_manual_downloads.py` | Procesa descargas manuales | ✅ Listo |
| `extract_dane_cnpv.py` | Descarga CNPV vía API | ⚠️ Error 403 |
| `extract_dane_cenu.py` | Descarga CENU vía API | ⚠️ Error 403 |

### Para Ejecución del Pipeline

```bash
# Ejecutar pipeline completo (usando datos existentes)
python -m "ingesta y validacion.orchestrator" --skip-extraction

# Forzar re-ejecución completa
python -m "ingesta y validacion.orchestrator" --force-update

# Solo extracción SECOP II (actualización mensual)
python -m "ingesta y validacion.orchestrator" --fuentes secop_ii
```

---

## 📞 URLs Oficiales de Descarga

### Portales Principales

1. **datos.gov.co** - Portal Nacional de Datos Abiertos
   - https://www.datos.gov.co/

2. **DANE** - Departamento Administrativo Nacional de Estadística
   - https://www.dane.gov.co/

3. **Microdatos DANE** (registro requerido)
   - https://microdatos.dane.gov.co/

4. **Colombia Compra Eficiente** (SECOP II directo)
   - https://www.colombiacompra.gov.co/

### Búsquedas Recomendadas

En datos.gov.co buscar:
- "IPM municipal DANE"
- "NBI municipio DANE"
- "Pobreza Multidimensional Colombia"
- "EMICRON micronegocios"
- "CENU censo económico"

---

## 📊 Metadatos de las Bases

### CNPV 2018
- **Vigencia:** 2018 (con proyecciones 2024-2025)
- **Unidad:** Municipio
- **Llave geográfica:** DIVIPOLA (5 dígitos)
- **Indicadores:** IPM, NBI, Población, Pobreza Monetaria

### CENU / EMICRON
- **Vigencia:** 2024 (más reciente)
- **Unidad:** Municipio + Sector CIIU
- **Llave geográfica:** DIVIPOLA
- **Indicadores:** Micronegocios, Economía Popular, Formalidad

### SECOP II
- **Vigencia:** Continua (actualización mensual)
- **Unidad:** Contrato público
- **Llave geográfica:** DIVIPOLA municipio
- **Indicadores:** Montos, Proveedores, Modalidad

---

## ⚠️ Consideraciones Importantes

### Secreto Estadístico

- Los microdatos individuales del DANE tienen secreto estadístico por ley
- **NO** se puede cruzar NIT de proveedores (SECOP) con microdatos del DANE
- **SÍ** se puede usar DIVIPOLA para análisis agregado por municipio

### Vigencia de Datos

- **CNPV:** Censal (una vez cada ~10 años). Última: 2018
- **CENU/EMICRON:** Trimestral
- **SECOP II:** Mensual (continua)
- **IPM/NBI:** Anual (derivado de CNPV)

### Calidad de Datos

Verificar siempre:
1. Completitud de DIVIPOLA (5 dígitos)
2. Consistencia temporal (vigencia)
3. Cobertura municipal (todos los 1,102 municipios)

---

## 📝 Contacto y Soporte

### Para problemas con descargas:

- **datos.gov.co:** soporte@datos.gov.co
- **DANE:** https://www.dane.gov.co/index.php/contactenos
- **Microdatos DANE:** microdatos@dane.gov.co

### Documentación del Proyecto:

- Ver `GUÍA_DESCARGA_DATOS_DANE.txt` para instrucciones detalladas
- Ver `INFORME_ESTADO_DATOS.txt` para análisis completo

---

**Última actualización:** 20 de marzo de 2026  
**Próxima revisión:** 27 de marzo de 2026
