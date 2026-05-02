/**
 * Ссылки «копировать» внутри iframe components.html.
 * Разметка: <a class="sconvert-clipboard-link" href="#" data-copy-b64="...">подпись</a>
 */
(function () {
  "use strict";

  function b64ToUtf8(b64) {
    try {
      const binary = atob(b64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i += 1) {
        bytes[i] = binary.charCodeAt(i);
      }
      return new TextDecoder("utf-8").decode(bytes);
    } catch (e) {
      return "";
    }
  }

  document.querySelectorAll("a.sconvert-clipboard-link").forEach(function (link) {
    const labelNormal = link.textContent;

    link.addEventListener("click", async function (e) {
      e.preventDefault();
      const b64 = link.getAttribute("data-copy-b64");
      const text = b64ToUtf8(b64 || "");
      try {
        await navigator.clipboard.writeText(text);
        link.textContent = "OK";
        window.setTimeout(function () {
          link.textContent = labelNormal;
        }, 900);
      } catch (err) {
        link.textContent = "ERR";
        window.setTimeout(function () {
          link.textContent = labelNormal;
        }, 900);
      }
    });
  });
})();
