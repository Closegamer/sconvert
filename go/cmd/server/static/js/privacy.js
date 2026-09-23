/**
 * Contact email reveal widget. The address is base64-encoded in the HTML
 * source (data-email-b64) so it never appears in plain text to scrapers;
 * decoded client-side only when the user clicks "Contact". Ported from
 * app/components/privacy.py's Streamlit iframe widget — no iframe needed
 * here since the Go page isn't sandboxed.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var wrap = document.getElementById("sc-privacy-email-wrap");
    var btn = document.getElementById("sc-privacy-reveal-btn");
    var text = document.getElementById("sc-privacy-email-text");
    if (!wrap || !btn || !text) return;

    var copiedLabel = wrap.getAttribute("data-copied-label") || "Copied";

    btn.addEventListener("click", function () {
      var email;
      try {
        email = atob(wrap.getAttribute("data-email-b64") || "");
      } catch (e) {
        return;
      }
      text.textContent = email;
      text.hidden = false;
      text.title = email;
      btn.hidden = true;

      text.addEventListener("click", function () {
        navigator.clipboard.writeText(email).then(function () {
          var original = text.textContent;
          text.textContent = copiedLabel;
          setTimeout(function () { text.textContent = original; }, 1200);
        }).catch(function () {});
      });
    });
  });
})();
