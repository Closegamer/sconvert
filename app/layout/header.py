import streamlit as st

try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:
    option_menu = None


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
        if option_menu is not None:
            selected_label = option_menu(
                menu_title=None,
                options=[view_to_label["units"], view_to_label["about"]],
                default_index=default_index,
                orientation="horizontal",
                key="header_menu",
                styles={
                    "container": {
                        "padding": "0",
                        "background-color": "transparent",
                    },
                    "nav": {
                        "gap": "0.45rem",
                        "justify-content": "flex-start",
                        "flex-wrap": "wrap",
                    },
                    "nav-link": {
                        "min-height": "2.15rem",
                        "padding": "0.4rem 0.9rem",
                        "font-size": "0.95rem",
                        "font-weight": "500",
                        "border-radius": "0.5rem",
                        "border": "1px solid var(--btn-border)",
                        "background": "linear-gradient(180deg, var(--btn-bg-top) 0%, var(--panel) 100%)",
                        "color": "var(--text)",
                        "white-space": "normal",
                        "line-height": "1.15",
                        "text-align": "center",
                    },
                    "nav-link-selected": {
                        "border": "1px solid var(--btn-border-hover)",
                        "background": "linear-gradient(180deg, var(--accent-top) 0%, var(--accent) 100%)",
                        "color": "var(--accent-text)",
                    },
                },
            )
        else:
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
