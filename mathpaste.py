#!/usr/bin/env python3
"""mathpaste — turn LaTeX on the clipboard into a native Word equation.

Copy raw LaTeX (e.g. \\frac{dv}{dt}=...) from ChatGPT, Claude, anywhere.
Run this. It reads the clipboard, converts LaTeX -> MathML, and rewrites the
clipboard as HTML-wrapped MathML on the macOS `public.html` flavor. Paste into
Microsoft Word for Mac and you get a real, rendered equation instead of the
raw source string.

Because it operates at the clipboard, it is app-agnostic: it does not care
which app the LaTeX came from, so it keeps working even when ChatGPT changes
what it puts on the clipboard.

Usage:
    mathpaste            # convert whatever LaTeX is on the clipboard
    mathpaste --check    # print the generated MathML, don't touch the clipboard
    echo '\\frac a b' | mathpaste -   # read LaTeX from stdin instead
"""
from __future__ import annotations

import sys

from latex2mathml.converter import convert as latex_to_mathml

import AppKit  # PyObjC — macOS NSPasteboard access


MATHML_NS = "http://www.w3.org/1998/Math/MathML"


def read_clipboard_text() -> str:
    """Return the plain-text contents of the macOS clipboard."""
    pb = AppKit.NSPasteboard.generalPasteboard()
    text = pb.stringForType_(AppKit.NSPasteboardTypeString)
    return text or ""


def strip_delimiters(latex: str) -> tuple[str, bool]:
    """Strip surrounding math delimiters and detect display (block) mode.

    Returns (clean_latex, is_display). Handles $$...$$, \\[...\\], $...$,
    \\(...\\), and a bare `\\begin{equation}`-style body left as-is.
    """
    s = latex.strip()
    is_display = False

    pairs = [
        ("$$", "$$", True),
        (r"\[", r"\]", True),
        (r"\(", r"\)", False),
        ("$", "$", False),
    ]
    for open_, close_, display in pairs:
        if s.startswith(open_) and s.endswith(close_) and len(s) >= len(open_) + len(close_):
            s = s[len(open_): len(s) - len(close_)].strip()
            is_display = display
            break

    return s, is_display


def latex_to_mathml_and_html(latex: str, display: bool | None = None) -> tuple[str, str]:
    """Convert LaTeX to (bare presentation MathML, HTML-wrapped MathML).

    `display=None` auto-detects block vs inline from the delimiters.
    """
    clean, detected_display = strip_delimiters(latex)
    if display is None:
        display = detected_display

    mathml = latex_to_mathml(clean)

    # latex2mathml emits display="inline" by default; honour block mode.
    if display:
        mathml = mathml.replace('display="inline"', 'display="block"', 1)

    # Minimal HTML wrapper. Word for Mac reads MathML from the public.html
    # flavor and rebuilds it into a native equation on plain Cmd+V.
    html = (
        "<html><head>"
        '<meta charset="utf-8"></head><body>'
        f"{mathml}"
        "</body></html>"
    )
    return mathml, html


def write_clipboard(html: str, mathml: str) -> None:
    """Write the equation to the macOS clipboard in two flavors.

    - public.html  -> HTML-wrapped MathML; plain Cmd+V into current Word for
      Mac auto-converts it to a native equation.
    - public.utf8-plain-text -> the raw MathML; on older Word builds this is the
      Edit -> Paste Special -> Unformatted Text fallback that still converts.
    """
    pb = AppKit.NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.declareTypes_owner_(
        [AppKit.NSPasteboardTypeHTML, AppKit.NSPasteboardTypeString], None
    )
    pb.setString_forType_(html, AppKit.NSPasteboardTypeHTML)
    pb.setString_forType_(mathml, AppKit.NSPasteboardTypeString)


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    from_stdin = "-" in argv

    if from_stdin:
        latex = sys.stdin.read()
    else:
        latex = read_clipboard_text()

    if not latex.strip():
        print("mathpaste: clipboard (or stdin) is empty — copy some LaTeX first.",
              file=sys.stderr)
        return 1

    try:
        mathml, html = latex_to_mathml_and_html(latex)
    except Exception as exc:  # noqa: BLE001 — surface any conversion failure plainly
        print(f"mathpaste: could not convert LaTeX -> MathML: {exc}", file=sys.stderr)
        print(f"  input was: {latex.strip()[:120]}", file=sys.stderr)
        return 2

    if check_only:
        print(html)
        return 0

    write_clipboard(html, mathml)
    preview = latex.strip().replace("\n", " ")
    if len(preview) > 60:
        preview = preview[:57] + "..."
    print(f"mathpaste: clipboard ready — paste into Word.  ({preview})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
