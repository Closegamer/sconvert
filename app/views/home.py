import streamlit as st


def render_home(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="splash">{texts["home.splash"]}</p>', unsafe_allow_html=True)
