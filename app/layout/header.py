import streamlit as st


def render_header(current_view: str) -> str:
    view_to_label = {
        "home": "sconvert",
        "units": "Единицы измерения",
        "files": "Файлы",
        "btc": "Биткоин (BTC)",
        "about": "О проекте",
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
    _left_spacer, menu_col, _right_spacer = st.columns([1, 8, 1], vertical_alignment="center")
    with menu_col:
        selected_label = st.segmented_control(
            "menu",
            options=options,
            default=options[default_index],
            label_visibility="collapsed",
        )
    selected_view = label_to_view.get(selected_label, current_view)
    if selected_view != current_view:
        st.session_state.view = selected_view
        st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return selected_view
