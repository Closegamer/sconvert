package web

import (
	"crypto/subtle"
	"net/http"

	"sconvert/internal/stats"
)

type AdminPageData struct {
	PageData
	Rows []stats.Row
}

// AdminStatsHandler renders the input-usage dashboard. The route it's
// mounted on and the Basic Auth credentials are supplied by the caller
// (main.go, from env vars) — this handler has no opinion on the path.
func AdminStatsHandler(store *stats.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		rows, err := store.All(r.Context())
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		data := &AdminPageData{
			PageData: NewPageData("ru", "sConvert — stats", "", ""),
			Rows:     rows,
		}
		Render(w, "page:admin_stats", data)
	}
}

// BasicAuth wraps a handler with HTTP Basic Auth, comparing credentials in
// constant time to avoid leaking their length/prefix via timing.
func BasicAuth(user, pass string, next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		u, p, ok := r.BasicAuth()
		userOK := subtle.ConstantTimeCompare([]byte(u), []byte(user)) == 1
		passOK := subtle.ConstantTimeCompare([]byte(p), []byte(pass)) == 1
		if !ok || !userOK || !passOK {
			w.Header().Set("WWW-Authenticate", `Basic realm="sconvert admin"`)
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		next(w, r)
	}
}
