import streamlit.components.v1 as components


def render_btc_price_component(texts: dict[str, str]) -> None:
    label_usd = texts.get("btc.price.usd", "USD")
    label_rub = texts.get("btc.price.rub", "RUB")
    label_updated = texts.get("btc.price.updated", "updated")
    label_error = texts.get("btc.price.error", "—")
    label_loading = texts.get("btc.price.loading", "...")
    refresh_ms = 30_000

    components.html(
        f"""
        <style>
          * {{ box-sizing: border-box; margin: 0; padding: 0; }}
          body {{ background: transparent; font-family: sans-serif; }}
          #widget {{
            display: flex;
            align-items: center;
            gap: 20px;
            padding: 10px 16px;
            background: #07110b;
            border: 1px solid #1d3324;
            border-radius: 8px;
            width: fit-content;
          }}
          .btc-logo {{
            font-size: 22px;
            color: #f7931a;
            font-weight: bold;
            flex-shrink: 0;
          }}
          .price-block {{
            display: flex;
            flex-direction: column;
            gap: 2px;
          }}
          .price-row {{
            display: flex;
            gap: 10px;
            align-items: baseline;
          }}
          .currency {{
            font-size: 11px;
            color: #86b593;
            min-width: 28px;
          }}
          .amount {{
            font-size: 15px;
            color: #d9ffe3;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            min-width: 120px;
          }}
          .meta {{
            font-size: 10px;
            color: #4e6b57;
            margin-top: 2px;
          }}
          .dot {{
            display: inline-block;
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #1fcf62;
            margin-right: 5px;
            animation: pulse 2s infinite;
          }}
          @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
          }}
        </style>
        <div id="widget">
          <div class="btc-logo">₿</div>
          <div class="price-block">
            <div class="price-row">
              <span class="currency">{label_usd}</span>
              <span class="amount" id="price-usd">{label_loading}</span>
            </div>
            <div class="price-row">
              <span class="currency">{label_rub}</span>
              <span class="amount" id="price-rub">{label_loading}</span>
            </div>
            <div class="meta">
              <span class="dot"></span>
              <span id="updated-at"></span>
            </div>
          </div>
        </div>
        <script>
          const USD_EL = document.getElementById('price-usd');
          const RUB_EL = document.getElementById('price-rub');
          const META_EL = document.getElementById('updated-at');
          const ERR = '{label_error}';
          const UPDATED_LABEL = '{label_updated}';

          function fmtNumber(n) {{
            return new Intl.NumberFormat('ru-RU').format(Math.round(n));
          }}

          function fmtTime(iso) {{
            try {{
              const d = new Date(iso);
              return UPDATED_LABEL + ': ' + d.toLocaleTimeString();
            }} catch(e) {{
              return '';
            }}
          }}

          function fetchPrice() {{
            const origin = (window.parent && window.parent.location && window.parent.location.origin)
              ? window.parent.location.origin
              : window.location.origin;
            fetch(origin + '/api/btc/price')
              .then(r => r.ok ? r.json() : Promise.reject(r.status))
              .then(data => {{
                USD_EL.textContent = fmtNumber(data.usd);
                RUB_EL.textContent = fmtNumber(data.rub);
                META_EL.textContent = fmtTime(data.updated_at);
              }})
              .catch(() => {{
                USD_EL.textContent = ERR;
                RUB_EL.textContent = ERR;
                META_EL.textContent = '';
              }});
          }}

          fetchPrice();
          setInterval(fetchPrice, {refresh_ms});
        </script>
        """,
        height=90,
    )
