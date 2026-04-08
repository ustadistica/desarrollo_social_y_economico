import os
import sys
import pandas as pd
from pyspark.sql import SparkSession

# Forzar codificación en salidas de Windows
sys.stdout.reconfigure(encoding='utf-8')

# [VITAL PARA WINDOWS - ENTORNOS AISLADOS DE HADOOP Y JAVA]
os.environ['JAVA_HOME'] = r'C:\Program Files\ojdkbuild\java-11-openjdk-11.0.15-1'
os.environ['HADOOP_HOME'] = r'C:\hadoop'
os.environ['PATH'] = os.environ['HADOOP_HOME'] + r'\bin;' + os.environ.get('PATH', '')

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

print("==================================================")
print(" SPRINT 2: GENERACIÓN DE INDICADORES (PYSPARK)")
print("==================================================")

secop_raw = os.path.join(project_root, 'datos', 'secop_nuevos1.parquet')
cruce_dane = os.path.join(project_root, 'datos', 'cruce_secop_dane_sprint2.parquet')
out_csv = os.path.join(project_root, 'INDICADORES_FINALES_SPRINT2.csv')
out_parquet = os.path.join(project_root, 'INDICADORES_FINALES_SPRINT2.parquet')

# Spark Session Configurada (Mismo motor probado en analisis_regresiones)
print(f"DEBUG: JAVA_HOME es {os.environ.get('JAVA_HOME')}")
print(f"DEBUG: HADOOP_HOME es {os.environ.get('HADOOP_HOME')}")

try:
    print("Iniciando Builder...")
    spark = SparkSession.builder \
        .appName("Entregables_Sprint2_PySpark") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
    print("Builder Completado!")
except Exception as e:
    print(f"ERROR TERRIBLE en pyspark: {e}")
    sys.exit(1)

spark.sparkContext.setLogLevel("ERROR")

print("[1/3] Cargando parquets en base de datos en memoria (PySpark)...")
# Usamos Pandas de puente a CSV porque PySpark estalla en Windows con:
# 1. "Illegal Parquet type: TIMESTAMP" (Error nativo de las versiones JVM)
# 2. "RecursionError: Pickling" (Error nativo de Python 3.14 con arrow)
temp_secop = os.path.join(project_root, 'tmp_secop.csv')
temp_dane = os.path.join(project_root, 'tmp_dane.csv')

pdf_secop = pd.read_parquet(secop_raw, columns=['ciudad_entidad', 'nit_del_proveedor_adjudicado', 'valor_total_adjudicacion'])
pdf_secop.to_csv(temp_secop, index=False, sep='|', encoding='utf-8')

pdf_dane = pd.read_parquet(cruce_dane)
pdf_dane.to_csv(temp_dane, index=False, sep='|', encoding='utf-8')

# Spark lee las tablas limpias desde disco (evade pickling y schemas corruptos)
df_secop = spark.read.csv(temp_secop, header=True, sep='|', inferSchema=True)
df_dane = spark.read.csv(temp_dane, header=True, sep='|', inferSchema=True)

df_secop.createOrReplaceTempView("secop_nuevos")
df_dane.createOrReplaceTempView("base_dane")

print("[2/3] Calculando HHI e Inversión Per Cápita bajo SQL Engine distribuido...")

# Script de Spark SQL limpio de uniones dañadas o datos crudos faltantes
sql_maestra = """
WITH secop_raw AS (
    SELECT 
        UPPER(TRIM(ciudad_entidad)) as ciudad_entidad,
        nit_del_proveedor_adjudicado,
        CAST(valor_total_adjudicacion AS DOUBLE) as valor
    FROM secop_nuevos
    WHERE ciudad_entidad IS NOT NULL AND valor_total_adjudicacion IS NOT NULL
),
totales_municipio AS (
    SELECT 
        ciudad_entidad,
        SUM(valor) as total_municipio
    FROM secop_raw
    WHERE valor > 0
    GROUP BY ciudad_entidad
),
sumas_proveedor AS (
    SELECT 
        ciudad_entidad,
        nit_del_proveedor_adjudicado,
        SUM(valor) as suma_proveedor
    FROM secop_raw
    WHERE valor > 0
    GROUP BY ciudad_entidad, nit_del_proveedor_adjudicado
),
hhi_calc AS (
    SELECT 
        s.ciudad_entidad,
        SUM(POWER((s.suma_proveedor / t.total_municipio) * 100, 2)) as hhi_concentracion
    FROM sumas_proveedor s
    JOIN totales_municipio t ON s.ciudad_entidad = t.ciudad_entidad
    GROUP BY s.ciudad_entidad
),
hhi_limpio AS (
    SELECT 
        ciudad_entidad,
        regexp_replace(
            regexp_replace(translate(UPPER(TRIM(ciudad_entidad)), 'ÁÉÍÓÚ', 'AEIOU'), ', D\\\\.C\\\\.', ''),
            ' D\\\\.C\\\\.', ''
        ) as ciudad_limpia,
        hhi_concentracion
    FROM hhi_calc
    WHERE ciudad_entidad IS NOT NULL AND TRIM(ciudad_entidad) != ''
),
dane_prep AS (
    SELECT 
        divipola_municipio,
        UPPER(TRIM(nombre_municipio)) as nombre_municipio,
        regexp_replace(
            regexp_replace(translate(UPPER(TRIM(nombre_municipio)), 'ÁÉÍÓÚ', 'AEIOU'), ', D\\\\.C\\\\.', ''),
            ' D\\\\.C\\\\.', ''
        ) as nombre_limpio,
        nombre_departamento,
        ipm_total,
        (etnia_ninguno_count / NULLIF(etnia_ninguno_pct / 100.0, 0)) AS poblacion_estimada,
        monto_total_contratos,
        num_contratos
    FROM base_dane
)
SELECT 
    d.divipola_municipio,
    d.nombre_municipio,
    d.nombre_departamento,
    d.poblacion_estimada,
    d.monto_total_contratos,
    d.num_contratos,
    (d.monto_total_contratos / NULLIF(d.poblacion_estimada, 0)) AS inversion_per_capita,
    d.ipm_total,
    COALESCE(h.hhi_concentracion, 0.0) as hhi_concentracion
FROM dane_prep d
LEFT JOIN hhi_limpio h ON d.nombre_limpio = h.ciudad_limpia
ORDER BY d.monto_total_contratos DESC NULLS LAST
"""

df_final_spark = spark.sql(sql_maestra)

import glob
import shutil

print("[3/3] Exportando los artefactos...")
out_csv_dir = out_csv + "_dir"

# PySpark Writer Directory (nativamente closterizado) a Parquet
df_final_spark.write.mode("overwrite").parquet(out_parquet)

# Escritura de CSV NATIVA de PySpark para esquivar PicklingError de Python 3.14
df_final_spark.write.mode("overwrite").option("header", "true").option("sep", ";").csv(out_csv_dir)

spark.stop()

# Ensamblado del CSV particionado de Spark en un único archivo humano para Excel
try:
    csv_parts = glob.glob(os.path.join(out_csv_dir, "part-*.csv"))
    if csv_parts:
        # Movemos la primera partición (que en nuestro caso de datos en una máquina local será única)
        # o combinamos si hubieran múltiples.
        with open(out_csv, 'w', encoding='utf-8') as outfile:
            for i, part in enumerate(csv_parts):
                with open(part, 'r', encoding='utf-8') as infile:
                    if i != 0:
                        next(infile) # Skip headers para el resto de particiones
                    shutil.copyfileobj(infile, outfile)
        
    # Limpiamos los temporales
    shutil.rmtree(out_csv_dir, ignore_errors=True)
    if os.path.exists(temp_secop): os.remove(temp_secop)
    if os.path.exists(temp_dane): os.remove(temp_dane)
except Exception as e:
    print(f"Nota: No se pudo ensamblar el CSV final automáticamente, revisa la carpeta {out_csv_dir}")

print(f" -> Guardado exitosamente (Carpetas Parquet Spark): {out_parquet}")
print(f" -> Guardado exitosamente (Archivo CSV Único): {out_csv}\n")
print("==================================================")
