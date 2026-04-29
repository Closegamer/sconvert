import streamlit as st


def render_unit_panel_header(
    *,
    panel_key: str,
    title: str,
    expanded_key: str,
    expand_button_key: str,
    favorite_toggle_key: str,
    favorite_state_key: str,
) -> None:
    with st.container(key=panel_key):
        title_col, favorite_col = st.columns([8, 2], vertical_alignment="center")
        with title_col:
            title_button_col, title_toggle_col = st.columns([9, 1], vertical_alignment="center")
            with title_button_col:
                if st.button(
                    f'{"▼" if st.session_state[expanded_key] else "▶"} {title}',
                    key=expand_button_key,
                    use_container_width=True,
                ):
                    st.session_state[expanded_key] = not bool(st.session_state[expanded_key])
                    st.rerun()
            with title_toggle_col:
                st.toggle("★", key=favorite_toggle_key)
                st.session_state[favorite_state_key] = bool(st.session_state[favorite_toggle_key])
        with favorite_col:
            pass
