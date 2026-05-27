from pathlib import Path

import pandas as pd

from src.transformacion.silver.cleaners.clean_emicron import clean_emicron_data


def test_clean_emicron_uses_factor_file_when_f_exp_is_zero(tmp_path: Path):
    bronze_path = tmp_path / "bronze" / "emicron"
    silver_path = tmp_path / "silver"
    bronze_path.mkdir(parents=True)

    auth_2019 = pd.DataFrame(
        {
            "DIRECTORIO": [1, 2],
            "SECUENCIA_P": [1, 1],
            "SECUENCIA_ENCUESTA": [1, 1],
            "COD_DEPTO": ["05", "05"],
            "F_EXP": [0.0, 0.0],
            "_source_version": ["EMICRON_2019", "EMICRON_2019"],
            "_emicron_year": [2019, 2019],
        }
    )
    auth_2019.to_parquet(
        bronze_path / "emicron_modulo_de_identificacion_2019_raw.parquet",
        index=False,
    )

    factors_2019 = pd.DataFrame(
        {
            "DIRECTORIO": [1, 2],
            "SECUENCIA_P": [1, 1],
            "SECUENCIA_ENCUESTA": [1, 1],
            "fex_c": [10.5, 20.5],
            "_source_version": ["EMICRON_2019", "EMICRON_2019"],
            "_emicron_year": [2019, 2019],
        }
    )
    factors_2019.to_parquet(
        bronze_path / "emicron_fex_proyecciones_cnpv_2018_2019_2019_raw.parquet",
        index=False,
    )

    auth_2021 = pd.DataFrame(
        {
            "DIRECTORIO": [3],
            "SECUENCIA_P": [1],
            "SECUENCIA_ENCUESTA": [1],
            "COD_DEPTO": ["08"],
            "F_EXP": [15.0],
            "_source_version": ["EMICRON_2021"],
            "_emicron_year": [2021],
        }
    )
    auth_2021.to_parquet(
        bronze_path / "emicron_modulo_de_identificacion_2021_raw.parquet",
        index=False,
    )

    result = clean_emicron_data(bronze_path, silver_path, settings=None)

    assert result["status"] == "success"
    assert result["factores_fallback"] == [
        {
            "anio": 2019,
            "factor_col": "fex_c",
            "source": "emicron_fex_proyecciones_cnpv_2018_2019_2019_raw.parquet",
            "filas": 2,
            "suma_factor": 31.0,
        }
    ]

    out = pd.read_parquet(silver_path / "silver_emicron_agregado.parquet")
    totals = out.groupby("anio_key")["volumen_micronegocios_exp"].sum().to_dict()

    assert totals[2019] == 31.0
    assert totals[2021] == 15.0
    assert out.duplicated(subset=["divipola_key", "anio_key"]).sum() == 0
