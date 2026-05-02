from pathlib import Path

import streamlit as st

_CONTENT_DIR = Path(__file__).resolve().parent.parent / "content"


def render_latex_guide(texts: dict[str, str]) -> None:
    lang = str(st.session_state.get("lang", "ru"))
    if lang not in ("ru", "en"):
        lang = "ru"
    path = _CONTENT_DIR / f"latex_guide_{lang}.md"
    body = path.read_text(encoding="utf-8")
    st.markdown(
        f'<p class="subtitle">{texts["latex_guide.title"]}</p>',
        unsafe_allow_html=True,
    )
    st.markdown(body)
