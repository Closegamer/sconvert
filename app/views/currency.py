import streamlit as st
from components.currency import render_currency_converter


def render_currency(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="title">{texts.get("curr.title", "Валюты")}</p>', unsafe_allow_html=True)
    render_currency_converter(texts)
