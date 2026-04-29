import streamlit as st


def render_footer(texts: dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="page-footer">
            <span>{texts["footer.copy"]}</span>
            <span> · </span>
            <a class="footer-link" href="/?policy=1" target="_self">{texts["footer.privacy"]}</a>
        </div>
        """,
        unsafe_allow_html=True,
    )
