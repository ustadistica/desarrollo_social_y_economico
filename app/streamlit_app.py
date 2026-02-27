"""
Dashboard interactivo del proyecto.

Uso:
    poetry run streamlit run app/streamlit_app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Observatorio Ustadistica",
    page_icon="\U0001f4ca",
    layout="wide",
)

st.title("\U0001f4ca Observatorio -- Ustadistica 2026-I")
st.info("\U0001f6a7 Dashboard en construccion. Consulta el README para el plan de desarrollo.")
