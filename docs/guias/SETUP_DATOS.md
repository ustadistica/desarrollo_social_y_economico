# 📦 Configuración de Datos - Guía Completa

## Estructura de Carpetas Esperada

El pipeline espera que la carpeta `Datos` esté **al mismo nivel que la carpeta del proyecto**, NO dentro del proyecto.

### ✅ Estructura Correcta

```
Octavo/
├── CONSULTORIA/
│   ├── Datos/                          ← AQUÍ debe estar la carpeta Datos
│   │   ├── CENSO 2018 dep/
│   │   ├── EMICRON 2019/
│   │   ├── EMICRON 2020/
│   │   ├── ...
│   │   ├── EMICRON 2024/
│   │   ├── SECOP_I_-_Procesos_de_Compra_Pública_20260412.csv
│   │   ├── SECOP_II_-_Contratos_Electrónicos_20260412.csv
│   │   └── PPED-AreaDep-2018-2050_VP.csv
│   │
│   └── Desarrollo social y economico/
│       └── desarrollo_social_y_economico/   ← El repositorio clonado
│           ├── src/
│           ├── data/
│           ├── README.md
│           └── ...
```

### ❌ Estructura Incorrecta

```
# INCORRECTO #1: Datos dentro del proyecto
desarrollo_social_y_economico/
└── Datos/  ← ❌ NO AQUÍ

# INCORRECTO #2: Datos en otro nivel
Octavo/
└── Datos/  ← ❌ Aquí NO funciona

# INCORRECTO #3: Datos en Downloads
~/Downloads/
└── Datos/  ← ❌ Fuera de la estructura del proyecto
```

---

## 🔧 Solución Rápida

### Opción 1: Estructura de Carpetas Correcta (Recomendado)

1. Asegúrate que tu estructura sea:
   ```
   Octavo/
   ├── CONSULTORIA/
   │   ├── Datos/              ← Carpeta con todos los CSVs
   │   └── Desarrollo social y economico/
   │       └── desarrollo_social_y_economico/
   ```

2. Verifica que la carpeta `Datos` contenga:
   ```bash
   ls CONSULTORIA/Datos/
   # Debe mostrar:
   # CENSO 2018 dep/
   # EMICRON 2019/, EMICRON 2020/, ..., EMICRON 2024/
   # SECOP_I_-_Procesos_de_Compra_Pública_*.csv
   # SECOP_II_-_Contratos_Electrónicos_*.csv
   # PPED-AreaDep-2018-2050_VP.csv
   ```

3. Ejecuta el pipeline:
   ```bash
   cd CONSULTORIA/Desarrollo\ social\ y\ economico/desarrollo_social_y_economico
   python src/ingesta/run_bronze.py
   ```

### Opción 2: Usar Variables de Entorno (.env)

Si **no puedes** poner la carpeta `Datos` al mismo nivel que CONSULTORIA, usa archivo `.env`:

1. Copia el archivo de configuración:
   ```bash
   cp .env.example .env
   ```

2. Edita `.env` con tus rutas reales:
   ```env
   CNPV_ROOT_DIR="/path/to/CENSO 2018 dep"
   SECOP_I_CSV_PATH="/path/to/SECOP_I_-_Procesos_de_Compra_Pública_20260412.csv"
   SECOP_CSV_PATH="/path/to/SECOP_II_-_Contratos_Electrónicos_20260412.csv"
   EMICRON_CSV_PATH="/path/to/carpeta/que/contiene/EMICRON/"
   PROYECCIONES_CENSO_PATH="/path/to/PPED-AreaDep-2018-2050_VP.csv"
   ```

3. Ejemplos de rutas válidas:
   ```env
   # Windows
   CNPV_ROOT_DIR="C:\Users\TuNombre\Descargas\CENSO 2018 dep"
   SECOP_I_CSV_PATH="C:\Users\TuNombre\Descargas\SECOP_I_-_Procesos_de_Compra_Pública_20260412.csv"
   
   # Mac/Linux
   CNPV_ROOT_DIR="/Users/tunombre/Descargas/CENSO 2018 dep"
   SECOP_I_CSV_PATH="/Users/tunombre/Descargas/SECOP_I_-_Procesos_de_Compra_Pública_20260412.csv"
   ```

---

## ✔️ Verificar que todo está correcto

Ejecuta el validador de datos:

```bash
python -m src.validadores.verificar_datos
```

Este script te dirá:
- ✅ Si encuentra la carpeta `Datos`
- ✅ Si encuentra cada subcarpeta/archivo
- ❌ Si falta algo, te indicará dónde debe estar

---

## 📊 Contenido de Cada Carpeta

### CENSO 2018 dep/
```
CENSO 2018 dep/
├── 05_ANTIOQUIA.csv       (33 archivos, uno por departamento)
├── 08_ATLANTICO.csv
├── ...
└── 76_VALLE_DEL_CAUCA.csv
```
**Total:** 33 archivos CSV (aprox. 8GB)

### EMICRON 2019/ a 2024/
```
EMICRON 2019/
├── encuesta_micronegocios_2019.csv    (o similar)
```
**Total:** 6 carpetas (2019-2024), ~100MB cada una

### Archivos raíz en Datos/
```
Datos/
├── SECOP_I_-_Procesos_de_Compra_Pública_20260412.csv    (~10.5GB)
├── SECOP_II_-_Contratos_Electrónicos_20260412.csv        (~9.6GB)
└── PPED-AreaDep-2018-2050_VP.csv                          (~140KB)
```

---

## 🐛 Si Aún Así Falla

### Error: "No hay datos de SECOP II en Bronze"

**Causa:** La carpeta `Datos` no se encontró.

**Solución:**
1. Verifica que la ruta sea: `CONSULTORIA/Datos/`
2. O configura `.env` con la ruta completa
3. Ejecuta: `python src/validadores/verificar_datos`

### Error: "CNPV: sin carpeta" o similar

**Causa:** La subcarpeta específica no existe en el lugar correcto.

**Solución:**
1. Asegúrate que `CENSO 2018 dep/` esté dentro de `Datos/`
2. Verifica que contenga los 33 CSVs departamentales
3. Los nombres deben ser exactos (sensible a mayúsculas/minúsculas en Linux/Mac)

### Error: "divipola_key no encontrado"

**Causa:** Probablemente el pipeline no se ejecutó correctamente porque los datos fuente no estaban disponibles.

**Solución:**
1. Asegúrate que **PRIMERO** ejecutes `python src/ingesta/run_bronze.py`
2. Verifica que los archivos en `data/bronze/` se crearon
3. Luego ejecuta `python src/transformacion/run_silver.py`
4. Finalmente `python src/transformacion/run_gold.py`

---

## 🚀 Flujo Completo

### Paso 1: Preparar datos
```bash
# Coloca la carpeta Datos/ al mismo nivel que CONSULTORIA/
# O configura .env con las rutas
```

### Paso 2: Verificar setup
```bash
python -m src.validadores.verificar_datos
```

### Paso 3: Ejecutar pipeline
```bash
# Bronze (ingesta)
python src/ingesta/run_bronze.py

# Silver (limpieza y validación)
python src/transformacion/run_silver.py

# Gold (dimensional y cruces)
python src/transformacion/run_gold.py
```

### Paso 4: Usar el OBT
```
data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet
```

---

## 📞 Checklist Rápido

- [ ] ¿La carpeta `Datos` está en `CONSULTORIA/Datos/`?
- [ ] ¿Contiene `CENSO 2018 dep/` con 33 CSVs?
- [ ] ¿Contiene `EMICRON 2019/` a `EMICRON 2024/`?
- [ ] ¿Contiene los 3 archivos CSV SECOP e PPED?
- [ ] ¿Ejecutaste `python src/ingesta/run_bronze.py` primero?
- [ ] ¿Se crearon archivos en `data/bronze/`?
- [ ] ¿Luego ejecutaste `run_silver.py` y `run_gold.py`?

Si todas las respuestas son ✅, el pipeline debería funcionar correctamente.

---

**Última actualización:** 2026-04-23  
**Responsable:** Pipeline Socioeconómico
