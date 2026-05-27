from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent.parent.resolve()
DATOS_BRONZE = ROOT / "data" / "bronze"


def create_mock_cnpv():
    data = {
        "municipio": ["Bogota", "Medellin", "Cali", "Barranquilla", "Cartagena"],
        "divipola_municipio": ["11001", "05001", "76001", "08001", "13001"],
        "poblacion": [7900000, 2500000, 2200000, 1300000, 1000000],
        "anio": [2018] * 5,
    }
    df = pd.DataFrame(data)
    df["_ingestion_timestamp"] = datetime.now().isoformat()
    df["_source"] = "Mock CNPV"

    out_dir = DATOS_BRONZE / "cnpv" / f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "cnpv_data.parquet", index=False)
    print(f"Mock CNPV creado en {out_dir}")


def create_mock_emicron():
    """Crear EMICRON demo compatible con el fallback de factores separados."""
    out_dir = DATOS_BRONZE / "emicron" / "2019"
    out_dir.mkdir(parents=True, exist_ok=True)

    identificacion = pd.DataFrame(
        {
            "DIRECTORIO": [1, 2, 3],
            "SECUENCIA_P": [1, 1, 1],
            "SECUENCIA_ENCUESTA": [1, 1, 1],
            "COD_DEPTO": ["05", "05", "08"],
            "F_EXP": [0.0, 0.0, 0.0],
            "_ingestion_timestamp": datetime.now().isoformat(),
            "_source": "Mock EMICRON",
            "_source_version": "EMICRON_2019",
            "_emicron_year": 2019,
        }
    )
    identificacion.to_parquet(
        out_dir / "emicron_modulo_de_identificacion_2019_raw.parquet",
        index=False,
    )

    factores = pd.DataFrame(
        {
            "DIRECTORIO": [1, 2, 3],
            "SECUENCIA_P": [1, 1, 1],
            "SECUENCIA_ENCUESTA": [1, 1, 1],
            "fex_c": [100.0, 120.0, 80.0],
            "_ingestion_timestamp": datetime.now().isoformat(),
            "_source": "Mock EMICRON",
            "_source_version": "EMICRON_2019",
            "_emicron_year": 2019,
        }
    )
    factores.to_parquet(
        out_dir / "emicron_fex_proyecciones_cnpv_2018_2019_2019_raw.parquet",
        index=False,
    )
    print(f"Mock EMICRON creado en {out_dir}")


def setup_secop_data():
    source = ROOT / "data" / "secop_nuevos1.parquet"
    if source.exists():
        df = pd.read_parquet(source)
        df["_ingestion_timestamp"] = datetime.now().isoformat()

        out_dir = DATOS_BRONZE / "secop_ii" / f"ingestion_date={datetime.now().strftime('%Y-%m-%d')}"
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_dir / "secop_data.parquet", index=False)
        print(f"Datos SECOP reales movidos a {out_dir}")
    else:
        print("No se encontro data/secop_nuevos1.parquet")


if __name__ == "__main__":
    create_mock_cnpv()
    create_mock_emicron()
    setup_secop_data()
