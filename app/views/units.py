import streamlit as st

from components import render_length_converter, render_temperature_converter


def render_units(texts: dict[str, str]) -> None:
    if "units_collapse_all_token" not in st.session_state:
        st.session_state.units_collapse_all_token = 0

    _left, right_col = st.columns([7, 3], vertical_alignment="center")
    with right_col:
        if st.button(texts["units.collapse_all"], key="units_collapse_all_btn", use_container_width=True):
            st.session_state.units_collapse_all_token += 1
            st.rerun()

    render_length_converter(texts)
    render_temperature_converter(texts)
