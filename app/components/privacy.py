from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# closegamer@mail.ru — base64-encoded, never appears in plain text in HTML source
_EMAIL_B64 = "Y2xvc2VnYW1lckBtYWlsLnJ1"
_THEME_SYNC_JS_PATH = Path(__file__).resolve().parent.parent / "static" / "js" / "theme_iframe_sync.js"


def render_privacy_component(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="title">{texts["privacy.title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{texts["privacy.text"]}</p>', unsafe_allow_html=True)

    btn_label = texts.get("privacy.contact_button", "Связаться")
    copied_label = texts.get("privacy.contact_copied", "Скопировано")
    theme_sync_js = _THEME_SYNC_JS_PATH.read_text(encoding="utf-8")

    components.html(
        f"""
        <script>{theme_sync_js}</script>
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; }}
          body {{ background: transparent; font-family: sans-serif; }}
          #email-wrap {{ display: flex; align-items: center; gap: 12px; }}
          :root {{ --p-bg: #0c1610; --p-muted: #86b593; --p-line: #1d3324; --p-text: #d9ffe3; --p-accent: #1fcf62; }}
          :root[data-theme="light"] {{ --p-bg: #eef6f0; --p-muted: #4c6357; --p-line: #c3dccb; --p-text: #12261b; --p-accent: #178a45; }}
          #reveal-btn {{
            background: var(--p-bg);
            color: var(--p-muted);
            border: 1px solid var(--p-line);
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
          }}
          #reveal-btn:hover {{ background: var(--p-line); color: var(--p-text); }}
          #email-text {{
            font-size: 14px;
            color: var(--p-accent);
            display: none;
            word-break: break-all;
          }}
        </style>
        <div id="email-wrap">
          <button id="reveal-btn" onclick="revealEmail()">{btn_label}</button>
          <span id="email-text"></span>
        </div>
        <script>
          function revealEmail() {{
            const email = atob("{_EMAIL_B64}");
            const el = document.getElementById("email-text");
            const btn = document.getElementById("reveal-btn");
            el.style.display = "inline";
            el.textContent = email;
            el.onclick = function() {{
              navigator.clipboard.writeText(email).then(() => {{
                const prev = el.textContent;
                el.textContent = "{copied_label}";
                setTimeout(() => {{ el.textContent = prev; }}, 1200);
              }});
            }};
            el.style.cursor = "pointer";
            el.title = "Нажмите, чтобы скопировать";
            btn.style.display = "none";
          }}
        </script>
        """,
        height=44,
    )
