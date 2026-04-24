"""
Validador de configuración de datos.

Este script verifica que la carpeta 'Datos' esté en el lugar correcto
y que contenga todos los archivos y subcarpetas requeridas.

Úsalo para diagnosticar problemas de ingesta.
"""

import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    # Obtener rutas
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    datos_folder = PROJECT_ROOT.parent.parent / "Datos"

    print("\n" + "="*70)
    print("VERIFICADOR DE CONFIGURACIÓN DE DATOS")
    print("="*70)

    print(f"\n📍 Carpeta del Proyecto: {PROJECT_ROOT}")
    print(f"📍 Carpeta Datos Esperada: {datos_folder}")

    # Verificar carpeta Datos
    print("\n" + "-"*70)
    print("1. VERIFICANDO CARPETA DATOS/")
    print("-"*70)

    if datos_folder.exists():
        print(f"✅ Encontrada: {datos_folder}")
    else:
        print(f"❌ NO ENCONTRADA: {datos_folder}")
        print("\n   Solución:")
        print(f"   1. Copia la carpeta 'Datos' a: {PROJECT_ROOT.parent.parent}/")
        print("   2. O configura las rutas en .env (ver SETUP_DATOS.md)")
        return False

    # Verificar subcarpetas
    print("\n" + "-"*70)
    print("2. VERIFICANDO SUBCARPETAS")
    print("-"*70)

    required_dirs = {
        "CENSO 2018 dep": "Censos nacionales (33 CSVs departamentales)",
        "EMICRON 2024": "Encuesta micronegocios 2024",
    }

    # Buscar carpetas EMICRON
    emicron_dirs = sorted([d for d in datos_folder.glob("EMICRON *") if d.is_dir()])

    for dir_name, description in required_dirs.items():
        dir_path = datos_folder / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ → {description}")
        else:
            print(f"⚠️  {dir_name}/ → NO encontrado")

    if emicron_dirs:
        print(f"\n✅ Encontrados {len(emicron_dirs)} años de EMICRON:")
        for emicron_dir in emicron_dirs:
            csv_count = len(list(emicron_dir.glob("*.csv")))
            print(f"   • {emicron_dir.name} ({csv_count} CSVs)")
    else:
        print(f"\n⚠️  No hay carpetas EMICRON (EMICRON 2019/, EMICRON 2020/, etc.)")

    # Verificar archivos raíz
    print("\n" + "-"*70)
    print("3. VERIFICANDO ARCHIVOS CSV PRINCIPALES")
    print("-"*70)

    required_files = {
        "SECOP_I_-_Procesos_de_Compra_Pública_*.csv": "SECOP I (10.5GB)",
        "SECOP_II_-_Contratos_Electrónicos_*.csv": "SECOP II (9.6GB)",
        "PPED-AreaDep-2018-2050_VP.csv": "Proyecciones DANE",
    }

    all_files_ok = True

    for pattern, description in required_files.items():
        matches = list(datos_folder.glob(pattern))
        if matches:
            file_path = matches[-1]  # El más reciente si hay varios
            size_gb = file_path.stat().st_size / (1024**3)
            print(f"✅ {file_path.name}")
            print(f"   Tamaño: {size_gb:.2f} GB → {description}")
        else:
            print(f"❌ No encontrado patrón: {pattern}")
            print(f"   Descripción: {description}")
            all_files_ok = False

    # Resumen
    print("\n" + "="*70)
    print("RESUMEN")
    print("="*70)

    if not all_files_ok:
        print("\n⚠️  FALTAN ARCHIVOS")
        print("\nPasos para resolver:")
        print("1. Verifica que los nombres de archivos sean EXACTOS")
        print("   • Deben coincidir con los patrones mostrados arriba")
        print("   • Los nombres son sensibles a mayúsculas/minúsculas en Linux/Mac")
        print(f"2. Coloca los archivos en: {datos_folder}/")
        print("3. Vuelve a ejecutar este validador")
        return False

    if not emicron_dirs:
        print("\n⚠️  No se encontraron años de EMICRON")
        print("   Es posible que falten las carpetas EMICRON 2019/, EMICRON 2020/, etc.")
        print(f"   Colócalas en: {datos_folder}/")

    print("\n✅ CONFIGURACIÓN CORRECTA")
    print("\nYa puedes ejecutar el pipeline:")
    print("  python src/ingesta/run_bronze.py")
    print("  python src/transformacion/run_silver.py")
    print("  python src/transformacion/run_gold.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
