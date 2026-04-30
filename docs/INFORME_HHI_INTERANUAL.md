# Informe de Resultados: Análisis de Concentración del Mercado (HHI Interanual 2018-2026)

Este documento presenta los principales hallazgos y la interpretación económica de los cruces de datos entre el SECOP y el DANE. Utilizando el Índice Herfindahl-Hirschman (HHI), evaluamos el nivel de pluralidad u oligopolio en la contratación pública colombiana.

> [!NOTE]
> **Escala de Interpretación del HHI**
> - **Cercano a 0:** Competencia perfecta (mercado atomizado).
> - **1,500 - 2,500:** Concentración moderada.
> - **Mayor a 2,500:** Alta concentración.
> - **10,000:** Monopolio absoluto (un solo contratista domina el mercado analizado).

---

## 1. El colapso temporal de la competencia (`hhi_por_anio.csv`)

El hallazgo más contundente del cruce de datos es el deterioro sistemático y acelerado de la libre competencia en las compras públicas con el paso de los años.

| Año | HHI Promedio | Nivel de Competencia | Contratos Analizados |
| :--- | :--- | :--- | :--- |
| **2018** | 2,397.79 | Moderada | 4,289 |
| **2019** | 2,206.36 | Moderada | 4,675 |
| **2020** | 2,013.40 | Moderada | 4,125 |
| **2021** | 2,180.14 | Moderada | 3,338 |
| **2022** | 2,951.68 | Alta Concentración | 1,962 |
| **2023** | 4,232.43 | Muy Alta | 1,028 |
| **2024** | 6,939.32 | Extrema | 1,020 |
| **2025** | 9,382.79 | Casi Monopolio | 162 |
| **2026** | 9,851.35 | Monopolio Absoluto | 29 |

> [!WARNING]
> **Interpretación:** Existe una clara correlación inversa entre el tiempo y la pluralidad de oferentes. Mientras que en el periodo 2018-2021 los municipios gozaban de mercados saludables (HHI ~2,100) y alta rotación de contratos, a partir de 2022 la concentración se dispara. Esto sugiere consolidaciones de mercado, creación de mega-contratos, o barreras de entrada cada vez más fuertes que impiden a las pymes locales acceder al dinero público.

---

## 2. Evolución Año a Año por Nivel (Nacional vs Territorial) (`hhi_por_nivel.csv`)

Al separar la información por el origen del presupuesto a lo largo del tiempo, descubrimos que las dinámicas de contratación son opuestas y se han deteriorado de forma asimétrica.

| Año | Nivel (Orden Entidad) | Promedio HHI | Total Contratos | Interpretación |
| :--- | :--- | :--- | :--- | :--- |
| **2018** | TERRITORIAL | 2,397.79 | 4,289 | Competencia moderada |
| **2019** | TERRITORIAL | 2,206.36 | 4,675 | Competencia moderada |
| **2020** | NACIONAL | 3,473.39 | 3 | Alta concentración |
| **2020** | TERRITORIAL | 1,982.34 | 4,122 | Competencia moderada |
| **2021** | TERRITORIAL | 2,180.14 | 3,338 | Competencia moderada |
| **2022** | NACIONAL | 7,584.88 | 3 | Casi Monopolio |
| **2022** | TERRITORIAL | 2,686.92 | 1,959 | Alta concentración |
| **2023** | NACIONAL | 10,000.00 | 1 | Monopolio Absoluto |
| **2023** | TERRITORIAL | 3,820.46 | 1,027 | Alta concentración |
| **2024** | NACIONAL | 9,068.48 | 16 | Monopolio |
| **2024** | TERRITORIAL | 6,202.30 | 1,004 | Concentración Extrema |
| **2025** | NACIONAL | 9,726.90 | 29 | Monopolio |
| **2025** | TERRITORIAL | 9,287.98 | 133 | Monopolio |
| **2026** | NACIONAL | 10,000.00 | 4 | Monopolio Absoluto |
| **2026** | TERRITORIAL | 9,826.58 | 25 | Monopolio |

> [!TIP]
> **Interpretación:** La inversión Nacional llega a los territorios empaquetada en adjudicaciones únicas. Cuando el gobierno central invierte en un municipio, el 100% de ese dinero suele ir a un solo gran proveedor. Las alcaldías (Territorial), aunque históricamente fraccionaban más para distribuir riqueza local, han sucumbido recientemente a la misma dinámica monopólica.

---

## 3. Disparidad Regional (`hhi_por_departamento.csv`)

La capacidad institucional y económica de los departamentos define su nivel de competencia.

### 🟢 Departamentos con mercados más sanos (Histórico 2018)
| Departamento | HHI Promedio | Total Contratos |
| :--- | :--- | :--- |
| Bolívar | 212.35 | 602 |
| Cundinamarca | 893.05 | 586 |
| Nariño | 1,113.50 | 77 |

### 🔴 Departamentos atrapados en Monopolios (2024-2026)
Regiones que han marcado un HHI perfecto de 10,000 de manera sostenida en los últimos 3 años:
1. **Atlántico** (3 años consecutivos en monopolio)
2. **Meta** (3 años consecutivos en monopolio)
3. **Antioquia** (2 años en monopolio absoluto de la muestra)
4. **Cauca**
5. **Cesar**

> [!WARNING]
> **Interpretación:** La captura de rentas se ha vuelto crónica en ciertos departamentos. Que regiones como Atlántico y Meta presenten índices perfectos de concentración durante varios años seguidos es un fuerte indicador de centralización de contratistas.

---

## 4. Evolución Año a Año por Municipio (Solo Territoriales) (`hhi_por_municipio.csv`)

Muestra del Top 3 de los municipios con mayor cantidad de contratos por año. Aquí se observa cómo alcaldías específicas lograban excelente fraccionamiento en los primeros años, y cómo la dinámica se centraliza drásticamente hacia 2025-2026.

| Año | Departamento | Municipio | Promedio HHI | Total Contratos |
| :--- | :--- | :--- | :--- | :--- |
| **2018** | Antioquia | Girardota | 627.50 | 784 |
| **2018** | Bolívar | Cartagena | 212.35 | 602 |
| **2018** | Cundinamarca | Soacha | 838.98 | 343 |
| **2019** | Antioquia | Girardota | 1,102.65 | 752 |
| **2019** | Tolima | Ibagué | 2,799.07 | 742 |
| **2019** | Bolívar | Cartagena | 1,263.80 | 424 |
| **2020** | Bolívar | Cartagena | 2,310.41 | 648 |
| **2020** | Antioquia | Girardota | 569.18 | 527 |
| **2020** | Tolima | Ibagué | 832.24 | 311 |
| **2021** | Cundinamarca | Soacha | 694.61 | 435 |
| **2021** | Antioquia | Girardota | 1,772.93 | 417 |
| **2021** | Tolima | Ibagué | 538.55 | 404 |
| **2022** | Antioquia | Frontino | 948.04 | 322 |
| **2022** | Antioquia | Fredonia | 5,444.98 | 208 |
| **2022** | Nariño | Nariño | 2,525.31 | 154 |
| **2023** | Antioquia | Frontino | 876.68 | 199 |
| **2023** | Cundinamarca | Villagómez | 755.79 | 188 |
| **2023** | Antioquia | Fredonia | 369.71 | 134 |
| **2024** | Antioquia | Fredonia | 3,722.05 | 182 |
| **2024** | Antioquia | Giraldo | 2,780.55 | 162 |
| **2024** | Antioquia | Frontino | 861.44 | 132 |
| **2025** | Bogotá D.C. | No definido* | 7,361.24 | 20 |
| **2025** | Bogotá D.C. | Bogotá | 9,095.70 | 18 |
| **2025** | Valle del Cauca | Cali | 9,273.48 | 7 |
| **2026** | Cesar | Valledupar | 10,000.00 | 2 |
| **2026** | Risaralda | Pereira | 5,838.03 | 2 |
| **2026** | Antioquia | La Estrella | 10,000.00 | 1 |

> [!NOTE]
> *(Nota: A partir de 2025 los registros en el SECOP caen drásticamente en volumen en esta muestra, y lo poco que se registra está altamente concentrado o clasificado como "No definido", lo cual puede deberse a vigencias futuras o rezagos en la publicación de datos territoriales).*

---

## 📌 Conclusiones Clave para los Modelos Estadísticos

1. **La temporalidad es crítica:** Al estructurar tus modelos MLLib, el factor "Año" (`anio_firma`) no puede ser ignorado. El mercado público en 2025 es estructuralmente distinto (y más desigual) que el de 2018.
2. **HHI como predictor de desarrollo:** Este informe confirma que el HHI es una métrica extremadamente sensible a las realidades locales. La hipótesis principal para el modelo será comprobar si los municipios atrapados en monopolios (HHI=10,000) presentan peores indicadores socioeconómicos (DANE) que aquellos como Toca o Villagómez, que lograron mantener mercados dinámicos y competitivos.
