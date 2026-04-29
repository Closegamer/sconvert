import streamlit as st


def render_privacy_component(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="title">{texts["privacy.title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{texts["privacy.text"]}</p>', unsafe_allow_html=True)
