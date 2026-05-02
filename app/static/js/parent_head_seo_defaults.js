/**
 * Дублирует базовые SEO meta/link в document родительского окна (iframe Streamlit).
 */
(() => {
  const head = window.parent?.document?.head;
  if (!head) return;
  const ensureMeta = (attr, key, content) => {
    let el = head.querySelector(`meta[${attr}="${key}"]`);
    if (!el) {
      el = window.parent.document.createElement("meta");
      el.setAttribute(attr, key);
      head.appendChild(el);
    }
    el.setAttribute("content", content);
  };
  const ensureLink = (rel, href) => {
    let el = head.querySelector(`link[rel="${rel}"][data-sconvert-seo="1"]`);
    if (!el) {
      el = window.parent.document.createElement("link");
      el.setAttribute("rel", rel);
      el.setAttribute("data-sconvert-seo", "1");
      head.appendChild(el);
    }
    el.setAttribute("href", href);
  };
  ensureMeta("name", "description", "sconvert: online converters for units, data formats, and Bitcoin tools.");
  ensureMeta("name", "robots", "index,follow,max-image-preview:large");
  ensureMeta("property", "og:type", "website");
  ensureMeta("property", "og:site_name", "sconvert");
  ensureMeta("property", "og:title", "sconvert - converters and BTC tools");
  ensureMeta(
    "property",
    "og:description",
    "Convert units, work with BTC keys/addresses, and use practical online tools."
  );
  ensureMeta("property", "og:url", "https://sconvert.ru/");
  ensureMeta("property", "og:image", "https://sconvert.ru/og-image.png");
  ensureMeta("name", "twitter:card", "summary_large_image");
  ensureMeta("name", "twitter:title", "sconvert - converters and BTC tools");
  ensureMeta(
    "name",
    "twitter:description",
    "Convert units, work with BTC keys/addresses, and use practical online tools."
  );
  ensureMeta("name", "twitter:image", "https://sconvert.ru/og-image.png");
  ensureLink("canonical", "https://sconvert.ru/");
})();
