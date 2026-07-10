# mathpaste

Copy LaTeX, paste a real equation into Word.

Ok real talk: you copy an equation from ChatGPT, paste it into Word, and instead of the actual
fraction you get `\frac{dv}{dt}=\frac{dv}{dx}\frac{dx}{dt}` sitting there as raw text. mathpaste
fixes that. You copy like normal, and when you paste into Word you get proper, rendered math.

It sits at the clipboard, so it doesn't care which app the LaTeX came from - ChatGPT, Claude, a
PDF, wherever. ChatGPT can change whatever they want next month and this still works.

## Why it happens

An equation can travel on the clipboard in different "languages":

- **LaTeX** (`\frac{dv}{dt}`) => the source code. Compact, but it's just text. Word won't render it.
- **MathML** => a structured description of the math that Word knows how to rebuild into an equation.

Claude puts MathML on the clipboard, so Word renders it. ChatGPT now puts only LaTeX text, so you
get the raw string. mathpaste is the missing translator: LaTeX => MathML, right at the clipboard.

## What you need

- **macOS**
- **Python 3.9+**
- **Microsoft Word for Mac** (that's where the equation actually renders)
- **Hammerspoon** for the automatic Cmd+C part (`brew install --cask hammerspoon`)

## Install

```sh
git clone https://github.com/eliasmocik/mathpaste.git
cd mathpaste
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
```

Then wire up the hotkey. Open [`hammerspoon-snippet.lua`](hammerspoon-snippet.lua), paste it into
your `~/.hammerspoon/init.lua` (make the file if it isn't there), and set `MATHPASTE` to wherever
you cloned this. Open Hammerspoon once, grant it **Accessibility** when it asks, and reload the
config (menu-bar hammer => Reload Config).

## Using it

Just copy. Normal **Cmd+C**.

1. Select math anywhere (ChatGPT, Claude, a PDF).
2. **Cmd+C**.
3. Wait for the **mathpaste ✓** flash (about half a second).
4. Paste into Word.

That's it. It watches the clipboard, and when it sees LaTeX it quietly swaps in the Word-friendly
version. Normal text copies are left completely alone - it only touches the clipboard when there's
actually math on it.

It's smart about mixed selections too: grab a whole chunk of prose + equations and it keeps the
words as words, keeps the line breaks, and only turns the math into math.

> **Wait for the ✓ before you paste.** If you paste instantly you'll get the raw copy - the
> conversion takes a beat.

### Without the hotkey

You can also just run it on whatever's on the clipboard:

```sh
./mathpaste            # convert the clipboard
./mathpaste --check    # print the MathML, don't touch the clipboard
echo '\frac a b' | ./mathpaste -   # read from stdin
```

## Where it works

- **Word for Mac** => native equation. This is the one it's built for.
- **Apple Mail / rich web editors** => usually works (they render MathML).
- **Google Docs** => no. Docs won't import MathML on paste, full stop.
- **Plain text stuff** (Slack, terminal, code) => you get the raw MathML, which is ugly. Don't.

## How it works

`latex2mathml` turns the LaTeX into presentation MathML with the full namespace (the one detail
that quietly breaks most DIY attempts - Word rejects MathML with a truncated namespace). That gets
written to the clipboard as HTML, which Word rebuilds into a real equation on paste. A little
Hammerspoon watcher runs the whole thing automatically on Cmd+C.

## Heads up

- ChatGPT doesn't tag its math, so "is this bit math?" is a heuristic. It's reliable for normal
  ChatGPT / Claude output, but it can miss a bare equation with no `\commands` in it.
- Really gnarly multi-line stuff (big `\begin{aligned}` blocks, huge matrices) can occasionally
  refuse to convert on Word's end. Simple, everyday math is solid.

## License

MIT - see [LICENSE](LICENSE).
