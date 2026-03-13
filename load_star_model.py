"""
ETL: Carga de Datos SECOP al Modelo Estrella

Transforma los datos crudos del SECOP (Parquet) al modelo estrella
con 8 tablas de dimension y 1 tabla de hechos.
"""

import pandas as pd
import sqlite3
import os
from datetime import datetime

# Rutas
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATOS_DIR = os.path.join(SCRIPT_DIR, 'datos')
SQLITE_DB = os.path.join(SCRIPT_DIR, 'modelo_estrella_sqlite', 'Proyect_SECOP.db')

def load_parquet_files():
    """Cargar archivos Parquet"""
    print("=== CARGANDO DATOS PARQUET ===\n")

    dfs = []
    for archivo in ['secop_nuevos1.parquet', 'secop_cambiados1.parquet']:
        path = os.path.join(DATOS_DIR, archivo)
        if os.path.exists(path):
            df = pd.read_parquet(path)
            print(f"  {archivo}: {len(df):,} registros")
            dfs.append(df)

    if not dfs:
        raise Exception("No se encontraron archivos Parquet en la carpeta datos/")

    # Unir todos los datos
    df_combined = pd.concat(dfs, ignore_index=True)
    print(f"\n  TOTAL: {len(df_combined):,} registros")

    # Eliminar duplicados por id_del_proceso
    df_combined = df_combined.drop_duplicates(subset=['id_del_proceso'], keep='last')
    print(f"  Despues de eliminar duplicados: {len(df_combined):,} registros")

    return df_combined


def create_dimension_tables(df):
    """Crear tablas de dimension"""
    print("\n=== CREANDO TABLAS DE DIMENSION ===\n")

    # D_Tiempo
    print("  Creando D_Tiempo...")
    df['fecha_de_publicacion_del'] = pd.to_datetime(df['fecha_de_publicacion_del'], errors='coerce')
    tiempo_data = df[['fecha_de_publicacion_del']].dropna().drop_duplicates().copy()
    tiempo_data['año'] = tiempo_data['fecha_de_publicacion_del'].dt.year
    tiempo_data['trimestre'] = (tiempo_data['fecha_de_publicacion_del'].dt.month - 1) // 3 + 1
    tiempo_data['mes'] = tiempo_data['fecha_de_publicacion_del'].dt.month
    tiempo_data['día'] = tiempo_data['fecha_de_publicacion_del'].dt.day
    tiempo_data['tiempo_id'] = range(1, len(tiempo_data) + 1)
    tiempo_data = tiempo_data[['tiempo_id', 'fecha_de_publicacion_del', 'año', 'trimestre', 'mes', 'día']]
    tiempo_data.columns = ['tiempo_id', 'fecha', 'año', 'trimestre', 'mes', 'día']

    # D_Entidad
    print("  Creando D_Entidad...")
    entidad_data = df[['entidad', 'codigo_entidad', 'ordenentidad', 'departamento_entidad', 'ciudad_entidad']].drop_duplicates().copy()
    entidad_data = entidad_data.dropna(subset=['entidad'], how='all')
    entidad_data = entidad_data.drop_duplicates(subset=['entidad'], keep='first')
    entidad_data['entidad_id'] = range(1, len(entidad_data) + 1)
    # Reordenar columnas
    entidad_data = entidad_data[['entidad_id', 'codigo_entidad', 'entidad', 'ordenentidad', 'departamento_entidad', 'ciudad_entidad']]

    # D_Proveedor
    print("  Creando D_Proveedor...")
    proveedor_data = df[['nombre_del_proveedor', 'nit_del_proveedor_adjudicado', 'departamento_proveedor', 'ciudad_proveedor']].drop_duplicates().copy()
    proveedor_data = proveedor_data.dropna(subset=['nombre_del_proveedor'], how='all')
    proveedor_data = proveedor_data.drop_duplicates(subset=['nombre_del_proveedor'], keep='first')
    proveedor_data['proveedor_id'] = range(1, len(proveedor_data) + 1)
    # Renombrar columna nit
    proveedor_data = proveedor_data.rename(columns={'nit_del_proveedor_adjudicado': 'nit'})
    proveedor_data = proveedor_data[['proveedor_id', 'nit', 'nombre_del_proveedor', 'departamento_proveedor', 'ciudad_proveedor']]

    # D_UbiEntidad
    print("  Creando D_UbiEntidad...")
    ubi_ent_data = df[['departamento_entidad', 'ciudad_entidad']].drop_duplicates().copy()
    ubi_ent_data = ubi_ent_data.dropna(subset=['departamento_entidad'], how='all')
    ubi_ent_data = ubi_ent_data.drop_duplicates(subset=['departamento_entidad', 'ciudad_entidad'], keep='first')
    ubi_ent_data['ubi_entidad_id'] = range(1, len(ubi_ent_data) + 1)
    ubi_ent_data = ubi_ent_data[['ubi_entidad_id', 'departamento_entidad', 'ciudad_entidad']]

    # D_UbiProveedor
    print("  Creando D_UbiProveedor...")
    ubi_prov_data = df[['departamento_proveedor', 'ciudad_proveedor']].drop_duplicates().copy()
    ubi_prov_data = ubi_prov_data.dropna(subset=['departamento_proveedor'], how='all')
    ubi_prov_data = ubi_prov_data.drop_duplicates(subset=['departamento_proveedor', 'ciudad_proveedor'], keep='first')
    ubi_prov_data['ubi_proveedor_id'] = range(1, len(ubi_prov_data) + 1)
    ubi_prov_data = ubi_prov_data[['ubi_proveedor_id', 'departamento_proveedor', 'ciudad_proveedor']]

    # D_Categoria
    print("  Creando D_Categoria...")
    cat_data = df[['codigo_principal_de_categoria']].drop_duplicates().copy()
    cat_data = cat_data.dropna(subset=['codigo_principal_de_categoria'], how='all')
    cat_data = cat_data.drop_duplicates(subset=['codigo_principal_de_categoria'], keep='first')
    cat_data['categoria_id'] = range(1, len(cat_data) + 1)
    cat_data.columns = ['codigo_principal_de_categoria', 'categoria_id']
    cat_data = cat_data[['categoria_id', 'codigo_principal_de_categoria']]

    # D_Modalidad
    print("  Creando D_Modalidad...")
    modal_data = df[['modalidad_de_contratacion', 'justificaci_n_modalidad_de']].drop_duplicates().copy()
    modal_data = modal_data.dropna(subset=['modalidad_de_contratacion'], how='all')
    modal_data = modal_data.drop_duplicates(subset=['modalidad_de_contratacion'], keep='first')
    modal_data['modalidad_id'] = range(1, len(modal_data) + 1)
    modal_data = modal_data[['modalidad_id', 'modalidad_de_contratacion', 'justificaci_n_modalidad_de']]

    # D_TipoContrato
    print("  Creando D_TipoContrato...")
    tipo_data = df[['tipo_de_contrato', 'subtipo_de_contrato']].drop_duplicates().copy()
    tipo_data = tipo_data.dropna(subset=['tipo_de_contrato'], how='all')
    tipo_data = tipo_data.drop_duplicates(subset=['tipo_de_contrato'], keep='first')
    tipo_data['tipo_contrato_id'] = range(1, len(tipo_data) + 1)
    tipo_data = tipo_data[['tipo_contrato_id', 'tipo_de_contrato', 'subtipo_de_contrato']]

    return {
        'D_Tiempo': tiempo_data,
        'D_Entidad': entidad_data,
        'D_Proveedor': proveedor_data,
        'D_UbiEntidad': ubi_ent_data,
        'D_UbiProveedor': ubi_prov_data,
        'D_Categoria': cat_data,
        'D_Modalidad': modal_data,
        'D_TipoContrato': tipo_data
    }


def create_fact_table(df, dim_tables):
    """Crear tabla de hechos"""
    print("\n=== CREANDO TABLA DE HECHOS ===\n")

    # Mapear IDs de dimensiones
    fact = df[['id_del_proceso']].copy()
    fact['id_del_proceso'] = fact['id_del_proceso'].astype(str)

    # Mapear tiempo
    df['fecha_de_publicacion_del'] = pd.to_datetime(df['fecha_de_publicacion_del'], errors='coerce')
    tiempo_map = dim_tables['D_Tiempo'].set_index('fecha')['tiempo_id'].to_dict()
    fact['tiempo_id'] = df['fecha_de_publicacion_del'].map(tiempo_map)

    # Mapear entidad
    entidad_map = dim_tables['D_Entidad'].set_index('entidad')['entidad_id'].to_dict()
    fact['entidad_id'] = df['entidad'].map(entidad_map)

    # Mapear proveedor
    proveedor_map = dim_tables['D_Proveedor'].set_index('nombre_del_proveedor')['proveedor_id'].to_dict()
    fact['proveedor_id'] = df['nombre_del_proveedor'].map(proveedor_map)

    # Mapear ubicación entidad
    ubi_ent_map = dim_tables['D_UbiEntidad'].set_index(['departamento_entidad', 'ciudad_entidad'])['ubi_entidad_id'].to_dict()
    fact['ubi_entidad_id'] = df.apply(lambda x: ubi_ent_map.get((x.get('departamento_entidad'), x.get('ciudad_entidad'))), axis=1)

    # Mapear ubicación proveedor
    ubi_prov_map = dim_tables['D_UbiProveedor'].set_index(['departamento_proveedor', 'ciudad_proveedor'])['ubi_proveedor_id'].to_dict()
    fact['ubi_proveedor_id'] = df.apply(lambda x: ubi_prov_map.get((x.get('departamento_proveedor'), x.get('ciudad_proveedor'))), axis=1)

    # Mapear categoría
    cat_map = dim_tables['D_Categoria'].set_index('codigo_principal_de_categoria')['categoria_id'].to_dict()
    fact['categoria_id'] = df['codigo_principal_de_categoria'].map(cat_map)

    # Mapear modalidad
    modal_map = dim_tables['D_Modalidad'].set_index('modalidad_de_contratacion')['modalidad_id'].to_dict()
    fact['modalidad_id'] = df['modalidad_de_contratacion'].map(modal_map)

    # Mapear tipo contrato
    tipo_map = dim_tables['D_TipoContrato'].set_index('tipo_de_contrato')['tipo_contrato_id'].to_dict()
    fact['tipo_contrato_id'] = df['tipo_de_contrato'].map(tipo_map)

    # Columnas de medidas
    fact['precio_base'] = pd.to_numeric(df['precio_base'], errors='coerce')
    fact['valor_total_adjudicacion'] = pd.to_numeric(df['valor_total_adjudicacion'], errors='coerce')
    fact['numero_de_lotes'] = pd.to_numeric(df['numero_de_lotes'], errors='coerce')
    fact['proveedores_invitados'] = pd.to_numeric(df['proveedores_invitados'], errors='coerce')
    fact['respuestas_al_procedimiento'] = pd.to_numeric(df['respuestas_al_procedimiento'], errors='coerce')

    # Columnas adicionales
    fact['estado_del_procedimiento'] = df.get('estado_del_procedimiento')
    fact['id_estado_del_procedimiento'] = df.get('id_estado_del_procedimiento')
    fact['id_adjudicacion'] = df.get('id_adjudicacion')
    fact['visualizaciones_del'] = pd.to_numeric(df.get('visualizaciones_del_procedimiento', pd.Series([None]*len(df))), errors='coerce')

    return fact


def save_to_sqlite(dim_tables, fact_table):
    """Guardar tablas en SQLite"""
    print("\n=== GUARDANDO EN SQLITE ===\n")

    # Eliminar DB existente
    if os.path.exists(SQLITE_DB):
        os.remove(SQLITE_DB)

    conn = sqlite3.connect(SQLITE_DB)

    # Guardar dimensiones
    for name, data in dim_tables.items():
        data.to_sql(name, conn, index=False, if_exists='replace')
        print(f"  {name}: {len(data):,} registros guardados")

    # Guardar hechos
    fact_table.to_sql('F_Proceso', conn, index=False, if_exists='replace')
    print(f"  F_Proceso: {len(fact_table):,} registros guardados")

    conn.close()
    print(f"\n  Base guardada en: {SQLITE_DB}")


def main():
    print("=" * 70)
    print("ETL: Carga de Datos SECOP al Modelo Estrella")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Cargar datos
    df = load_parquet_files()

    # Crear dimensiones
    dim_tables = create_dimension_tables(df)

    # Crear tabla de hechos
    fact_table = create_fact_table(df, dim_tables)

    # Guardar en SQLite
    save_to_sqlite(dim_tables, fact_table)

    print("\n" + "=" * 70)
    print("ETL COMPLETADO EXITOSAMENTE")
    print("=" * 70)

    # Resumen
    print("\nRESUMEN:")
    for name, data in dim_tables.items():
        print(f"  {name}: {len(data):,} registros")
    print(f"  F_Proceso: {len(fact_table):,} registros")


if __name__ == "__main__":
    main()
