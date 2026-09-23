package web

import (
	"context"
	"encoding/json"
	"html/template"
	"net/http"

	"sconvert/internal/currency"
	"sconvert/internal/stats"
	"sconvert/internal/units"
)

type UnitsPageData struct {
	PageData
	Categories []units.Category
	UnitsJSON  template.JS
}

// UnitsHandler renders /units, ordering categories by popularity (per-input
// hit counts collected via /api/stats/hit and summed per category — see
// StatsHitHandler and stats.Store.CategoryTotals).
func UnitsHandler(store *stats.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		counts := store.CategoryTotals(r.Context(), "units", units.Keys())
		ranked := units.RankedBy(counts)

		payload, err := json.Marshal(ranked)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		data := &UnitsPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.units", "Units - sConvert"),
				i18nOr(lang, "seo.description.units", ""),
				"https://sconvert.ru/units",
			),
			Categories: ranked,
			UnitsJSON:  template.JS(payload),
		}
		Render(w, "page:units", data)
	}
}

// StatsHitHandler records one anonymous use of a single input (e.g. typing
// into the "km" field of the "length" category). scope/category/input are
// validated against the known unit registry so the endpoint can't be used
// to write arbitrary rows.
func StatsHitHandler(store *stats.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var body struct {
			Scope    string `json:"scope"`
			Category string `json:"category"`
			Input    string `json:"input"`
		}
		if err := json.NewDecoder(http.MaxBytesReader(w, r.Body, 256)).Decode(&body); err != nil {
			w.WriteHeader(http.StatusNoContent) // best-effort beacon; never error to the client
			return
		}
		switch body.Scope {
		case "units":
			if cat, ok := units.ByKey(body.Category); ok {
				for _, u := range cat.Units {
					if u.Code == body.Input {
						store.Hit(context.Background(), body.Scope, body.Category, body.Input)
						break
					}
				}
			}
		case "currency":
			if body.Category == "currency" && currency.Contains(body.Input) {
				store.Hit(context.Background(), body.Scope, body.Category, body.Input)
			}
		}
		w.WriteHeader(http.StatusNoContent)
	}
}
