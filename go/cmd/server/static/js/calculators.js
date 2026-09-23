/**
 * /calculators — two independent, fully client-side calculators (no
 * server round trip, same pattern as units/currency's live recalculation).
 */
(function () {
  "use strict";

  function parseNumber(raw) {
    var s = (raw || "").trim().replace(",", ".");
    if (!s) return null;
    var v = parseFloat(s);
    return isFinite(v) && v > 0 ? v : null;
  }

  function formatNumber(value, decimals) {
    if (!isFinite(value)) return "";
    return value.toFixed(decimals == null ? 2 : decimals);
  }

  // --- Price per kilogram ---
  function initPricePerKg() {
    var priceEl = document.getElementById("sc-calc-kg-price");
    var gramsEl = document.getElementById("sc-calc-kg-grams");
    var resultEl = document.getElementById("sc-calc-kg-result");
    if (!priceEl || !gramsEl || !resultEl) return;

    function recalc() {
      var price = parseNumber(priceEl.value);
      var grams = parseNumber(gramsEl.value);
      if (price === null || grams === null) {
        resultEl.value = "";
        return;
      }
      resultEl.value = formatNumber((price / grams) * 1000);
    }

    priceEl.addEventListener("input", recalc);
    gramsEl.addEventListener("input", recalc);
    recalc();
  }

  // --- Surebet (sports betting arbitrage) calculator ---
  function initSurebet() {
    var totalEl = document.getElementById("sc-surebet-total");
    var outcomes = Array.prototype.slice.call(document.querySelectorAll(".sc-surebet-outcome"));
    var outcome3 = document.getElementById("sc-surebet-outcome-3");
    var statusEl = document.getElementById("sc-surebet-status");
    var marginEl = document.getElementById("sc-surebet-margin");
    var payoutEl = document.getElementById("sc-surebet-payout");
    var profitEl = document.getElementById("sc-surebet-profit");
    var mode2Btn = document.getElementById("sc-surebet-mode-2");
    var mode3Btn = document.getElementById("sc-surebet-mode-3");
    if (!totalEl || !outcomes.length || !statusEl) return;

    var activeCount = 2;

    function setMode(count) {
      activeCount = count;
      if (outcome3) outcome3.hidden = count < 3;
      if (mode2Btn) mode2Btn.classList.toggle("sc-calc-mode-active", count === 2);
      if (mode3Btn) mode3Btn.classList.toggle("sc-calc-mode-active", count === 3);
      recalc();
    }

    if (mode2Btn) mode2Btn.addEventListener("click", function () { setMode(2); });
    if (mode3Btn) mode3Btn.addEventListener("click", function () { setMode(3); });

    function recalc() {
      var total = parseNumber(totalEl.value);
      var active = outcomes.slice(0, activeCount);
      var oddsList = active.map(function (row) {
        return parseNumber(row.querySelector(".sc-surebet-odds").value);
      });

      var allValid = total !== null && oddsList.every(function (o) { return o !== null; });

      active.forEach(function (row) {
        row.querySelector(".sc-surebet-stake").value = "";
      });
      if (!allValid) {
        statusEl.textContent = "";
        marginEl.value = "";
        payoutEl.value = "";
        profitEl.value = "";
        return;
      }

      var invSum = oddsList.reduce(function (sum, o) { return sum + 1 / o; }, 0);
      var marginPercent = invSum * 100;
      var payout = total / invSum;
      var profit = payout - total;
      var isArb = invSum < 1;

      active.forEach(function (row, i) {
        var stake = total * (1 / oddsList[i]) / invSum;
        row.querySelector(".sc-surebet-stake").value = formatNumber(stake);
      });

      var profitPercent = (profit / total) * 100;

      marginEl.value = formatNumber(marginPercent) + "%";
      payoutEl.value = formatNumber(payout);
      profitEl.value = (profit >= 0 ? "+" : "") + formatNumber(profit) + " (" + (profitPercent >= 0 ? "+" : "") + formatNumber(profitPercent) + "%)";

      var i18n = window.SCONVERT_CALC_I18N || {};
      statusEl.textContent = isArb ? (i18n.arbFound || "") : (i18n.arbNotFound || "");
      statusEl.classList.toggle("sc-calc-status-ok", isArb);
      statusEl.classList.toggle("sc-calc-status-bad", !isArb);
    }

    totalEl.addEventListener("input", recalc);
    outcomes.forEach(function (row) {
      row.querySelector(".sc-surebet-odds").addEventListener("input", recalc);
    });

    setMode(2);
  }

  document.addEventListener("DOMContentLoaded", function () {
    initPricePerKg();
    initSurebet();
  });
})();
