package web

import (
	"html/template"
	"net/http"
)

// contactEmailB64 is "closegamer@mail.ru" base64-encoded, matching the
// original Python component — never appears in plain text in the HTML
// source, only decoded client-side on click (see static/js/privacy.js).
const contactEmailB64 = "Y2xvc2VnYW1lckBtYWlsLnJ1"

type PrivacyPageData struct {
	PageData
	Text          template.HTML
	ContactEmailB64 string
}

// PrivacyHandler renders /privacy. Text is trusted, static HTML (headings,
// <br>, a link to Yandex's own privacy policy) ported verbatim from
// app/lang/*.py's privacy.text. The original's iframe-sandboxed email
// reveal widget (Streamlit components.html) becomes plain inline
// markup+JS here — no sandbox needed since the Go page isn't embedded.
func PrivacyHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := &PrivacyPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.privacy", "Privacy Policy - sConvert"),
				i18nOr(lang, "seo.description.privacy", ""),
				"https://sconvert.ru/privacy",
			),
			Text:            template.HTML(i18nOr(lang, "privacy.text", "")),
			ContactEmailB64: contactEmailB64,
		}
		Render(w, "page:privacy", data)
	}
}
