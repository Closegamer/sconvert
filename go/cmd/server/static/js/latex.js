/**
 * Client engine for /latex. Fully client-side — delimiter stripping and
 * math rendering both happen here (KaTeX, vendored), so there's no server
 * round trip while typing. PNG export renders the same KaTeX-produced DOM
 * node to a canvas via html-to-image, so the downloaded picture can never
 * disagree with the on-page preview (unlike the original's separate
 * matplotlib rasterization, which used a different TeX subset).
 */
(function () {
  "use strict";

  function normalize(raw) {
    var t = raw.trim();
    if (!t) return t;
    if (t.length >= 4 && t.slice(0, 2) === "$$" && t.slice(-2) === "$$") {
      return t.slice(2, -2).trim();
    }
    if (t.length >= 2 && t[0] === "$" && t[t.length - 1] === "$") {
      return t.slice(1, -1).trim();
    }
    if (t.length >= 4 && t.slice(0, 2) === "\\(" && t.slice(-2) === "\\)") {
      return t.slice(2, -2).trim();
    }
    if (t.length >= 4 && t.slice(0, 2) === "\\[" && t.slice(-2) === "\\]") {
      return t.slice(2, -2).trim();
    }
    return t;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("sc-latex-input");
    var preview = document.getElementById("sc-latex-preview");
    var emptyHint = document.getElementById("sc-latex-empty-hint");
    var errorEl = document.getElementById("sc-latex-error");
    var normalizedWrap = document.getElementById("sc-latex-normalized-wrap");
    var normalizedEl = document.getElementById("sc-latex-normalized");
    if (!input || !preview || typeof katex === "undefined") return;

    function render() {
      var raw = input.value;
      var trimmed = raw.trim();
      errorEl.hidden = true;

      if (!trimmed) {
        preview.textContent = "";
        emptyHint.hidden = false;
        normalizedWrap.hidden = true;
        return;
      }
      emptyHint.hidden = true;

      var normalized = normalize(trimmed);
      try {
        katex.render(normalized, preview, { throwOnError: true, displayMode: true });
      } catch (e) {
        errorEl.textContent = (e && e.message) || String(e);
        errorEl.hidden = false;
      }

      if (normalized !== trimmed) {
        normalizedEl.textContent = normalized;
        normalizedWrap.hidden = false;
      } else {
        normalizedWrap.hidden = true;
      }
    }

    input.addEventListener("input", render);
    render();

    var copyBtn = document.getElementById("sc-latex-copy-source");
    if (copyBtn) {
      copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(input.value).then(function () {
          var original = copyBtn.textContent;
          copyBtn.textContent = "OK";
          setTimeout(function () { copyBtn.textContent = original; }, 900);
        }).catch(function () {});
      });
    }

    var downloadBtn = document.getElementById("sc-latex-download-png");
    var pngError = document.getElementById("sc-latex-png-error");
    if (downloadBtn && typeof htmlToImage !== "undefined") {
      downloadBtn.addEventListener("click", function () {
        pngError.hidden = true;
        if (!preview.textContent.trim()) return;
        htmlToImage.toPng(preview, { backgroundColor: "#ffffff", pixelRatio: 2 })
          .then(function (dataUrl) {
            var a = document.createElement("a");
            a.href = dataUrl;
            a.download = "latex-formula.png";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
          })
          .catch(function () {
            pngError.hidden = false;
          });
      });
    }
  });
})();
