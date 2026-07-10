# mathpaste

Copy LaTeX, paste a real equation into Word.

Copy an equation from ChatGPT into Word and you get raw `\frac{dv}{dt}` instead of the math.
mathpaste fixes that at the clipboard.

## Install

```sh
git clone https://github.com/eliasmocik/mathpaste.git
cd mathpaste
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
brew install --cask hammerspoon
```

Paste [`hammerspoon-snippet.lua`](hammerspoon-snippet.lua) into `~/.hammerspoon/init.lua`, set
`MATHPASTE` to this folder, open Hammerspoon, grant **Accessibility**, and reload the config.

## Use

1. Select math anywhere.
2. **Cmd+C**.
3. Wait for **mathpaste ✓**.
4. Paste into Word.

Normal copies are untouched. Mixed prose + equations keep their formatting.

## Where it works

- **Word for Mac** => native equation.
- **Apple Mail, rich web editors** => works.
- **Google Docs** => no (can't import MathML).

MIT.
