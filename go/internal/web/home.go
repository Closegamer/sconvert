package web

import (
	"encoding/json"
	"html/template"
	"net/http"

	"sconvert/internal/stats"
	"sconvert/internal/units"
)

// HomeHandler renders "/". The page always ships every category's data +
// markup (same as /units) so the client can instantly show/hide favorited
// ones from localStorage — see static/js/units.js (initFavoritesSection).
func HomeHandler(store *stats.Store) http.HandlerFunc {
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
				i18nOr(lang, "seo.title.home", "sConvert"),
				i18nOr(lang, "seo.description.home", ""),
				"https://sconvert.ru/",
			),
			Categories: ranked,
			UnitsJSON:  template.JS(payload),
		}
		Render(w, "page:home", data)
	}
}
