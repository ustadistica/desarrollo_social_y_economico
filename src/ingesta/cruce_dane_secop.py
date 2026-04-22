import duckdb
conn = duckdb.connect()
conn.execute(r"ATTACH 'C:\Users\Usuario\Downloads\secop_proyecto\modelo_estrella_duckdb\Proyect_SECOP.db' AS secop (TYPE SQLITE)")

for tabla in ['D_UbiEntidad', 'D_UbiProveedor']:
    print(f'\n--- {tabla} ---')
    df = conn.execute(f'SELECT * FROM secop.{tabla} LIMIT 5').fetchdf()
    print(df.to_string())