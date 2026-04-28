import streamlit as st


def render_files(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="title">{texts["files.title"]}</p>', unsafe_allow_html=True)
    st.markdown(
        f'<p class="subtitle">{texts["files.subtitle"]}</p>',
        unsafe_allow_html=True,
    )
