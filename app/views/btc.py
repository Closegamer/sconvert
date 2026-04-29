import streamlit as st

from components import render_btc_keys_component

def render_btc(texts: dict[str, str]) -> None:
    st.markdown(
        (
            '<p class="subtitle btc-disclaimer">'
            f'{texts["btc.disclaimer"]}'
            "</p>"
        ),
        unsafe_allow_html=True,
    )

    render_btc_keys_component(texts)
