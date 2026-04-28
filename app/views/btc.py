import streamlit as st


def render_btc(texts: dict[str, str]) -> None:
    st.markdown(
        f'<p class="subtitle">{texts["btc.subtitle"]}</p>',
        unsafe_allow_html=True,
    )
