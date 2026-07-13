# mathpaste

ChatGPT equations used to paste into Word as real math. Now you just get raw LaTeX like
`\frac{dv}{dt}`. mathpaste fixes that: copy the LaTeX, hit one hotkey, paste a real equation.

## Install

```sh
git clone https://github.com/eliasmocik/mathpaste.git
cd mathpaste
./setup
```

Needs macOS, Python 3.9+, [Hammerspoon](https://www.hammerspoon.org), and Word for Mac.
Remove it with `./setup --uninstall`.

## Use

1. Copy math (LaTeX) anywhere — a normal **Cmd+C**.
2. Press **⌘⌥C** (command + option + C) to convert the clipboard.
3. Paste into Word with **Cmd+V**.

The hotkey only ever touches the clipboard when you press it, and only rewrites it when the
selection actually contains math — so ordinary copy/paste is never affected. Mixed prose +
equations keep their formatting.

> Earlier versions ran a background watcher that auto-converted on plain **Cmd+C**. That
> silently mangled ordinary copies whose text merely *looked* mathy (a `$`, an underscore in a
> filename like `platform_linux.py`), so it was replaced by the explicit hotkey above.

## Where it works

- **Word for Mac** => native equation.
- **Apple Mail, rich web editors** => works.
- **Google Docs** => no (can't import MathML).
