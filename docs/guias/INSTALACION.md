# 🚀 Guía de Instalación para Compañeros

Esta guía explica cómo clonar el repositorio y configurarlo correctamente para ejecutar el pipeline completo (ingesta, validación, cruce).

---

## 1️⃣ Clonar el Repositorio

```bash
# Navega a la carpeta CONSULTORIA
cd /ruta/a/CONSULTORIA

# Clona el repositorio
git clone <URL_DEL_REPO>
cd desarrollo_social_y_economico
```

---

## 2️⃣ Descargar la Base de Datos "Datos"

Johann les proporcionó una **carpeta llamada "Datos"**. Esta carpeta debe colocarse **AL MISMO NIVEL que CONSULTORIA**, no dentro del proyecto.

### Estructura Correcta:

```
Octavo/
├── CONSULTORIA/
│   ├── Datos/                           ← AQUÍ va la carpeta (al nivel de CONSULTORIA)
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
│       └── desarrollo_social_y_economico/    ← El repositorio clonado
│           ├── src/
│           ├── data/
│           └── ...
```

### Pasos:

1. **Recibe la carpeta "Datos"** de Johann (usualmente via Google Drive, Dropbox, etc.)
2. **Descomprime** en `CONSULTORIA/Datos/`
3. **Verifica** que contenga:
   - `CENSO 2018 dep/` (carpeta con 33 CSVs)
   - `EMICRON 2019/`, `EMICRON 2020/`, ..., `EMICRON 2024/` (carpetas)
   - `SECOP_I_-_Procesos_de_Compra_Pública_*.csv`
   - `SECOP_II_-_Contratos_Electrónicos_*.csv`
   - `PPED-AreaDep-2018-2050_VP.csv`

---

## 3️⃣ Instalar Dependencias Python

```bash
# Desde la carpeta del proyecto
cd Desarrollo\ social\ y\ economico/desarrollo_social_y_economico

# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Instalar dependencias
pip install -e .

# Verificar que se instaló correctamente
pip list | grep pandas
```

---

## 4️⃣ Verificar Configuración de Datos

Antes de ejecutar el pipeline, verifica que todo esté en el lugar correcto:

```bash
# Ejecuta el validador
python -m src.validadores.verificar_datos
```

Debería mostrar:

```
✅ SECOP_I_-_Procesos_de_Compra_Pública_*.csv
✅ SECOP_II_-_Contratos_Electrónicos_*.csv
✅ PPED-AreaDep-2018-2050_VP.csv
✅ CENSO 2018 dep/
✅ Encontrados 6 años de EMICRON

✅ CONFIGURACIÓN CORRECTA
```

Si ves ❌ en algún lado, significa que la carpeta "Datos" no está en el lugar correcto.

---

## 5️⃣ Ejecutar el Pipeline

### Opción A: Completo (Ingesta → Validación → Cruce)

```bash
# Bronze (Ingesta de datos)
python src/ingesta/run_bronze.py

# Silver (Validación y limpieza)
python src/transformacion/run_silver.py

# Gold (Cruce y modelo dimensional)
python src/transformacion/run_gold.py
```

Cada paso crea carpetas en `data/`:
- `data/bronze/` — Datos crudos en Parquet
- `data/silver/` — Datos limpios y validados
- `data/gold/` — Tablas de hechos y OBT final

### Opción B: Paso a Paso (Recomendado si es la primera vez)

```bash
# 1. Verifica que todo está en su lugar
python -m src.validadores.verificar_datos

# 2. Ejecuta Bronze (si tarda mucho, es normal, son 9.6GB de SECOP II)
python src/ingesta/run_bronze.py
# ⏱️ Tiempo estimado: 5-15 minutos

# 3. Verifica que se creó data/bronze/
ls data/bronze/

# 4. Ejecuta Silver
python src/transformacion/run_silver.py
# ⏱️ Tiempo estimado: 2-5 minutos

# 5. Verifica que se creó data/silver/
ls data/silver/

# 6. Ejecuta Gold
python src/transformacion/run_gold.py
# ⏱️ Tiempo estimado: 1-2 minutos

# 7. Verifica que se creó data/gold/marts/latest/
ls data/gold/marts/latest/
```

---

## 6️⃣ Usar el Resultado Final

Una vez completado el pipeline, la tabla analítica lista está en:

```
data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet
```

Para cargarla en Python:

```python
import pandas as pd

# Cargar el OBT (One Big Table)
obt = pd.read_parquet("data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet")

print(obt.shape)  # (3129, 23) — 3129 filas, 23 columnas
print(obt.columns)  # Nombres de todas las columnas
print(obt.head())  # Primeras 5 filas
```

---

## ❓ Preguntas Frecuentes

### ❓ ¿Dónde va la carpeta "Datos"?

**R:** En `CONSULTORIA/Datos/`, al mismo nivel que la carpeta `Desarrollo social y economico/`

```
CONSULTORIA/
├── Datos/                  ← AQUÍ (al nivel de CONSULTORIA)
└── Desarrollo social y economico/
    └── desarrollo_social_y_economico/
```

### ❓ ¿Qué pasa si la carpeta "Datos" está en otro lugar?

**R:** El pipeline no la encontrará. Puedes:

1. **Mover la carpeta** al lugar correcto (`CONSULTORIA/Datos/`)
2. **O** editar `.env` con la ruta absoluta completa:
   ```env
   CNPV_ROOT_DIR="C:\Users\TuNombre\Descargas\CENSO 2018 dep"
   SECOP_I_CSV_PATH="C:\Users\TuNombre\Descargas\SECOP_I_*.csv"
   SECOP_CSV_PATH="C:\Users\TuNombre\Descargas\SECOP_II_*.csv"
   EMICRON_CSV_PATH="C:\Users\TuNombre\Descargas"
   PROYECCIONES_CENSO_PATH="C:\Users\TuNombre\Descargas\PPED-AreaDep-2018-2050_VP.csv"
   ```

### ❓ ¿Cuánto tarda el pipeline?

**R:** Aproximadamente:
- Bronze: 5-15 min (lee 9.6GB de SECOP II)
- Silver: 2-5 min
- Gold: 1-2 min
- **Total: 10-25 min**

### ❓ ¿Qué si falla la ingesta?

**R:** Ejecuta el validador:
```bash
python -m src.validadores.verificar_datos
```

Esto te dirá qué archivos faltan y dónde deben estar.

### ❓ ¿Necesito ejecutar todo de nuevo?

**R:** No, a menos que cambien los datos originales. El OBT ya está listo en `data/gold/marts/latest/` después de ejecutar los tres comandos.

---

## 🔧 Troubleshooting

### Error: "Carpeta 'Datos' no encontrada"

```
❌ Carpeta 'Datos' no encontrada en las ubicaciones esperadas
```

**Solución:**
1. Verifica que exista: `CONSULTORIA/Datos/`
2. Ejecuta: `python -m src.validadores.verificar_datos`
3. Si no aparece, mueve la carpeta al lugar correcto

### Error: "CNPV: sin carpeta"

```
❌ No se pudo leer CNPV: carpeta no existe
```

**Solución:**
- Verifica que exista: `CONSULTORIA/Datos/CENSO 2018 dep/`
- Contiene debe tener 33 CSVs (uno por departamento)

### Error: "SECOP_I_*.csv no encontrado"

```
❌ No hay datos de SECOP I en Bronze
```

**Solución:**
- Verifica que exista: `CONSULTORIA/Datos/SECOP_I_-_Procesos_de_Compra_Pública_*.csv`
- El nombre debe ser exacto (incluyendo tildes)

### Error: "ModuleNotFoundError: No module named 'src'"

```python
ModuleNotFoundError: No module named 'src'
```

**Solución:**
```bash
# Asegúrate de estar en la carpeta correcta
cd desarrollo_social_y_economico

# Reinstala el paquete
pip install -e .
```

---

## ✅ Checklist Final

- [ ] Clonaste el repositorio
- [ ] Descargaste la carpeta "Datos" de Johann
- [ ] Colocaste "Datos" en `CONSULTORIA/Datos/`
- [ ] Creaste y activaste el entorno virtual
- [ ] Instalaste dependencias con `pip install -e .`
- [ ] Ejecutaste `python -m src.validadores.verificar_datos` y viste ✅
- [ ] Ejecutaste `python src/ingesta/run_bronze.py`
- [ ] Se creó la carpeta `data/bronze/` con archivos
- [ ] Ejecutaste `python src/transformacion/run_silver.py`
- [ ] Se creó la carpeta `data/silver/` con archivos
- [ ] Ejecutaste `python src/transformacion/run_gold.py`
- [ ] Se creó `data/gold/marts/latest/mart_*.parquet` (el OBT final)

Si todos los ✅ están marcados, **¡el pipeline funciona correctamente!**

---

## 📞 ¿Problemas?

Si algo falla:
1. Ejecuta el validador: `python -m src.validadores.verificar_datos`
2. Revisa SETUP_DATOS.md para más detalles
3. Contacta a Johann con:
   - El mensaje de error exacto
   - El output del validador

---

**Última actualización:** 2026-04-23  
**Versión:** 1.0 (Pipeline completo operacional)
