import streamlit as st


def render_files() -> None:
    st.markdown('<p class="title">Файлы</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Раздел в разработке. Здесь будет конвертация файлов.</p>',
        unsafe_allow_html=True,
    )
