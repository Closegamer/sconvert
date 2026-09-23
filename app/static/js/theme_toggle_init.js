/**
 * Переключатель темы (light/dark). Должен жить в iframe components.html,
 * т.к. <script> внутри st.markdown(unsafe_allow_html=True) не исполняется —
 * Streamlit рендерит markdown через react-markdown/rehype-raw, а React
 * не выполняет script-теги при вставке в DOM. Поэтому логика применяется
 * к родительскому документу через window.parent (тот же приём, что и в
 * parent_head_seo_defaults.js).
 */
(() => {
  const parentDoc = window.parent?.document;
  if (!parentDoc) return;

  const KEY = "sconvert_theme";

  function currentTheme() {
    try {
      return window.localStorage.getItem(KEY) === "light" ? "light" : "dark";
    } catch (e) {
      return "dark";
    }
  }

  function applyTheme(theme) {
    parentDoc.documentElement.setAttribute("data-theme", theme);
  }

  applyTheme(currentTheme());

  window.parent.sconvertToggleTheme = function () {
    const next = currentTheme() === "light" ? "dark" : "light";
    try {
      window.localStorage.setItem(KEY, next);
    } catch (e) {}
    applyTheme(next);
  };
})();
