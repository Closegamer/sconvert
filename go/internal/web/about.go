package web

import (
	"html/template"
	"net/http"
)

// walletAddress is the donation address ported verbatim from
// app/lang/*.py's about.subtitle. Split out from the surrounding i18n
// prose so the template can drop a copy button right next to it.
const walletAddress = "bc1qh9crcvmfvx2qrg8lwm5leg05ytx87uctd9l3lp"

type AboutPageData struct {
	PageData
	Before  template.HTML
	Address string
	After   template.HTML
}

// AboutHandler renders /about. Before/After are trusted, static text
// (ported verbatim from app/lang/*.py's about.subtitle) — wrapped as
// template.HTML explicitly here rather than making the general i18n
// lookup unescaped for everyone.
func AboutHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := &AboutPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.about", "About sConvert"),
				i18nOr(lang, "seo.description.about", ""),
				"https://sconvert.ru/about",
			),
			Before:  template.HTML(i18nOr(lang, "about.subtitle_before", "")),
			Address: walletAddress,
			After:   template.HTML(i18nOr(lang, "about.subtitle_after", "")),
		}
		Render(w, "page:about", data)
	}
}
