package web

import (
	"encoding/json"
	"html/template"
	"net/http"

	"sconvert/internal/currency"
	"sconvert/internal/stats"
)

type CurrencyPageData struct {
	PageData
	Currencies []currency.Entry
	RatesJSON  template.JS
	UpdatedAt  string
	RatesError bool
}

// CurrencyHandler renders /currency: 153 currency fields, client-side
// recalculation against a USD-based rate table fetched once per page load
// (see currency.Provider — Redis-cached for up to an hour, same as the old
// FastAPI /api/currency/rates endpoint). Fields are ordered by popularity
// (per-code hit counts collected via /api/stats/hit and RankedBy — see
// StatsHitHandler and static/js/currency.js's search-driven hits), the
// same pattern UnitsHandler uses for categories.
func CurrencyHandler(store *stats.Store, provider *currency.Provider) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		counts := store.InputTotals(r.Context(), "currency", "currency", currency.Codes())
		ranked := currency.RankedBy(counts)

		data := &CurrencyPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.currency", "Currency - sConvert"),
				i18nOr(lang, "seo.description.currency", ""),
				"https://sconvert.ru/currency",
			),
			Currencies: ranked,
		}

		rates, err := provider.Rates(r.Context())
		if err != nil {
			data.RatesError = true
			Render(w, "page:currency", data)
			return
		}

		payload, err := json.Marshal(rates.Rates)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		data.RatesJSON = template.JS(payload)
		data.UpdatedAt = rates.UpdatedAt
		Render(w, "page:currency", data)
	}
}
