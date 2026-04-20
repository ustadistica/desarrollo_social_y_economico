# 🥈 Capa Silver - Limpieza, Homologación y Pre-Agregación

La arquitectura de la capa Silver fue re-diseñada para actuar como un embudo estricto y seguro de validación analítica. Con la refactorización reciente, **Silver asume la responsabilidad funcional de pre-agregar la data al grano objetivo (`Municipio - Año`)** antes de inyectarla o enlazarla en Gold.

## Características de la Nueva Generación Silver

1. **Reestructuración de Llaves Geográficas (Homologación Territorial):**
   - Todos los códigos, sin importar cómo se llamen en DANE (U_MPIO, COD_MUNICIPIO) o en SECOP (codigo_entidad, municipio_entidad), son transformados matemáticamente a la columna unificada: `divipola_key`.
   - Se aplica padding con `0` a la izquierda obligatoriamente asegurando una PK estricta de 5 caracteres.
   
2. **Reestructuración Temporal (Homologación Anual):**
   - Transaccionales como `fecha_de_publicacion` o `fecha_de_firma` son truncadas a su respectivo `anio_key`.
   - Elementos censales son anclados fuertemente (ej. CNPV amarrado en 2018).
   - Registros prospectivos (Proyecciones DANE 2018-2050) son acotados rigurosamente hasta la actualidad (2025 máximo) para prohibir extrapolaciones ilusorias.

3. **Prevención contra Inflación Matricial:**
   - La directiva clave es: *No pasar a Gold nada que todavía esté inconsistente o propense a multiplicar métricas por un JOIN*.
   - Silver agrega intrínsecamente las volumetrías (`COUNT(DISTINCT contrato)` o `SUM(fex_c)`).
   - Gold solo se encargará estrictamente del Modelo Estrella final y Datamart.

## Modularidad

| Script                     | Operación de Extracción | Operación Analítica |
| -------------------------- | ----------------------- | ------------------- |
| `clean_secop_i.py`   | DuckDB read histórico   | Agrupa por divipola_key/anio_key el monto y adjudicaciones. |
| `clean_secop_ii.py`  | DuckDB read actual      | Mapea identificadores SECOP II al mismo schema homologado SECOP I. |
| `clean_emicron.py`         | Lectura Multiparte      | Unifica los submódulos, identifica factores de expansión (`fex_c`) reales y hace sumatorias estadísticas de representatividad. |
| `clean_cnpv.py`            | Lectura Base Pura       | Agrupación censal fijada a 2018 sin dobles conteos. |

## Orquestación

Lanzar una única vez desde la raíz usando el script unificado:

```bash
python run_silver.py
```

*Saldrá consolidado el reporte automatizado `SILVER_DATA_QUALITY_REPORT.md` validando unicidad, nulos y reglas en la carpeta de documentación.*
