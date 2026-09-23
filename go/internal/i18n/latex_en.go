package i18n

// Ported from app/lang/en.py — see latex_ru.go for what changed vs. the original.
var latexEN = Dict{
	"latex.title":             "LaTeX formulas",
	"latex.lead":               "Enter TeX below. Plain TeX or delimiters \\(...\\), $...$, $$...$$ — delimiters are stripped before preview. You can then copy your formula when it is ready or download result picture.",
	"latex.input_label":        "Source formula (TeX / LaTeX)",
	"latex.preview_label":      "Preview",
	"latex.clipboard_result":   "Preview TeX — select, then Ctrl+C (⌘C)",
	"latex.copy_source_button": "Copy",
	"latex.formula_png_label":  "Formula image (PNG)",
	"latex.download_png":       "Download PNG",
	"latex.png_unavailable":    "Could not generate a PNG for this formula.",
	"latex.empty_hint":         "Enter a formula above…",
	"latex.example":            "\\int_{-\\infty}^{\\infty} e^{-x^2}\\,dx = \\sqrt{\\pi}",
	"footer.latex_guide":       "LaTeX cheat sheet",
	"latex_guide.title":        "LaTeX cheat sheet (math typesetting)",
}
