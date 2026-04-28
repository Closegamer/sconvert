import streamlit as st


def render_footer(texts: dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="page-footer">
            <span>{texts["footer.copy"]}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
