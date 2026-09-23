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
  var PINNED_KEY = "sconvert_pinned_units_categories";
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

  function pinCategory(key) {
    var set = readSet(PINNED_KEY);
    if (!set.has(key)) {
      set.add(key);
      writeSet(PINNED_KEY, set);
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

      // Picking a field out of the search results (click or Tab into it
      // while it's a match) counts as a use for popularity — same
      // debounced hit as typing a value — and also pins the whole category
      // to the top of the list for this browser (localStorage), clearing
      // the search box. Pins accumulate: a later pin joins earlier ones at
      // the top instead of replacing them. Only wired when a search handle
      // is passed in (the /units page, not the Home favorites section).
      input.addEventListener("focus", function () {
        var field = input.parentNode;
        // A panel can match via its category title alone (no individual
        // field's label/code contains the query) — in that case only the
        // panel gets sc-search-match, not the field, so check both.
        var matched = (field && field.classList.contains("sc-search-match")) ||
          panel.classList.contains("sc-search-match");
        if (matched) {
          scheduleHit(key, input.getAttribute("data-unit-code"));
          if (opts.search) {
            pinCategory(key);
            opts.search.clear();
            opts.search.applyPinnedOrder();
          }
        }
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

  // Filters category panels against the search box (matches category title,
  // each field's label, and its unit code) and moves matches to the top of
  // the list. Only present on /units (#sc-units-list) — the Home favorites
  // list is short enough not to need it.
  function initSearch() {
    var input = document.getElementById("sc-units-search");
    var list = document.getElementById("sc-units-list");
    if (!input || !list) return { clear: function () {}, applyPinnedOrder: function () {} };
    var panels = Array.prototype.slice.call(list.querySelectorAll(".sc-unit-panel"));

    function normalize(s) { return (s || "").toLowerCase(); }

    function fieldMatches(field, query) {
      var span = field.querySelector("span");
      var code = field.querySelector("input").getAttribute("data-unit-code");
      return normalize(span.textContent).indexOf(query) !== -1 || normalize(code).indexOf(query) !== -1;
    }

    function panelMatches(panel, query) {
      var toggle = panel.querySelector(".sc-unit-toggle");
      if (toggle && normalize(toggle.textContent).indexOf(query) !== -1) return true;
      var fields = panel.querySelectorAll(".sc-unit-field");
      for (var i = 0; i < fields.length; i++) {
        if (fieldMatches(fields[i], query)) return true;
      }
      return false;
    }

    function clear() {
      input.value = "";
      panels.forEach(function (panel) {
        panel.hidden = false;
        panel.classList.remove("sc-search-match");
        panel.querySelectorAll(".sc-unit-field").forEach(function (f) {
          f.classList.remove("sc-search-match");
        });
      });
    }

    function applyPinnedOrder() {
      var pinned = Array.from(readSet(PINNED_KEY));
      pinned.slice().reverse().forEach(function (key) {
        var panel = list.querySelector('.sc-unit-panel[data-category="' + key + '"]');
        if (panel) list.insertBefore(panel, list.firstChild);
      });
    }

    input.addEventListener("input", function () {
      var query = normalize(input.value.trim());
      if (!query) {
        panels.forEach(function (panel) {
          panel.hidden = false;
          panel.classList.remove("sc-search-match");
          panel.querySelectorAll(".sc-unit-field").forEach(function (f) {
            f.classList.remove("sc-search-match");
          });
        });
        return;
      }

      var matched = [];
      panels.forEach(function (panel) {
        var isMatch = panelMatches(panel, query);
        panel.hidden = !isMatch;
        panel.classList.toggle("sc-search-match", isMatch);
        if (!isMatch) return;

        matched.push(panel);
        panel.querySelectorAll(".sc-unit-field").forEach(function (f) {
          f.classList.toggle("sc-search-match", fieldMatches(f, query));
        });

        var body = panel.querySelector(".sc-unit-body");
        var toggleBtn = panel.querySelector(".sc-unit-toggle");
        if (body && body.hidden) {
          body.hidden = false;
          panel.classList.add("sc-unit-open");
          if (toggleBtn) toggleBtn.setAttribute("aria-expanded", "true");
        }
      });
      matched.slice().reverse().forEach(function (panel) { list.insertBefore(panel, list.firstChild); });
    });

    return { clear: clear, applyPinnedOrder: applyPinnedOrder };
  }

  document.addEventListener("DOMContentLoaded", function () {
    var search = initSearch();

    var favoritesSection = document.getElementById("sc-favorites-section");
    if (favoritesSection) {
      initFavoritesSection(favoritesSection);
    } else {
      document.querySelectorAll(".sc-unit-panel").forEach(function (p) {
        initCategory(p, { search: search });
      });
      search.applyPinnedOrder();
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
