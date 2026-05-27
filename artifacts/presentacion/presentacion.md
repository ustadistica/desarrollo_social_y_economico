---
marp: true
theme: default
paginate: true
size: 16:9
header: 'Sinergia socioeconómica · HHI SECOP · USTA 2026-I'
footer: 'Consultorio de Estadística USTA · Observatorio Ustadística'
style: |
  section { font-family: Arial, sans-serif; }
  h1 { color: #1f2937; }
  h2 { color: #4e79a7; }
  table { font-size: 18px; }
  .small { font-size: 16px; color: #555; }
---

<!-- _class: lead -->

# Concentración de la contratación pública territorial en Colombia

## Índice Herfindahl-Hirschman (HHI) aplicado a SECOP I + II

**Proyecto:** Sinergia socioeconómica
**Equipo:** Consultorio de Estadística USTA · Observatorio Ustadística 2026-I
**Periodo:** 2018-2026

---

## 1. Problema

- La contratación pública es uno de los canales principales de redistribución del Estado.
- Pregunta central: ¿el valor adjudicado se distribuye entre varios proveedores o se concentra en pocos?
- Implicaciones: competencia efectiva, riesgos de captura de rentas, eficiencia del gasto.

---

## 2. Objetivo

Medir y describir la concentración del valor contratado en Colombia entre 2018 y 2026, a escala municipio × año × orden de entidad, usando datos abiertos SECOP I+II procesados en una arquitectura Medallion reproducible.

---

## 3. Fuentes de datos abiertos

| Fuente | Portal | Identificador | Periodo |
|---|---|---|---|
| SECOP I | Datos Abiertos Colombia | `f789-7hwg` | 2018-2026 |
| SECOP II | Datos Abiertos Colombia | `jbjy-vk9h` | 2018-2026 |
| CNPV 2018 | DANE | Catálogo 643 | 2018 |
| EMICRON | DANE | Catálogo 875 (2024) | 2019-2024 |
| Proyecciones población | DANE | CNPV-2018 base | 2018-2050 |

<span class="small">Fecha de consulta: 2026-05-27</span>

---

## 4. Arquitectura Medallion

```text
Portales → Bronze (Parquet crudo)
        → Silver (limpieza, tipos, DIVIPOLA, NIT, valores)
        → Gold (hechos + dimensiones + mart municipio-año)
        → Indicadores (HHI, EMICRON, CNPV)
```

- Deduplicación por `id_contrato` en la unión SECOP I + II.
- `orden_entidad` clasificado en NACIONAL / TERRITORIAL / OTRO / NO_DEFINIDO.
- Trazabilidad por hashes y metadatos en Bronze.

---

## 5. Método: HHI

$$
HHI_m = \sum_{i=1}^{n_m} \left( \frac{valor_{im}}{\sum_i valor_{im}} \times 100 \right)^2
$$

Escala 0-10,000.

| Rango | Interpretación |
|---:|---|
| < 1,500 | Baja concentración |
| 1,500-2,500 | Moderada |
| ≥ 2,500 | Alta |
| 10,000 | Un solo proveedor concentra el 100 % |

Mercado: `anio_key × divipola_key × orden_entidad`.

---

## 6. Resultado: tendencia anual

| Año | HHI promedio | HHI mediana | Mercados |
|---:|---:|---:|---:|
| 2018 | 1,221.87 | 669.65 | 1,258 |
| 2020 | 1,040.57 | 460.45 | 1,296 |
| 2022 | 1,373.02 | 667.29 | 1,361 |
| 2024 | 1,114.10 | 515.55 | 1,324 |
| 2025 | 1,484.07 | 680.59 | 1,354 |
| 2026 | 1,422.50 | 701.35 | 1,292 |

Concentración promedio nacional: **baja a moderada**.

![bg right:40% fit](../hhi/hhi_tendencia_anual.png)

---

## 7. Diferencia por orden de entidad

![bg right:50% fit](../hhi/hhi_por_nivel.png)

- **Nacional** consistentemente más concentrado que **Territorial**.
- En 2025: HHI nacional 2,809 vs territorial 1,147.
- Coherente con contratos nacionales de mayor escala.

---

## 8. Distribución y anomalías

![bg right:50% fit](../hhi/hhi_distribucion_municipal.png)

- 11,792 mercados en total.
- HHI mínimo: 18.81; máximo: 10,000.
- Solo **186 (1.58 %)** alcanzan el máximo:
  - 167 con 1 contrato + 1 proveedor (trivial)
  - 19 monopolios reales
  - 0 inconsistencias

---

## 9. Departamentos con mayor concentración (2026)

| Departamento | HHI promedio | Mercados |
|---|---:|---:|
| Atlántico | 2,824.15 | 31 |
| Chocó | 2,695.77 | 19 |
| Magdalena | 2,053.98 | 34 |
| La Guajira | 1,885.03 | 20 |
| Boyacá | 1,816.14 | 143 |
| Antioquia | 1,747.16 | 153 |

---

## 10. Hallazgos clave

1. La concentración promedio se mantiene **baja-moderada** en la definición amplia de mercado.
2. La contratación **nacional concentra más** que la territorial (consistente con contratos de mayor escala).
3. Existen **focos territoriales** que requieren análisis caso a caso.
4. El HHI es **indicador de alerta**, no prueba de irregularidad.

---

## 11. Limitaciones

- Municipio = lugar de la entidad contratante, no necesariamente lugar de ejecución.
- HHI mide valor adjudicado, no oferentes ni competencia efectiva por proceso.
- `NO_DEFINIDO` se conserva sin imputar.
- 2026 depende del corte disponible localmente.

---

## 12. Artefactos entregables

- `docs/INFORME_HHI_DETALLADO.md` — informe estadístico completo.
- `artifacts/hhi/hhi_report.html` — reporte HTML interactivo.
- `app/streamlit_app.py` — dashboard preliminar.
- `data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv` — tabla maestra.
- `data/hhi_por_*.csv` — agregaciones anuales, por orden, departamento, municipio.

---

## 13. Reproducción

```bash
python -m src.cli all               # pipeline completo Bronze→Gold
python -m src.features.indicador_hhi_cruce
python scripts/generar_graficas_hhi.py
streamlit run app/streamlit_app.py
```

Validación:

```bash
python -m pytest tests/test_indicador_hhi_cruce.py -q
```

---

<!-- _class: lead -->

# Gracias

**Repositorio:** `desarrollo_social_y_economico`
**Documento técnico:** `docs/INFORME_HHI_DETALLADO.md`
**Equipo:** Consultorio de Estadística USTA — Observatorio Ustadística 2026-I
