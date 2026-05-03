import streamlit as st

_VIEW_ORDER = ("home", "units", "latex", "btc", "about")
_MENU_VIEWS = frozenset(_VIEW_ORDER)


def render_header(current_lang: str, texts: dict[str, str]) -> str:
    if "_sync_lang_toggles_to" in st.session_state:
        synced_value = bool(st.session_state.pop("_sync_lang_toggles_to"))
        st.session_state["sidebar_lang_toggle"] = synced_value
        st.session_state["desktop_lang_toggle"] = synced_value

    view_to_label = {
        "home": texts["nav.favorites"],
        "units": texts["nav.units"],
        "latex": texts["nav.latex"],
        "btc": texts["nav.btc"],
        "about": texts["nav.about"]
    }
    label_to_view = {value: key for key, value in view_to_label.items()}
    options = [view_to_label[v] for v in _VIEW_ORDER]
    default_by_view = {
        "home": 0,
        "units": 1,
        "latex": 2,
        "btc": 3,
        "about": 4
    }

    with st.sidebar:
        st.markdown(
            f'<p class="sidebar-brand">{texts["nav.home"]}</p>',
            unsafe_allow_html=True,
        )
        for view in _VIEW_ORDER:
            label = view_to_label[view]
            active = st.session_state.view == view
            if st.button(
                label,
                key=f"sb_nav_{view}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.view = view

        st.divider()
        use_english_sb = st.toggle(
            texts["sidebar.english_ui"],
            value=current_lang == "en",
            help=f'{texts["lang.ru"]} / {texts["lang.en"]}',
            key="sidebar_lang_toggle",
        )

    with st.container(key="mobile_header_brand"):
        st.markdown(
            f'<span class="mobile-header-brand-text">{texts["nav.home"]}</span>',
            unsafe_allow_html=True,
        )

    current_view = str(st.session_state.view)
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
            use_english_dk = st.toggle(
                " ",
                value=current_lang == "en",
                help=f'{texts["lang.ru"]} / {texts["lang.en"]}',
                key="desktop_lang_toggle",
            )

    selected_view = label_to_view.get(selected_label, current_view)
    need_rerun = False
    if current_view in _MENU_VIEWS:
        if selected_view != st.session_state.view:
            st.session_state.view = selected_view
            need_rerun = True
    else:
        if st.session_state.get("_nav_seg_aux_page") != current_view:
            st.session_state._nav_seg_aux_page = current_view
            st.session_state._nav_seg_baseline = selected_label
        elif st.session_state.get("_nav_seg_baseline") != selected_label:
            st.session_state._nav_seg_baseline = selected_label
            new_view = label_to_view.get(selected_label, current_view)
            if new_view in _MENU_VIEWS:
                st.session_state.view = new_view
                need_rerun = True

    new_lang = current_lang
    if use_english_sb != (current_lang == "en"):
        new_lang = "en" if use_english_sb else "ru"
    elif use_english_dk != (current_lang == "en"):
        new_lang = "en" if use_english_dk else "ru"
    if new_lang != current_lang:
        st.session_state.lang = new_lang
        st.session_state._sync_lang_toggles_to = new_lang == "en"
        need_rerun = True

    if need_rerun:
        st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return str(st.session_state.view)
