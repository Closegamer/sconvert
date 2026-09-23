/**
 * Клиентский движок конвертера валют. Курсы приходят как JSON
 * (window.SCONVERT_CURRENCY_RATES, USD-базовые — см. internal/currency) —
 * пересчёт мгновенный, без похода на сервер после первой загрузки страницы.
 */
(function () {
  "use strict";

  var RATES = window.SCONVERT_CURRENCY_RATES || {};
  var HIT_DEBOUNCE_MS = 800;
  var hitTimers = {};
  var PINNED_KEY = "sconvert_pinned_currencies";

  function readPinned() {
    try {
      var raw = localStorage.getItem(PINNED_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function writePinned(list) {
    try {
      localStorage.setItem(PINNED_KEY, JSON.stringify(list));
    } catch (e) {}
  }

  function pinCurrency(code) {
    var pinned = readPinned();
    if (pinned.indexOf(code) === -1) {
      pinned.push(code);
      writePinned(pinned);
    }
  }

  function formatNumber(value) {
    if (!isFinite(value)) return "";
    var abs = Math.abs(value);
    if (abs !== 0 && (abs < 1e-4 || abs > 1e6)) {
      return value.toExponential(6);
    }
    return String(Math.round(value * 1e10) / 1e10);
  }

  function parseNumber(raw) {
    var s = (raw || "").trim().replace(",", ".");
    if (!s) return null;
    var v = parseFloat(s);
    return isFinite(v) ? v : null;
  }

  function sendHit(code) {
    try {
      var payload = JSON.stringify({ scope: "currency", category: "currency", input: code });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/api/stats/hit", new Blob([payload], { type: "application/json" }));
      } else {
        fetch("/api/stats/hit", { method: "POST", body: payload, keepalive: true });
      }
    } catch (e) {}
  }

  // One anonymous "use" per input field per HIT_DEBOUNCE_MS of typing
  // inactivity — matches static/js/units.js's debounce behavior.
  function scheduleHit(code) {
    if (hitTimers[code]) clearTimeout(hitTimers[code]);
    hitTimers[code] = setTimeout(function () {
      sendHit(code);
      delete hitTimers[code];
    }, HIT_DEBOUNCE_MS);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var inputs = document.querySelectorAll("input[data-currency-code]");
    if (!inputs.length) return;

    function syncFromBaseUsd(baseUsd, exceptCode) {
      inputs.forEach(function (input) {
        var code = input.getAttribute("data-currency-code");
        if (code === exceptCode) return;
        var rate = RATES[code];
        input.value = rate ? formatNumber(baseUsd * rate) : "";
      });
    }

    var search = initSearch();

    inputs.forEach(function (input) {
      input.addEventListener("input", function () {
        var code = input.getAttribute("data-currency-code");
        var rate = RATES[code];
        var v = parseNumber(input.value);
        if (v === null || !rate) return;
        var baseUsd = v / rate;
        syncFromBaseUsd(baseUsd, code);
        scheduleHit(code);
      });

      // Picking a field out of the search results (click or Tab into it
      // while it's a match) counts as a use for popularity — same
      // debounced hit as typing a value — and also pins that currency to
      // the top of the grid for this browser (localStorage), clearing the
      // search box so the next search starts fresh. Pins accumulate: a
      // later pin joins earlier ones at the top instead of replacing them.
      input.addEventListener("focus", function () {
        var field = input.parentNode;
        if (field && field.classList.contains("sc-search-match")) {
          var code = input.getAttribute("data-currency-code");
          scheduleHit(code);
          pinCurrency(code);
          search.clear();
          search.applyPinnedOrder();
        }
      });
    });

    syncFromBaseUsd(1, null); // seed all fields with 1 USD worth on load
    search.applyPinnedOrder();
  });

  // Filters the 153 currency fields against the search box (matches label
  // text and the currency code), moves matches to the top of the grid, and
  // keeps previously pinned currencies (see pinCurrency above) at the very
  // top across searches/reloads.
  function initSearch() {
    var input = document.getElementById("sc-currency-search");
    var grid = document.getElementById("sc-currency-grid");
    if (!input || !grid) return { clear: function () {}, applyPinnedOrder: function () {} };
    var fields = Array.prototype.slice.call(grid.querySelectorAll(".sc-unit-field"));

    function normalize(s) { return (s || "").toLowerCase(); }

    function fieldMatches(field, query) {
      var span = field.querySelector("span");
      var code = field.querySelector("input").getAttribute("data-currency-code");
      return normalize(span.textContent).indexOf(query) !== -1 || normalize(code).indexOf(query) !== -1;
    }

    function clear() {
      input.value = "";
      fields.forEach(function (field) {
        field.hidden = false;
        field.classList.remove("sc-search-match");
      });
    }

    function applyPinnedOrder() {
      var pinned = readPinned();
      pinned.slice().reverse().forEach(function (code) {
        var pinnedInput = grid.querySelector('[data-currency-code="' + code + '"]');
        if (pinnedInput) grid.insertBefore(pinnedInput.parentNode, grid.firstChild);
      });
    }

    input.addEventListener("input", function () {
      var query = normalize(input.value.trim());
      if (!query) {
        fields.forEach(function (field) {
          field.hidden = false;
          field.classList.remove("sc-search-match");
        });
        return;
      }

      var matched = [];
      fields.forEach(function (field) {
        var isMatch = fieldMatches(field, query);
        field.hidden = !isMatch;
        field.classList.toggle("sc-search-match", isMatch);
        if (isMatch) matched.push(field);
      });
      matched.slice().reverse().forEach(function (field) { grid.insertBefore(field, grid.firstChild); });
    });

    return { clear: clear, applyPinnedOrder: applyPinnedOrder };
  }
})();
