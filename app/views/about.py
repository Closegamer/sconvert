import streamlit as st


def render_about() -> None:
    st.markdown('<p class="title">О проекте</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">sconvert — проект конвертации форматов и единиц с упором на простоту и расширяемость.</p>',
        unsafe_allow_html=True,
    )
