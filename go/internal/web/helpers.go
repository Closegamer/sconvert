package web

import (
	"net/http"

	"sconvert/internal/i18n"
)

// langFromRequest reads the UI language from a cookie, defaulting to "ru".
// Set/changed via the language toggle (see layout.html); no server round
// trip needed for the switch itself.
func langFromRequest(r *http.Request) string {
	if c, err := r.Cookie("sconvert_lang"); err == nil && c.Value == "en" {
		return "en"
	}
	return "ru"
}

func i18nOr(lang, key, fallback string) string {
	v, ok := i18n.For(lang)[key]
	if !ok || v == "" {
		return fallback
	}
	return v
}
