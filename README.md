# mathpaste

Copy LaTeX. Paste a real equation into Word.

When you copy an equation from ChatGPT and paste it into Microsoft Word, you
get the raw source — `\frac{dv}{dt}=\frac{dv}{dx}\frac{dx}{dt}` — instead of the
rendered math. **mathpaste** fixes that. It sits at the clipboard, converts the
LaTeX to MathML (the format Word rebuilds into a native equation), and rewrites
the clipboard so your next paste is proper math.

```
copy LaTeX  →  ⌥⌘M  →  paste into Word  →  native equation
```

## Why the clipboard, not a browser extension

An equation can travel on the clipboard in different "languages":

- **LaTeX** — the source code. Compact, but it's just text. Word won't render it.
- **MathML** — a structured description Word knows how to rebuild into a real equation.

Some apps (Claude) put MathML on the clipboard, so Word renders on paste.
ChatGPT now puts **only LaTeX text**, so you get the raw string. mathpaste
inserts the missing translation step — LaTeX → MathML — right at the clipboard.

Because it lives at the clipboard, it's **app-agnostic**: ChatGPT can change
whatever it wants and this still works, unlike a site-specific extension that
breaks every time they touch their page.

## Requirements

- macOS
- Python 3.9+
- Microsoft Word for Mac (for the native-equation paste). Plain `Cmd+V`
  auto-converts on recent builds (≈ Version 16.100+); older builds use the
  Paste Special fallback below.

## Install

```bash
git clone https://github.com/eliasmocik/mathpaste.git
cd mathpaste
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

## v0 — CLI

```bash
# 1. Copy some LaTeX (from ChatGPT, Claude, anywhere)
# 2. Convert the clipboard in place:
./mathpaste
# 3. Paste into Word.
```

Other forms:

```bash
echo '\frac{a}{b}=c^2' | ./mathpaste -   # read LaTeX from stdin
./mathpaste --check                       # print the MathML, don't touch clipboard
```

Delimiters are handled automatically: `$…$` and `\(…\)` → inline,
`$$…$$` and `\[…\]` → display (block).

## v1 — global hotkey (Hammerspoon)

So you never see a terminal:

```bash
brew install --cask hammerspoon
```

Open Hammerspoon once and grant it Accessibility permission when asked. Then
append [`hammerspoon-snippet.lua`](hammerspoon-snippet.lua) to
`~/.hammerspoon/init.lua` and reload the config (menu-bar icon → Reload Config).

Now: **copy LaTeX → ⌥⌘M → paste into Word.**

## If plain paste shows raw markup

On older Word for Mac builds, plain `Cmd+V` may not auto-convert. Use
**Edit → Paste Special → Unformatted Text** instead — mathpaste also puts the
raw MathML on the plain-text flavor for exactly this fallback.

## How it works

`latex2mathml` converts the LaTeX to **presentation MathML** with the full
`http://www.w3.org/1998/Math/MathML` namespace (the one detail that breaks most
DIY attempts — Word silently refuses MathML with a truncated namespace). The
result is written to the macOS clipboard via `NSPasteboard` in two flavors:
`public.html` (HTML-wrapped MathML, for plain-paste) and `public.utf8-plain-text`
(raw MathML, for the Paste Special fallback).

## Limitations

- Very complex multiline structures (`\begin{aligned}`, big matrices) can
  occasionally fail to convert on Word's side. Simple/standard math is reliable.
- Word for Mac must have the MathML import filter (any reasonably current build).

## License

MIT — see [LICENSE](LICENSE).
