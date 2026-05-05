import os
import sys
from pyspark.sql import SparkSession

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv() # Cargar variables del .env si existen

# Verificamos si JAVA_HOME / HADOOP_HOME están configurados
if not os.environ.get('JAVA_HOME'):
    print("Advertencia: JAVA_HOME no está configurado.")
if not os.environ.get('HADOOP_HOME') and os.name == 'nt':
    print("Advertencia: HADOOP_HOME no está configurado (Requerido en Windows).")


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)

print("=======================================================")
print(" PROCESAMIENTO PYSPARK - DATASET MASIVO SECOP (9.6 GB)")
print("=======================================================")

from src.config.settings import settings
csv_masivo = str(settings.SECOP_CSV_PATH)
out_dir = os.path.join(project_root, 'datos', 'HHI_MASIVO_RESULTADOS.csv')

print("[1/3] Iniciando SparkSession con optimización de RAM (6GB Driver)...")
spark = SparkSession.builder \
    .appName("PySpark_Masivo_HHI_10GB") \
    .config("spark.driver.memory", "6g") \
    .config("spark.executor.memory", "6g") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()
    
spark.sparkContext.setLogLevel("ERROR")

print("[2/3] Leyendo archivo de 10 GB y configurando DAG (Lazy Evaluation)...")
# PySpark lee CSVs nativamente rapidísimo si no se intenta inferir esquemas complejos
df = spark.read.csv(csv_masivo, header=True, sep=',', inferSchema=False)

# Mapeamos a una vista SQL
df.createOrReplaceTempView("secop_bruto")

print("[3/3] Desplegando Motor SQL Distribuido para limpieza y cálculo HHI...")

# Este query extrae ciudad, NIT y valor, limpia el caracter de dinero de la columna y hace todas las sumas.
sql_hhi_masivo = """
WITH clean_data AS (
    SELECT 
        UPPER(TRIM(Ciudad)) as ciudad_entidad,
        `Documento Proveedor` as nit_del_proveedor_adjudicado,
        -- Quitar signos peso, comas y puntos, todo el parseo de suciedad:
        CAST(regexp_replace(regexp_replace(`Valor del Contrato`, '[\\$\\,\\.]', ''), '[a-zA-Z]', '') AS DOUBLE) as valor
    FROM secop_bruto
    WHERE Ciudad IS NOT NULL AND `Valor del Contrato` IS NOT NULL
),
totales_municipio AS (
    SELECT 
        ciudad_entidad,
        SUM(valor) as total_municipio
    FROM clean_data
    WHERE valor > 0
    GROUP BY ciudad_entidad
),
sumas_proveedor AS (
    SELECT 
        ciudad_entidad,
        nit_del_proveedor_adjudicado,
        SUM(valor) as suma_proveedor
    FROM clean_data
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
)
SELECT 
    ciudad_entidad, 
    hhi_concentracion 
FROM hhi_calc
ORDER BY hhi_concentracion DESC
"""

df_resultado = spark.sql(sql_hhi_masivo)

print(" -> Forzando ejecución en disco...")
df_resultado.write.mode("overwrite").option("header", "true").option("sep", ";").csv(out_dir)

spark.stop()

# Ensamblado del archivo resultante al igual que en Entregables
import glob
import shutil

try:
    csv_parts = glob.glob(os.path.join(out_dir, "part-*.csv"))
    final_file = out_dir + "_final.csv"
    if csv_parts:
        with open(final_file, 'w', encoding='utf-8') as outfile:
            for i, part in enumerate(csv_parts):
                with open(part, 'r', encoding='utf-8') as infile:
                    if i != 0: next(infile)
                    shutil.copyfileobj(infile, outfile)
        shutil.rmtree(out_dir, ignore_errors=True)
        print(f"\n¡ÉXITO ROTUNDO! Archivo final ensamblado en: {final_file}")
except Exception as e:
    print(f"\nCSV generado particionado en: {out_dir}")

print("=======================================================")
