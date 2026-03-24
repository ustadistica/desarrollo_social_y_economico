import pandas as pd
import numpy as np
from pathlib import Path

def main():
    print("Iniciando Cruce SECOP II con indicadores DANE (Sprint 2)...")
    
    # Rutas relativas asumiendo ejecución desde la raíz del proyecto
    dane_path = Path('../datos/dane_2018/nbi_municipios_2018.parquet')
    secop_path = Path('../datos/secop_nuevos1.parquet')
    output_path = Path('../datos/cruce_secop_dane_sprint2.parquet')
    
    # 1. Cargar datos de DANE (NBI, etc.)
    print(f"Cargando DANE desde: {dane_path}")
    if not dane_path.exists():
        print("ERROR: Archivo DANE no encontrado.")
        return
    dane_df = pd.read_parquet(dane_path)
    
    # 2. Cargar datos de SECOP
    print(f"Cargando SECOP desde: {secop_path}")
    if not secop_path.exists():
        print("ERROR: Archivo SECOP no encontrado.")
        return
    secop_df = pd.read_parquet(secop_path)
    
    # 3. Preparar DANE: Asegurar que el código de municipio (divipola) sea de 5 dígitos
    print("Preparando llaves de cruce...")
    # DANE tiene `código_departamento` y `código_municipio` o similar.
    # Combinamos para obtener 5 dígitos si `código_municipio` tiene 3, o usamos directamente si tiene 5.
    
    col_dane_muni = [c for c in dane_df.columns if 'municipio' in c.lower()][0]
    
    # Validar si el código de municipio en DANE es de 5 o 3 dígitos.
    # Si el código departamento existe, lo concatenamos si es necesario.
    if 'código_departamento' in dane_df.columns:
        dane_df['divipola_municipio'] = dane_df['código_departamento'].astype(str).str.zfill(2) + \
                                        dane_df[col_dane_muni].astype(str).str.zfill(3)
        # Si ya era de 5, la concatenación lo haría de más de 5, así que tomamos los últimos 5
        dane_df['divipola_municipio'] = dane_df['divipola_municipio'].str[-5:]
    else:
        dane_df['divipola_municipio'] = dane_df[col_dane_muni].astype(str).str.zfill(5)
        
    print(f"DANE shape: {dane_df.shape}")
    
    # 4. Preparar SECOP: Convertir nombres de ciudad a código divipola usando el módulo del compañero
    import sys
    sys.path.append('ingesta y validacion')
    from transform.standardize_geo import standardize_divipola
    
    print("Mapeando nombres de ciudad_entidad a divipola_municipio...")
    secop_df = standardize_divipola(secop_df, column_municipio='divipola_municipio', column_nombre='ciudad_entidad')
    
    # Asegurar montos numéricos
    col_monto = 'valor_contrato' if 'valor_contrato' in secop_df.columns else 'valor_total_adjudicacion'
    if col_monto not in secop_df.columns:
        col_monto = [c for c in secop_df.columns if 'valor' in c.lower() or 'monto' in c.lower()][0]
        
    secop_df['monto_contrato'] = pd.to_numeric(secop_df[col_monto], errors='coerce').fillna(0)
    
    # Agrupar SECOP a nivel municipal
    print("Agregando SECOP a nivel municipal...")
    secop_agg = secop_df.groupby('divipola_municipio').agg(
        num_contratos=('monto_contrato', 'count'),
        monto_total_contratos=('monto_contrato', 'sum'),
        monto_promedio=('monto_contrato', 'mean')
    ).reset_index()
    print(f"SECOP agregado shape: {secop_agg.shape}")
    
    # 5. CRUZAR (Join left since DANE should cover all municipalities theoretically)
    print("Realizando Join por código municipio...")
    cruce_df = dane_df.merge(secop_agg, on='divipola_municipio', how='left')
    
    # Rellenar NA en contratos con 0 (municipios sin contratos en SECOP en este extracto)
    cruce_df['num_contratos'] = cruce_df['num_contratos'].fillna(0)
    cruce_df['monto_total_contratos'] = cruce_df['monto_total_contratos'].fillna(0)
    cruce_df['monto_promedio'] = cruce_df['monto_promedio'].fillna(0)
    
    print(f"Resultado del join shape: {cruce_df.shape}")
    print("Muestra del cruce resultante:")
    print(cruce_df[['divipola_municipio', 'num_contratos', 'monto_total_contratos']].head())
    
    # 6. Guardar
    print(f"Guardando resultado en {output_path}...")
    cruce_df.to_parquet(output_path, engine='pyarrow', compression='snappy')
    print("¡Proceso finalizado con éxito!")

if __name__ == '__main__':
    main()
