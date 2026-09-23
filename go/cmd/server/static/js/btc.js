/**
 * Client engine for /btc. Ports app/components/btc_keys.py's reactive
 * fan-out: entering any one of 13 fields POSTs {field, value} to
 * /btc/convert, which derives every other representation server-side
 * (secp256k1, WIF, addresses, blockstream.info lookups) and returns JSON —
 * this script just applies that JSON to the form. The two SVG
 * visualizations (key-line position, curve point) are computed here in
 * pure JS/BigInt from the returned hex/dec values instead of being
 * rendered server-side, since it's presentation-only math the browser can
 * do without a round trip.
 */
(function () {
  "use strict";

  var FIELD_TO_KEY = {
    private_dec: "privateDec",
    private_hex: "privateHex",
    private_hex_norm: "privateHexNorm",
    private_wif: "privateWIF",
    private_wif_uncompressed: "privateWIFU",
    public_key: "publicKeyC",
    public_key_uncompressed: "publicKeyU",
    ripemd160: "ripemd160C",
    ripemd160_uncompressed: "ripemd160U",
    address: "addressC",
    address_uncompressed: "addressU",
    address_p2sh: "addressP2SH",
    address_p2wpkh: "addressP2WPKH",
    address_info: "addressInfo",
    balance: "balance",
    address_summary: "addressSummary",
    utxos: "utxos",
    txs: "txs"
  };

  var SCALE = 1000000000000000000n; // 1e18, for BigInt-precise division -> float
  var FIELD_PRIME = (1n << 256n) - (1n << 32n) - 977n; // secp256k1 field prime p

  function bigDivToFloat(numerator, denominator) {
    return Number((numerator * SCALE) / denominator) / 1e18;
  }

  function updateCount(field) {
    var countEl = document.querySelector('[data-count-for="btc-' + field + '"]');
    var el = document.getElementById("btc-" + field);
    if (countEl && el) {
      countEl.textContent = "[" + (el.value || "").length + "]";
    }
  }

  function setStatus(field, text) {
    var el = document.getElementById("btc-" + field + "-status");
    if (el) el.textContent = text || "";
  }

  function updateQR(addressC, addressU) {
    var wrap = document.getElementById("sc-btc-qr-wrap");
    var img = document.getElementById("sc-btc-qr");
    var value = addressC || addressU || "";
    if (!value) {
      wrap.hidden = true;
      return;
    }
    img.src = "https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=" + encodeURIComponent(value);
    wrap.hidden = false;
  }

  function updateKeyLine(privateDecStr) {
    var wrap = document.getElementById("sc-btc-keyline-wrap");
    if (!privateDecStr) {
      wrap.hidden = true;
      return;
    }
    var n, priv;
    try {
      n = BigInt("0x" + window.SCONVERT_BTC_CURVE_ORDER_HEX);
      priv = BigInt(privateDecStr);
    } catch (e) {
      wrap.hidden = true;
      return;
    }
    if (priv <= 0n || priv >= n) {
      wrap.hidden = true;
      return;
    }

    var ratio = bigDivToFloat(priv - 1n, n - 2n);
    var x1 = 28, x2 = 492;
    var px = x1 + (x2 - x1) * ratio;

    document.getElementById("sc-btc-keyline-current").textContent = privateDecStr;
    document.getElementById("sc-btc-keyline-position").textContent = (ratio * 100).toFixed(12);
    document.getElementById("sc-btc-keyline-point").setAttribute("cx", px.toFixed(3));
    wrap.hidden = false;
  }

  function toSvgPoint(xr, yr, xMin, xMax, yMin, yMax, pad, plotW, plotH) {
    var nx = (xr - xMin) / (xMax - xMin);
    var ny = (yr - yMin) / (yMax - yMin);
    return [pad + nx * plotW, pad + (1 - ny) * plotH];
  }

  function updateCurve(xHex, yHex, onCurve) {
    var wrap = document.getElementById("sc-btc-curve-wrap");
    if (!xHex || !yHex) {
      wrap.hidden = true;
      return;
    }

    var x = BigInt("0x" + xHex);
    var xNorm = bigDivToFloat(x, FIELD_PRIME);

    var svgW = 520, svgH = 300, pad = 36;
    var plotW = svgW - pad * 2, plotH = svgH - pad * 2;
    var xMin = -4.0, xMax = 4.0;
    var yAbsMax = Math.sqrt(xMax * xMax * xMax + 7.0);
    var yPadding = Math.max(0.6, yAbsMax * 0.08);
    var yMin = -(yAbsMax + yPadding), yMax = yAbsMax + yPadding;

    function toSvg(xr, yr) {
      return toSvgPoint(xr, yr, xMin, xMax, yMin, yMax, pad, plotW, plotH);
    }

    var samples = 360;
    var top = [], bottom = [];
    for (var i = 0; i <= samples; i++) {
      var xr = xMin + (xMax - xMin) * (i / samples);
      var val = xr * xr * xr + 7.0;
      if (val <= 0) continue;
      var yr = Math.sqrt(val);
      var t = toSvg(xr, yr), b = toSvg(xr, -yr);
      top.push(t[0].toFixed(2) + "," + t[1].toFixed(2));
      bottom.push(b[0].toFixed(2) + "," + b[1].toFixed(2));
    }

    var xrPoint = xMin + xNorm * (xMax - xMin);
    var valPoint = xrPoint * xrPoint * xrPoint + 7.0;
    if (valPoint <= 0) {
      xrPoint = 2.0;
      valPoint = xrPoint * xrPoint * xrPoint + 7.0;
    }
    var yrPoint = Math.sqrt(valPoint);
    var yLastByte = parseInt(yHex.slice(-2), 16);
    if (!isNaN(yLastByte) && yLastByte % 2 === 1) yrPoint = -yrPoint;
    var point = toSvg(xrPoint, yrPoint);

    var axisX0 = toSvg(xMin, 0), axisX1 = toSvg(xMax, 0);
    var axisY0 = toSvg(0, yMax), axisY1 = toSvg(0, yMin);

    document.getElementById("sc-btc-curve-x").textContent = xHex;
    document.getElementById("sc-btc-curve-y").textContent = yHex;
    document.getElementById("sc-btc-curve-oncurve").textContent = onCurve ? window.SCONVERT_BTC_I18N.yesWord : window.SCONVERT_BTC_I18N.noWord;

    var axisXEl = document.getElementById("sc-btc-curve-axis-x");
    axisXEl.setAttribute("x1", axisX0[0].toFixed(2));
    axisXEl.setAttribute("y1", axisX0[1].toFixed(2));
    axisXEl.setAttribute("x2", axisX1[0].toFixed(2));
    axisXEl.setAttribute("y2", axisX1[1].toFixed(2));

    var axisYEl = document.getElementById("sc-btc-curve-axis-y");
    axisYEl.setAttribute("x1", axisY0[0].toFixed(2));
    axisYEl.setAttribute("y1", axisY0[1].toFixed(2));
    axisYEl.setAttribute("x2", axisY1[0].toFixed(2));
    axisYEl.setAttribute("y2", axisY1[1].toFixed(2));

    document.getElementById("sc-btc-curve-top").setAttribute("points", top.join(" "));
    document.getElementById("sc-btc-curve-bottom").setAttribute("points", bottom.join(" "));

    var pointEl = document.getElementById("sc-btc-curve-point");
    pointEl.setAttribute("cx", point[0].toFixed(2));
    pointEl.setAttribute("cy", point[1].toFixed(2));
    var labelEl = document.getElementById("sc-btc-curve-point-label");
    labelEl.setAttribute("x", (point[0] + 10).toFixed(2));
    labelEl.setAttribute("y", (point[1] - 10).toFixed(2));

    wrap.hidden = false;
  }

  function applyResponse(json) {
    var errorEl = document.getElementById("sc-btc-error");
    if (json.error) {
      errorEl.textContent = json.error;
      errorEl.hidden = false;
    } else {
      errorEl.hidden = true;
    }

    Object.keys(FIELD_TO_KEY).forEach(function (field) {
      var el = document.getElementById("btc-" + field);
      if (!el) return;
      el.value = json[FIELD_TO_KEY[field]] || "";
      updateCount(field);
    });

    setStatus("address", json.addressCStatus);
    setStatus("address_uncompressed", json.addressUStatus);
    setStatus("address_p2sh", json.addressP2SHStatus);
    setStatus("address_p2wpkh", json.addressP2WPKHStatus);

    updateQR(json.addressC, json.addressU);
    updateKeyLine(json.privateDec);
    updateCurve(json.pubkeyXHex, json.pubkeyYHex, json.pubkeyOnCurve);
  }

  function submitField(field, value) {
    fetch("/btc/convert", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ field: field, value: value })
    })
      .then(function (r) { return r.json(); })
      .then(applyResponse)
      .catch(function () {});
  }

  document.addEventListener("DOMContentLoaded", function () {
    var entryEls = document.querySelectorAll("[data-btc-field]");
    entryEls.forEach(function (el) {
      var field = el.getAttribute("data-btc-field");

      el.addEventListener("input", function () { updateCount(field); });

      el.addEventListener("change", function () {
        var v = el.value.trim();
        if (v) submitField(field, el.value);
      });

      el.addEventListener("keydown", function (e) {
        var isSubmitKey = e.key === "Enter" && (el.tagName !== "TEXTAREA" || e.ctrlKey || e.metaKey);
        if (!isSubmitKey) return;
        e.preventDefault();
        var v = el.value.trim();
        if (v) submitField(field, el.value);
      });
    });

    document.querySelectorAll("[data-copy-target]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var target = document.getElementById(btn.getAttribute("data-copy-target"));
        if (!target || !target.value) return;
        navigator.clipboard.writeText(target.value).then(function () {
          var original = btn.textContent;
          btn.textContent = "OK";
          setTimeout(function () { btn.textContent = original; }, 900);
        }).catch(function () {});
      });
    });

    var clearBtn = document.getElementById("sc-btc-clear-all");
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        document.querySelectorAll(".sc-btc-form input, .sc-btc-form textarea").forEach(function (el) {
          el.value = "";
        });
        document.querySelectorAll(".sc-btc-count").forEach(function (el) { el.textContent = ""; });
        document.querySelectorAll(".sc-btc-caption").forEach(function (el) { el.textContent = ""; });
        document.getElementById("sc-btc-error").hidden = true;
        document.getElementById("sc-btc-keyline-wrap").hidden = true;
        document.getElementById("sc-btc-curve-wrap").hidden = true;
        document.getElementById("sc-btc-qr-wrap").hidden = true;
      });
    }
  });
})();
