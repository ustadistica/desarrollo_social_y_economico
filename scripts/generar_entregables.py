import duckdb
import pandas as pd
from pathlib import Path
import os
import sys

# Forzar UTF-8 en stdout
sys.stdout.reconfigure(encoding='utf-8')

print("--------------------------------------------------")
print("[Iniciando Generacion de Entregables SPRINT 2]")
print("--------------------------------------------------")

plata_dir = Path("datos/plata")
bronze_dir = Path("datos/bronze")

try:
    cnpv_file = list((plata_dir / "cnpv").glob("*.parquet"))[0]
    secop_file = list((plata_dir / "secop").glob("*.parquet"))[0]
    emicron_file = list((bronze_dir / "emicron").glob("*.parquet"))[0]
except IndexError as e:
    print(f"[Error] Archivos faltantes: {e}")
    exit(1)

con = duckdb.connect()
con.execute(f"CREATE OR REPLACE VIEW cnpv AS SELECT * FROM read_parquet('{cnpv_file}')")
con.execute(f"CREATE OR REPLACE VIEW secop AS SELECT * FROM read_parquet('{secop_file}')")
con.execute(f"CREATE OR REPLACE VIEW emicron AS SELECT * FROM read_parquet('{emicron_file}')")

print("[OK] Bases de datos leidas. Calculando indicadores...\n")

# 1. INDICADORES SOCIALES (CNPV)
q_social = """
    SELECT 
        divipola_municipio,
        poblacion_total
    FROM cnpv
    ORDER BY poblacion_total DESC
"""
df_social = con.execute(q_social).df()
f1 = "1_INDICADORES_SOCIALES_CNPV.csv"
df_social.to_csv(f1, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f1} (Top:\n{df_social.head(3).to_string()})\n")

# 2. INDICADORES INVERSION PUBLICA (SECOP)
q_inversion = """
    SELECT 
        Departamento as departamento,
        Ciudad as municipio,
        COUNT(*) AS numero_contratos,
        SUM(TRY_CAST("Valor del Contrato" AS NUMERIC)) AS inversion_publica_total
    FROM secop
    WHERE Departamento IS NOT NULL
    GROUP BY 1, 2
    ORDER BY inversion_publica_total DESC NULLS LAST
"""
df_inversion = con.execute(q_inversion).df()
f2 = "2_INDICADORES_INVERSION_SECOP.csv"
df_inversion.to_csv(f2, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f2} (Top:\n{df_inversion.head(3).to_string()})\n")

# 3. INDICADORES ECONOMIA POPULAR (EMICRON)
q_economia = """
    SELECT 
        LPAD(CAST(COD_DEPTO AS VARCHAR), 2, '0') AS cod_departamento,
        SUM(TRY_CAST(F_EXP AS NUMERIC)) AS total_empresas_estimadas,
        SUM(CASE WHEN TRY_CAST(P1633 AS VARCHAR) = '1' THEN TRY_CAST(F_EXP AS NUMERIC) ELSE 0 END) AS formales,
        SUM(CASE WHEN TRY_CAST(P1633 AS VARCHAR) != '1' THEN TRY_CAST(F_EXP AS NUMERIC) ELSE 0 END) AS informales,
        ROUND((SUM(CASE WHEN TRY_CAST(P1633 AS VARCHAR) = '1' THEN TRY_CAST(F_EXP AS NUMERIC) ELSE 0 END) * 100.0) / 
              NULLIF(SUM(TRY_CAST(F_EXP AS NUMERIC)), 0), 1) AS porcentaje_formalidad,
        SUM(TRY_CAST(P2991 AS NUMERIC) * TRY_CAST(F_EXP AS NUMERIC)) AS ingresos_totales
    FROM emicron
    GROUP BY 1
    ORDER BY total_empresas_estimadas DESC
"""
df_economia = con.execute(q_economia).df()
f3 = "3_INDICADORES_ECONOMIA_POPULAR.csv"
df_economia.to_csv(f3, index=False, sep=';', encoding='utf-8-sig')
print(f" -> Guardado: {f3} (Top:\n{df_economia.head(3).to_string()})\n")

print("==================================================")
print("[EXITO COMPLETADO] Tienes los 3 archivos CSV listos en tu carpeta.")
print("==================================================")
