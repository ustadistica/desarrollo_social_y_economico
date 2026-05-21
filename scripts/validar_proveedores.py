import pandas as pd
from pathlib import Path

def main():
    silver_dir = Path("data/silver")
    secop_i_path = silver_dir / "silver_secop_i_transaccional.parquet"
    secop_ii_path = silver_dir / "silver_secop_ii_transaccional.parquet"
    
    if not secop_i_path.exists() or not secop_ii_path.exists():
        print("Faltan archivos parquet transaccionales en Silver para SECOP I o II.")
        return

    # Cargar datos
    df_i = pd.read_parquet(secop_i_path)
    df_ii = pd.read_parquet(secop_ii_path)

    # Filtrar SECOP I
    df_i = df_i.dropna(subset=['fecha_firma', 'divipola_key', 'nit_contratista']).copy()
    df_i['anio_key'] = pd.to_numeric(df_i['anio_key'], errors='coerce')
    df_i = df_i[(df_i['anio_key'] >= 2018) & (df_i['anio_key'] <= 2025)].copy()
    df_i = df_i.rename(columns={'nit_contratista': 'nit'})
    df_i['fuente'] = 'SECOP_I'
    secop_i_raw = df_i[['divipola_key', 'anio_key', 'nit', 'fuente']]

    # Filtrar SECOP II
    df_ii = df_ii.dropna(subset=['fecha_firma', 'divipola_key', 'nit_contratista']).copy()
    df_ii['anio_key'] = pd.to_numeric(df_ii['anio_key'], errors='coerce')
    df_ii = df_ii[(df_ii['anio_key'] >= 2018) & (df_ii['anio_key'] <= 2025)].copy()
    df_ii = df_ii.rename(columns={'nit_contratista': 'nit'})
    df_ii['fuente'] = 'SECOP_II'
    secop_ii_raw = df_ii[['divipola_key', 'anio_key', 'nit', 'fuente']]

    combinado = pd.concat([secop_i_raw, secop_ii_raw], ignore_index=True)

    # Agrupar
    agregado_i = combinado[combinado['fuente'] == 'SECOP_I'].groupby(['divipola_key', 'anio_key'])['nit'].nunique().reset_index().rename(columns={'nit': 'prov_solo_i'})
    agregado_ii = combinado[combinado['fuente'] == 'SECOP_II'].groupby(['divipola_key', 'anio_key'])['nit'].nunique().reset_index().rename(columns={'nit': 'prov_solo_ii'})
    agregado_union = combinado.groupby(['divipola_key', 'anio_key'])['nit'].nunique().reset_index().rename(columns={'nit': 'prov_union'})

    # Merge all
    agregado = pd.merge(agregado_union, agregado_i, on=['divipola_key', 'anio_key'], how='left').fillna({'prov_solo_i': 0})
    agregado = pd.merge(agregado, agregado_ii, on=['divipola_key', 'anio_key'], how='left').fillna({'prov_solo_ii': 0})
    
    agregado['suma_naiva'] = agregado['prov_solo_i'] + agregado['prov_solo_ii']
    agregado['doble_conteo'] = agregado['suma_naiva'] - agregado['prov_union']
    
    df = agregado.sort_values(by=['anio_key', 'divipola_key'])

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
    if tot_suma_naiva > 0:
        pct = (tot_doble_conteo/tot_suma_naiva)*100
    else:
        pct = 0.0
    print(f"  Doble Conteo Detectado: {tot_doble_conteo:,.0f} ({pct:.1f}%)")
    
    # Prepare markdown table for summary
    md_content = f"""
| Métrica | Valor (Agregado Nacional de las Múltiples Municipalidades) |
| --- | --- |
| Total Proveedores SECOP I | {tot_i:,.0f} |
| Total Proveedores SECOP II | {tot_ii:,.0f} |
| **Suma Naíve (A+B)** | **{tot_suma_naiva:,.0f}** |
| **Unión Verdadera COUNT(DISTINCT NIT)** | **{tot_union_municipio:,.0f}** |
| **Doble Conteo Evitado** | **{tot_doble_conteo:,.0f} ({pct:.1f}%)** |
"""
    
    with open("documentacion_tecnica/validacion_proveedores_summary.md", "w", encoding='utf-8') as f:
        f.write(md_content)
        
    print(f"Archivos guardados en documentacion_tecnica/")

if __name__ == "__main__":
    main()
