import streamlit as st


def render_header(current_view: str) -> str:
    left_col, right_col = st.columns([1.1, 2.4], vertical_alignment="center")

    with left_col:
        st.markdown('<span class="brand-link">sconvert</span>', unsafe_allow_html=True)

    view_to_label = {
        "units": "Единицы измерения",
        "about": "О проекте",
    }
    label_to_view = {value: key for key, value in view_to_label.items()}

    default_index = 0 if current_view != "about" else 1
    with right_col:
        selected_label = st.segmented_control(
            "menu",
            options=[view_to_label["units"], view_to_label["about"]],
            default=view_to_label["about"] if default_index == 1 else view_to_label["units"],
            label_visibility="collapsed",
        )

    selected_view = label_to_view.get(selected_label, current_view)
    if selected_view != current_view:
        st.session_state.view = selected_view
        st.rerun()

    st.markdown('<div class="top-nav-divider"></div>', unsafe_allow_html=True)
    return selected_view
