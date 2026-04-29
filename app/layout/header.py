import streamlit as st


def render_header(current_view: str, current_lang: str, texts: dict[str, str]) -> str:
    view_to_label = {
        "home": texts["nav.home"],
        "units": texts["nav.units"],
        "files": texts["nav.files"],
        "btc": texts["nav.btc"],
        "about": texts["nav.about"],
    }
    label_to_view = {value: key for key, value in view_to_label.items()}
    options = [
        view_to_label["home"],
        view_to_label["units"],
        view_to_label["files"],
        view_to_label["btc"],
        view_to_label["about"],
    ]
    default_by_view = {"home": 0, "units": 1, "files": 2, "btc": 3, "about": 4}
    default_index = default_by_view.get(current_view, 0)
    with st.container(key="desktop_nav"):
        _left_spacer, menu_col, lang_col = st.columns([0.6, 8.2, 1.2], vertical_alignment="center")
        with menu_col:
            selected_label = st.segmented_control(
                "menu",
                options=options,
                default=options[default_index],
                label_visibility="collapsed",
            )

        with lang_col:
            use_english = st.toggle(
                " ",
                value=current_lang == "en",
                key="lang_switch",
                help=f'{texts["lang.ru"]} / {texts["lang.en"]}',
            )
    selected_lang = "en" if use_english else "ru"
    if selected_lang != current_lang:
        st.session_state.lang = selected_lang
        st.rerun()

    selected_view = label_to_view.get(selected_label, current_view)
    if selected_view != current_view:
        st.session_state.view = selected_view
        st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return selected_view
