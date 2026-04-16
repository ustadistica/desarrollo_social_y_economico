"""
src/cruce_secop_dane.py
=======================
Cruce SECOP II con indicadores DANE 2018-2025
Motor: DuckDB (sin PySpark) - archivos locales
Muestra representativa: 50,000 registros por año
Rama: feature/cruce-secop-dane
"""

import os
import pandas as pd
import numpy as np
import duckdb
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.svm import OneClassSVM
from sklearn.impute import KNNImputer

# ==========================================
# CONFIGURACION
# ==========================================
SECOP_II_RAW  = os.path.join("datos", "bronze", "secop", "secop_ii_20260323_204019_raw.parquet")
SECOP_NUEVOS  = os.path.join("datos", "secop_nuevos1.parquet")
IPM_FILE      = os.path.join("datos", "dane_2018", "ipm.xlsx")
NBI_FILE      = os.path.join("datos", "dane_2018", "nbi_municipios_2018.parquet")
ETNIA_FILE    = os.path.join("datos", "etnia_checkpoint.parquet")
PROCESSED_DIR = os.path.join("datos", "processed")

YEARS         = range(2018, 2026)
SAMPLE_PER_YEAR = 50000  # muestra representativa por año


# ==========================================
# UTILIDADES
# ==========================================
def zfill5(s):
    return s.astype(str).str.replace(r'\.0$', '', regex=True).str.zfill(5)


# ==========================================
# CAPA BRONCE
# ==========================================
def bronze_secop():
    """Carga muestra representativa de SECOP por año."""
    print("Cargando SECOP II (muestra representativa por año)...")
    
    df_raw = pd.read_parquet(SECOP_II_RAW)
    
    # Extraer año de Fecha de Firma
    df_raw['anio'] = pd.to_datetime(df_raw['Fecha de Firma'], errors='coerce').dt.year
    
    # Filtrar 2018-2025
    df_raw = df_raw[df_raw['anio'].between(2018, 2025)].copy()
    
    # Muestra representativa por año
    dfs = []
    for year in YEARS:
        df_year = df_raw[df_raw['anio'] == year]
        if len(df_year) > SAMPLE_PER_YEAR:
            df_year = df_year.sample(n=SAMPLE_PER_YEAR, random_state=42)
        dfs.append(df_year)
        print(f"  {year}: {len(df_year)} registros")
    
    df_secop = pd.concat(dfs, ignore_index=True)
    
    # Estandarizar columnas
    df_secop = df_secop.rename(columns={
        'Nombre Entidad':    'nombre_entidad',
        'Nit Entidad':       'nit_entidad',
        'Departamento':      'departamento_entidad',
        'Ciudad':            'municipio_entidad',
        'Sector':            'sector',
        'ID Contrato':       'id_contrato',
        'Estado Contrato':   'estado_contrato',
        'Tipo de Contrato':  'tipo_de_contrato',
        'Modalidad de Contratacion': 'modalidad_contratacion',
        'Fecha de Firma':    'fecha_de_firma',
        'Valor del Contrato':'precio_base',
    })
    
    df_secop['precio_base'] = pd.to_numeric(df_secop['precio_base'], errors='coerce').fillna(0)
    df_secop['valor_total_adjudicacion'] = df_secop['precio_base']
    df_secop['origen'] = 'SECOPII'
    
    # Agregar secop_nuevos (2025)
    if os.path.exists(SECOP_NUEVOS):
        df_nuevos = pd.read_parquet(SECOP_NUEVOS)
        df_nuevos['anio'] = pd.to_datetime(
            df_nuevos.get('fecha_de_publicacion_del', pd.NaT), errors='coerce'
        ).dt.year.fillna(2025).astype(int)
        df_nuevos['origen'] = 'SECOP_NUEVOS'
        if 'precio_base' not in df_nuevos.columns and 'valor_contrato' in df_nuevos.columns:
            df_nuevos['precio_base'] = pd.to_numeric(df_nuevos['valor_contrato'], errors='coerce').fillna(0)
        df_nuevos['valor_total_adjudicacion'] = df_nuevos.get('precio_base', 0)
        df_secop = pd.concat([df_secop, df_nuevos], ignore_index=True)
        print(f"  secop_nuevos1 (2025): {len(df_nuevos)} registros")
    
    # es_nacional
    if 'ordenentidad' in df_secop.columns:
        df_secop['es_nacional'] = df_secop['ordenentidad'].str.strip().str.lower() == 'nacional'
    elif 'sector' in df_secop.columns:
        nacionales = ['defensa', 'hacienda', 'presidencia', 'interior', 'justicia',
                      'relaciones exteriores', 'comercio', 'agricultura', 'minas',
                      'salud', 'educacion', 'transporte', 'vivienda', 'trabajo',
                      'tecnologias', 'ambiente', 'cultura', 'ciencia']
        df_secop['es_nacional'] = df_secop['sector'].str.lower().str.contains(
            '|'.join(nacionales), na=False
        )
    else:
        df_secop['es_nacional'] = False
    
    # DIVIPOLA desde municipio_entidad
    if 'municipio_entidad' in df_secop.columns:
        df_secop['divipola_municipio'] = zfill5(df_secop['municipio_entidad'].astype(str))
    else:
        df_secop['divipola_municipio'] = '00000'
    
    print(f"SECOP total: {len(df_secop)} registros")
    return df_secop


def bronze_dane():
    """Carga indicadores DANE locales."""
    print("Cargando IPM...")
    df_ipm = pd.read_excel(IPM_FILE)
    if 'anio' in df_ipm.columns:
        df_ipm = df_ipm.drop(columns=['anio'])
    key = next((c for c in df_ipm.columns if any(x in c.lower() 
               for x in ['municipio', 'divipola', 'codigo'])), df_ipm.columns[1])
    df_ipm = df_ipm.rename(columns={key: 'divipola_municipio'})
    df_ipm['divipola_municipio'] = zfill5(df_ipm['divipola_municipio'])
    print(f"  IPM: {len(df_ipm)} municipios")

    print("Cargando NBI (cobertura servicios)...")
    df_nbi = pd.read_parquet(NBI_FILE)
    if 'código_municipio' in df_nbi.columns:
        df_nbi = df_nbi.rename(columns={'código_municipio': 'divipola_municipio'})
    if 'divipola_municipio' in df_nbi.columns:
        df_nbi['divipola_municipio'] = zfill5(df_nbi['divipola_municipio'])
    if 'anio' in df_nbi.columns:
        df_nbi = df_nbi.drop(columns=['anio'])
    print(f"  NBI: {len(df_nbi)} municipios")

    print("Cargando composicion etnica...")
    df_etnia = pd.read_parquet(ETNIA_FILE)
    if 'divipola_municipio' in df_etnia.columns:
        df_etnia['divipola_municipio'] = zfill5(df_etnia['divipola_municipio'])
    if 'anio' in df_etnia.columns:
        df_etnia = df_etnia.drop(columns=['anio'])
    print(f"  Etnia: {len(df_etnia)} municipios")

    return df_ipm, df_nbi, df_etnia


# ==========================================
# CAPA PLATA - CRUCE CON DUCKDB
# ==========================================
def silver_cruce(df_secop, df_ipm, df_nbi, df_etnia):
    """Cruce SECOP + DANE con DuckDB en memoria."""
    con = duckdb.connect()
    con.register('secop', df_secop)
    con.register('ipm',   df_ipm)
    con.register('nbi',   df_nbi)
    con.register('etnia', df_etnia)

    print("Cruzando SECOP + DANE con DuckDB...")

    sql = """
    SELECT
        s.*,
        i.* EXCLUDE (divipola_municipio),
        n.* EXCLUDE (divipola_municipio),
        et.* EXCLUDE (divipola_municipio)
    FROM secop s
    LEFT JOIN ipm   i  ON s.divipola_municipio = i.divipola_municipio
    LEFT JOIN nbi   n  ON s.divipola_municipio = n.divipola_municipio
    LEFT JOIN etnia et ON s.divipola_municipio = et.divipola_municipio
    """

    df_cruce = con.execute(sql).df()
    con.close()

    print(f"Cruce: {len(df_cruce)} registros totales")

    df_nac = df_cruce[df_cruce['es_nacional'] == True].copy()
    df_ter = df_cruce[df_cruce['es_nacional'] == False].copy()
    print(f"  Nacional: {len(df_nac)} | Territorial: {len(df_ter)}")

    return df_nac, df_ter


# ==========================================
# CAPA ORO - MODELOS NO LINEALES
# ==========================================
def detect_outliers(df, batch_size=10000):
    for f in ['precio_base', 'valor_total_adjudicacion']:
        df[f] = pd.to_numeric(df.get(f, 0), errors='coerce').fillna(0)

    n = len(df)
    all_if  = np.zeros(n, dtype=bool)
    all_lof = np.zeros(n, dtype=bool)
    all_svm = np.zeros(n, dtype=bool)
    sc_if = np.ones(n); sc_lof = np.ones(n); sc_svm = np.ones(n)

    for s in range(0, n, batch_size):
        e = min(s + batch_size, n)
        X = df.iloc[s:e][['precio_base', 'valor_total_adjudicacion']].values
        if len(X) < 5: continue

        m1 = IsolationForest(contamination=0.05, random_state=42)
        p1 = m1.fit_predict(X)
        all_if[s:e] = (p1 == -1); sc_if[s:e] = m1.decision_function(X)

        m2 = LocalOutlierFactor(n_neighbors=min(20, len(X)-1), contamination=0.05)
        p2 = m2.fit_predict(X)
        all_lof[s:e] = (p2 == -1); sc_lof[s:e] = m2.negative_outlier_factor_

        m3 = OneClassSVM(kernel='rbf', nu=0.05)
        p3 = m3.fit_predict(X)
        all_svm[s:e] = (p3 == -1); sc_svm[s:e] = m3.decision_function(X)

        print(f"  Lote {s}-{e} OK")

    df['atipico_isolation_forest'] = all_if
    df['score_isolation_forest']   = sc_if
    df['atipico_lof']              = all_lof
    df['score_lof']                = sc_lof
    df['atipico_svm']              = all_svm
    df['score_svm']                = sc_svm

    votos = all_if.astype(int) + all_lof.astype(int) + all_svm.astype(int)
    df['es_atipico'] = (votos >= 2)

    med_pb = df['precio_base'].median()
    med_va = df['valor_total_adjudicacion'].median()
    df['tipo_atipico'] = 'normal'
    mask = df['es_atipico']
    df.loc[mask & ((df['precio_base'] > med_pb) | (df['valor_total_adjudicacion'] > med_va)), 'tipo_atipico'] = 'alto'
    df.loc[mask & ((df['precio_base'] <= med_pb) & (df['valor_total_adjudicacion'] <= med_va)), 'tipo_atipico'] = 'bajo'

    return df


def treat_outliers(df):
    df['valor_tratado_precio_base']  = df['precio_base']
    df['valor_tratado_adjudicacion'] = df['valor_total_adjudicacion']
    df['metodo_tratamiento']         = 'sin_tratamiento'

    mask = df['es_atipico']
    if mask.sum() == 0: return df

    p05_pb = df['precio_base'].quantile(0.05); p95_pb = df['precio_base'].quantile(0.95)
    p05_va = df['valor_total_adjudicacion'].quantile(0.05); p95_va = df['valor_total_adjudicacion'].quantile(0.95)

    df.loc[mask, 'valor_tratado_precio_base']  = np.clip(df.loc[mask, 'precio_base'], p05_pb, p95_pb)
    df.loc[mask, 'valor_tratado_adjudicacion'] = np.clip(df.loc[mask, 'valor_total_adjudicacion'], p05_va, p95_va)
    df.loc[mask, 'metodo_tratamiento'] = 'winsorizado'

    X2 = df[['valor_tratado_precio_base', 'valor_tratado_adjudicacion']].values
    still = mask & (IsolationForest(contamination=0.05, random_state=42).fit_predict(X2) == -1)
    if still.sum() > 0:
        df.loc[still, 'valor_tratado_precio_base']  = np.nan
        df.loc[still, 'valor_tratado_adjudicacion'] = np.nan
        df.loc[still, 'metodo_tratamiento'] = 'imputado_knn'
        imp = KNNImputer(n_neighbors=5)
        res = imp.fit_transform(df[['valor_tratado_precio_base', 'valor_tratado_adjudicacion']])
        df['valor_tratado_precio_base']  = res[:, 0]
        df['valor_tratado_adjudicacion'] = res[:, 1]

    return df


def gold_layer(df_nac, df_ter):
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    print("Capa Oro: Nacional...")
    df_nac = detect_outliers(df_nac)
    df_nac = treat_outliers(df_nac)

    print("Capa Oro: Territorial...")
    df_ter = detect_outliers(df_ter)
    df_ter = treat_outliers(df_ter)

    reporte_cols = [
        'divipola_municipio', 'anio', 'precio_base', 'valor_total_adjudicacion',
        'valor_tratado_precio_base', 'valor_tratado_adjudicacion',
        'atipico_isolation_forest', 'atipico_lof', 'atipico_svm',
        'es_atipico', 'tipo_atipico', 'metodo_tratamiento', 'origen'
    ]
    df_rep = pd.concat([
        df_nac[df_nac['es_atipico'] == True],
        df_ter[df_ter['es_atipico'] == True]
    ], ignore_index=True)
    df_rep = df_rep[[c for c in reporte_cols if c in df_rep.columns]]

    p1 = os.path.join(PROCESSED_DIR, "cruce_secop_dane_nacional_2018_2025.parquet")
    p2 = os.path.join(PROCESSED_DIR, "cruce_secop_dane_territorial_2018_2025.parquet")
    p3 = os.path.join(PROCESSED_DIR, "reporte_atipicos_2018_2025.parquet")

    df_nac.to_parquet(p1, compression='snappy', index=False)
    df_ter.to_parquet(p2, compression='snappy', index=False)
    df_rep.to_parquet(p3, compression='snappy', index=False)

    print(f"Nacional:    {len(df_nac)} registros -> {p1}")
    print(f"Territorial: {len(df_ter)} registros -> {p2}")
    print(f"Atipicos:    {len(df_rep)} registros -> {p3}")


# ==========================================
# MAIN
# ==========================================
def main():
    print("=" * 55)
    print("CRUCE SECOP II + DANE 2018-2025 | DuckDB")
    print("Muestra: 50,000 registros por año")
    print("=" * 55)

    print("\n[1/4] Cargando SECOP...")
    df_secop = bronze_secop()
    if df_secop is None: return

    print("\n[2/4] Cargando DANE...")
    df_ipm, df_nbi, df_etnia = bronze_dane()

    print("\n[3/4] Cruce con DuckDB...")
    df_nac, df_ter = silver_cruce(df_secop, df_ipm, df_nbi, df_etnia)

    print("\n[4/4] Modelos no lineales...")
    gold_layer(df_nac, df_ter)

    print("\n✅ Pipeline ejecutado exitosamente.")


if __name__ == "__main__":
    main()

