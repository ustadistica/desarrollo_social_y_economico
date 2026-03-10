import duckdb

SQLITE_PATH = "C:/Users/Usuario/Downloads/secop_proyecto/modelo_estrella_duckdb/Proyect_SECOP.db"
DUCKDB_PATH = "C:/Users/Usuario/Downloads/secop_proyecto/modelo_estrella_duckdb/Proyect_SECOP.duckdb"

TABLAS = [
    'F_Proceso',
    'D_Categoria',
    'D_Entidad',
    'D_Modalidad',
    'D_Proveedor',
    'D_Tiempo',
    'D_TipoContrato',
    'D_UbiEntidad',
    'D_UbiProveedor'
]

print("Iniciando migración SQLite → DuckDB...")
print(f"  Origen:  {SQLITE_PATH}")
print(f"  Destino: {DUCKDB_PATH}\n")

duck_conn = duckdb.connect(DUCKDB_PATH)

# Instalar y cargar extensión SQLite
duck_conn.execute("INSTALL sqlite;")
duck_conn.execute("LOAD sqlite;")

# Adjuntar la base SQLite
duck_conn.execute(f"ATTACH '{SQLITE_PATH}' AS sqlite_db (TYPE SQLITE, READ_ONLY);")

# Migrar cada tabla directamente SQLite → DuckDB sin pasar por pandas
for tabla in TABLAS:
    print(f"Migrando {tabla}...")
    duck_conn.execute(f"DROP TABLE IF EXISTS {tabla}")
    duck_conn.execute(f"CREATE TABLE {tabla} AS SELECT * FROM sqlite_db.{tabla}")
    n = duck_conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    print(f"  ✅ {tabla}: {n:,} filas\n")

# Crear vista vw_proceso_full
print("Creando vista vw_proceso_full...")
duck_conn.execute("DROP VIEW IF EXISTS vw_proceso_full")
duck_conn.execute("""
CREATE VIEW vw_proceso_full AS
SELECT
  f.id_del_proceso,
  f.id_adjudicacion,
  f.precio_base,
  f.valor_total_adjudicacion,
  f.numero_de_lotes,
  f.proveedores_invitados,
  f.respuestas_al_procedimiento,
  f.visualizaciones_del,
  f.estado_del_procedimiento,
  f.id_estado_del_procedimiento,
  e.entidad,
  e.codigo_entidad,
  e.ordenentidad                     AS orden_entidad,
  e.codigo_pci,
  e.nombre_de_la_unidad_de           AS unidad_entidad,
  ue.departamento_entidad            AS dpto_entidad,
  ue.ciudad_entidad                  AS mpio_entidad,
  p.nit                              AS proveedor_nit,
  p.nombre_del_proveedor             AS proveedor_nombre,
  up.departamento_proveedor          AS dpto_proveedor,
  up.ciudad_proveedor                AS mpio_proveedor,
  m.modalidad_de_contratacion        AS modalidad,
  tc.tipo_de_contrato                AS tipo_contrato,
  tc.subtipo_de_contrato             AS subtipo_contrato,
  c.codigo_principal_de_categoria    AS unspsc,
  t.fecha,
  t."año"                            AS anio,
  t.trimestre,
  t.mes,
  t."día"                            AS dia
FROM F_Proceso f
LEFT JOIN D_Entidad      e  ON f.entidad_id       = e.entidad_id
LEFT JOIN D_UbiEntidad   ue ON f.ubi_entidad_id   = ue.ubi_entidad_id
LEFT JOIN D_Proveedor    p  ON f.proveedor_id     = p.proveedor_id
LEFT JOIN D_UbiProveedor up ON f.ubi_proveedor_id = up.ubi_proveedor_id
LEFT JOIN D_Modalidad    m  ON f.modalidad_id     = m.modalidad_id
LEFT JOIN D_TipoContrato tc ON f.tipo_contrato_id = tc.tipo_contrato_id
LEFT JOIN D_Categoria    c  ON f.categoria_id     = c.categoria_id
LEFT JOIN D_Tiempo       t  ON f.tiempo_id        = t.tiempo_id
""")
print("✅ Vista vw_proceso_full creada\n")

# Verificación final
print("=== VERIFICACIÓN FINAL ===")
for tabla in TABLAS:
    sqlite_n = duck_conn.execute(f"SELECT COUNT(*) FROM sqlite_db.{tabla}").fetchone()[0]
    duck_n   = duck_conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    ok = "✅" if sqlite_n == duck_n else "❌"
    print(f"  {ok} {tabla}: SQLite={sqlite_n:,} | DuckDB={duck_n:,}")

duck_conn.close()
print("\nMigración completada exitosamente.")
print(f"Base DuckDB guardada en: {DUCKDB_PATH}")
