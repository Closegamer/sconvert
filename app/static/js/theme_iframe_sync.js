/**
 * Синхронизация темы (light/dark) внутри изолированных iframe components.html.
 * Источник истины — localStorage ключ "sconvert_theme", общий для всех
 * same-origin документов (родительский app + каждый iframe).
 */
(function () {
  "use strict";

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme === "light" ? "light" : "dark");
  }

  function readTheme() {
    try {
      return window.localStorage.getItem("sconvert_theme") === "light" ? "light" : "dark";
    } catch (e) {
      return "dark";
    }
  }

  applyTheme(readTheme());

  window.addEventListener("storage", function (e) {
    if (e.key === "sconvert_theme") {
      applyTheme(e.newValue === "light" ? "light" : "dark");
    }
  });
})();
