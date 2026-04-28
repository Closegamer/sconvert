import streamlit as st


def render_header(current_view: str) -> str:
    left_col, right_col = st.columns([1.1, 2.4], vertical_alignment="center")

    with left_col:
        st.markdown('<span class="brand-link">sconvert</span>', unsafe_allow_html=True)

    selected_view = current_view
    with right_col:
        menu_col_1, menu_col_2, _menu_spacer = st.columns([1.6, 1.0, 1.6], gap="small")
        with menu_col_1:
            if st.button(
                "Единицы измерения",
                key="nav_units",
                type="primary" if current_view == "units" else "secondary",
            ):
                selected_view = "units"
                st.session_state.view = selected_view
                st.rerun()
        with menu_col_2:
            if st.button(
                "О проекте",
                key="nav_about",
                type="primary" if current_view == "about" else "secondary",
            ):
                selected_view = "about"
                st.session_state.view = selected_view
                st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return selected_view
