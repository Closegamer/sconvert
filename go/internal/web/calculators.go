package web

import "net/http"

// CalculatorsHandler renders /calculators. Both calculators (price-per-kg,
// surebet arbitrage) are pure client-side arithmetic — see
// static/js/calculators.js — so there's no server-side computation here,
// same pattern as /units and /currency.
func CalculatorsHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := NewPageData(
			lang,
			i18nOr(lang, "seo.title.calculators", "Calculators - sConvert"),
			i18nOr(lang, "seo.description.calculators", ""),
			"https://sconvert.ru/calculators",
		)
		Render(w, "page:calculators", &data)
	}
}
