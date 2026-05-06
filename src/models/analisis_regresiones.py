import os
import sys

from dotenv import load_dotenv
load_dotenv() # Cargar variables del .env

# Forzar la inclusión de las variables de entorno de Java y Hadoop en la sesión actual
if not os.environ.get('JAVA_HOME'):
    print("Advertencia: JAVA_HOME no está configurado.")
if not os.environ.get('HADOOP_HOME') and os.name == 'nt':
    print("Advertencia: HADOOP_HOME no está configurado (Requerido en Windows para PySpark).")


import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, log1p, when
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression, GeneralizedLinearRegression
from pyspark.ml.classification import LogisticRegression

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Inicializar PySpark localmente
    spark = SparkSession.builder \
        .appName("AnalisisRegresionesSECOP") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
        
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    file_path = os.path.join(project_root, "datos", "cruce_secop_dane_sprint2.parquet")
    
    logger.info(f"Cargando dataset con PySpark: {file_path}")
    
    try:
        df = spark.read.parquet(file_path)
    except Exception as e:
        logger.error(f"Error cargando el archivo parquet en PySpark: {e}")
        spark.stop()
        return
    
    # -----------------------------------------------------
    # 1. PREPARACIÓN DE VARIABLES
    # -----------------------------------------------------
    logger.info("Preparando columnas e indicadores derivados en PySpark...")
    
    # Buscar dinámicamente la columna NBI
    cols = df.columns
    nbi_col_rara = [c for c in cols if 'prop_de_personas_en_nbi' in c][0]
    df = df.withColumnRenamed(nbi_col_rara, 'nbi_proporcion')
    
    # Castear todas las métricas numéricas cruciales a Double
    columnas_numericas = ['etnia_ninguno_count', 'etnia_ninguno_pct', 'monto_total_contratos', 'nbi_proporcion', 'ipm_total', 'num_contratos']
    for c in columnas_numericas:
        if c in df.columns:
            df = df.withColumn(c, col(c).cast("double"))
        
    df = df.withColumn("etnia_ninguno_pct_decimal", col("etnia_ninguno_pct") / 100.0)
    df = df.withColumn("etnia_ninguno_pct_decimal", when(col("etnia_ninguno_pct_decimal") == 0, None).otherwise(col("etnia_ninguno_pct_decimal")))
    df = df.withColumn("poblacion_estimada", col("etnia_ninguno_count") / col("etnia_ninguno_pct_decimal"))
    
    df = df.withColumn("inversion_per_capita", col("monto_total_contratos") / col("poblacion_estimada"))
    df = df.withColumn("log_inversion_pc", log1p(col("inversion_per_capita")))
    
    df_clean = df.dropna(subset=['log_inversion_pc', 'ipm_total', 'nbi_proporcion', 'num_contratos'])
    
    median_inversion = df_clean.approxQuantile("inversion_per_capita", [0.5], 0.01)[0]
    df_clean = df_clean.withColumn("alta_inversion", when(col("inversion_per_capita") > median_inversion, 1.0).otherwise(0.0))

    assembler = VectorAssembler(inputCols=["ipm_total", "nbi_proporcion"], outputCol="features", handleInvalid="skip")
    df_model = assembler.transform(df_clean)

    # -----------------------------------------------------
    # 2. MODELO OLS: Inversión Per Cápita vs IPM y NBI
    # -----------------------------------------------------
    logger.info("\n=== MODELO 1: OLS (Linear Regression) ===")
    lr = LinearRegression(featuresCol="features", labelCol="log_inversion_pc")
    lr_model = lr.fit(df_model)
    
    print(">> Resultados OLS:")
    print(" - Coeficientes (IPM, NBI):", lr_model.coefficients)
    print(" - Intercepto:            ", lr_model.intercept)
    print(" - R-squared:             ", lr_model.summary.r2)
    try:
        print(" - P-values (Int., IPM, NBI):", lr_model.summary.pValues)
    except Exception:
        pass

    # -----------------------------------------------------
    # 3. MODELO BINOMIAL NEGATIVA / POISSON: Cantidad de Contratos
    # -----------------------------------------------------
    logger.info("\n=== MODELO 2: CONTEO (Poisson GLM) ===")
    glr_poisson = GeneralizedLinearRegression(family="poisson", link="log", featuresCol="features", labelCol="num_contratos")
    glr_poisson_model = glr_poisson.fit(df_model)
    
    print("\n>> Resultados Poisson:")
    print(" - Coeficientes (IPM, NBI):", glr_poisson_model.coefficients)
    print(" - Intercepto:            ", glr_poisson_model.intercept)
    print(" - P-values (Int., IPM, NBI):", glr_poisson_model.summary.pValues)

    # -----------------------------------------------------
    # 4. MODELO LOGIT: Probabilidad de Alta Inversión
    # -----------------------------------------------------
    logger.info("\n=== MODELO 3: REGRESIÓN LOGÍSTICA ===")
    logit = LogisticRegression(featuresCol="features", labelCol="alta_inversion")
    logit_model = logit.fit(df_model)
    
    print("\n>> Resultados Logit:")
    print(" - Coeficientes (IPM, NBI):", logit_model.coefficientMatrix)
    print(" - Intercepto:            ", logit_model.interceptVector)
    
    spark.stop()

if __name__ == "__main__":
    main()
