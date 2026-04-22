# Guía de Configuración: Censo Nacional de Población y Vivienda (CNPV) 2018

**Fecha:** 2026-04-21

La integración analítica del Censo 2018 requiere que cada miembro del equipo apunte el pipeline a su copia local de los microdatos. Debido al gran tamaño del dataset (y a sus decenas de subcarpetas), este no se versiona en GitHub.

## Estructura Esperada de la Carpeta

El pipeline es flexible e inspecciona automáticamente la carpeta raíz en busca de subcarpetas departamentales y archivos CSV. La estructura típica entregada en disco duro o descargada debe lucir así:

```text
CENSO 2018 dep/
├── 05_Antioquia_CSV/
│   ├── CNPV2018_1VIV_A2_05.CSV
│   ├── CNPV2018_2HOG_A2_05.CSV
│   ├── CNPV2018_3FALL_A2_05.CSV
│   ├── CNPV2018_5PER_A2_05.CSV
│   └── CNPV2018_MGN_A2_05.CSV
├── 08_Atlantico_CSV/
│   └── ...
└── 11_Bogota_CSV/
    └── ...
```

## Configuración del Entorno Local (.env)

Debes indicarle al código dónde vive esta carpeta raíz mediante la variable `CNPV_ROOT_DIR`.

**Pasos a seguir:**

1. Copia el archivo `pipeline/.env.example` y renómbralo a `pipeline/.env`.
2. Edita la variable `CNPV_ROOT_DIR` colocando la ruta absoluta a la carpeta descomprimida. 

**Ejemplo en Windows:**
```env
CNPV_ROOT_DIR="C:\Users\TuNombre\Downloads\Datos\CENSO 2018 dep"
```

**Ejemplo en Mac/Linux:**
```env
CNPV_ROOT_DIR="/Users/tunombre/Data/CENSO 2018 dep"
```

> **Nota:** Si todos en el equipo mantienen la convención de guardar la carpeta de datos en `../Datos/CENSO 2018 dep` relativa a la raíz del repositorio, el pipeline la autodetectará sin necesidad de configurar el `.env`.

## Ejecución

Una vez configurado, ejecuta el pipeline completo o solo la capa Silver para ingerir y agregar el censo:

```bash
# Ingesta completa (procesa todos los CSV multicarpeta a formato Parquet Bronze)
python -m pipeline bronze --source cnpv

# Agregación analítica Silver
python -m pipeline silver
```

El pipeline generará automáticamente el archivo `silver_cnpv_agregado.parquet` utilizando exclusivamente el módulo poblacional de personas (`5PER`).
