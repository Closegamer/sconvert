A concise reference for **TeX/LaTeX math** you can paste into the **LaTeX formulas** section on this site. Preview uses **KaTeX** (a subset of LaTeX): many full-LaTeX packages and macros are **not** available here.

---

### 1. Delimiters: inline vs display

| Syntax | Role |
|--------|------|
| `$...$` | inline math |
| `$$...$$` | display (block) math |
| `\(...\)` | inline (alternative) |
| `\[...\]` | display (alternative) |

This app **strips outer delimiters** before feeding KaTeX. You can keep or omit wrappers when copying—the normalized preview stays consistent.

---

### 2. Letters, digits, text

Letters and digits are set in math italics. For **words** inside math use `\text{...}`:

```tex
\text{if } x>0\text{ then }y=x^2
```

---

### 3. Subscripts and superscripts

- Subscript: `x_1`, groups: `x_{10}`
- Superscript: `x^2`, groups: `x^{10}`
- Combined: `x_1^2`, `e^{-x^2}`

---

### 4. Greek letters

`\alpha`, `\beta`, `\gamma`, `\pi`, `\sigma`, `\omega`, `\Gamma`, `\Delta`, `\Omega`, etc.

---

### 5. Fractions and roots

- `\frac{numerator}{denominator}` — e.g. `\frac{1}{2}`, `\frac{a+b}{c}`
- `\sqrt{x}`, `\sqrt[n]{x}`

---

### 6. Sums, products, integrals

- `\sum_{i=1}^{n} i`
- `\prod_{k=1}^{n} k`
- `\int_a^b f(x)\,dx` — thin space before `dx`: `\,`
- `\oint`, `\iint`, `\iiint`
- `\lim_{x\to 0}`, `\lim_{n\to\infty}`

Infinity: `\infty`.

---

### 7. Delimiters that resize

```tex
\left( \frac{a}{b} \right)
```

Also `\left[ \right]`, `\left\{ \right\}`, `\left| \right|`. Brace literals need escaping: `\{` `\}`.

---

### 8. Matrices

```tex
\begin{pmatrix} a & b \\ c & d \end{pmatrix}
```

Other environments (`bmatrix`, `vmatrix`) exist; KaTeX supports a limited set—simplify if preview breaks.

---

### 9. Operators and relations

- `\cdot`, `\times`, `\div`
- `\leq`, `\geq`, `\neq`, `\approx`, `\equiv`
- `\in`, `\subset`, `\cup`, `\cap`, `\emptyset`
- `\land`, `\lor`, `\neg`, `\forall`, `\exists`

---

### 10. Arrows and accents

- `\rightarrow`, `\Rightarrow`, `\leftrightarrow`, `\mapsto`
- `\vec{x}`, `\hat{x}`, `\bar{x}`, `\tilde{x}`, `\dot{x}`, `\ddot{x}`

---

### 11. Spacing

- `\ ` explicit space
- `\,` thin (often before `dx`)
- `\:` `\;` medium / thick
- `\quad`, `\qquad` wide gaps

---

### 12. Fonts

- `\mathrm{sin}`, `\mathrm{d}` — upright sin / differential d
- `\mathbf{v}` — bold
- `\mathcal{L}` — script
- `\mathbb{R}` — blackboard (if font glyphs exist)

---

### 13. Multi-line alignment

```tex
\begin{aligned} a &= b+c \\ d &= e \end{aligned}
```

If KaTeX complains, split into two formulas.

---

### 14. What often fails

Full LaTeX with arbitrary packages, `\includegraphics`, custom macros, etc. may not render. Prefer standard math commands; see [KaTeX supported functions](https://katex.org/docs/supported.html).

---

### 15. Quick test

Try:

```tex
\int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
```

If it previews correctly, you’re within typical KaTeX usage for this app.
