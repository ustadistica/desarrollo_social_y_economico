# 🏛️ Dashboard SECOP–DANE
### Análisis de Contratación Pública vs Vulnerabilidad Social · Colombia

---

## 📦 Instalación

```bash
pip install -r requirements.txt
```

## 🚀 Ejecutar

```bash
streamlit run app.py
```

Abrir en el navegador: `http://localhost:8501`

---

## 📋 Páginas del Dashboard

| Página | Descripción |
|--------|-------------|
| 🏠 Resumen Ejecutivo | KPIs, hallazgos clave, gauge Gini |
| 💰 Distribución de Inversión | Histogramas, top municipios, Curva de Lorenz |
| 📊 Vulnerabilidad Social | NBI, IPM, componentes NBI, radar |
| 🔗 Inversión vs Vulnerabilidad | Correlaciones, cuadrantes, heatmap |
| 🗺️ Análisis Departamental | Mapa de burbujas, rankings por dpto |
| ⚠️ Municipios Críticos | Alta pobreza + cero inversión |
| 🔬 Análisis Étnico | Brecha étnico-territorial |

---

## 📊 Fuentes de Datos

- **SECOP II**: Sistema Electrónico de Contratación Pública de Colombia
- **DANE**: Indicadores NBI, IPM y composición étnica por municipio
- **Cobertura**: 1.124 municipios colombianos

## 🔍 Hallazgos Principales

1. **Gini = 0.999** — La distribución de contratos más desigual posible
2. **99.3%** de municipios sin contratos registrados
3. **$22.2B COP** concentrados en 8 municipios
4. Correlación **-0.64** entre IPM y monto contratado
5. **561 municipios** de alta vulnerabilidad con $0 de inversión

---

## 🛠️ Tecnologías

- Python 3.12
- Streamlit 1.32+
- Plotly 5.18+
- Pandas · NumPy

---

## ⚠️ Nota sobre los datos

El dataset original requiere el archivo `cruce_secop_dane_sprint2.parquet`.
La versión actual usa datos sintéticos calibrados con los valores reales del EDA
para fines de demostración. Para usar el dataset real, reemplazar la función
`cargar_datos()` con la lectura del parquet original.
