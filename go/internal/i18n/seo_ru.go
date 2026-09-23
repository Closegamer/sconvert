package i18n

// SEO <title>/<meta description> text per page, ported from
// app/Home.py's _inject_seo_meta (title_by_view/description_by_view) —
// distinct from on-page headings/subtitles, which is why these live in
// their own key namespace instead of reusing e.g. "units.subtitle" (a
// stale placeholder, wrong to also use as a meta description).
var seoRU = Dict{
	"seo.title.home":            "sConvert - онлайн конвертер величин, данных и BTC-инструментов",
	"seo.description.home":      "sConvert: конвертер единиц измерения, форматов данных и инструменты для Bitcoin.",
	"seo.title.units":           "Конвертер единиц измерения - sConvert",
	"seo.description.units":     "Быстрый конвертер единиц: длина, масса, время, энергия, давление и другие категории.",
	"seo.title.currency":        "Конвертер валют онлайн - sConvert",
	"seo.description.currency":  "Онлайн конвертер валют с актуальным курсом: USD, EUR, RUB, GBP, CNY, JPY и другие.",
	"seo.title.btc":             "Bitcoin (BTC) инструменты: ключи, адреса, проверки - sConvert",
	"seo.description.btc":       "Инструменты Bitcoin: преобразование ключей и адресов, формат WIF, RIPEMD160, UTXO и транзакции.",
	"seo.title.latex":           "Формулы LaTeX: предпросмотр KaTeX - sConvert",
	"seo.description.latex":     "Предпросмотр формул TeX/LaTeX через KaTeX, с экспортом готовой картинки в PNG.",
	"seo.title.latex_guide":     "Памятка по LaTeX и математическому набору - sConvert",
	"seo.description.latex_guide": "Справочник: разделители, дроби, интегралы, матрицы, греческие буквы и ограничения KaTeX.",
	"seo.title.about":           "О проекте sConvert",
	"seo.description.about":     "Информация о проекте sConvert и назначении сервиса.",
	"seo.title.privacy":         "Политика конфиденциальности - sConvert",
	"seo.description.privacy":   "Какие данные собирает sConvert через Яндекс.Метрику и как они обрабатываются.",
}
