package web

import (
	"bytes"
	"html/template"
	"net/http"

	"sconvert/internal/i18n"
)

type PageData struct {
	Lang        string
	Title       string
	Description string
	Canonical   string
	T           i18n.Dict
	Content     template.HTML
}

func NewPageData(lang, title, description, canonical string) PageData {
	return PageData{
		Lang:        lang,
		Title:       title,
		Description: description,
		Canonical:   canonical,
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
