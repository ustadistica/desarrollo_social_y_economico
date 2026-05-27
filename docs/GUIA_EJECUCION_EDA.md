# Guía de Ejecución del EDA — Cruce SECOP-DANE 2018–2024

Esta guía explica paso a paso cómo ejecutar el análisis exploratorio de datos (EDA)
del proyecto. Está escrita para alguien que nunca ha abierto el proyecto antes.

---

## ¿Qué es este EDA y qué muestra?

El EDA es un notebook de Jupyter (un documento interactivo que mezcla código Python
y gráficas) que analiza el cruce entre:

- **SECOP I y II**: todos los contratos públicos municipales de Colombia (2018–2024)
- **CNPV 2018**: datos del Censo Nacional (NBI, pobreza, etnia por municipio)
- **EMICRON**: encuesta de micronegocios DANE (economía popular, 2019–2024)
- **Proyecciones DANE**: población municipal por año

Al ejecutarlo verás 16 secciones con tablas y gráficas: evolución de la inversión,
desigualdad (Gini), municipios en abandono, correlación pobreza–contratos, y más.

---

## Lo que necesitas tener instalado antes de empezar

| Herramienta | Versión mínima | Cómo verificar que ya la tienes |
|---|---|---|
| Python | 3.9 o superior | `python --version` en la terminal |
| pip | Cualquiera reciente | `pip --version` |
| Git | Cualquiera | `git --version` |

> Si alguno de estos comandos te da error de "comando no encontrado",
> descarga Python desde https://www.python.org/downloads/ (versión 3.12 recomendada).
> Git desde https://git-scm.com/downloads.

---

## Paso 1 — Obtener el código del repositorio

### Si es la primera vez que descargas el proyecto:

Abre una terminal (en Windows puedes usar **Git Bash** o **PowerShell**) y escribe:

```bash
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico
```

### Si ya tienes el repositorio y quieres actualizarlo:

Entra a la carpeta del proyecto y descarga los últimos cambios:

```bash
cd desarrollo_social_y_economico
git checkout main
git pull origin main
```

---

## Paso 2 — Crear un entorno virtual de Python

Un entorno virtual es una "burbuja" de Python aislada para este proyecto.
Evita conflictos con otras instalaciones de Python en tu computador.

### En Windows (PowerShell o Git Bash):

```bash
python -m venv .venv
```

Luego actívalo:

```bash
# En PowerShell:
.venv\Scripts\Activate.ps1

# En Git Bash:
source .venv/Scripts/activate
```

Sabrás que está activado porque verás `(.venv)` al inicio de tu línea de comandos.

### En Mac o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> **Importante:** Cada vez que abras una terminal nueva tendrás que volver a activar
> el entorno con el comando `source` (o `Activate.ps1` en Windows).

---

## Paso 3 — Instalar las dependencias del proyecto

Con el entorno virtual activado, instala todas las librerías necesarias:

```bash
pip install -r requirements.txt
```

Esto puede tardar entre 3 y 10 minutos la primera vez. Verás muchos mensajes
de descarga, eso es normal.

Luego instala Jupyter (el programa que abre los notebooks):

```bash
pip install notebook
```

---

## Paso 4 — Verificar que los datos estén listos

El notebook necesita un archivo de datos llamado
`data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet`.

Para verificar que existe, ejecuta:

```bash
python -c "
from pathlib import Path
p = Path('data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet')
print('DATOS OK' if p.exists() else 'FALTA EL MART — ve al Paso 4b')
"
```

### Caso A: dice `DATOS OK`

Puedes pasar directamente al Paso 5.

### Caso B: dice `FALTA EL MART`

Los datos procesados no están en tu copia local. Esto pasa cuando clonas el repo
por primera vez (los archivos de datos no se guardan en Git por su tamaño).

Tienes dos opciones:

**Opción B1 (recomendada si tienes los archivos raw):** Ejecuta el pipeline completo:

```bash
python -m src.main
```

Esto tarda entre 10 y 30 minutos según tu computador.

**Opción B2:** Pídele a alguien del equipo que te comparta el archivo
`mart_desarrollo_social_economico_municipio_anio.parquet` y colócalo en
`data/gold/marts/latest/`. Asegúrate también de tener:
- `data/cruce_secop_dane_sprint2.parquet`
- `data/etnia_checkpoint.parquet`

---

## Paso 5 — Abrir el notebook

### Opción A: Jupyter Notebook (en el navegador)

Con el entorno virtual activado, desde la raíz del proyecto escribe:

```bash
jupyter notebook
```

Se abrirá automáticamente tu navegador web en una página con los archivos del proyecto.
Navega a la carpeta `notebooks/` y haz clic en:

```
EDA_SECOP_DANE_Gold_2018_2024.ipynb
```

### Opción B: VS Code

1. Abre VS Code
2. Abre la carpeta del proyecto: **Archivo → Abrir Carpeta** y selecciona `desarrollo_social_y_economico`
3. En el explorador de archivos (panel izquierdo) navega a `notebooks/`
4. Haz clic en `EDA_SECOP_DANE_Gold_2018_2024.ipynb`
5. VS Code lo reconoce como notebook automáticamente

> Si VS Code te dice que necesita una extensión, instala **Jupyter** (de Microsoft)
> desde el panel de extensiones.

---

## Paso 6 — Ejecutar todas las celdas

Una vez abierto el notebook, debes ejecutar todas las celdas en orden.

### En Jupyter Notebook (navegador):

En el menú superior haz clic en:

```
Kernel → Restart & Run All
```

Confirma haciendo clic en **"Restart and Run All Cells"**.

### En VS Code:

En la parte superior del notebook haz clic en el botón:

```
▶▶  Run All
```

O usa el atajo de teclado `Ctrl + Alt + R`.

> Cuando te pregunte qué kernel usar, selecciona el que dice **Python 3** y apunte
> a tu entorno `.venv` (aparece como `.venv/bin/python` o `.venv\Scripts\python.exe`).

---

## Paso 7 — Esperar la ejecución

La ejecución completa tarda entre **3 y 8 minutos** dependiendo de tu computador.
Verás que las celdas van mostrando tablas y gráficas una a una mientras se ejecutan.

Un indicador `[*]` a la izquierda de una celda significa que está en ejecución.
Cuando termina cambia a un número como `[1]`, `[2]`, etc.

---

## ¿Qué verás cuando termine?

El notebook tiene 16 secciones, cada una con gráficas y tablas:

| Sección | Qué muestra |
|---|---|
| **1. Carga inicial** | Dimensiones del dataset, nulos, años disponibles |
| **2. Evolución temporal** | Monto total y número de contratos 2018–2024 |
| **3. Distribución del monto** | Histogramas por año (escala logarítmica) |
| **4. Vulnerabilidad (NBI e IPM)** | Boxplots de pobreza por año |
| **5. Top 15 municipios** | Ranking de inversión por año |
| **6. Coeficiente de Gini** | Equidad territorial vía inversión per cápita |
| **7. NBI vs Monto** | Dispersión: ¿reciben más los más pobres? |
| **8. Departamentos y regiones** | Evolución por departamento y región |
| **9. Cuadrantes de abandono** | Alta pobreza + poca inversión (municipios en rojo) |
| **10. Municipios críticos** | NBI muy alto y cero contratos en ese año |
| **11. Ticket promedio** | Valor promedio del contrato según nivel de pobreza |
| **12. Correlaciones** | Matrices de correlación entre todas las variables |
| **13. Alta vulnerabilidad** | % del total que reciben los más pobres |
| **14. Micronegocios** | Evolución de la economía popular por departamento |
| **15. Pandemia y elecciones** | Efecto del contexto histórico en la contratación |
| **16. Resumen ejecutivo** | Tabla resumen con todos los indicadores clave |

---

## Solución de problemas frecuentes

### Error: `ModuleNotFoundError: No module named 'pandas'`

El entorno virtual no está activado o las dependencias no están instaladas.
Vuelve al Paso 2 y asegúrate de que el entorno está activado (debe verse `(.venv)`
en tu terminal), luego repite el Paso 3.

### Error: `FileNotFoundError` al cargar el parquet

El archivo de datos no existe en la ruta esperada. Ve al Paso 4 y sigue la Opción B.

### El notebook carga el kernel pero no ejecuta

Prueba en la barra de menú: `Kernel → Change Kernel` y selecciona Python 3
con el entorno `.venv`.

### VS Code no muestra la opción de notebook

Instala la extensión **Jupyter** desde el Marketplace de VS Code
(`Ctrl+Shift+X` → buscar "Jupyter" → Instalar).

### La ejecución se detiene en alguna celda con error rojo

Lee el mensaje de error. Los más comunes son:
- `KeyError: 'nbi_pct'` → el archivo `cruce_secop_dane_sprint2.parquet` no está en `data/`
- `MemoryError` → cierra otras aplicaciones y vuelve a intentar
- Cualquier otro: comparte el mensaje de error en el canal del equipo

---

## Regenerar el notebook (solo si lo modificas)

El notebook se genera automáticamente desde el script
`scripts/generate_eda_notebook.py`. Si necesitas modificar alguna sección,
edita ese script y luego ejecuta:

```bash
python scripts/generate_eda_notebook.py
```

Esto sobreescribe el `.ipynb` con la versión actualizada.

---

## Resumen rápido (para los que ya saben)

```bash
git pull origin main
python -m venv .venv && source .venv/Scripts/activate   # o source .venv/bin/activate en Mac/Linux
pip install -r requirements.txt && pip install notebook
jupyter notebook notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb
# → Kernel → Restart & Run All
```
