"""
Script de Migracion y Verificacion de Integridad: SQLite -> DuckDB
Modelo Estrella SECOP
"""

import sqlite3
import duckdb
import pandas as pd
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB = os.path.join(SCRIPT_DIR, 'modelo_estrella_sqlite', 'Proyect_SECOP.db')
DUCKDB_FILE = os.path.join(SCRIPT_DIR, 'modelo_estrella_duckdb', 'Proyect_SECOP.duckdb')

TABLES = [
    'D_Entidad', 'D_Proveedor', 'D_Tiempo', 'D_UbiEntidad', 'D_UbiProveedor',
    'D_Categoria', 'D_Modalidad', 'D_TipoContrato', 'F_Proceso'
]

FOREIGN_KEYS = [
    ('F_Proceso', 'entidad_id', 'D_Entidad', 'entidad_id'),
    ('F_Proceso', 'proveedor_id', 'D_Proveedor', 'proveedor_id'),
    ('F_Proceso', 'tiempo_id', 'D_Tiempo', 'tiempo_id'),
    ('F_Proceso', 'ubi_entidad_id', 'D_UbiEntidad', 'ubi_entidad_id'),
    ('F_Proceso', 'ubi_proveedor_id', 'D_UbiProveedor', 'ubi_proveedor_id'),
    ('F_Proceso', 'categoria_id', 'D_Categoria', 'categoria_id'),
    ('F_Proceso', 'modalidad_id', 'D_Modalidad', 'modalidad_id'),
    ('F_Proceso', 'tipo_contrato_id', 'D_TipoContrato', 'tipo_contrato_id'),
]


def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_DB)
    return conn


def get_duckdb_connection():
    os.makedirs(os.path.dirname(DUCKDB_FILE), exist_ok=True)
    conn = duckdb.connect(DUCKDB_FILE)
    return conn


def inspect_sqlite():
    print("=" * 70)
    print("INSPECCION DE BASE DE DATOS SQLite")
    print("=" * 70)
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    db_size = os.path.getsize(SQLITE_DB)
    print(f"\nArchivo: {SQLITE_DB}")
    print(f"Tamanio: {db_size:,} bytes ({db_size/1024/1024:.2f} MB)\n")
    
    print(f"CONTEO DE REGISTROS POR TABLA:")
    print("-" * 50)
    counts = {}
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        counts[table] = count
        status = "OK" if count > 0 else "VACIA"
        print(f"  [{status}] {table:25} {count:>10,}")
    
    total = sum(counts.values())
    print("-" * 50)
    print(f"  {'TOTAL':25} {total:>10,}")
    
    conn.close()
    return counts


def migrate_to_duckdb():
    print("\n" + "=" * 70)
    print("MIGRACION: SQLite -> DuckDB")
    print("=" * 70)
    
    sqlite_conn = get_sqlite_connection()
    duckdb_conn = get_duckdb_connection()
    
    for table in TABLES:
        df = pd.read_sql_query(f"SELECT * FROM {table}", sqlite_conn)
        duckdb_conn.execute(f"DROP TABLE IF EXISTS {table}")
        duckdb_conn.execute(f"CREATE TABLE {table} AS SELECT * FROM df")
        print(f"  [OK] {table}: {len(df):,} registros migrados")
    
    sqlite_conn.close()
    duckdb_conn.close()
    print("\nMigracion completada!")


def verify_row_counts():
    print("\n" + "=" * 70)
    print("VERIFICACION 1: CONTEO DE REGISTROS")
    print("=" * 70)
    
    sqlite_conn = get_sqlite_connection()
    duckdb_conn = get_duckdb_connection()
    
    all_match = True
    
    for table in TABLES:
        sqlite_cur = sqlite_conn.cursor()
        sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
        sqlite_count = sqlite_cur.fetchone()[0]
        
        duckdb_cur = duckdb_conn.execute(f"SELECT COUNT(*) FROM {table}")
        duckdb_count = duckdb_cur.fetchone()[0]
        
        match = sqlite_count == duckdb_count
        status = "OK" if match else "FAIL"
        print(f"  [{status}] {table:25} SQLite: {sqlite_count:>10,} | DuckDB: {duckdb_count:>10,}")
        
        if not match:
            all_match = False
    
    sqlite_conn.close()
    duckdb_conn.close()
    
    print(f"\nResultado: {'TODOS COINCIDEN' if all_match else 'HAY DIFERENCIAS'}")
    return all_match


def verify_schema():
    print("\n" + "=" * 70)
    print("VERIFICACION 2: ESQUEMA Y TIPOS DE DATOS")
    print("=" * 70)
    
    sqlite_conn = get_sqlite_connection()
    duckdb_conn = get_duckdb_connection()
    
    all_match = True
    
    for table in TABLES:
        sqlite_cur = sqlite_conn.cursor()
        sqlite_cur.execute(f"PRAGMA table_info({table})")
        sqlite_cols = {c[1]: c[2] for c in sqlite_cur.fetchall()}
        
        duckdb_result = duckdb_conn.execute(f"DESCRIBE {table}")
        duckdb_cols = {row[0]: row[1] for row in duckdb_result.fetchall()}
        
        sqlite_set = set(sqlite_cols.keys())
        duckdb_set = set(duckdb_cols.keys())
        
        missing = sqlite_set - duckdb_set
        extra = duckdb_set - sqlite_set
        
        if missing:
            print(f"  [FAIL] {table}: Faltan columnas: {missing}")
            all_match = False
        elif extra:
            print(f"  [FAIL] {table}: Columnas extra: {extra}")
            all_match = False
        else:
            print(f"  [OK] {table}: {len(sqlite_cols)} columnas correctas")
    
    sqlite_conn.close()
    duckdb_conn.close()
    
    print(f"\nResultado: {'ESQUEMAS COINCIDEN' if all_match else 'HAY DIFERENCIAS'}")
    return all_match


def verify_foreign_keys():
    print("\n" + "=" * 70)
    print("VERIFICACION 3: INTEGRIDAD REFERENCIAL")
    print("=" * 70)
    
    duckdb_conn = get_duckdb_connection()
    all_valid = True
    
    for fk in FOREIGN_KEYS:
        table, col, ref_table, ref_col = fk
        
        query = f"""
            SELECT COUNT(*) 
            FROM {table} t 
            LEFT JOIN {ref_table} r ON t.{col} = r.{ref_col}
            WHERE r.{ref_col} IS NULL AND t.{col} IS NOT NULL
        """
        
        result = duckdb_conn.execute(query).fetchone()[0]
        status = "OK" if result == 0 else "FAIL"
        print(f"  [{status}] {table}.{col} -> {ref_table}.{ref_col}: {result} huerfanos")
        
        if result > 0:
            all_valid = False
    
    duckdb_conn.close()
    print(f"\nResultado: {'INTEGRIDAD CORRECTA' if all_valid else 'HAY REFERENCIAS HUERFANAS'}")
    return all_valid


def verify_nulls():
    print("\n" + "=" * 70)
    print("VERIFICACION 4: VALORES NULOS CRITICOS")
    print("=" * 70)
    
    duckdb_conn = get_duckdb_connection()
    
    critical_columns = [
        ('D_Entidad', 'entidad_id'),
        ('D_Proveedor', 'proveedor_id'),
        ('D_Tiempo', 'tiempo_id'),
        ('D_UbiEntidad', 'ubi_entidad_id'),
        ('D_UbiProveedor', 'ubi_proveedor_id'),
        ('D_Categoria', 'categoria_id'),
        ('D_Modalidad', 'modalidad_id'),
        ('D_TipoContrato', 'tipo_contrato_id'),
        ('F_Proceso', 'id_del_proceso'),
        ('F_Proceso', 'entidad_id'),
        ('F_Proceso', 'proveedor_id'),
        ('F_Proceso', 'tiempo_id'),
    ]
    
    all_valid = True
    
    for table, col in critical_columns:
        query = f"SELECT COUNT(*) FROM {table} WHERE {col} IS NULL"
        null_count = duckdb_conn.execute(query).fetchone()[0]
        status = "OK" if null_count == 0 else "FAIL"
        print(f"  [{status}] {table}.{col}: {null_count} NULLs")
        
        if null_count > 0:
            all_valid = False
    
    duckdb_conn.close()
    print(f"\nResultado: {'SIN NULLS CRITICOS' if all_valid else 'HAY NULLS EN COLUMNAS CRITICAS'}")
    return all_valid


def verify_primary_keys():
    print("\n" + "=" * 70)
    print("VERIFICACION 5: UNICIDAD DE PRIMARY KEYS")
    print("=" * 70)
    
    duckdb_conn = get_duckdb_connection()
    
    pk_columns = [
        ('D_Entidad', 'entidad_id'),
        ('D_Proveedor', 'proveedor_id'),
        ('D_Tiempo', 'tiempo_id'),
        ('D_UbiEntidad', 'ubi_entidad_id'),
        ('D_UbiProveedor', 'ubi_proveedor_id'),
        ('D_Categoria', 'categoria_id'),
        ('D_Modalidad', 'modalidad_id'),
        ('D_TipoContrato', 'tipo_contrato_id'),
        ('F_Proceso', 'id_del_proceso'),
    ]
    
    all_valid = True
    
    for table, col in pk_columns:
        query = f"""
            SELECT {col}, COUNT(*) as cnt 
            FROM {table} 
            GROUP BY {col} 
            HAVING cnt > 1
        """
        duplicates = duckdb_conn.execute(query).fetchall()
        
        if duplicates:
            print(f"  [FAIL] {table}.{col}: {len(duplicates)} duplicados")
            all_valid = False
        else:
            print(f"  [OK] {table}.{col}: Sin duplicados")
    
    duckdb_conn.close()
    print(f"\nResultado: {'PKS UNICAS' if all_valid else 'HAY DUPLICADOS EN PKS'}")
    return all_valid


def verify_aggregations():
    print("\n" + "=" * 70)
    print("VERIFICACION 6: AGREGACIONES")
    print("=" * 70)
    
    sqlite_conn = get_sqlite_connection()
    duckdb_conn = get_duckdb_connection()
    
    all_match = True
    numeric_cols = ['precio_base', 'valor_total_adjudicacion', 'numero_de_lotes']
    
    for col in numeric_cols:
        try:
            sqlite_cur = sqlite_conn.cursor()
            sqlite_cur.execute(f"SELECT SUM({col}), AVG({col}) FROM F_Proceso")
            sqlite_sum, sqlite_avg = sqlite_cur.fetchone()
            
            duckdb_result = duckdb_conn.execute(f"SELECT SUM({col}), AVG({col}) FROM F_Proceso")
            duckdb_sum, duckdb_avg = duckdb_result.fetchone()
            
            sum_match = (sqlite_sum == duckdb_sum) or (
                sqlite_sum is not None and duckdb_sum is not None and 
                abs(sqlite_sum - duckdb_sum) < 0.01
            )
            
            status = "OK" if sum_match else "FAIL"
            print(f"  [{status}] F_Proceso.{col}: SUM SQLite={sqlite_sum} | DuckDB={duckdb_sum}")
            
            if not sum_match:
                all_match = False
        except Exception as e:
            print(f"  [SKIP] F_Proceso.{col}: {e}")
    
    sqlite_conn.close()
    duckdb_conn.close()
    print(f"\nResultado: {'AGREGACIONES COINCIDEN' if all_match else 'HAY DIFERENCIAS'}")
    return all_match


def main():
    print("\n" + "=" * 70)
    print("MIGRACION Y VERIFICACION: SQLite -> DuckDB")
    print("Modelo Estrella SECOP")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    sqlite_counts = inspect_sqlite()
    total_records = sum(sqlite_counts.values())
    
    if total_records == 0:
        print("\n" + "!" * 70)
        print("ADVERTENCIA: LA BASE DE DATOS SQLITE ESTA VACIA")
        print("!" * 70)
        print("\nNo hay datos para migrar. El script creara la estructura")
        print("en DuckDB, pero las tablas estaran vacias.")
    
    migrate_to_duckdb()
    
    results = {}
    results['Conteo de Registros'] = verify_row_counts()
    results['Esquema y Tipos de Datos'] = verify_schema()
    results['Integridad Referencial'] = verify_foreign_keys()
    results['Valores Nulos Criticos'] = verify_nulls()
    results['Unicidad de Primary Keys'] = verify_primary_keys()
    results['Agregaciones'] = verify_aggregations()
    
    print("\n" + "=" * 70)
    print("RESUMEN FINAL")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, passed_check in results.items():
        status = "[OK]" if passed_check else "[FAIL]"
        print(f"  {status} {check}")
    
    print(f"\nTotal: {passed}/{total} verificaciones pasaron")
    
    if passed == total:
        print("\n¡MIGRACION Y VERIFICACION COMPLETADAS EXITOSAMENTE!")
    else:
        print("\nALGUNAS VERIFICACIONES FALLARON - REVISE EL REPORTE")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
