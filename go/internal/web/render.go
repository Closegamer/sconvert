package web

import (
	"bytes"
	"encoding/json"
	"html/template"
	"net/http"

	"sconvert/internal/i18n"
)

const (
	siteBaseURL = "https://sconvert.ru"
	ogImageURL  = siteBaseURL + "/og-image.png"
)

type PageData struct {
	Lang        string
	Title       string
	Description string
	Canonical   string
	OGLocale    string
	OGImage     string
	SiteBaseURL string
	JSONLD      template.JS
	T           i18n.Dict
	Content     template.HTML
}

type websiteJSONLD struct {
	Context     string   `json:"@context"`
	Type        string   `json:"@type"`
	Name        string   `json:"name"`
	URL         string   `json:"url"`
	InLanguage  []string `json:"inLanguage"`
	Description string   `json:"description"`
}

// NewPageData centralizes the SEO fields every page needs (ported from
// Python's _inject_seo_meta in app/Home.py) so each handler only supplies
// the per-page title/description/canonical — OG locale and the JSON-LD
// WebSite block are derived here once instead of duplicated per handler.
func NewPageData(lang, title, description, canonical string) PageData {
	ogLocale := "ru_RU"
	if lang == "en" {
		ogLocale = "en_US"
	}
	jsonLD, _ := json.Marshal(websiteJSONLD{
		Context:     "https://schema.org",
		Type:        "WebSite",
		Name:        "sConvert",
		URL:         siteBaseURL,
		InLanguage:  []string{"ru", "en"},
		Description: description,
	})
	return PageData{
		Lang:        lang,
		Title:       title,
		Description: description,
		Canonical:   canonical,
		OGLocale:    ogLocale,
		OGImage:     ogImageURL,
		SiteBaseURL: siteBaseURL,
		JSONLD:      template.JS(jsonLD),
		T:           i18n.For(lang),
	}
}

// contentSetter lets Render populate the shared .Content field on any page
// data struct that embeds PageData (by value), as long as a pointer to it
// is passed in — Go promotes the pointer-receiver method through the
// embedded field automatically.
type contentSetter interface {
	setContent(template.HTML)
}

func (p *PageData) setContent(h template.HTML) { p.Content = h }

// Render executes the named content template ("page:xxx"), then wraps the
// result in the shared layout. data must be a pointer to a struct
// embedding PageData (e.g. *PageData, *UnitsPageData). Content templates
// only ever receive already-known-safe server data, so re-wrapping the
// rendered bytes as template.HTML here does not introduce an injection
// risk.
func Render(w http.ResponseWriter, contentName string, data contentSetter) {
	var buf bytes.Buffer
	if err := templates.ExecuteTemplate(&buf, contentName, data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data.setContent(template.HTML(buf.String()))

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	if err := templates.ExecuteTemplate(w, "layout", data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}
