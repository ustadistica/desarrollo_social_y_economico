# Infografía preliminar

Versión preliminar de la infografía resumen del indicador HHI según indicación del enunciado de entrega.

## Archivo

- [`infografia_hhi.png`](infografia_hhi.png) — 11 x 16 pulgadas, 180 dpi.

## Reproducción

```bash
python scripts/generar_infografia_hhi.py
```

Lee de `data/`:
- `hhi_por_anio.csv`
- `hhi_por_nivel.csv`
- `HHI_CRUCE_SECOP_DANE_RESULTADOS_final.csv`

Genera la imagen final en `artifacts/infografia/infografia_hhi.png`.

## Contenido

1. Título y subtítulo del proyecto.
2. KPIs principales (mercados, HHI promedio, años, monopolios).
3. Tendencia anual del HHI promedio y mediana.
4. HHI por orden de entidad (panel inferior izquierdo).
5. Distribución del HHI municipio-año-orden (panel inferior derecho).
6. Top 10 departamentos por HHI promedio del último año disponible.
7. Leyenda de bandas de concentración y citación de fuentes.

Esta versión es **boceto** y puede editarse manualmente en software vectorial (Inkscape, Illustrator) para la versión final.
