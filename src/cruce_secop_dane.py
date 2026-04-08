import os
import requests
import pandas as pd
import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, lpad, trim, when

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# CONSTANTES Y URLS
# ==========================================

# SECOP Integrado (contiene SECOP I y SECOP II, diferenciados por columna 'origen')
SECOP_INTEGRADO_URL = "https://www.datos.gov.co/resource/rpmr-utcd.json?$limit=50000"

# Rutas locales de archivos DANE
RAW_DIR = os.path.join("datos", "raw")
DANE_DIR = os.path.join("datos", "dane_2018")

IPM_FILE       = os.path.join(DANE_DIR, "ipm.xlsx")
NBI_FILE       = os.path.join(DANE_DIR, "nbi_municipios_2018.parquet")
ETNIA_FILE     = os.path.join("datos", "etnia_checkpoint.parquet")
DIVIPOLA_FILE  = os.path.join(DANE_DIR, "divipola_municipios.parquet")

OUTPUT_DIR  = os.path.join("datos", "processed")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "cruce_secop_dane.parquet")


# ==========================================
# SPARK
# ==========================================

def create_spark_session() -> SparkSession:
    """Inicializa la sesión de Spark."""
    return SparkSession.builder \
        .appName("Cruce_SECOP_DANE") \
        .config("spark.driver.memory", "6g") \
        .getOrCreate()


# ==========================================
# DESCARGA SECOP INTEGRADO
# ==========================================

def download_secop_integrado() -> pd.DataFrame:
    """
    Descarga el SECOP Integrado desde la API pública de datos.gov.co.
    Contiene registros de SECOP I y SECOP II diferenciados por la columna 'origen'.
    """
    try:
        logger.info(f"Descargando SECOP Integrado desde {SECOP_INTEGRADO_URL}...")
        resp = requests.get(SECOP_INTEGRADO_URL, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data)
        logger.info(f"SECOP Integrado descargado. {len(df)} registros.")

        # Mostrar distribución de origen (SECOP I vs SECOP II)
        if 'origen' in df.columns:
            logger.info(f"Distribución por origen:\n{df['origen'].value_counts()}")

        return df
    except Exception as e:
        logger.error(f"Error en descarga de SECOP Integrado: {e}")
        return pd.DataFrame()


# ==========================================
# LIMPIEZA
# ==========================================

def clean_spark_df(spark_df, divipola_col=None):
    """
    Aplica limpieza profesional al DataFrame de Spark:
    - Elimina duplicados
    - Trim y minúsculas en strings
    - Estandariza DIVIPOLA a 5 dígitos con lpad
    - Elimina nulos en la llave primaria
    """
    if spark_df is None:
        return None

    spark_df = spark_df.dropDuplicates()

    for campo, dtype in spark_df.dtypes:
        if dtype == 'string':
            spark_df = spark_df.withColumn(campo, trim(lower(col(campo))))

    if divipola_col and divipola_col in spark_df.columns:
        spark_df = spark_df.dropna(subset=[divipola_col])
        spark_df = spark_df.withColumn(
            divipola_col,
            lpad(col(divipola_col), 5, "0")
        )

    return spark_df


# ==========================================
# CARGA DANE
# ==========================================

def load_nbi(spark) -> object:
    """Carga el archivo NBI que incluye componente de cobertura de servicios."""
    if not os.path.exists(NBI_FILE):
        logger.warning(f"Archivo NBI no encontrado: {NBI_FILE}")
        return None

    logger.info(f"Cargando NBI desde: {NBI_FILE}")
    pdf = pd.read_parquet(NBI_FILE)

    # Estandarizar llave DIVIPOLA
    for col_name in pdf.columns:
        if 'municipio' in col_name.lower() or 'divipola' in col_name.lower() or 'codigo' in col_name.lower():
            pdf = pdf.rename(columns={col_name: 'divipola_municipio'})
            break

    pdf['divipola_municipio'] = pdf['divipola_municipio'].astype(str).str.zfill(5)

    # Renombrar columnas para evitar ambigüedad
    pdf.columns = [
        'divipola_municipio' if c == 'divipola_municipio' else f"nbi_{c}"
        for c in pdf.columns
    ]

    df = spark.createDataFrame(pdf)
    return clean_spark_df(df, 'divipola_municipio')


def load_ipm(spark) -> object:
    """Carga el archivo IPM desde Excel."""
    if not os.path.exists(IPM_FILE):
        logger.warning(f"Archivo IPM no encontrado: {IPM_FILE}")
        return None

    logger.info(f"Cargando IPM desde: {IPM_FILE}")
    try:
        pdf = pd.read_excel(IPM_FILE, sheet_name='IPM_Municipios', skiprows=12, dtype=str)
    except Exception:
        pdf = pd.read_excel(IPM_FILE, skiprows=12, dtype=str)

    # Buscar columna de código municipio
    pdf.columns = [str(c).strip() for c in pdf.columns]
    key_col = None
    for c in pdf.columns:
        if 'municipio' in c.lower() or 'codigo' in c.lower() or 'divipola' in c.lower():
            key_col = c
            break
    if key_col is None:
        key_col = pdf.columns[1]  # Fallback: segunda columna

    pdf = pdf.rename(columns={key_col: 'divipola_municipio'})
    pdf['divipola_municipio'] = pdf['divipola_municipio'].astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)
    pdf = pdf.dropna(subset=['divipola_municipio'])

    # Buscar columna de valor IPM total
    ipm_col = None
    for c in pdf.columns:
        if 'total' in c.lower() or 'ipm' in c.lower():
            ipm_col = c
            break
    if ipm_col is None:
        ipm_col = pdf.columns[3]  # Fallback: cuarta columna

    pdf = pdf[['divipola_municipio', ipm_col]].rename(columns={ipm_col: 'ipm_total'})
    pdf['ipm_total'] = pd.to_numeric(pdf['ipm_total'], errors='coerce')

    df = spark.createDataFrame(pdf)
    return clean_spark_df(df, 'divipola_municipio')


def load_etnia(spark) -> object:
    """Carga composición étnica desde checkpoint."""
    if not os.path.exists(ETNIA_FILE):
        logger.warning(f"Archivo étnia no encontrado: {ETNIA_FILE}")
        return None

    logger.info(f"Cargando composición étnica desde: {ETNIA_FILE}")
    pdf = pd.read_parquet(ETNIA_FILE)
    pdf['divipola_municipio'] = pdf['divipola_municipio'].astype(str).str.zfill(5)

    df = spark.createDataFrame(pdf)
    return clean_spark_df(df, 'divipola_municipio')


def load_divipola(spark) -> object:
    """Carga tabla DIVIPOLA para mapeo de municipios."""
    if not os.path.exists(DIVIPOLA_FILE):
        logger.warning(f"Archivo DIVIPOLA no encontrado: {DIVIPOLA_FILE}")
        return None

    logger.info(f"Cargando DIVIPOLA desde: {DIVIPOLA_FILE}")
    pdf = pd.read_parquet(DIVIPOLA_FILE)
    pdf.columns = [str(c).strip().lower() for c in pdf.columns]

    # Estandarizar código municipio
    for c in pdf.columns:
        if 'municipio' in c or 'divipola' in c or 'codigo' in c:
            pdf = pdf.rename(columns={c: 'divipola_municipio'})
            break

    pdf['divipola_municipio'] = pdf['divipola_municipio'].astype(str).str.zfill(5)
    df = spark.createDataFrame(pdf)
    return clean_spark_df(df, 'divipola_municipio')


# ==========================================
# MAIN
# ==========================================

def main():
    spark = create_spark_session()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("=========================================")
    logger.info("  INICIANDO CRUCE SECOP I + II CON DANE  ")
    logger.info("=========================================")

    # 1. Descargar SECOP Integrado (I + II)
    df_secop_pd = download_secop_integrado()
    if df_secop_pd.empty:
        logger.error("No se pudo descargar el SECOP Integrado. Abortando.")
        return

    # Estandarizar llave de municipio en SECOP
    # La columna de municipio en SECOP Integrado es 'municipio_entidad' o 'codigo_entidad_en_secop'
    llave_secop = None
    for posible in ['codigo_entidad_en_secop', 'municipio_entidad', 'codigo_municipio', 'divipola_municipio']:
        if posible in df_secop_pd.columns:
            llave_secop = posible
            break

    if llave_secop is None:
        logger.warning("No se encontró columna de municipio en SECOP. Usando primera columna disponible.")
        llave_secop = df_secop_pd.columns[0]

    df_secop_pd = df_secop_pd.rename(columns={llave_secop: 'divipola_municipio'})
    df_secop_pd['divipola_municipio'] = df_secop_pd['divipola_municipio'].astype(str).str.zfill(5)

    # Agregar columna indicadora de origen (SECOP I o SECOP II)
    if 'origen' not in df_secop_pd.columns:
        df_secop_pd['origen'] = 'DESCONOCIDO'

    logger.info(f"SECOP Integrado: {len(df_secop_pd)} registros.")

    secop_spark = spark.createDataFrame(df_secop_pd)
    secop_limpio = clean_spark_df(secop_spark, 'divipola_municipio')

    # 2. Cargar indicadores DANE
    logger.info("Cargando indicadores DANE...")
    nbi_df    = load_nbi(spark)
    ipm_df    = load_ipm(spark)
    etnia_df  = load_etnia(spark)

    # 3. Consolidar DANE en un solo DataFrame
    logger.info("Consolidando indicadores DANE...")
    dane_consolidado = nbi_df

    if ipm_df is not None:
        dane_consolidado = dane_consolidado.join(ipm_df, on='divipola_municipio', how='left')
        logger.info("IPM agregado al consolidado DANE.")

    if etnia_df is not None:
        dane_consolidado = dane_consolidado.join(etnia_df, on='divipola_municipio', how='left')
        logger.info("Composición étnica agregada al consolidado DANE.")

    # 4. Cruce SECOP con DANE (Left Join por divipola_municipio)
    logger.info("Realizando Left Join SECOP con DANE por divipola_municipio...")

    if dane_consolidado is not None:
        # Evitar columnas duplicadas
        cols_secop = set(secop_limpio.columns) - {'divipola_municipio'}
        cols_dane  = set(dane_consolidado.columns) - {'divipola_municipio'}
        duplicadas = cols_secop.intersection(cols_dane)

        for c in duplicadas:
            dane_consolidado = dane_consolidado.withColumnRenamed(c, f"{c}_dane")

        resultado = secop_limpio.join(dane_consolidado, on='divipola_municipio', how='left')
    else:
        logger.warning("No hay datos DANE disponibles. El resultado solo tendrá SECOP.")
        resultado = secop_limpio

    # 5. Guardar resultado
    count = resultado.count()
    logger.info(f"Guardando {count} registros en: {OUTPUT_FILE}")
    resultado.write.parquet(OUTPUT_FILE, mode="overwrite", compression="snappy")

    logger.info("=========================================")
    logger.info("  ✅ CRUCE COMPLETADO Y GUARDADO         ")
    logger.info("  ⚠️  NO HACER MERGE A MAIN              ")
    logger.info("=========================================")

    spark.stop()


if __name__ == "__main__":
    main()
