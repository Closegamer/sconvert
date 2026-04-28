import streamlit as st


def render_about(texts: dict[str, str]) -> None:
    st.markdown(
        f'<p class="subtitle">{texts["about.subtitle"]}</p>',
        unsafe_allow_html=True,
    )
