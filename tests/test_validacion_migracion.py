"""
Script de Validación de la Migración a PySpark.
Verifica importaciones, módulos del proyecto y sintaxis de archivos modificados.
"""
import sys
import os

# Agregar el directorio del pipeline al sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ingesta y validacion'))

def main():
    resultados = {"ok": 0, "fail": 0}

    def check(nombre, fn):
        try:
            fn()
            print(f"  [OK] {nombre}")
            resultados["ok"] += 1
        except Exception as e:
            print(f"  [FAIL] {nombre}: {e}")
            resultados["fail"] += 1

    # =============================================
    print("=" * 60)
    print("VALIDACION 1: IMPORTACIONES DE LIBRERIAS")
    print("=" * 60)

    check("pyspark", lambda: __import__("pyspark"))
    check("pyspark.sql.SparkSession", lambda: __import__("pyspark.sql", fromlist=["SparkSession"]))
    check("pandas", lambda: __import__("pandas"))
    check("numpy", lambda: __import__("numpy"))
    check("pyarrow", lambda: __import__("pyarrow"))

    # =============================================
    print()
    print("=" * 60)
    print("VALIDACION 2: MODULOS DEL PROYECTO")
    print("=" * 60)

    check("utils.spark_session (get_spark_session)",
          lambda: __import__("utils.spark_session", fromlist=["get_spark_session"]))

    def check_settings():
        from config.settings import Settings
        s = Settings()
        assert hasattr(s, "MODELO_ESTRELLA_PATH"), "Falta MODELO_ESTRELLA_PATH"
        print(f"       MODELO_ESTRELLA_PATH = {s.MODELO_ESTRELLA_PATH}")
        print(f"       BRONZE_PATH = {s.BRONZE_PATH}")
        print(f"       PLATA_PATH = {s.PLATA_PATH}")

    check("config.settings - MODELO_ESTRELLA_PATH", check_settings)

    # =============================================
    print()
    print("=" * 60)
    print("VALIDACION 3: SINTAXIS DE ARCHIVOS MODIFICADOS")
    print("=" * 60)

    import importlib.util
    archivos = [
        ("silver/cleaners/clean_cnpv.py", "ingesta y validacion/silver/cleaners/clean_cnpv.py"),
        ("gold/marts/create_datamart_social.py", "ingesta y validacion/gold/marts/create_datamart_social.py"),
        ("orchestrator.py", "ingesta y validacion/orchestrator.py"),
        ("config/settings.py", "ingesta y validacion/config/settings.py"),
        ("utils/spark_session.py", "ingesta y validacion/utils/spark_session.py"),
    ]
    for nombre, ruta in archivos:
        def verificar(r=ruta, n=nombre):
            full = os.path.join(os.path.dirname(__file__), r)
            if not os.path.exists(full):
                raise FileNotFoundError(f"{full} no existe")
            spec = importlib.util.spec_from_file_location(n.replace("/", "."), full)
            # Solo compilar, no ejecutar
            with open(full, "r", encoding="utf-8") as f:
                compile(f.read(), full, "exec")
        check(f"Sintaxis {nombre}", verificar)



    # =============================================
    print()
    print("=" * 60)
    print("VALIDACION 5: DOCUMENTACION ACTUALIZADA")
    print("=" * 60)

    def check_docs_pyspark(filepath, keyword="PySpark"):
        full = os.path.join(os.path.dirname(__file__), filepath)
        with open(full, "r", encoding="utf-8") as f:
            content = f.read()
        if keyword not in content:
            raise AssertionError(f"No menciona '{keyword}'")

    docs = [
        ("presentacion_ingesta_validacion.md", "PySpark"),
        ("ingesta y validacion/INSTRUCCIONES_EQUIPO.md", "PySpark"),
        ("ingesta y validacion/INSTRUCCIONES_EQUIPO.md", "setup_java"),
        ("ingesta y validacion/requirements.txt", "pyspark"),
    ]
    for filepath, kw in docs:
        check(f"{os.path.basename(filepath)} menciona '{kw}'",
              lambda p=filepath, k=kw: check_docs_pyspark(p, k))

    # =============================================
    print()
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    total = resultados["ok"] + resultados["fail"]
    print(f"  Pasaron:  {resultados['ok']}/{total}")
    print(f"  Fallaron: {resultados['fail']}/{total}")

    if resultados["fail"] == 0:
        print("\n  === TODAS LAS VALIDACIONES PASARON ===")
    else:
        print("\n  === ALGUNAS VALIDACIONES FALLARON ===")

    return resultados["fail"]


if __name__ == "__main__":
    sys.exit(main())
