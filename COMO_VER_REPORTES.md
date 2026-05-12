# Cómo ver el EDA y los indicadores HHI desde cualquier PC

Esta guía explica, paso a paso, cómo cualquier integrante del equipo puede
abrir en su navegador:

- El **EDA del cruce SECOP-DANE Gold 2018-2024** (notebook ejecutado y
  exportado a HTML).
- El **reporte de indicadores HHI** (Herfindahl-Hirschman Index) con sus
  tres gráficas y la tabla resumen anual.

Funciona en **Windows, macOS y Linux**. Si solo quieres mirar los reportes,
basta con clonar el repo y abrir dos archivos en el navegador (Sección 2).
Si los archivos HTML no están subidos o quieres re-ejecutar todo con datos
actualizados, sigue la Sección 3.

---

## 1. Resumen rápido

| Reporte | Archivo a abrir | Cómo se genera |
|---|---|---|
| EDA Gold 2018-2024 | `notebooks/EDA_Report.html` | `jupyter nbconvert --to html --execute notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb --output EDA_Report.html` |
| Indicadores HHI | `artifacts/hhi/hhi_report.html` | `python scripts/generar_graficas_hhi.py` |

Ambos son **HTML estáticos**: una vez generados, se abren en cualquier
navegador moderno (Chrome, Edge, Firefox, Safari) **sin necesidad de
levantar ningún servidor** y **sin pedir token de autenticación**.

---

## 2. Opción A — Solo abrir los reportes (la más simple)

Usa esta ruta si los archivos `.html` ya están versionados en el repo o si
otro compañero te pasó los archivos por Drive / WeTransfer.

### 2.1. Clonar el repositorio

```bash
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico
```

> Si no tienes git instalado: <https://git-scm.com/downloads>.
> Alternativa sin git: descarga el ZIP desde el botón verde **Code →
> Download ZIP** en GitHub y descomprímelo.

### 2.2. Abrir el EDA

- **Windows (Explorador):** doble clic sobre
  `notebooks\EDA_Report.html`.
- **macOS / Linux:** doble clic, o desde terminal:
  ```bash
  open notebooks/EDA_Report.html        # macOS
  xdg-open notebooks/EDA_Report.html    # Linux
  start notebooks\EDA_Report.html       # Windows (cmd o PowerShell)
  ```

### 2.3. Abrir el reporte HHI

Igual que el EDA, pero en:
```
artifacts/hhi/hhi_report.html
```

> **Nota:** la carpeta `artifacts/` está en `.gitignore`, por lo que
> **no está versionada**. Si esa ruta no existe en tu copia, salta a la
> **Opción B** para generarla con un solo comando.

---

## 3. Opción B — Regenerar los reportes desde los datos

Úsala si los HTML no están en tu copia del repo, o si los CSV de HHI o el
Gold Mart cambiaron y quieres volver a producir todo con los datos
actualizados.

### 3.1. Prerrequisitos

| Herramienta | Versión mínima | Descarga |
|---|---|---|
| Python | 3.10 (recomendado 3.12) | <https://www.python.org/downloads/> |
| pip    | el que viene con Python | — |
| git    | cualquiera reciente | <https://git-scm.com/downloads> |

> **Windows:** durante la instalación de Python, marca la casilla
> **"Add Python to PATH"**. Sin ella, los comandos `python` y `pip` no
> funcionarán desde la terminal.

Verifica que todo esté instalado:

```bash
python --version    # debe imprimir 3.10 o superior
pip --version
git --version
```

### 3.2. Clonar el repo y entrar a la carpeta

```bash
git clone https://github.com/ustadistica/desarrollo_social_y_economico.git
cd desarrollo_social_y_economico
```

### 3.3. (Opcional pero recomendado) Crear un entorno virtual

Evita ensuciar tu Python global.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Si PowerShell bloquea la activación con
> *"running scripts is disabled on this system"*, ejecuta una vez como
> administrador:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
> ```

### 3.4. Instalar dependencias

Las únicas librerías necesarias para **ver** los dos reportes son
`pandas`, `numpy`, `matplotlib` y `jupyter`. Las puedes instalar con:

```bash
pip install pandas numpy matplotlib jupyter nbconvert pyarrow
```

O bien, si quieres instalar todo el pipeline (puede tardar más):

```bash
pip install -r requirements.txt
```

### 3.5. Regenerar el reporte HHI

Es el más rápido (segundos):

```bash
python scripts/generar_graficas_hhi.py
```

Salida esperada en consola:

```
Cargando datos HHI...
  hhi_por_anio        : 9 filas
  hhi_por_nivel       : 15 filas
  HHI_CRUCE_SECOP_DANE: 432 filas

Generando figuras...
  ✓ artifacts/hhi/hhi_tendencia_anual.png
  ✓ artifacts/hhi/hhi_por_nivel.png
  ✓ artifacts/hhi/hhi_distribucion_municipal.png

Generando reporte HTML...
  ✓ artifacts/hhi/hhi_report.html
```

Luego abre `artifacts/hhi/hhi_report.html` en tu navegador.

### 3.6. Regenerar el EDA completo

Tarda 2-4 minutos porque vuelve a ejecutar todas las celdas:

```bash
jupyter nbconvert --to html --execute \
    --ExecutePreprocessor.timeout=300 \
    notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb \
    --output EDA_Report.html
```

**En Windows (una sola línea):**
```cmd
jupyter nbconvert --to html --execute --ExecutePreprocessor.timeout=300 notebooks/EDA_SECOP_DANE_Gold_2018_2024.ipynb --output EDA_Report.html
```

Al terminar verás un mensaje tipo
`[NbConvertApp] Writing 2469408 bytes to EDA_Report.html`. Abre
`notebooks/EDA_Report.html` en tu navegador.

> **Importante:** el EDA depende del **Gold Mart**
> (`data/gold/marts/latest/mart_desarrollo_social_economico_municipio_anio.parquet`).
> Si ese archivo no está en tu copia del repo, el EDA fallará en la
> sección 1. En ese caso, pide el archivo al equipo o ejecuta el pipeline
> de ingesta antes (ver `README.md` principal del repo).

---

## 4. Estructura de archivos clave

```
desarrollo_social_y_economico/
├── COMO_VER_REPORTES.md                   ← esta guía
├── notebooks/
│   ├── EDA_SECOP_DANE_Gold_2018_2024.ipynb  ← fuente del EDA
│   └── EDA_Report.html                      ← EDA exportado (Opción A)
├── scripts/
│   └── generar_graficas_hhi.py            ← script generador HHI
├── data/
│   ├── hhi_por_anio.csv                   ← insumo: HHI por año
│   ├── hhi_por_nivel.csv                  ← insumo: HHI por orden de entidad
│   ├── hhi_por_departamento.csv           ← insumo: HHI por departamento
│   ├── hhi_por_municipio.csv              ← insumo: HHI por municipio
│   └── HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv  ← insumo: tabla maestra
└── artifacts/hhi/                         ← salida del script HHI (gitignored)
    ├── hhi_report.html                    ← reporte HTML
    ├── hhi_tendencia_anual.png
    ├── hhi_por_nivel.png
    └── hhi_distribucion_municipal.png
```

---

## 5. Qué hay dentro de cada reporte

### 5.1. `EDA_Report.html` — EDA Gold SECOP-DANE 2018-2024

17 secciones que cubren, sobre el Gold Mart cruzado con CNPV y EMICRON:

- Evolución temporal de la contratación (monto, contratos, variación %).
- Distribución del monto por año (escala log) y por departamento.
- Vulnerabilidad social: NBI e IPM (CNPV 2018).
- Concentración por municipio (Top 15 anual) y Gini.
- Relación inversión-vulnerabilidad (dispersión NBI vs log Monto).
- Cuadrantes de abandono relativo y municipios críticos.
- Ticket promedio por cuartil de NBI.
- Matrices de correlación anuales.
- Micronegocios y economía popular (EMICRON).
- Contexto histórico (pandemia, ciclos electorales).
- Resumen ejecutivo.

### 5.2. `hhi_report.html` — Indicadores HHI

- KPIs: HHI promedio 2018, 2024 y 2026; número de observaciones en
  HHI = 10.000.
- **Figura 1**: Evolución del HHI promedio nacional 2018-2026, con valor
  real, número de contratos y municipios por año.
- **Figura 2**: HHI por orden de entidad (Nacional vs Territorial).
- **Figura 3**: Histograma de las 432 observaciones (municipio × año ×
  nivel) del cruce, segmentado por la escala estándar HHI
  (convención DOJ/FTC).
- Tabla resumen del HHI promedio anual.

Todas las cifras provienen de los CSV de entrada producidos por
`src/features/indicador_hhi_cruce.py`; no hay valores estimados ni
interpolados.

---

## 6. Problemas frecuentes y cómo resolverlos

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python: command not found` (Win) | Python no está en el PATH | Reinstala marcando "Add Python to PATH" o usa `py` en vez de `python` |
| `jupyter: command not found` | Jupyter no instalado | `pip install jupyter nbconvert` |
| El navegador pide *Token authentication* | Levantaste `jupyter notebook` en vez de abrir el `.html` | Cierra Jupyter, abre directamente el archivo `.html` con doble clic |
| `FileNotFoundError: hhi_por_anio.csv` | Estás ejecutando el script desde otra carpeta | Asegúrate de estar en la raíz del repo o ejecuta con la ruta completa |
| `FileNotFoundError: mart_desarrollo_social_economico_municipio_anio.parquet` | El Gold Mart no está sincronizado | Pide el archivo al equipo o ejecuta el pipeline ETL antes |
| Las gráficas HHI salen pero el HTML no | No hay carpeta `artifacts/hhi` | El script la crea sola; verifica permisos de escritura |
| `ModuleNotFoundError: pyarrow` | Falta dependencia para Parquet | `pip install pyarrow` |
| Caracteres raros en consola (Windows) | Encoding del terminal | Ejecuta antes: `chcp 65001` |

---

## 7. Datos fuente

Los CSV en `data/` que alimentan el reporte HHI son producidos por el
módulo `src/features/indicador_hhi_cruce.py`. Si quieres recalcularlos
desde cero, ejecuta:

```bash
python -m src.features.indicador_hhi_cruce
```

El cálculo usa la fórmula estándar Herfindahl-Hirschman escalada a
0-10.000:

```
HHI = Σ [(suma_proveedor_i / inversion_total) × 100]²
```

agrupada por `(anio_firma, divipola_municipio, orden_entidad)`.

---

## 8. Contacto y dudas

Si algo falla y la tabla de la Sección 6 no lo cubre, abre un issue en
GitHub o escribe al canal del equipo con:

1. Sistema operativo y versión.
2. Salida de `python --version`.
3. El comando exacto que ejecutaste.
4. El mensaje de error completo (copiado, no foto).
