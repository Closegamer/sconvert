package web

import (
	"html/template"
	"net/http"

	"sconvert/internal/latexguide"
)

type LatexPageData struct {
	PageData
	Example string
}

// LatexHandler renders /latex. There's no server-side computation at all:
// delimiter-stripping and KaTeX rendering happen entirely client-side (see
// static/js/latex.js) — the original Python's matplotlib PNG rasterization
// is replaced by rendering the same client-side KaTeX DOM node to a PNG via
// html-to-image, so preview and download can never disagree with each other.
func LatexHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := &LatexPageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.latex", "LaTeX - sConvert"),
				i18nOr(lang, "seo.description.latex", ""),
				"https://sconvert.ru/latex",
			),
			Example: i18nOr(lang, "latex.example", ""),
		}
		Render(w, "page:latex", data)
	}
}

type LatexGuidePageData struct {
	PageData
	Body template.HTML
}

// LatexGuideHandler renders /latex_guide: the cheat sheet markdown
// (app/content/latex_guide_*.md), pre-rendered to HTML at startup.
func LatexGuideHandler() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		lang := langFromRequest(r)
		data := &LatexGuidePageData{
			PageData: NewPageData(
				lang,
				i18nOr(lang, "seo.title.latex_guide", "LaTeX guide - sConvert"),
				i18nOr(lang, "seo.description.latex_guide", ""),
				"https://sconvert.ru/latex_guide",
			),
			Body: latexguide.HTML(lang),
		}
		Render(w, "page:latex_guide", data)
	}
}
