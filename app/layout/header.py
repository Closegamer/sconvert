import streamlit as st

_MENU_VIEWS = frozenset({"home", "units", "latex", "btc", "about"})


def render_header(current_view: str, current_lang: str, texts: dict[str, str]) -> str:
    view_to_label = {
        "home": texts["nav.home"],
        "units": texts["nav.units"],
        # "files": texts["nav.files"],  # Temporarily hidden from menu
        "latex": texts["nav.latex"],
        "btc": texts["nav.btc"],
        "about": texts["nav.about"],
    }
    label_to_view = {value: key for key, value in view_to_label.items()}
    options = [
        view_to_label["home"],
        view_to_label["units"],
        view_to_label["latex"],
        view_to_label["btc"],
        view_to_label["about"],
    ]
    default_by_view = {"home": 0, "units": 1, "latex": 2, "files": 0, "btc": 3, "about": 4}
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
                help=f'{texts["lang.ru"]} / {texts["lang.en"]}',
            )
    selected_lang = "en" if use_english else "ru"
    if selected_lang != current_lang:
        st.session_state.lang = selected_lang
        st.rerun()

    selected_view = label_to_view.get(selected_label, current_view)

    if current_view in _MENU_VIEWS:
        if selected_view != current_view:
            st.session_state.view = selected_view
            st.rerun()
    else:
        # Страницы вне меню (latex_guide, files): первое значение segmented_control — не «переход»,
        # иначе default=главная мгновенно подменяет view.
        if st.session_state.get("_nav_seg_aux_page") != current_view:
            st.session_state._nav_seg_aux_page = current_view
            st.session_state._nav_seg_baseline = selected_label
        elif st.session_state.get("_nav_seg_baseline") != selected_label:
            st.session_state._nav_seg_baseline = selected_label
            new_view = label_to_view.get(selected_label, current_view)
            if new_view in _MENU_VIEWS:
                st.session_state.view = new_view
                st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return str(st.session_state.view)
