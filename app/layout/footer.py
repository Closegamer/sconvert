import streamlit as st

def render_footer(texts: dict[str, str]) -> None:
    st.markdown(
        f"""
        <div class="page-footer">
            <span>{texts["footer.copy"]}</span>
            <span> · </span>
            <a class="footer-link" href="/?policy=1" target="_self">{texts["footer.privacy"]}</a>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
