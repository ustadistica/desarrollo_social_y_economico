import duckdb
import pandas as pd
from pathlib import Path

def main():
    base_dir = Path("datos/bronze")
    secop_i_path = base_dir / "secop_i" / "*.parquet"
    secop_ii_path = base_dir / "secop_ii" / "*.parquet"
    
    # Check if files exist
    if not list((base_dir / "secop_i").glob("*.parquet")) or not list((base_dir / "secop_ii").glob("*.parquet")):
        print("Faltan archivos parquet en Bronze para SECOP I o II.")
        return

    # Usaremos duckdb para consolidar los NITs por municipio-año para ambas plataformas
    query = f"""
    WITH secop_i_raw AS (
        SELECT 
            LPAD(CAST(divipola_key_mapped AS VARCHAR), 5, '0') AS divipola_key,
            TRY_CAST(RIGHT(CAST("Fecha de Firma del Contrato" AS VARCHAR), 4) AS INT) AS anio_key,
            CAST("Identificacion del Contratista" AS VARCHAR) AS nit,
            'SECOP_I' as fuente
        FROM read_parquet('{secop_i_path}')
        WHERE "Fecha de Firma del Contrato" IS NOT NULL 
          AND divipola_key_mapped IS NOT NULL
          AND "Identificacion del Contratista" IS NOT NULL
    ),
    secop_ii_raw AS (
        SELECT 
            LPAD(CAST(divipola_key_mapped AS VARCHAR), 5, '0') AS divipola_key,
            TRY_CAST(RIGHT(CAST("Fecha de Firma" AS VARCHAR), 4) AS INT) AS anio_key,
            CAST("Documento Proveedor" AS VARCHAR) AS nit,
            'SECOP_II' as fuente
        FROM read_parquet('{secop_ii_path}')
        WHERE "Fecha de Firma" IS NOT NULL 
          AND divipola_key_mapped IS NOT NULL
          AND "Documento Proveedor" IS NOT NULL
    ),
    combinado AS (
        SELECT * FROM secop_i_raw WHERE anio_key BETWEEN 2018 AND 2025
        UNION ALL
        SELECT * FROM secop_ii_raw WHERE anio_key BETWEEN 2018 AND 2025
    ),
    agregado AS (
        SELECT 
            divipola_key, 
            anio_key,
            COUNT(DISTINCT CASE WHEN fuente = 'SECOP_I' THEN nit END) AS prov_solo_i,
            COUNT(DISTINCT CASE WHEN fuente = 'SECOP_II' THEN nit END) AS prov_solo_ii,
            COUNT(DISTINCT nit) AS prov_union
        FROM combinado
        GROUP BY 1, 2
    )
    SELECT *, 
        (prov_solo_i + prov_solo_ii) AS suma_naiva,
        ((prov_solo_i + prov_solo_ii) - prov_union) AS doble_conteo
    FROM agregado
    ORDER BY anio_key, divipola_key
    """
    
    con = duckdb.connect()
    df = con.query(query).df()
    
    # Save raw CSV
    output_csv = "documentacion_tecnica/validacion_proveedores.csv"
    Path("documentacion_tecnica").mkdir(exist_ok=True)
    df.to_csv(output_csv, index=False)
    
    # Total aggregates
    tot_i = df['prov_solo_i'].sum()
    tot_ii = df['prov_solo_ii'].sum()
    tot_union_municipio = df['prov_union'].sum()
    tot_suma_naiva = df['suma_naiva'].sum()
    tot_doble_conteo = df['doble_conteo'].sum()
    
    print(f"Total nacional (agregado nivel municipio-año):")
    print(f"  Proveedores en SECOP I (suma municipal): {tot_i:,.0f}")
    print(f"  Proveedores en SECOP II (suma municipal): {tot_ii:,.0f}")
    print(f"  Suma naíve (I + II): {tot_suma_naiva:,.0f}")
    print(f"  Proveedores Unión Verdadera: {tot_union_municipio:,.0f}")
    print(f"  Doble Conteo Detectado: {tot_doble_conteo:,.0f} ({(tot_doble_conteo/tot_suma_naiva)*100:.1f}%)")
    
    # Prepare markdown table for summary
    md_content = f"""
| Métrica | Valor (Agregado Nacional de las Múltiples Municipalidades) |
| --- | --- |
| Total Proveedores SECOP I | {tot_i:,.0f} |
| Total Proveedores SECOP II | {tot_ii:,.0f} |
| **Suma Naíve (A+B)** | **{tot_suma_naiva:,.0f}** |
| **Unión Verdadera COUNT(DISTINCT NIT)** | **{tot_union_municipio:,.0f}** |
| **Doble Conteo Evitado** | **{tot_doble_conteo:,.0f} ({(tot_doble_conteo/tot_suma_naiva)*100:.1f}%)** |
"""
    
    with open("documentacion_tecnica/validacion_proveedores_summary.md", "w", encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Archivos guardados en documentacion_tecnica/")

if __name__ == "__main__":
    main()
