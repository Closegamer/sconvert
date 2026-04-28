from pathlib import Path

import streamlit as st
from layout import render_footer, render_header
from views import render_about, render_btc, render_files, render_home, render_units

st.set_page_config(
    page_title="sconvert",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

_css_path = Path(__file__).resolve().parent / "static" / "home.css"
st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

if "view" not in st.session_state or st.session_state.view not in {"home", "units", "files", "btc", "about"}:
    st.session_state.view = "home"

st.session_state.view = render_header(st.session_state.view)

if st.session_state.view == "home":
    render_home()
elif st.session_state.view == "units":
    render_units()
elif st.session_state.view == "files":
    render_files()
elif st.session_state.view == "btc":
    render_btc()
else:
    render_about()

render_footer()
