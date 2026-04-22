"""
Script de verificación completa del pipeline de ingesta Bronze.
Ejecuta cada parser y validador para comprobar que todo funciona.
"""

import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("test_pipeline")


def separator(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def test_imports():
    separator("TEST 1: IMPORTS DE TODOS LOS MODULOS")
    
    modules = {
        "Bronze parsers": lambda: __import__("bronze"),
        "Config settings": lambda: __import__("config.settings", fromlist=["settings"]),
        "Transform clean_text": lambda: __import__("transform.clean_text", fromlist=["normalize_unicode"]),
        "Transform standardize_geo": lambda: __import__("transform.standardize_geo", fromlist=["validate_divipola"]),
        "Transform type_cast": lambda: __import__("transform.type_cast", fromlist=["cast_to_schema"]),
        "Transform create_dimensions": lambda: __import__("transform.create_dimensions", fromlist=["create_dim_tiempo"]),
        "Transform create_facts": lambda: __import__("transform.create_facts", fromlist=["create_fact_vulnerabilidad"]),
        "Validate validate_bronze": lambda: __import__("validate.validate_bronze", fromlist=["validate_bronze_layer"]),
        "Validate validate_plata": lambda: __import__("validate.validate_plata", fromlist=["validate_plata_layer"]),
        "Load datamart_social": lambda: __import__("load.create_datamart_social", fromlist=["create_datamart_social"]),
        "Load datamart_economico": lambda: __import__("load.create_datamart_economico", fromlist=["create_datamart_economico"]),
        "Utils logger": lambda: __import__("utils.logger", fromlist=["get_logger"]),
        "Utils divipola_catalog": lambda: __import__("utils.divipola_catalog", fromlist=["DIVIPOLA_COMPLETO"]),
    }
    
    ok_count = 0
    fail_count = 0
    for name, importer in modules.items():
        try:
            importer()
            print(f"  [OK] {name}")
            ok_count += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            fail_count += 1
    
    print(f"\n  Resultado: {ok_count}/{ok_count + fail_count} modulos OK")
    return fail_count == 0


def test_cnpv():
    separator("TEST 2: INGESTA CNPV 2018 (XML)")
    
    from bronze.parsers.parser_xml_cnpv import parse_cnpv_xml, CNPV_XML_PATH
    
    print(f"  Ruta XML: {CNPV_XML_PATH}")
    print(f"  Existe: {CNPV_XML_PATH.exists()}")
    
    if not CNPV_XML_PATH.exists():
        print("  [SKIP] Archivo XML no encontrado")
        return True
    
    # Primero explorar estructura
    from bronze.parsers.parser_xml_cnpv import get_xml_structure
    estructura = get_xml_structure(max_elements=3)
    print(f"  Estructura XML: root={estructura.get('root')}")
    print(f"  Elementos unicos: {estructura.get('elementos_unicos', [])[:5]}")
    
    # Ejecutar parser
    result = parse_cnpv_xml()
    print(f"  Status: {result.get('status')}")
    print(f"  Registros: {result.get('registros', 'N/A')}")
    
    if result.get("archivo"):
        print(f"  Archivo: {result['archivo']}")
    if result.get("error"):
        print(f"  Error: {result['error']}")
    if result.get("columnas"):
        print(f"  Columnas ({len(result['columnas'])}): {result['columnas'][:8]}")
    
    return result.get("status") in ("success", "warning")


def test_emicron():
    separator("TEST 3: INGESTA EMICRON 2024 (CSV)")
    
    from bronze.parsers.parser_csv_emicron import parse_emicron_csv, EMICRON_CSV_PATH, inspect_csv_structure
    
    print(f"  Ruta CSV: {EMICRON_CSV_PATH}")
    print(f"  Existe: {EMICRON_CSV_PATH.exists()}")
    
    if not EMICRON_CSV_PATH.exists():
        print("  [SKIP] Archivo CSV no encontrado")
        return True
    
    # Inspeccionar estructura
    estructura = inspect_csv_structure(preview_rows=2)
    if "error" not in estructura:
        print(f"  Encoding: {estructura.get('encoding')}")
        print(f"  Separador: '{estructura.get('separador')}'")
        print(f"  Columnas ({estructura.get('num_columnas')}): {estructura.get('columnas', [])[:6]}")
        print(f"  Tamano: {estructura.get('tamaño_mb', 'N/A')} MB")
    else:
        print(f"  Error inspeccionando: {estructura['error']}")
    
    # Ejecutar parser
    result = parse_emicron_csv()
    print(f"  Status: {result.get('status')}")
    print(f"  Registros: {result.get('registros', 'N/A')}")
    
    if result.get("archivo"):
        print(f"  Archivo: {result['archivo']}")
    if result.get("error"):
        print(f"  Error: {result['error']}")
    
    return result.get("status") in ("success", "warning")


def test_secop():
    separator("TEST 4: INGESTA SECOP II (API)")
    
    from bronze.parsers.parser_api_secop import test_api_connection, check_secop_vigencia
    
    # Probar conexion
    print("  Probando conexion con API SECOP II...")
    conexion = test_api_connection()
    print(f"  Conexion: {conexion.get('status')} - {conexion.get('message')}")
    
    if conexion.get("status") != "success":
        print("  [SKIP] No hay conexion con la API")
        return True
    
    # Verificar vigencia
    vigencia = check_secop_vigencia()
    print(f"  Ultima publicacion: {vigencia.get('ultima_publicacion', 'N/A')}")
    
    # Ingesta (solo un batch pequeno para prueba)
    from bronze.parsers.parser_api_secop import ingest_secop_ii
    result = ingest_secop_ii(batch_size=100, force_download=True)
    print(f"  Status: {result.get('status')}")
    print(f"  Registros: {result.get('registros', 'N/A')}")
    
    if result.get("archivo"):
        print(f"  Archivo: {result['archivo']}")
    if result.get("error"):
        print(f"  Error: {result['error']}")
    
    return result.get("status") in ("success", "warning", "skipped")


def test_generic():
    separator("TEST 5: INGESTA IPM/NBI (GENERICO)")
    
    from bronze.parsers.parser_generic import ingest_ipm, ingest_nbi
    
    print("  Intentando IPM...")
    result_ipm = ingest_ipm()
    print(f"  IPM Status: {result_ipm.get('status')}")
    if result_ipm.get("error"):
        print(f"  IPM Error: {result_ipm['error']}")
    if result_ipm.get("registros"):
        print(f"  IPM Registros: {result_ipm['registros']}")
    
    print("  Intentando NBI...")
    result_nbi = ingest_nbi()
    print(f"  NBI Status: {result_nbi.get('status')}")
    if result_nbi.get("error"):
        print(f"  NBI Error: {result_nbi['error']}")
    if result_nbi.get("registros"):
        print(f"  NBI Registros: {result_nbi['registros']}")
    
    return True  # IPM/NBI son opcionales


def test_validator():
    separator("TEST 6: VALIDADOR BRONZE")
    
    from bronze.validators.bronze_validator import BronzeValidator
    import pandas as pd
    
    # Crear datos de prueba
    df = pd.DataFrame({
        "divipola_municipio": ["11001", "05001", "76001"],
        "divipola_departamento": ["11", "05", "76"],
        "ipm_total": [0.25, 0.35, 0.15],
        "poblacion_total": [8000000, 2500000, 2200000],
    })
    
    validator = BronzeValidator()
    result = validator.validate_dataframe(df, source_name="test_data")
    
    print(f"  Valido: {result.get('valid')}")
    print(f"  Checks realizados: {list(result.get('checks', {}).keys())}")
    
    for check_name, check_result in result.get("checks", {}).items():
        status = check_result.get("status", "?")
        message = check_result.get("message", "")
        print(f"    [{status.upper()}] {check_name}: {message}")
    
    return result.get("valid", False)


def test_transform_functions():
    separator("TEST 7: FUNCIONES DE TRANSFORMACION")
    
    import pandas as pd
    
    # Test clean_text
    from transform.clean_text import normalize_unicode, standardize_column_names
    
    test_text = "  Bogota  D.C.  "
    cleaned = normalize_unicode(test_text)
    print(f"  clean_text: '{test_text}' -> '{cleaned}'")
    
    df = pd.DataFrame({"Nombre Municipio": ["Bogota"], "Codigo DIVIPOLA": ["11001"]})
    df = standardize_column_names(df)
    print(f"  standardize_columns: {list(df.columns)}")
    
    # Test standardize_geo
    from transform.standardize_geo import validate_divipola, load_divipola_catalog
    
    valid, code = validate_divipola("11001")
    print(f"  validate_divipola('11001'): valid={valid}, code={code}")
    
    valid, code = validate_divipola("99999")
    print(f"  validate_divipola('99999'): valid={valid}, code={code}")
    
    catalog = load_divipola_catalog()
    print(f"  Catalogo DIVIPOLA: {len(catalog)} municipios")
    
    # Test type_cast
    from transform.type_cast import apply_plata_schema
    
    df = pd.DataFrame({
        "divipola_municipio": ["11001", "05001"],
        "monto_contrato": ["1000000", "2000000"],
        "ipm_total": ["0.25", "0.35"],
    })
    df = apply_plata_schema(df, contexto="contratacion")
    print(f"  type_cast contratacion: {dict(df.dtypes)}")
    
    return True


def test_create_dim_tiempo():
    separator("TEST 8: CREAR dim_tiempo (2018-2026)")
    
    from transform.create_dimensions import create_dim_tiempo
    from pathlib import Path
    
    # Crear en ruta temporal
    output = Path("../datos/plata/dim_tiempo")
    result = create_dim_tiempo(anio_inicio=2018, anio_fin=2026, output_path=output)
    
    print(f"  Status: {result.get('status')}")
    print(f"  Registros: {result.get('registros')}")
    print(f"  Archivo: {result.get('archivo')}")
    print(f"  Columnas: {result.get('columnas')}")
    
    return result.get("status") == "success"


def test_create_dim_ciiu():
    separator("TEST 9: CREAR dim_sector_ciiu")
    
    from transform.create_dimensions import create_dim_sector_ciiu
    from pathlib import Path
    
    output = Path("../datos/plata/dim_sector_ciiu")
    result = create_dim_sector_ciiu(output_path=output)
    
    print(f"  Status: {result.get('status')}")
    print(f"  Registros (codigos CIIU): {result.get('registros')}")
    print(f"  Archivo: {result.get('archivo')}")
    
    return result.get("status") == "success"


def test_create_dim_unspsc():
    separator("TEST 10: CREAR dim_sector_unspsc")
    
    from transform.create_dimensions import create_dim_sector_unspsc
    from pathlib import Path
    
    output = Path("../datos/plata/dim_sector_unspsc")
    result = create_dim_sector_unspsc(output_path=output)
    
    print(f"  Status: {result.get('status')}")
    print(f"  Registros (codigos UNSPSC): {result.get('registros')}")
    print(f"  Archivo: {result.get('archivo')}")
    
    return result.get("status") == "success"


def test_create_dim_municipio():
    separator("TEST 11: CREAR dim_municipio")
    
    from transform.create_dimensions import create_dim_municipio
    from pathlib import Path
    
    output = Path("../datos/plata/dim_municipio")
    result = create_dim_municipio(output_path=output)
    
    print(f"  Status: {result.get('status')}")
    print(f"  Registros (municipios): {result.get('registros')}")
    print(f"  Archivo: {result.get('archivo')}")
    print(f"  Columnas: {result.get('columnas')}")
    
    return result.get("status") == "success"


def test_create_facts():
    separator("TEST 12: CREAR TABLAS DE HECHOS (vacias)")
    
    import pandas as pd
    from transform.create_facts import create_fact_vulnerabilidad, create_fact_tejido_productivo, create_fact_contratacion
    from pathlib import Path
    
    # Con DataFrames vacios
    result1 = create_fact_vulnerabilidad(
        cnpv_df=pd.DataFrame(),
        output_path=Path("../datos/plata/fact_vulnerabilidad"),
    )
    print(f"  fact_vulnerabilidad: {result1.get('status')} ({result1.get('registros', 0)} registros)")
    
    result2 = create_fact_tejido_productivo(
        cenu_df=pd.DataFrame(),
        output_path=Path("../datos/plata/fact_tejido_productivo"),
    )
    print(f"  fact_tejido_productivo: {result2.get('status')} ({result2.get('registros', 0)} registros)")
    
    result3 = create_fact_contratacion(
        secop_df=pd.DataFrame(),
        output_path=Path("../datos/plata/fact_contratacion"),
    )
    print(f"  fact_contratacion: {result3.get('status')} ({result3.get('registros', 0)} registros)")
    
    return True


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print()
    print("*" * 60)
    print("  VERIFICACION COMPLETA DEL PIPELINE")
    print("  Arquitectura Medallion - Bronze/Silver/Gold")
    print("*" * 60)
    
    results = {}
    
    results["imports"] = test_imports()
    results["cnpv"] = test_cnpv()
    results["emicron"] = test_emicron()
    results["secop"] = test_secop()
    results["generic"] = test_generic()
    results["validator"] = test_validator()
    results["transform"] = test_transform_functions()
    results["dim_tiempo"] = test_create_dim_tiempo()
    results["dim_ciiu"] = test_create_dim_ciiu()
    results["dim_unspsc"] = test_create_dim_unspsc()
    results["dim_municipio"] = test_create_dim_municipio()
    results["facts"] = test_create_facts()
    
    separator("RESUMEN FINAL")
    for test_name, passed in results.items():
        status = "OK" if passed else "FAIL"
        print(f"  [{status}] {test_name}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"\n  Total: {total} | OK: {passed} | FAIL: {failed}")
    print("=" * 60)
