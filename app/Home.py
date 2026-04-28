from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="sconvert",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

_css_path = Path(__file__).resolve().parent / "static" / "home.css"
st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

if "view" not in st.session_state or st.session_state.view not in {"home", "units"}:
    st.session_state.view = "home"

query_view = st.query_params.get("view", "")
if isinstance(query_view, list):
    query_view = query_view[0] if query_view else ""
if query_view in {"home", "units"}:
    st.session_state.view = query_view

left_col, right_col = st.columns([1.1, 2.4], vertical_alignment="center")
with left_col:
    st.markdown('<a class="brand-link" href="?view=home">sconvert</a>', unsafe_allow_html=True)
with right_col:
    if st.button("Единицы измерения", key="go_units"):
        st.session_state.view = "units"

st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)

if st.session_state.view == "home":
    st.markdown('<p class="splash">проект sconvert</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="title">Единицы измерения</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">Раздел в разработке. Здесь будет конвертер единиц.</p>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="page-footer">
        <span>writtenBy('Closegamer', 2026)</span>
    </div>
    """,
    unsafe_allow_html=True,
)
