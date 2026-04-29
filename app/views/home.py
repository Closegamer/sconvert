import streamlit as st
from components import render_length_converter, render_temperature_converter


def render_home(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="splash">{texts["home.splash"]}</p>', unsafe_allow_html=True)
    favorites = []
    if st.session_state.get("favorite_length", False):
        favorites.append("length")
    if st.session_state.get("favorite_temperature", False):
        favorites.append("temperature")

    if favorites:
        st.markdown(f'<p class="title">{texts["home.favorites.title"]}</p>', unsafe_allow_html=True)
        for favorite in favorites:
            if favorite == "length":
                render_length_converter(texts)
            elif favorite == "temperature":
                render_temperature_converter(texts)
