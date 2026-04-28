import streamlit as st


def render_btc() -> None:
    st.markdown('<p class="title">Биткоин (BTC)</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Раздел в разработке. Здесь будет конвертер и инструменты для BTC.</p>',
        unsafe_allow_html=True,
    )
