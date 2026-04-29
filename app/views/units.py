import streamlit as st

from components import render_acceleration_converter, render_angle_converter, render_area_converter, render_current_converter, render_data_converter, render_density_converter, render_energy_converter, render_flow_converter, render_force_converter, render_frequency_converter, render_illuminance_converter, render_length_converter, render_mass_converter, render_power_converter, render_pressure_converter, render_radiation_converter, render_resistance_converter, render_speed_converter, render_temperature_converter, render_time_converter, render_voltage_converter, render_volume_converter


def render_units(texts: dict[str, str]) -> None:
    if "units_collapse_all_token" not in st.session_state:
        st.session_state.units_collapse_all_token = 0

    _left, right_col = st.columns([7, 3], vertical_alignment="center")
    with right_col:
        if st.button(texts["units.collapse_all"], key="units_collapse_all_btn", use_container_width=True):
            st.session_state.units_collapse_all_token += 1
            st.rerun()

    render_length_converter(texts)
    render_area_converter(texts)
    render_mass_converter(texts)
    render_volume_converter(texts)
    render_speed_converter(texts)
    render_time_converter(texts)
    render_pressure_converter(texts)
    render_energy_converter(texts)
    render_power_converter(texts)
    render_force_converter(texts)
    render_frequency_converter(texts)
    render_angle_converter(texts)
    render_density_converter(texts)
    render_flow_converter(texts)
    render_acceleration_converter(texts)
    render_current_converter(texts)
    render_voltage_converter(texts)
    render_resistance_converter(texts)
    render_illuminance_converter(texts)
    render_radiation_converter(texts)
    render_data_converter(texts)
    render_temperature_converter(texts)
