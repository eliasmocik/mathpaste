# mathpaste

ChatGPT equations used to paste into Word as real math. Now you just get raw LaTeX like
`\frac{dv}{dt}`. mathpaste fixes that automatically at the clipboard: copy as normal, paste a
real equation.

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
