package i18n

// "latex.*"/"latex_guide.*" keys, Russian. The PNG is rendered client-side
// from the same KaTeX DOM node the preview uses (via html-to-image), so the
// download always matches the preview.
var latexRU = Dict{
	"latex.title":              "Формулы LaTeX",
	"latex.lead":                "Введите формулу на языке TeX. Голый TeX или с разделителями \\(...\\), $...$, $$...$$ — перед предпросмотром разделители снимаются. Когда формула будет готова, её можно скопировать в буфер в исходном виде или скачать результирующую картинку.",
	"latex.input_label":         "Исходная формула (TeX / LaTeX)",
	"latex.preview_label":       "Предпросмотр",
	"latex.clipboard_result":    "TeX для предпросмотра — выделите и Ctrl+C (⌘C)",
	"latex.copy_source_button":  "Копировать",
	"latex.formula_png_label":   "Картинка готовой формулы (PNG)",
	"latex.download_png":        "Скачать PNG",
	"latex.png_unavailable":     "Не удалось сгенерировать PNG для этой формулы.",
	"latex.empty_hint":          "Введите формулу выше…",
	"latex.example":             "\\int_{-\\infty}^{\\infty} e^{-x^2}\\,dx = \\sqrt{\\pi}",
	"footer.latex_guide":        "Памятка LaTeX",
	"latex_guide.title":         "Памятка по LaTeX (математический набор)",
}
