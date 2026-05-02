import io

import streamlit as st

from .clipboard_iframe import render_clipboard_iframe_button


def _tex_for_streamlit_latex(raw: str) -> str:
    """st.latex ожидает выражение без обёрток \\(...\\), $...$, \\[...\\] — иначе они показываются текстом."""
    t = raw.strip()
    if not t:
        return t
    if len(t) >= 4 and t.startswith("$$") and t.endswith("$$"):
        return t[2:-2].strip()
    if len(t) >= 2 and t[0] == "$" and t[-1] == "$" and not t.startswith("$$"):
        return t[1:-1].strip()
    if len(t) >= 4 and t.startswith("\\(") and t.endswith("\\)"):
        return t[2:-2].strip()
    if len(t) >= 4 and t.startswith("\\[") and t.endswith("\\]"):
        return t[2:-2].strip()
    return t


def _latex_to_png_bytes(tex: str, *, dpi: int = 200) -> bytes | None:
    if not tex.strip():
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.mathtext import math_to_image
    except ImportError:
        return None

    def _render_one(expr: str) -> bytes | None:
        buf = io.BytesIO()
        try:
            math_to_image(f"${expr}$", buf, dpi=dpi, format="png", color="black")
            out = buf.getvalue()
            return out if out else None
        except Exception:
            return None

    primary = _render_one(tex)
    if primary is not None:
        return primary
    simplified = tex.replace("\\,", " ").replace("\\:", " ").replace("\\;", " ")
    if simplified != tex:
        return _render_one(simplified)
    return None


def _preview_heading_and_copy(texts: dict[str, str], raw_source: str) -> None:
    st.markdown(f"**{texts['latex.preview_label']}**")


def _source_heading_and_copy(texts: dict[str, str], raw_source: str) -> None:
    title_col, btn_col = st.columns([4, 1])
    with title_col:
        st.markdown(f"**{texts['latex.input_label']}**")
    with btn_col:
        render_clipboard_iframe_button(
            label=texts["latex.copy_source_button"].lower(),
            value=raw_source,
            element_key="latex_source_tex_clip",
            height=32,
            iframe_width=160,
        )


def _formula_png_and_download(texts: dict[str, str], normalized: str) -> None:
    png = _latex_to_png_bytes(normalized)
    if png is None:
        st.caption(texts["latex.png_unavailable"])
        return
    st.caption(texts["latex.formula_png_label"])
    with st.container(key="latex_formula_png"):
        st.image(io.BytesIO(png), use_container_width=False)
    st.download_button(
        label=texts["latex.download_png"],
        data=png,
        file_name="latex-formula.png",
        mime="image/png",
        key="latex_download_formula_png",
    )


def _preview_body(texts: dict[str, str], raw: str, normalized: str) -> None:
    _preview_heading_and_copy(texts, raw)
    st.latex(normalized)
    _formula_png_and_download(texts, normalized)


def render_latex_preview(texts: dict[str, str]) -> None:
    if "latex_input" not in st.session_state:
        st.session_state.latex_input = texts["latex.example"]

    st.markdown(
        f'<p style="text-align:left; margin:0 0 0.2rem 0; color:var(--muted);">{texts["latex.lead"]} <a class="footer-link" href="/?view=latex_guide" target="_self">{texts["footer.latex_guide"]}</a>.</p><br><br>',
        unsafe_allow_html=True,
    )
    _source_heading_and_copy(texts, str(st.session_state.get("latex_input", "")))
    st.text_area(
        texts["latex.input_label"],
        key="latex_input",
        height=160,
        label_visibility="collapsed",
    )

    raw_input = str(st.session_state.get("latex_input", ""))
    raw = raw_input.strip()

    if not raw:
        st.markdown(f"**{texts['latex.preview_label']}**")
        st.caption(texts["latex.empty_hint"])
    else:
        normalized = _tex_for_streamlit_latex(raw)
        if normalized != raw:
            prev_left, prev_right = st.columns([3, 2])
            with prev_left:
                _preview_body(texts, raw_input, normalized)
            with prev_right:
                st.caption(texts["latex.clipboard_result"])
                st.code(normalized, language="tex", line_numbers=False, wrap_lines=True)
        else:
            _preview_body(texts, raw_input, normalized)

    st.caption(texts["latex.hint"])
