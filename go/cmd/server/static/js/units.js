/**
 * Клиентский движок конвертера единиц. Все категории приходят как JSON
 * (window.SCONVERT_UNITS, см. internal/units) — пересчёт мгновенный,
 * без похода на сервер (base = value*A + B для каждой единицы).
 *
 * На /units показываются все категории (свёрнуты по умолчанию).
 * На / (если на странице есть #sc-favorites-section) показываются только
 * категории, отмеченные звездой в этом браузере — сразу развёрнутыми.
 */
(function () {
  "use strict";

  var DATA = window.SCONVERT_UNITS || [];
  var FAVORITES_KEY = "sconvert_favorites_units";
  var EXPANDED_KEY = "sconvert_expanded_units";
  var HIT_DEBOUNCE_MS = 800;
  var hitTimers = {};

  function readSet(storageKey) {
    try {
      var raw = localStorage.getItem(storageKey);
      return raw ? new Set(JSON.parse(raw)) : new Set();
    } catch (e) {
      return new Set();
    }
  }

  function writeSet(storageKey, set) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(Array.from(set)));
    } catch (e) {}
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

  function sendHit(scope, category, input) {
    try {
      var payload = JSON.stringify({ scope: scope, category: category, input: input });
      if (navigator.sendBeacon) {
        navigator.sendBeacon("/api/stats/hit", new Blob([payload], { type: "application/json" }));
      } else {
        fetch("/api/stats/hit", { method: "POST", body: payload, keepalive: true });
      }
    } catch (e) {}
  }

  // One anonymous "use" per input field per HIT_DEBOUNCE_MS of typing
  // inactivity — not per keystroke, so typing "123.45" counts as one use.
  function scheduleHit(category, code) {
    var timerKey = category + ":" + code;
    if (hitTimers[timerKey]) clearTimeout(hitTimers[timerKey]);
    hitTimers[timerKey] = setTimeout(function () {
      sendHit("units", category, code);
      delete hitTimers[timerKey];
    }, HIT_DEBOUNCE_MS);
  }

  function initCategory(panel, opts) {
    opts = opts || {};
    var key = panel.getAttribute("data-category");
    var cat = DATA.find(function (c) { return c.key === key; });
    if (!cat) return;

    var inputs = panel.querySelectorAll("input[data-unit-code]");
    var body = panel.querySelector(".sc-unit-body");
    var toggleBtn = panel.querySelector(".sc-unit-toggle");
    var favBtn = panel.querySelector(".sc-unit-fav");

    function unitByCode(code) {
      return cat.units.find(function (u) { return u.code === code; });
    }

    function syncFromBase(baseValue, exceptCode) {
      inputs.forEach(function (input) {
        var code = input.getAttribute("data-unit-code");
        if (code === exceptCode) return;
        var u = unitByCode(code);
        input.value = formatNumber((baseValue - u.b) / u.a);
      });
    }

    inputs.forEach(function (input) {
      input.addEventListener("input", function () {
        var code = input.getAttribute("data-unit-code");
        var u = unitByCode(code);
        var v = parseNumber(input.value);
        if (v === null) return;
        var base = v * u.a + u.b;
        syncFromBase(base, code);
        scheduleHit(key, code);
      });
    });

    function setExpanded(isOpen) {
      body.hidden = !isOpen;
      panel.classList.toggle("sc-unit-open", isOpen);
      if (toggleBtn) toggleBtn.setAttribute("aria-expanded", String(isOpen));
      if (!opts.skipExpandPersistence) {
        var set = readSet(EXPANDED_KEY);
        if (isOpen) {
          set.add(key);
        } else {
          set.delete(key);
        }
        writeSet(EXPANDED_KEY, set);
      }
    }
    setExpanded(opts.forceExpanded || readSet(EXPANDED_KEY).has(key));

    if (toggleBtn) {
      toggleBtn.addEventListener("click", function () {
        setExpanded(body.hidden);
      });
    }

    if (favBtn) {
      var favorites = readSet(FAVORITES_KEY);
      function paintFav(isFav) {
        favBtn.classList.toggle("sc-fav-active", isFav);
        favBtn.setAttribute("aria-pressed", String(isFav));
      }
      paintFav(favorites.has(key));
      favBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        var set = readSet(FAVORITES_KEY);
        var isFav = set.has(key);
        if (isFav) {
          set.delete(key);
        } else {
          set.add(key);
        }
        writeSet(FAVORITES_KEY, set);
        paintFav(!isFav);
        if (opts.onFavoriteChange) opts.onFavoriteChange();
      });
    }
  }

  function initFavoritesSection(section) {
    var favorites = readSet(FAVORITES_KEY);
    var title = document.getElementById("sc-favorites-title");
    var panels = section.querySelectorAll(".sc-unit-panel");

    function refresh() {
      var current = readSet(FAVORITES_KEY);
      var anyVisible = false;
      panels.forEach(function (panel) {
        var key = panel.getAttribute("data-category");
        var show = current.has(key);
        panel.hidden = !show;
        if (show) anyVisible = true;
      });
      if (title) title.hidden = !anyVisible;
    }

    panels.forEach(function (panel) {
      initCategory(panel, {
        forceExpanded: true,
        skipExpandPersistence: true,
        onFavoriteChange: refresh,
      });
    });
    refresh();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var favoritesSection = document.getElementById("sc-favorites-section");
    if (favoritesSection) {
      initFavoritesSection(favoritesSection);
    } else {
      document.querySelectorAll(".sc-unit-panel").forEach(function (p) {
        initCategory(p);
      });
    }

    var collapseAllBtn = document.getElementById("sc-units-collapse-all");
    if (collapseAllBtn) {
      collapseAllBtn.addEventListener("click", function () {
        document.querySelectorAll(".sc-unit-panel .sc-unit-body").forEach(function (body) {
          body.hidden = true;
        });
        document.querySelectorAll(".sc-unit-panel").forEach(function (p) {
          p.classList.remove("sc-unit-open");
        });
        writeSet(EXPANDED_KEY, new Set());
      });
    }
  });
})();
