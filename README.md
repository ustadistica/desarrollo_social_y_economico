# Sinergia Socioeconómica - Plataforma Analítica (Medallion Architecture)

Repositorio para el análisis de Sinergia Socioeconómica, Gasto Público (SECOP) y Micronegocios (EMICRON). Pipeline ETL bajo **Arquitectura Medallion (Bronze → Silver → Gold)** con DuckDB y PyArrow.

## Arquitectura

1. **BRONZE** (`datos/bronze/`): Ingesta cruda a Parquet con hash y timestamp.
2. **SILVER** (`datos/plata/`): Estandarización DIVIPOLA, agregación a grano `Municipio-Año`.
3. **GOLD** (`datos/oro/`): Modelo estrella (dimensiones + hechos) y Datamart OBT.

## Output Final para Analistas

No es necesario re-ejecutar el pipeline. El resultado consumible está en:

```
datos/oro/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet
```

Los reportes de calidad están en `documentacion_tecnica/`.

---

## 🚀 Instalación Rápida

### Para Nuevos Compañeros

⭐ **Lee primero:** [`INSTALACION_COMPAÑEROS.md`](INSTALACION_COMPAÑEROS.md)

Esta guía te explica:
1. Cómo clonar el repo
2. **DÓNDE colocar la carpeta "Datos"** (problema común)
3. Cómo verificar la configuración
4. Cómo ejecutar el pipeline completo

### Paso a Paso

```bash
# 1. Clonar el repositorio
git clone <url> && cd desarrollo_social_y_economico

# 2. Crear entorno virtual (recomendado)
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate  # Mac/Linux

# 3. Instalar el paquete
pip install -e .

# 4. Verificar que la carpeta "Datos" esté en el lugar correcto
python -m src.validadores.verificar_datos

# 5. Configurar datos externos (opcional, solo si "Datos" está en otro lado)
cp .env.example .env
# Editar .env con tus rutas locales (ver SETUP_DATOS.md)
```

### ⚠️ Problema Común: "Carpeta Datos no encontrada"

La carpeta "Datos" debe estar en:
```
CONSULTORIA/
├── Datos/                           ← AQUÍ (al lado de CONSULTORIA)
└── Desarrollo social y economico/
    └── desarrollo_social_y_economico/
```

**NO** en:
- ❌ `desarrollo_social_y_economico/Datos/`
- ❌ `Octavo/Datos/`
- ❌ `~/Descargas/Datos/`

Ver [`SETUP_DATOS.md`](SETUP_DATOS.md) para detalles.

## Ejecución del Pipeline (Flujo Oficial)

```bash
# Pipeline completo (Bronze → Silver → Gold)
socioeco-pipeline

# Capas individuales
socioeco-bronze
socioeco-silver
socioeco-gold

# Alternativa via módulo Python
python -m src.cli all
python -m src.cli bronze
python -m src.cli silver
python -m src.cli gold
```

> **Nota:** También puedes ejecutar el orquestador principal mediante `python src/main.py`.

## Dependencias

Gestionadas en `pyproject.toml`. Instalación con `pip install -e .`. No se usa Poetry.

## Documentación Técnica

| Documento | Contenido |
|-----------|-----------|
| `INSTALACION_LIMPIA.md` | Guía detallada de instalación paso a paso |
| `CLI_USAGE.md` | Referencia completa de comandos del CLI |
| `IMPORT_CONVENTION.md` | Convención de imports del proyecto |
| `pipeline/INSTRUCCIONES_EQUIPO.md` | Guía de configuración de datos para el equipo |
| `documentacion_tecnica/DICCIONARIO_GOLD.md` | Diccionario de variables del modelo Gold |
