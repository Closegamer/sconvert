// Package latexguide renders the LaTeX cheat sheet (app/content/latex_guide_*.md,
// ported verbatim) to HTML once at startup via goldmark (GFM tables, the
// content uses them for the "typical sources of LaTeX" reference table).
package latexguide

import (
	"bytes"
	"embed"
	"html/template"

	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/extension"
)

//go:embed content/*.md
var contentFS embed.FS

var md = goldmark.New(goldmark.WithExtensions(extension.GFM))

var rendered = map[string]template.HTML{}

func init() {
	for _, lang := range []string{"ru", "en"} {
		raw, err := contentFS.ReadFile("content/latex_guide_" + lang + ".md")
		if err != nil {
			panic(err)
		}
		var buf bytes.Buffer
		if err := md.Convert(raw, &buf); err != nil {
			panic(err)
		}
		rendered[lang] = template.HTML(buf.String())
	}
}

// HTML returns the pre-rendered cheat sheet for lang ("ru" or "en",
// defaulting to "ru" for anything else).
func HTML(lang string) template.HTML {
	if h, ok := rendered[lang]; ok {
		return h
	}
	return rendered["ru"]
}
