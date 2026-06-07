import streamlit as st
import streamlit.components.v1 as components


# closegamer@mail.ru — base64-encoded, never appears in plain text in HTML source
_EMAIL_B64 = "Y2xvc2VnYW1lckBtYWlsLnJ1"


def render_privacy_component(texts: dict[str, str]) -> None:
    st.markdown(f'<p class="title">{texts["privacy.title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="subtitle">{texts["privacy.text"]}</p>', unsafe_allow_html=True)

    if st.button(texts.get("privacy.close", "Закрыть"), key="privacy_close_btn"):
        st.session_state.show_privacy = False
        st.rerun()

    btn_label = texts.get("privacy.contact_button", "Связаться")
    copied_label = texts.get("privacy.contact_copied", "Скопировано")

    components.html(
        f"""
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; }}
          body {{ background: transparent; font-family: sans-serif; }}
          #email-wrap {{ display: flex; align-items: center; gap: 12px; }}
          #reveal-btn {{
            background: #0c1610;
            color: #86b593;
            border: 1px solid #1d3324;
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 13px;
            cursor: pointer;
            transition: background 0.15s, color 0.15s;
          }}
          #reveal-btn:hover {{ background: #1d3324; color: #d9ffe3; }}
          #email-text {{
            font-size: 14px;
            color: #1fcf62;
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
