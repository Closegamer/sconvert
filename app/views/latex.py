import streamlit as st

from components import render_latex_preview


def render_latex(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="subtitle">{texts["latex.title"]}</p>', unsafe_allow_html=True)
    render_latex_preview(texts)
