package web

import (
	"html/template"
	"net/http"
)

// contactEmailB64 is "closegamer@mail.ru" base64-encoded — never appears in plain text in the HTML
// source, only decoded client-side on click (see static/js/privacy.js).
const contactEmailB64 = "Y2xvc2VnYW1lckBtYWlsLnJ1"

type PrivacyPageData struct {
	PageData
	Text          template.HTML
	ContactEmailB64 string
}

// PrivacyHandler renders /privacy. Text is trusted, static HTML (headings,
// <br>, <code>) from the privacy.text i18n key. The email reveal is plain
// inline markup+JS (static/js/privacy.js).
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
