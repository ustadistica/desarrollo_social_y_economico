# Informe HHI SECOP 2018-2026

Este informe reemplaza los valores anteriores del HHI. La version previa no era
reproducible desde el repo: citaba CSV y scripts que no existian, usaba una tabla
de resultados no versionada y mostraba una caida artificial de contratos en
2024-2026 que no aparece al recalcular desde Silver transaccional.

## Metodologia corregida

El calculo oficial queda en `src/features/indicador_hhi_cruce.py` y se genera
con:

```bash
python -m src.features.indicador_hhi_cruce
```

Reglas aplicadas:

- Fuente contractual: `data/silver/silver_secop_i_transaccional.parquet` y
  `data/silver/silver_secop_ii_transaccional.parquet`.
- Ventana analitica: 2018-2026.
- Filtros: contratos con `valor_del_contrato > 0`, `nit_contratista` valido,
  `divipola_key` valido y `anio_key` dentro de la ventana.
- Deduplicacion: `drop_duplicates(id_contrato)`, igual que
  `src/transformacion/gold/build_facts.py`, para no inflar montos ni cuotas.
- Mercado HHI: `anio_key x divipola_key x orden_entidad`.
- `orden_entidad`: se toma de Silver cuando exista; para Silver historico sin
  esa columna se reconstruye desde Bronze. Los faltantes quedan como
  `NO_DEFINIDO`; no se imputan como `TERRITORIAL`.
- Formula:

```text
HHI = sum(((suma_proveedor_i / inversion_total_mercado) * 100)^2)
```

## Resultados anuales corregidos

| Año | HHI promedio | HHI mediana | Mercados | Contratos |
|---:|---:|---:|---:|---:|
| 2018 | 1,221.87 | 669.65 | 1,258 | 1,083,791 |
| 2019 | 1,405.88 | 792.15 | 1,273 | 1,182,159 |
| 2020 | 1,040.57 | 460.45 | 1,296 | 1,127,055 |
| 2021 | 1,121.26 | 582.21 | 1,313 | 1,283,497 |
| 2022 | 1,373.02 | 667.29 | 1,361 | 1,092,707 |
| 2023 | 1,483.89 | 768.95 | 1,321 | 960,198 |
| 2024 | 1,114.10 | 515.55 | 1,324 | 954,524 |
| 2025 | 1,484.07 | 680.59 | 1,354 | 1,041,632 |
| 2026 | 1,422.50 | 701.35 | 1,292 | 503,992 |

Lectura: con la Silver actual no hay evidencia de un colapso nacional de
competencia hacia HHI 9,000-10,000. El promedio nacional se mantiene entre
1,040 y 1,484 en la ventana, con picos relativos en 2023 y 2025.

## Nacional vs Territorial

| Año | Orden | HHI promedio | HHI mediana | Mercados | Contratos |
|---:|---|---:|---:|---:|---:|
| 2018 | NACIONAL | 2,145.84 | 1,280.62 | 174 | 183,969 |
| 2018 | TERRITORIAL | 1,047.54 | 614.63 | 1,068 | 895,886 |
| 2019 | NACIONAL | 2,002.97 | 1,379.62 | 186 | 212,493 |
| 2019 | TERRITORIAL | 1,291.19 | 724.75 | 1,070 | 966,889 |
| 2020 | NACIONAL | 1,752.16 | 1,082.99 | 207 | 155,432 |
| 2020 | TERRITORIAL | 881.54 | 424.96 | 1,074 | 968,957 |
| 2021 | NACIONAL | 1,727.96 | 940.87 | 210 | 177,179 |
| 2021 | TERRITORIAL | 994.16 | 550.64 | 1,077 | 1,100,656 |
| 2022 | NACIONAL | 2,336.49 | 1,377.00 | 245 | 169,935 |
| 2022 | TERRITORIAL | 1,098.89 | 613.01 | 1,080 | 914,060 |
| 2023 | NACIONAL | 2,800.75 | 1,322.86 | 203 | 202,271 |
| 2023 | TERRITORIAL | 1,213.17 | 737.89 | 1,079 | 748,330 |
| 2024 | NACIONAL | 2,217.48 | 983.20 | 199 | 222,109 |
| 2024 | TERRITORIAL | 881.05 | 495.35 | 1,082 | 721,323 |
| 2025 | NACIONAL | 2,809.30 | 1,291.63 | 215 | 240,476 |
| 2025 | TERRITORIAL | 1,147.46 | 645.72 | 1,086 | 789,752 |
| 2026 | NACIONAL | 2,189.69 | 774.96 | 179 | 133,738 |
| 2026 | TERRITORIAL | 1,237.99 | 679.92 | 1,067 | 364,432 |

Lectura: el orden nacional tiende a concentrarse mas que el territorial, pero
esa diferencia no implica monopolio nacional generalizado. La mediana nacional
queda por debajo de 1,500 en todos los años salvo ningun caso extremo de serie
completa.

## Departamentos 2026

Departamentos con mayor HHI promedio en 2026:

| Departamento | HHI promedio | HHI mediana | Mercados | Contratos |
|---|---:|---:|---:|---:|
| Atlantico | 2,824.15 | 920.92 | 31 | 19,924 |
| Choco | 2,695.77 | 872.71 | 19 | 2,048 |
| Magdalena | 2,053.98 | 908.15 | 34 | 14,826 |
| La Guajira | 1,885.03 | 680.46 | 20 | 4,498 |
| Boyaca | 1,816.14 | 894.85 | 143 | 18,804 |

Departamentos con menor HHI promedio en 2026:

| Departamento | HHI promedio | HHI mediana | Mercados | Contratos |
|---|---:|---:|---:|---:|
| Guainia | 494.91 | 252.44 | 3 | 1,573 |
| Quindio | 517.53 | 437.92 | 13 | 9,988 |
| Amazonas | 628.64 | 238.01 | 4 | 3,057 |
| Vaupes | 690.53 | 677.81 | 4 | 1,255 |
| Santander | 884.46 | 498.52 | 97 | 25,918 |

## Validaciones

- Tabla maestra generada: `data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv`
  con 11,792 mercados.
- Rango observado: HHI minimo 18.81 y maximo 10,000.00.
- Observaciones con HHI perfecto de 10,000: 186 mercados.
- Cobertura geografica: 0 mercados sin nombre de departamento en el cruce con
  el Gold Mart.
- Distribucion por orden en la tabla maestra: 9,683 territoriales, 1,818
  nacionales, 204 otros y 87 no definidos.

## Archivos generados

- `data/hhi_por_anio.csv`
- `data/hhi_por_nivel.csv`
- `data/hhi_por_departamento.csv`
- `data/hhi_por_municipio.csv`
- `data/HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv`
- `artifacts/hhi/hhi_report.html`

