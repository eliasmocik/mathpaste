# mathpaste

Copy LaTeX, paste a real equation into Word.

Copy an equation from ChatGPT into Word and you get raw `\frac{dv}{dt}` instead of the math.
mathpaste fixes that at the clipboard.

## Install

```sh
git clone https://github.com/eliasmocik/mathpaste.git
cd mathpaste
./setup
```

Needs macOS, Python 3.9+, and Word for Mac. Runs as a small background agent that starts at login.
Remove it with `./setup --uninstall`.

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
