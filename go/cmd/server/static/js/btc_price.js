/**
 * BTC price widget. Polls /api/btc/price (CoinGecko proxy, Redis-cached
 * server-side for 60s) every 30s. Ported from app/components/btc_price.py's
 * Streamlit iframe widget — no iframe needed here since Go pages aren't
 * sandboxed the way Streamlit components are.
 */
(function () {
  "use strict";

  var REFRESH_MS = 30000;
  var usdEl = document.getElementById("sc-btc-price-usd");
  var rubEl = document.getElementById("sc-btc-price-rub");
  var metaEl = document.getElementById("sc-btc-price-updated");
  if (!usdEl || !rubEl || !metaEl) return;

  var ERR = usdEl.getAttribute("data-error-label") || "—";
  var UPDATED_LABEL = usdEl.getAttribute("data-updated-label") || "updated";

  function fmtNumber(n) {
    return new Intl.NumberFormat("ru-RU").format(Math.round(n));
  }

  function fmtTime(iso) {
    try {
      var d = new Date(iso);
      return UPDATED_LABEL + ": " + d.toLocaleTimeString();
    } catch (e) {
      return "";
    }
  }

  function fetchPrice() {
    fetch("/api/btc/price")
      .then(function (r) { return r.ok ? r.json() : Promise.reject(r.status); })
      .then(function (data) {
        usdEl.textContent = fmtNumber(data.usd);
        rubEl.textContent = fmtNumber(data.rub);
        metaEl.textContent = fmtTime(data.updated_at);
      })
      .catch(function () {
        usdEl.textContent = ERR;
        rubEl.textContent = ERR;
        metaEl.textContent = "";
      });
  }

  fetchPrice();
  setInterval(fetchPrice, REFRESH_MS);
})();
