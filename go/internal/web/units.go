package web

import (
	"context"
	"encoding/json"
	"html/template"
	"net/http"

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
				"sConvert — "+i18nOr(lang, "units.title", "Units"),
				i18nOr(lang, "units.subtitle", ""),
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
		if body.Scope == "units" {
			if cat, ok := units.ByKey(body.Category); ok {
				for _, u := range cat.Units {
					if u.Code == body.Input {
						store.Hit(context.Background(), body.Scope, body.Category, body.Input)
						break
					}
				}
			}
		}
		w.WriteHeader(http.StatusNoContent)
	}
}
