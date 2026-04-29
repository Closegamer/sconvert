import streamlit as st
from components import render_acceleration_converter, render_angle_converter, render_area_converter, render_current_converter, render_data_converter, render_density_converter, render_energy_converter, render_flow_converter, render_force_converter, render_frequency_converter, render_illuminance_converter, render_length_converter, render_mass_converter, render_power_converter, render_pressure_converter, render_radiation_converter, render_resistance_converter, render_speed_converter, render_temperature_converter, render_time_converter, render_voltage_converter, render_volume_converter


def render_home(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="splash">{texts["home.splash"]}</p>', unsafe_allow_html=True)
    favorites = []
    if st.session_state.get("favorite_length", False):
        favorites.append("length")
    if st.session_state.get("favorite_temperature", False):
        favorites.append("temperature")
    if st.session_state.get("favorite_mass", False):
        favorites.append("mass")
    if st.session_state.get("favorite_area", False):
        favorites.append("area")
    if st.session_state.get("favorite_volume", False):
        favorites.append("volume")
    if st.session_state.get("favorite_speed", False):
        favorites.append("speed")
    if st.session_state.get("favorite_time", False):
        favorites.append("time")
    if st.session_state.get("favorite_pressure", False):
        favorites.append("pressure")
    if st.session_state.get("favorite_energy", False):
        favorites.append("energy")
    if st.session_state.get("favorite_power", False):
        favorites.append("power")
    if st.session_state.get("favorite_force", False):
        favorites.append("force")
    if st.session_state.get("favorite_frequency", False):
        favorites.append("frequency")
    if st.session_state.get("favorite_angle", False):
        favorites.append("angle")
    if st.session_state.get("favorite_density", False):
        favorites.append("density")
    if st.session_state.get("favorite_flow", False):
        favorites.append("flow")
    if st.session_state.get("favorite_acc", False):
        favorites.append("acc")
    if st.session_state.get("favorite_current", False):
        favorites.append("current")
    if st.session_state.get("favorite_voltage", False):
        favorites.append("voltage")
    if st.session_state.get("favorite_resistance", False):
        favorites.append("resistance")
    if st.session_state.get("favorite_illuminance", False):
        favorites.append("illuminance")
    if st.session_state.get("favorite_radiation", False):
        favorites.append("radiation")
    if st.session_state.get("favorite_data", False):
        favorites.append("data")

    if favorites:
        st.markdown(f'<p class="title">{texts["home.favorites.title"]}</p>', unsafe_allow_html=True)
        for favorite in favorites:
            if favorite == "length":
                render_length_converter(texts)
            elif favorite == "area":
                render_area_converter(texts)
            elif favorite == "mass":
                render_mass_converter(texts)
            elif favorite == "volume":
                render_volume_converter(texts)
            elif favorite == "speed":
                render_speed_converter(texts)
            elif favorite == "time":
                render_time_converter(texts)
            elif favorite == "pressure":
                render_pressure_converter(texts)
            elif favorite == "energy":
                render_energy_converter(texts)
            elif favorite == "power":
                render_power_converter(texts)
            elif favorite == "force":
                render_force_converter(texts)
            elif favorite == "frequency":
                render_frequency_converter(texts)
            elif favorite == "angle":
                render_angle_converter(texts)
            elif favorite == "density":
                render_density_converter(texts)
            elif favorite == "flow":
                render_flow_converter(texts)
            elif favorite == "acc":
                render_acceleration_converter(texts)
            elif favorite == "current":
                render_current_converter(texts)
            elif favorite == "voltage":
                render_voltage_converter(texts)
            elif favorite == "resistance":
                render_resistance_converter(texts)
            elif favorite == "illuminance":
                render_illuminance_converter(texts)
            elif favorite == "radiation":
                render_radiation_converter(texts)
            elif favorite == "data":
                render_data_converter(texts)
            elif favorite == "temperature":
                render_temperature_converter(texts)
