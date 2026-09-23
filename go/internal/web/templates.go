package web

import (
	"embed"
	"fmt"
	"html/template"
)

//go:embed templates/*.html
var templateFS embed.FS

var funcMap = template.FuncMap{
	// dict lets a {{template "name" (dict "K1" v1 "K2" v2)}} call pass
	// multiple values (e.g. the outer .T dict plus one category) into a
	// shared partial — html/template only ever passes a single value.
	"dict": func(pairs ...any) (map[string]any, error) {
		if len(pairs)%2 != 0 {
			return nil, fmt.Errorf("dict: odd number of arguments")
		}
		m := make(map[string]any, len(pairs)/2)
		for i := 0; i < len(pairs); i += 2 {
			key, ok := pairs[i].(string)
			if !ok {
				return nil, fmt.Errorf("dict: key %v is not a string", pairs[i])
			}
			m[key] = pairs[i+1]
		}
		return m, nil
	},
}

var templates = template.Must(template.New("").Funcs(funcMap).ParseFS(templateFS, "templates/*.html"))
