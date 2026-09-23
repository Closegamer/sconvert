/**
 * Copy-icon button next to the donation address — copies the literal
 * value in data-copy-value to the clipboard, with a brief checkmark
 * confirmation.
 */
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var btn = document.getElementById("sc-about-copy-address");
    if (!btn) return;

    btn.addEventListener("click", function () {
      var value = btn.getAttribute("data-copy-value");
      if (!value) return;
      navigator.clipboard.writeText(value).then(function () {
        var original = btn.textContent;
        btn.textContent = "✓";
        setTimeout(function () { btn.textContent = original; }, 900);
      }).catch(function () {});
    });
  });
})();
