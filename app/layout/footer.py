import streamlit as st


def render_footer() -> None:
    st.markdown(
        """
        <div class="page-footer">
            <span>writtenBy('Closegamer', 2026)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
