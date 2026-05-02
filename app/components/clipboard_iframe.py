import base64
import hashlib
import html
from pathlib import Path

import streamlit.components.v1 as components

_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_CLIPBOARD_IFRAME_CSS_PATH = _STATIC_DIR / "css" / "component_clipboard_iframe.css"
_CLIPBOARD_IFRAME_JS_PATH = _STATIC_DIR / "js" / "component_clipboard_link.js"
_clipboard_iframe_assets_cache: tuple[str, str] | None = None


def clipboard_iframe_assets() -> tuple[str, str]:
    global _clipboard_iframe_assets_cache
    if _clipboard_iframe_assets_cache is None:
        _clipboard_iframe_assets_cache = (
            _CLIPBOARD_IFRAME_CSS_PATH.read_text(encoding="utf-8"),
            _CLIPBOARD_IFRAME_JS_PATH.read_text(encoding="utf-8"),
        )
    return _clipboard_iframe_assets_cache


def render_clipboard_iframe_button(
    *,
    label: str,
    value: str,
    element_key: str,
    height: int = 32,
    iframe_width: int | None = None,
) -> None:
    """Кнопка-копирование внутри iframe (как на странице BTC).

    У каждого экземпляра должен быть уникальный ``element_key`` и своё содержимое.
    Для разных ``iframe_width`` у потоков Streamlit не сливаются два подряд iframe.
    """
    if not value:
        return
    css, js = clipboard_iframe_assets()
    safe_label = html.escape(label)
    payload_b64 = base64.b64encode(value.encode("utf-8")).decode("ascii")
    # Уникальный отпечаток в DOM, чтобы два components.html не совпали по содержимому.
    clip_sig = hashlib.sha256(
        f"{element_key}\0{value}\0{payload_b64[:32]}".encode("utf-8"),
    ).hexdigest()[:20]
    header = f"<!-- sconvert-clip:{element_key}:{clip_sig} -->\n"
    body = f"""{header}<style>{css}</style>
<a class="sconvert-clipboard-link" href="#" id="{html.escape(element_key, quote=True)}" data-copy-b64="{payload_b64}">{safe_label}</a>
<script>{js}</script>"""
    kwargs: dict = {"height": height}
    if iframe_width is not None:
        kwargs["width"] = iframe_width
    components.html(body, **kwargs)
