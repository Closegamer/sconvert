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
  ensureMeta("name", "yandex-verification", "3c93613f1bcf5ed3");
  ensureMeta("name", "description", "sConvert: online converters for units, data formats, and Bitcoin tools.");
  ensureMeta("name", "robots", "index,follow,max-image-preview:large");
  ensureMeta("property", "og:type", "website");
  ensureMeta("property", "og:site_name", "sConvert");
  ensureMeta("property", "og:title", "sConvert - converters and BTC tools");
  ensureMeta(
    "property",
    "og:description",
    "Convert units, work with BTC keys/addresses, and use practical online tools."
  );
  ensureMeta("property", "og:url", "https://sconvert.ru/");
  ensureMeta("property", "og:image", "https://sconvert.ru/og-image.png");
  ensureMeta("name", "twitter:card", "summary_large_image");
  ensureMeta("name", "twitter:title", "sConvert - converters and BTC tools");
  ensureMeta(
    "name",
    "twitter:description",
    "Convert units, work with BTC keys/addresses, and use practical online tools."
  );
  ensureMeta("name", "twitter:image", "https://sconvert.ru/og-image.png");
  ensureLink("canonical", "https://sconvert.ru/");

  // Yandex Metrika — injected once, guarded by window.parent.ym check
  const parentWin = window.parent;
  if (parentWin && !parentWin.ym) {
    const s = parentWin.document.createElement("script");
    s.type = "text/javascript";
    s.textContent = "(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r){return;}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)})(window,document,\"script\",\"https://mc.yandex.ru/metrika/tag.js?id=109708961\",\"ym\");ym(109708961,\"init\",{ssr:true,webvisor:true,clickmap:true,ecommerce:\"dataLayer\",referrer:document.referrer,url:location.href,accurateTrackBounce:true,trackLinks:true});";
    parentWin.document.head.appendChild(s);
    const ns = parentWin.document.createElement("noscript");
    ns.innerHTML = "<div><img src=\"https://mc.yandex.ru/watch/109708961\" style=\"position:absolute;left:-9999px;\" alt=\"\"></div>";
    parentWin.document.body && parentWin.document.body.appendChild(ns);
  }
})();
