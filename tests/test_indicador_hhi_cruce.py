import pandas as pd

from src.features.indicador_hhi_cruce import (
    attach_order,
    classify_order,
    compute_hhi,
    prepare_transactions,
)


def test_hhi_deduplica_contrato_y_calcula_participaciones(tmp_path):
    tx = pd.DataFrame(
        [
            {
                "id_contrato": "A",
                "divipola_key": "11001",
                "anio_key": 2024,
                "valor_del_contrato": 80,
                "nit_contratista": "9001",
                "orden_entidad": "Territorial",
            },
            {
                "id_contrato": "B",
                "divipola_key": "11001",
                "anio_key": 2024,
                "valor_del_contrato": 20,
                "nit_contratista": "9002",
                "orden_entidad": "Territorial",
            },
            {
                "id_contrato": "B",
                "divipola_key": "11001",
                "anio_key": 2024,
                "valor_del_contrato": 20,
                "nit_contratista": "9002",
                "orden_entidad": "Territorial",
            },
        ]
    )

    prepared = prepare_transactions(tx)
    prepared = attach_order(prepared, tmp_path)
    master = compute_hhi(prepared)

    assert len(prepared) == 2
    assert len(master) == 1
    assert round(master.loc[0, "HHI"], 6) == 6800.0
    assert master.loc[0, "total_contratos"] == 2
    assert master.loc[0, "total_proveedores"] == 2


def test_clasifica_orden_sin_imputar_no_definidos_como_territorial():
    assert classify_order("Nacional Centralizado") == "NACIONAL"
    assert classify_order("Territorial Distrital Municipal Nivel 1") == "TERRITORIAL"
    assert classify_order("Corporacion Autonoma") == "OTRO"
    assert classify_order("No definido") == "NO_DEFINIDO"
    assert classify_order(None) == "NO_DEFINIDO"

