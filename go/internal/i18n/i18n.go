// Package i18n будет прямым портом app/lang/ru.py и en.py.
// Пока — минимальный набор ключей для скелета (Фаза 1).
package i18n

type Dict map[string]string

// Base keys ported verbatim from app/lang/ru.py / en.py (dotted naming,
// matching the original — kept 1:1 so both sources stay easy to diff).
var RU = Dict{
	"nav.home":       "sConvert",
	"nav.units":      "Единицы измерения",
	"nav.currency":   "Валюты",
	"nav.btc":        "Биткоин (BTC)",
	"nav.latex":      "Формулы (LaTeX)",
	"nav.about":      "О проекте",
	"footer.privacy": "Политика конфиденциальности",
	"home.splash":    "проект sConvert",
	"home.favorites.title": "Избранные компоненты",
}

var EN = Dict{
	"nav.home":       "sConvert",
	"nav.units":      "Units",
	"nav.currency":   "Currency",
	"nav.btc":        "Bitcoin (BTC)",
	"nav.latex":      "LaTeX formulas",
	"nav.about":      "About",
	"footer.privacy": "Privacy policy",
	"home.splash":    "project sConvert",
	"home.favorites.title": "Favorite components",
}

func For(lang string) Dict {
	if lang == "en" {
		return EN
	}
	return RU
}

func init() {
	for k, v := range unitsRU {
		RU[k] = v
	}
	for k, v := range unitsEN {
		EN[k] = v
	}
}
