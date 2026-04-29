from pathlib import Path
import json

import streamlit as st
from lang import EN_TEXTS, RU_TEXTS
from layout import render_footer, render_header
from views import render_about, render_btc, render_files, render_home, render_units
from components import render_privacy_component

try:
    from streamlit_local_storage import LocalStorage  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:
    class LocalStorage:  # type: ignore[no-redef]
        def getItem(self, _key: str, key: str | None = None) -> None:
            return None

        def setItem(self, _key: str, _value: str, key: str | None = None) -> None:
            return None

st.set_page_config(
    page_title="sconvert",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={"Get help": None, "Report a bug": None, "About": None},
)

_css_path = Path(__file__).resolve().parent / "static" / "home.css"
st.markdown(f"<style>{_css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

allowed_views = {"home", "units", "files", "btc", "about"}
if "view" not in st.session_state or st.session_state.view not in allowed_views:
    st.session_state.view = "home"
if "lang" not in st.session_state or st.session_state.lang not in {"ru", "en"}:
    st.session_state.lang = "ru"
if "mobile_menu_open" not in st.session_state:
    st.session_state.mobile_menu_open = False

requested_view = st.query_params.get("view")
if isinstance(requested_view, list):
    requested_view = requested_view[0] if requested_view else None
if requested_view in allowed_views:
    st.session_state.view = requested_view
    st.query_params.clear()
    st.rerun()

if "show_privacy" not in st.session_state:
    st.session_state.show_privacy = False
if "privacy_origin_view" not in st.session_state:
    st.session_state.privacy_origin_view = None

requested_policy = st.query_params.get("policy")
if isinstance(requested_policy, list):
    requested_policy = requested_policy[0] if requested_policy else None
if str(requested_policy) == "1":
    st.session_state.show_privacy = True
    st.session_state.privacy_origin_view = st.session_state.view
    st.query_params.clear()
    st.rerun()

local_storage = LocalStorage()
favorites_storage_key = "sconvert_favorites"


def _favorites_from_storage(raw_value: str | dict[str, bool] | None) -> dict[str, bool]:
    if not raw_value:
        return {}
    if isinstance(raw_value, dict):
        return {k: bool(v) for k, v in raw_value.items()}
    try:
        decoded = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return {}
    if not isinstance(decoded, dict):
        return {}
    return {k: bool(v) for k, v in decoded.items()}


if "favorites_local_bootstrapped" not in st.session_state:
    st.session_state.favorites_local_bootstrapped = False
if "favorites_local_bootstrap_tries" not in st.session_state:
    st.session_state.favorites_local_bootstrap_tries = 0

if st.session_state.view != "privacy" and not st.session_state.favorites_local_bootstrapped:
    local_storage.refreshItems()
    stored_favorites_raw = local_storage.getItem(favorites_storage_key)
    if stored_favorites_raw is not None:
        stored_favorites = _favorites_from_storage(stored_favorites_raw)
        st.session_state.favorite_length = bool(stored_favorites.get("length", False))
        st.session_state.favorite_temperature = bool(stored_favorites.get("temperature", False))
        st.session_state.units_length_expanded = bool(stored_favorites.get("length_expanded", False))
        st.session_state.units_temperature_expanded = bool(stored_favorites.get("temperature_expanded", False))
        st.session_state.favorites_local_bootstrapped = True
        st.session_state.favorites_local_last_payload = json.dumps(
            {
                "length": bool(st.session_state.favorite_length),
                "temperature": bool(st.session_state.favorite_temperature),
                "length_expanded": bool(st.session_state.units_length_expanded),
                "temperature_expanded": bool(st.session_state.units_temperature_expanded),
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    else:
        if "favorite_length" not in st.session_state:
            st.session_state.favorite_length = False
        if "favorite_temperature" not in st.session_state:
            st.session_state.favorite_temperature = False
        if "units_length_expanded" not in st.session_state:
            st.session_state.units_length_expanded = False
        if "units_temperature_expanded" not in st.session_state:
            st.session_state.units_temperature_expanded = False
        st.session_state.favorites_local_bootstrap_tries += 1
        if st.session_state.favorites_local_bootstrap_tries >= 2:
            # Storage may genuinely be empty; allow normal save flow afterwards.
            st.session_state.favorites_local_bootstrapped = True
        else:
            st.rerun()

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
    burger_col, logo_col = st.columns([0.55, 4.45], vertical_alignment="center")
    with burger_col:
        if st.button("✕" if st.session_state.mobile_menu_open else "☰", key="mobile_trigger_btn"):
            st.session_state.mobile_menu_open = not st.session_state.mobile_menu_open
            st.rerun()
    with logo_col:
        st.markdown('<span class="mobile-trigger-logo">sconvert</span>', unsafe_allow_html=True)

if st.session_state.mobile_menu_open:
    with st.container(key="mobile_drawer_overlay"):
        st.markdown("")
    with st.container(key="mobile_drawer"):
        selected_mobile_label = st.radio(
            "menu",
            options=list(view_to_label.values()),
            index=["home", "units", "files", "btc", "about"].index(
                st.session_state.view if st.session_state.view in {"home", "units", "files", "btc", "about"} else "home"
            ),
            key="mobile_drawer_menu",
        )
        selected_mobile_view = label_to_view.get(selected_mobile_label, st.session_state.view)
        if selected_mobile_view != st.session_state.view:
            st.session_state.view = selected_mobile_view
            st.session_state.mobile_menu_open = False
            st.rerun()

        drawer_use_english = st.toggle(
            " ",
            value=st.session_state.lang == "en",
            key="mobile_drawer_lang",
            help=f'{texts["lang.ru"]}/{texts["lang.en"]}',
        )
        selected_drawer_lang = "en" if drawer_use_english else "ru"
        if selected_drawer_lang != st.session_state.lang:
            st.session_state.lang = selected_drawer_lang
            st.rerun()

st.session_state.view = render_header(st.session_state.view, st.session_state.lang, texts)

if st.session_state.show_privacy and st.session_state.view != st.session_state.privacy_origin_view:
    st.session_state.show_privacy = False

if st.session_state.show_privacy:
    render_privacy_component(texts)
else:
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

favorites_payload = json.dumps(
    {
        "length": bool(st.session_state.get("favorite_length", False)),
        "temperature": bool(st.session_state.get("favorite_temperature", False)),
        "length_expanded": bool(st.session_state.get("units_length_expanded", False)),
        "temperature_expanded": bool(st.session_state.get("units_temperature_expanded", False)),
    },
    ensure_ascii=True,
    sort_keys=True,
)
if (
    st.session_state.get("favorites_local_bootstrapped", False)
    and st.session_state.get("favorites_local_last_payload") != favorites_payload
):
    set_key = f"favorites_set_{abs(hash(favorites_payload))}"
    local_storage.setItem(favorites_storage_key, favorites_payload, key=set_key)
    st.session_state.favorites_local_last_payload = favorites_payload

render_footer(texts)
