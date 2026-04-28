from pathlib import Path

import streamlit as st
from lang import EN_TEXTS, RU_TEXTS
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
if "lang" not in st.session_state or st.session_state.lang not in {"ru", "en"}:
    st.session_state.lang = "ru"
if "mobile_menu_open" not in st.session_state:
    st.session_state.mobile_menu_open = False

texts = RU_TEXTS if st.session_state.lang == "ru" else EN_TEXTS

view_to_label = {
    "home": texts["nav.home"],
    "units": texts["nav.units"],
    "files": texts["nav.files"],
    "btc": texts["nav.btc"],
    "about": texts["nav.about"],
}
label_to_view = {value: key for key, value in view_to_label.items()}

with st.container(key="mobile_trigger"):
    if st.button("✕" if st.session_state.mobile_menu_open else "☰", key="mobile_trigger_btn"):
        st.session_state.mobile_menu_open = not st.session_state.mobile_menu_open
        st.rerun()

if st.session_state.mobile_menu_open:
    with st.container(key="mobile_drawer_overlay"):
        st.markdown("")
    with st.container(key="mobile_drawer"):
        drawer_use_english = st.toggle(
            "ENG",
            value=st.session_state.lang == "en",
            key="mobile_drawer_lang",
            help=f'{texts["lang.ru"]} / {texts["lang.en"]}',
        )
        selected_mobile_label = st.radio(
            "menu",
            options=list(view_to_label.values()),
            index=["home", "units", "files", "btc", "about"].index(st.session_state.view),
            key="mobile_drawer_menu",
        )
        selected_drawer_lang = "en" if drawer_use_english else "ru"
        if selected_drawer_lang != st.session_state.lang:
            st.session_state.lang = selected_drawer_lang
            st.rerun()

        selected_mobile_view = label_to_view.get(selected_mobile_label, st.session_state.view)
        if selected_mobile_view != st.session_state.view:
            st.session_state.view = selected_mobile_view
            st.session_state.mobile_menu_open = False
            st.rerun()

st.session_state.view = render_header(st.session_state.view, st.session_state.lang, texts)

if st.session_state.view == "home":
    render_home(texts)
elif st.session_state.view == "units":
    render_units(texts)
elif st.session_state.view == "files":
    render_files(texts)
elif st.session_state.view == "btc":
    render_btc(texts)
else:
    render_about(texts)

render_footer(texts)
