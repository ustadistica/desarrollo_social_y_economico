import os
import requests
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, lower, lpad, lit, when
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, BooleanType, IntegerType
)
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.impute import KNNImputer

def create_spark_session():
    return SparkSession.builder \
        .appName("Cruce_SECOP_DANE_Pipeline") \
        .config("spark.driver.memory", "8g") \
        .config("spark.executor.memory", "8g") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
        .getOrCreate()

# ==========================================
# CAPA BRONCE
# ==========================================
def fetch_secop_api(spark, years=range(2018, 2026)):
    base_url = "https://www.datos.gov.co/resource/rpmr-utcd.json"
    limit = 50000
    
    dfs = []
    for year in years:
        offset = 0
        while True:
            url = f"{base_url}?$limit={limit}&$offset={offset}&$where=fecha_de_publicacion_del >= '{year}-01-01T00:00:00' AND fecha_de_publicacion_del <= '{year}-12-31T23:59:59'"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if not data:
                    break
                df_chunk = pd.DataFrame(data)
                dfs.append(df_chunk)
                offset += limit
            else:
                print(f"Error cargando API para el año {year}: {response.status_code}")
                break
                
    if not dfs:
        return None
    pdf = pd.concat(dfs, ignore_index=True)
    
    # Asegurar tipos básicos antes de pasar a Spark para evitar errores
    pdf['precio_base'] = pd.to_numeric(pdf.get('precio_base', 0), errors='coerce').fillna(0)
    pdf['valor_total_adjudicacion'] = pd.to_numeric(pdf.get('valor_total_adjudicacion', 0), errors='coerce').fillna(0)
    pdf['anio'] = pd.to_numeric(pdf.get('anio', 0), errors='coerce').fillna(0).astype(int)
    
    return spark.createDataFrame(pdf)

def fetch_api_all(url_base):
    dfs = []
    limit = 50000
    offset = 0
    while True:
        url = f"{url_base}?$limit={limit}&$offset={offset}"
        resp = requests.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if not data:
                break
            dfs.append(pd.DataFrame(data))
            offset += limit
        else:
            break
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    return pd.DataFrame()

def load_dane_data(spark):
    # IPM (CNPV)
    pdf_ipm = pd.read_excel("datos/dane_2018/ipm.xlsx")
    if 'anio' in pdf_ipm.columns:
        pdf_ipm = pdf_ipm.drop(columns=['anio'])
    df_ipm = spark.createDataFrame(pdf_ipm)
    
    # NBI (CNPV)
    df_nbi = spark.read.parquet("datos/dane_2018/nbi_municipios_2018.parquet")
    if 'anio' in df_nbi.columns:
        df_nbi = df_nbi.drop("anio")
        
    # ETNIA (CNPV)
    df_etnia = spark.read.parquet("datos/etnia_checkpoint.parquet")
    if 'anio' in df_etnia.columns:
        df_etnia = df_etnia.drop("anio")
        
    # EMICRON / CENU
    pdf_emicron = fetch_api_all("https://www.datos.gov.co/resource/r2bh-bfag.json")
    if not pdf_emicron.empty:
        if 'divipola_municipio' in pdf_emicron.columns:
            pdf_emicron['divipola_municipio'] = pdf_emicron['divipola_municipio'].astype(str).str.zfill(5)
            
        if 'anio' in pdf_emicron.columns:
            pdf_emicron['anio'] = pd.to_numeric(pdf_emicron['anio'], errors='coerce').fillna(0).astype(int)
        else:
            date_col = next((c for c in pdf_emicron.columns if 'fecha' in c.lower()), None)
            if date_col:
                pdf_emicron['anio'] = pd.to_datetime(pdf_emicron[date_col], errors='coerce').dt.year.fillna(2024).astype(int)
            else:
                pdf_emicron['anio'] = 2024
    # Crear con dummy en caso de venir vacio temporalmente para schema match
    df_emicron = spark.createDataFrame(pdf_emicron) if not pdf_emicron.empty else spark.createDataFrame(pd.DataFrame({'divipola_municipio': [], 'anio': []}))
    
    # TerriData
    pdf_terridata = fetch_api_all("https://www.datos.gov.co/resource/64cq-xb2k.json")
    if not pdf_terridata.empty:
        for col_name in ['código entidad territorial', 'codigo_entidad_territorial', 'Código Entidad Territorial']:
            if col_name in pdf_terridata.columns:
                pdf_terridata = pdf_terridata.rename(columns={col_name: 'divipola_municipio'})
                break
                
        if 'divipola_municipio' in pdf_terridata.columns:
            pdf_terridata['divipola_municipio'] = pdf_terridata['divipola_municipio'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)
            
        if 'anio' in pdf_terridata.columns:
            pdf_terridata['anio'] = pd.to_numeric(pdf_terridata['anio'], errors='coerce').fillna(0).astype(int)
        else:
            # Asegurar que TerriData siempre tenga columna anio
            year_col = next((c for c in pdf_terridata.columns if 'año' in c.lower() or 'year' in c.lower() or 'anio' in c.lower()), None)
            date_col = next((c for c in pdf_terridata.columns if 'fecha' in c.lower()), None)
            if year_col:
                pdf_terridata['anio'] = pd.to_numeric(pdf_terridata[year_col], errors='coerce').fillna(0).astype(int)
            elif date_col:
                pdf_terridata['anio'] = pd.to_datetime(pdf_terridata[date_col], errors='coerce').dt.year.fillna(0).astype(int)
            else:
                # Si no hay ninguna columna de año, usar el año más reciente disponible
                pdf_terridata['anio'] = 2024
    df_terridata = spark.createDataFrame(pdf_terridata) if not pdf_terridata.empty else spark.createDataFrame(pd.DataFrame({'divipola_municipio': [], 'anio': []}))
        
    return df_ipm, df_nbi, df_etnia, df_emicron, df_terridata

# ==========================================
# CAPA PLATA
# ==========================================
def process_silver_layer(df_secop, df_ipm, df_nbi, df_etnia, df_emicron, df_terridata):
    # Estandarización de SECOP
    df_s = df_secop.dropDuplicates()
    for c in df_s.columns:
        df_s = df_s.withColumn(c, trim(col(c)))
        
    if "ordenentidad" in df_s.columns:
        df_s = df_s.withColumn("es_nacional", col("ordenentidad") == "Nacional")
    else:
        df_s = df_s.withColumn("es_nacional", lit(False))
        
    if "divipola_municipio" in df_s.columns:
        df_s = df_s.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0'))
        
    # Helper para evitar columnas duplicadas
    def rename_cols(df, keys, suffix):
        for c in df.columns:
            if c not in keys:
                df = df.withColumnRenamed(c, f"{c}_{suffix}")
        return df

    # Estandarización de DANE y Renombres
    df_ipm = rename_cols(df_ipm.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0')), ["divipola_municipio"], "ipm")
    df_nbi = rename_cols(df_nbi.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0')), ["divipola_municipio"], "nbi")
    df_etnia = rename_cols(df_etnia.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0')), ["divipola_municipio"], "etnia")
    
    if "divipola_municipio" in df_emicron.columns:
        df_emicron = df_emicron.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0'))
    df_emicron = rename_cols(df_emicron, ["divipola_municipio", "anio"], "emicron")
    
    if "divipola_municipio" in df_terridata.columns:
        df_terridata = df_terridata.withColumn("divipola_municipio", lpad(col("divipola_municipio").cast("string"), 5, '0'))
    df_terridata = rename_cols(df_terridata, ["divipola_municipio", "anio"], "terridata")

    # Cruces (CNPV solo por municipio)
    df_joined = df_s.join(df_ipm, ["divipola_municipio"], "left") \
                    .join(df_nbi, ["divipola_municipio"], "left") \
                    .join(df_etnia, ["divipola_municipio"], "left")
                    
    # Dinámicos (por municipio y año)
    if "divipola_municipio" in df_emicron.columns and "anio" in df_emicron.columns:
        df_joined = df_joined.join(df_emicron, ["divipola_municipio", "anio"], "left")
    if "divipola_municipio" in df_terridata.columns and "anio" in df_terridata.columns:
        df_joined = df_joined.join(df_terridata, ["divipola_municipio", "anio"], "left")
                    
    df_nacional = df_joined.filter(col("es_nacional") == True)
    df_territorial = df_joined.filter(col("es_nacional") == False)
    
    return df_nacional, df_territorial

# ==========================================
# CAPA ORO
# ==========================================
def detect_and_treat_outliers_pandas(pdf: pd.DataFrame) -> pd.DataFrame:
    if len(pdf) < 5:
        # No hay suficientes datos para correr SVM o KNN apropiadamente
        pdf['atipico_isolation_forest'] = False
        pdf['score_isolation_forest'] = 1.0
        pdf['atipico_lof'] = False
        pdf['score_lof'] = 1.0
        pdf['atipico_svm'] = False
        pdf['score_svm'] = 1.0
        pdf['es_atipico'] = False
        pdf['tipo_atipico'] = 'normal'
        pdf['metodo_tratamiento'] = 'sin_tratamiento'
        pdf['valor_tratado_precio_base'] = pdf['precio_base']
        pdf['valor_tratado_adjudicacion'] = pdf['valor_total_adjudicacion']
        return pdf

    features = ['precio_base', 'valor_total_adjudicacion']
    X = pdf[features].fillna(0).values

    # Modelos de Detección
    if_model = IsolationForest(contamination=0.05, random_state=42)
    lof_model = LocalOutlierFactor(n_neighbors=20, contamination=0.05)
    svm_model = OneClassSVM(kernel='rbf', nu=0.05)

    preds_if = if_model.fit_predict(X)
    scores_if = if_model.decision_function(X)
    
    preds_lof = lof_model.fit_predict(X)
    scores_lof = lof_model.negative_outlier_factor_
    
    preds_svm = svm_model.fit_predict(X)
    scores_svm = svm_model.decision_function(X)

    pdf['atipico_isolation_forest'] = (preds_if == -1)
    pdf['score_isolation_forest'] = scores_if
    pdf['atipico_lof'] = (preds_lof == -1)
    pdf['score_lof'] = scores_lof
    pdf['atipico_svm'] = (preds_svm == -1)
    pdf['score_svm'] = scores_svm

    # Votación
    anom_sum = pdf['atipico_isolation_forest'].astype(int) + \
               pdf['atipico_lof'].astype(int) + \
               pdf['atipico_svm'].astype(int)
               
    pdf['es_atipico'] = (anom_sum >= 2)
    
    # Tipo Atípico Alto/Bajo
    median_pb = pdf['precio_base'].median()
    median_va = pdf['valor_total_adjudicacion'].median()
    
    def get_tipo(row):
        if not row['es_atipico']: return 'normal'
        if row['precio_base'] > median_pb or row['valor_total_adjudicacion'] > median_va:
            return 'alto'
        return 'bajo'
        
    pdf['tipo_atipico'] = pdf.apply(get_tipo, axis=1)

    # Tratamiento (Winsorización -> KNN)
    pdf['valor_tratado_precio_base'] = pdf['precio_base']
    pdf['valor_tratado_adjudicacion'] = pdf['valor_total_adjudicacion']
    pdf['metodo_tratamiento'] = 'sin_tratamiento'
    
    # Winsorización
    p05_pb = pdf['precio_base'].quantile(0.05)
    p95_pb = pdf['precio_base'].quantile(0.95)
    p05_va = pdf['valor_total_adjudicacion'].quantile(0.05)
    p95_va = pdf['valor_total_adjudicacion'].quantile(0.95)

    is_outlier = pdf['es_atipico']
    
    pdf.loc[is_outlier, 'valor_tratado_precio_base'] = np.clip(pdf.loc[is_outlier, 'precio_base'], p05_pb, p95_pb)
    pdf.loc[is_outlier, 'valor_tratado_adjudicacion'] = np.clip(pdf.loc[is_outlier, 'valor_total_adjudicacion'], p05_va, p95_va)
    pdf.loc[is_outlier, 'metodo_tratamiento'] = 'winsorizado'

    # Imputación KNN para los que después de Winsorización sigan siendo atípicos.
    # ¿Cómo sabemos si siguen siendo atípicos? 
    # Podemos re-evaluar con un IF simple de validación.
    X_treated = pdf[['valor_tratado_precio_base', 'valor_tratado_adjudicacion']].values
    still_outlier_preds = if_model.fit_predict(X_treated)
    still_anomalous_mask = is_outlier & (still_outlier_preds == -1)

    if still_anomalous_mask.sum() > 0:
        pdf.loc[still_anomalous_mask, 'valor_tratado_precio_base'] = np.nan
        pdf.loc[still_anomalous_mask, 'valor_tratado_adjudicacion'] = np.nan
        pdf.loc[still_anomalous_mask, 'metodo_tratamiento'] = 'imputado_knn'
        
        imputer = KNNImputer(n_neighbors=5)
        # We need identifying features for the imputer technically, but for this PDF partition it corresponds to the same group.
        # Adding some noise to avoid identical neighbor issues
        imputed_data = imputer.fit_transform(pdf[['valor_tratado_precio_base', 'valor_tratado_adjudicacion']])
        
        pdf['valor_tratado_precio_base'] = imputed_data[:, 0]
        pdf['valor_tratado_adjudicacion'] = imputed_data[:, 1]

    return pdf

def process_gold_layer(df):
    group_cols = ['ordenentidad', 'anio']
    
    # Validate missing columns to avoid failing
    # In some datasets 'ordenentidad' could be null, replace 
    df = df.fillna({'ordenentidad': 'Desconocido', 'anio': 2018})
    
    # Define returning schema from Pandas UDF
    out_schema = StructType(df.schema.fields + [
        StructField("atipico_isolation_forest", BooleanType()),
        StructField("score_isolation_forest", DoubleType()),
        StructField("atipico_lof", BooleanType()),
        StructField("score_lof", DoubleType()),
        StructField("atipico_svm", BooleanType()),
        StructField("score_svm", DoubleType()),
        StructField("es_atipico", BooleanType()),
        StructField("tipo_atipico", StringType()),
        StructField("valor_tratado_precio_base", DoubleType()),
        StructField("valor_tratado_adjudicacion", DoubleType()),
        StructField("metodo_tratamiento", StringType())
    ])

    return df.groupBy(*group_cols).applyInPandas(detect_and_treat_outliers_pandas, schema=out_schema)

# ==========================================
# MAIN ROUTINE
# ==========================================
def main():
    spark = create_spark_session()
    
    print("Iniciando Capa Bronce: Extracción de SECOP y DANE...")
    df_secop = fetch_secop_api(spark)
    if df_secop is None:
        print("No se pudieron obtener datos de SECOP.")
        return
        
    df_ipm, df_nbi, df_etnia, df_emicron, df_terridata = load_dane_data(spark)
    
    print("Iniciando Capa Plata: Transformación y Cruce...")
    df_nacional, df_territorial = process_silver_layer(df_secop, df_ipm, df_nbi, df_etnia, df_emicron, df_terridata)
    
    print("Iniciando Capa Oro: Modelos No Lineales en DF Nacional...")
    df_gold_nacional = process_gold_layer(df_nacional)
    
    print("Iniciando Capa Oro: Modelos No Lineales en DF Territorial...")
    df_gold_territorial = process_gold_layer(df_territorial)
    
    # Reportes atipicos
    df_reporte_nac = df_gold_nacional.filter(col("es_atipico") == True)
    df_reporte_ter = df_gold_territorial.filter(col("es_atipico") == True)
    df_reporte = df_reporte_nac.unionByName(df_reporte_ter, allowMissingColumns=True)
    
    # Seleccionar columnas relevantes para el reporte
    select_cols = [
        "divipola_municipio", "anio", "precio_base", "valor_total_adjudicacion", 
        "valor_tratado_precio_base", "valor_tratado_adjudicacion",
        "atipico_isolation_forest", "atipico_lof", "atipico_svm", "metodo_tratamiento"
    ]
    df_reporte_final = df_reporte.select(*[c for c in select_cols if c in df_reporte.columns])
    
    print("Guardando archivos finales en datos/processed (Compresión Snappy)...")
    os.makedirs("datos/processed", exist_ok=True)
    
    df_gold_nacional.write.mode("overwrite").parquet("datos/processed/cruce_secop_dane_nacional_2018_2025.parquet", compression="snappy")
    df_gold_territorial.write.mode("overwrite").parquet("datos/processed/cruce_secop_dane_territorial_2018_2025.parquet", compression="snappy")
    df_reporte_final.write.mode("overwrite").parquet("datos/processed/reporte_atipicos_2018_2025.parquet", compression="snappy")
    
    print("Pipeline ejecutado exitosamente.")

if __name__ == "__main__":
    main()
