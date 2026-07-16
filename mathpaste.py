#!/usr/bin/env python3
"""mathpaste — turn copied LaTeX into native Word equations, formatting intact.

Copy a mix of prose and LaTeX (e.g. from ChatGPT), trigger mathpaste, and paste
into Microsoft Word. It splits the selection into paragraphs, converts only the
ones that are math (LaTeX -> MathML), keeps the prose and the line breaks, and
rewrites the clipboard so Word rebuilds each equation as a native object.

Because ChatGPT does not tag its math, "is this paragraph math?" is a heuristic:
a block is treated as math if it carries LaTeX commands / operators and reads
like an equation rather than a sentence. Paragraph-level classification keeps
that reliable for normal ChatGPT / Claude output.

Usage:
    mathpaste            # convert whatever is on the clipboard
    mathpaste --check    # print the generated HTML, don't touch the clipboard
    echo '...' | mathpaste -   # read text from stdin instead
"""
from __future__ import annotations

import re
import sys
import time
from html import escape as html_escape
from html.parser import HTMLParser

from latex2mathml.converter import convert as latex_to_mathml

import AppKit  # PyObjC — macOS NSPasteboard access


# A private flavor we stamp on clipboards we've already converted, so an
# always-on watcher never reprocesses mathpaste's own output.
MARKER_TYPE = "org.mathpaste.processed"


# ---------------------------------------------------------------------------
# Clipboard I/O
# ---------------------------------------------------------------------------

def read_clipboard() -> tuple[str | None, str | None]:
    """Return (html, plain_text) from the clipboard; either may be None."""
    pb = AppKit.NSPasteboard.generalPasteboard()
    html = pb.stringForType_(AppKit.NSPasteboardTypeHTML)
    text = pb.stringForType_(AppKit.NSPasteboardTypeString)
    return html, text


def clipboard_is_marked() -> bool:
    """True if we already converted whatever is on the clipboard."""
    pb = AppKit.NSPasteboard.generalPasteboard()
    return MARKER_TYPE in list(pb.types() or [])


def write_clipboard(html: str, plain: str) -> None:
    """Write the result to the clipboard as HTML (+ plain-text fallback + marker)."""
    pb = AppKit.NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.declareTypes_owner_(
        [AppKit.NSPasteboardTypeHTML, AppKit.NSPasteboardTypeString, MARKER_TYPE], None
    )
    pb.setString_forType_(html, AppKit.NSPasteboardTypeHTML)
    pb.setString_forType_(plain, AppKit.NSPasteboardTypeString)
    pb.setString_forType_("1", MARKER_TYPE)


# ---------------------------------------------------------------------------
# Splitting the selection into paragraph blocks
# ---------------------------------------------------------------------------

_BLOCK_TAGS = {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6",
               "tr", "blockquote", "pre"}


class _BlockExtractor(HTMLParser):
    """Collect block-level text runs from HTML, <br> -> newline."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._cur: str | None = None

    def _flush(self) -> None:
        if self._cur is not None and self._cur.strip():
            self.blocks.append(self._cur.strip())
        self._cur = None

    def handle_starttag(self, tag, attrs):
        if tag in _BLOCK_TAGS:
            self._flush()
            self._cur = ""
        elif tag == "br":
            if self._cur is None:
                self._cur = ""
            self._cur += "\n"

    def handle_endtag(self, tag):
        if tag in _BLOCK_TAGS:
            self._flush()

    def handle_data(self, data):
        if self._cur is None:
            self._cur = ""
        self._cur += data

    def close(self):
        super().close()
        self._flush()


def split_blocks(html: str | None, text: str | None) -> list[str]:
    """Return an ordered list of paragraph blocks from HTML (preferred) or text."""
    if html and "<" in html:
        parser = _BlockExtractor()
        parser.feed(html)
        parser.close()
        if parser.blocks:
            return parser.blocks
    # Fallback: split plain text on blank lines.
    if text:
        return [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    return []


# ---------------------------------------------------------------------------
# Math detection + conversion
# ---------------------------------------------------------------------------

_LATEX_CMD = re.compile(r"\\[a-zA-Z]+")
_WORD = re.compile(r"[A-Za-z]{3,}")          # a real word => leans prose
_MATH_OP = re.compile(r"[=<>]")


def strip_delimiters(latex: str) -> tuple[str, bool]:
    """Strip $…$, $$…$$, \\[…\\], \\(…\\) and report display (block) mode."""
    s = latex.strip()
    for open_, close_, display in (("$$", "$$", True), (r"\[", r"\]", True),
                                   (r"\(", r"\)", False), ("$", "$", False)):
        if s.startswith(open_) and s.endswith(close_) and len(s) >= len(open_) + len(close_):
            return s[len(open_):len(s) - len(close_)].strip(), display
    return s, False


_BOX_CMD = re.compile(r"\\(?:boxed|fbox|framebox|boxed\*)\s*\{")


def unbox(latex: str) -> str:
    r"""Strip \boxed{…} / \fbox{…} wrappers, keeping the contents.

    ChatGPT often wraps a final answer in \boxed{…}. That renders faithfully as
    a framed equation in Word — which Elias then deletes by hand. We unwrap it
    here (brace-matched, so nested {…} inside the box survive) before conversion.
    Repeats until no wrapper remains, so \boxed{\boxed{x}} fully unwinds.
    """
    while True:
        m = _BOX_CMD.search(latex)
        if not m:
            return latex
        start = m.start()          # index of the backslash
        open_brace = m.end() - 1   # index of the '{'
        depth = 0
        close = None
        for i in range(open_brace, len(latex)):
            c = latex[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    close = i
                    break
        if close is None:
            # Unbalanced braces — leave the string alone rather than mangle it.
            return latex
        inner = latex[open_brace + 1:close]
        latex = latex[:start] + inner + latex[close + 1:]


def is_math(block: str) -> bool:
    """Heuristic: does this paragraph read as an equation rather than prose?"""
    s = block.strip()
    core, _ = strip_delimiters(s)
    core = core.strip()
    if not core:
        return False
    # Explicitly delimited math ($…$, $$…$$, \[…\], \(…\)) is math, period —
    # the author told us so by wrapping it.
    if core != s:
        return True
    # Undelimited: only a real LaTeX command (\frac, \int, \ln, \alpha, …) marks
    # a bare block as math. A lone ^ or _ is NOT enough: underscores and carets
    # live in ordinary prose and code (snake_case, file names like
    # platform_linux.py), and firing on them is what shreds normal text into one
    # character per line. See the matching guard in watch().
    if _LATEX_CMD.search(core):
        return True
    # A standalone equation with a relational operator and no real words (only
    # variables), e.g. "E = mc^2".
    words = _WORD.findall(re.sub(r"\\[a-zA-Z]+", "", core))
    if _MATH_OP.search(core) and not words:
        return True
    return False


def convert_block(block: str) -> tuple[str, str]:
    """Convert one block -> (html_fragment, plain_fragment).

    Math blocks become <p>MathML</p>; anything that isn't math, or fails to
    convert, is kept verbatim as escaped text so one bad block never derails the
    whole paste.
    """
    if is_math(block):
        core, display = strip_delimiters(block)
        core = unbox(core)  # drop \boxed{…}/\fbox{…} wrappers, keep the contents
        core = " ".join(core.split())  # join multi-line equations onto one line
        try:
            mathml = latex_to_mathml(core)
            if display:
                mathml = mathml.replace('display="inline"', 'display="block"', 1)
            else:
                # Standalone equation blocks read better as display math.
                mathml = mathml.replace('display="inline"', 'display="block"', 1)
            return f"<p>{mathml}</p>", core
        except Exception:
            pass  # fall through to text
    # Prose (or unconvertible): keep text, turn internal newlines into <br>.
    safe = "<br>".join(html_escape(line) for line in block.split("\n"))
    return f"<p>{safe}</p>", block


def build(blocks: list[str]) -> tuple[str, str, int]:
    """Assemble the output HTML + plain text; return (html, plain, math_count)."""
    html_parts, text_parts, n_math = [], [], 0
    for b in blocks:
        frag_html, frag_text = convert_block(b)
        if "<math" in frag_html:
            n_math += 1
        html_parts.append(frag_html)
        text_parts.append(frag_text)
    html = ("<html><head><meta charset=\"utf-8\"></head><body>"
            + "".join(html_parts) + "</body></html>")
    return html, "\n".join(text_parts), n_math


# ---------------------------------------------------------------------------
# Background watcher (launchd agent) — auto-convert on plain Cmd+C
# ---------------------------------------------------------------------------

# A copy only looks like math if it carries a real LaTeX command (\frac, \int, …)
# or a math delimiter ($…$, $$…$$, \[…\], \(…\)). A bare ^ or _ is NOT enough:
# underscores and carets are everywhere in ordinary text (snake_case, file names,
# subscript-style notes), and firing on them is what broke normal pasting.
_LOOKS_MATH = re.compile(r"\\[a-zA-Z]+|\$|\\\[|\\\(")


def watch(poll: float = 0.4) -> int:
    """Poll the clipboard; when math is copied, convert it in place.

    Non-math copies are ignored; our own output is skipped via the marker, so
    this never loops on itself. Reads/writes the clipboard only — no keystroke
    simulation, so it needs no Accessibility permission.
    """
    pb = AppKit.NSPasteboard.generalPasteboard()
    last = pb.changeCount()
    while True:
        time.sleep(poll)
        try:
            cc = pb.changeCount()
            if cc == last:
                continue
            last = cc
            if clipboard_is_marked():
                continue
            html, text = read_clipboard()
            # Only ever fire on a copy carrying a real LaTeX command / math
            # delimiter (browser copies from ChatGPT/Claude keep the raw source;
            # so does plain text). A rich copy from Word renders its equations,
            # so its plain text has no \command or $ and is skipped here — which
            # is why we don't need a separate RTF guard. Browser math copies also
            # carry an RTF flavor, so guarding on RTF wrongly blocked them.
            if not (text and _LOOKS_MATH.search(text)):
                continue
            blocks = split_blocks(html, text)
            if not blocks:
                continue
            out_html, out_text, n_math = build(blocks)
            if n_math == 0:
                continue
            write_clipboard(out_html, out_text)
            last = pb.changeCount()  # swallow our own write
        except Exception as exc:  # keep the daemon alive no matter what
            print(f"mathpaste watch error: {exc}", file=sys.stderr, flush=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    if "--watch" in argv:
        return watch()

    check_only = "--check" in argv
    from_stdin = "-" in argv
    auto = "--auto" in argv  # watcher mode: stay silent on no-op cases

    # In watcher mode, never touch a clipboard we already converted (loop guard).
    if auto and not from_stdin and clipboard_is_marked():
        return 0

    if from_stdin:
        html, text = None, sys.stdin.read()
    else:
        html, text = read_clipboard()

    blocks = split_blocks(html, text)
    if not blocks:
        if auto:
            return 0
        print("mathpaste: clipboard (or stdin) is empty — copy something first.",
              file=sys.stderr)
        return 1

    out_html, out_text, n_math = build(blocks)

    if n_math == 0:
        if auto:
            return 0  # nothing to convert — leave the clipboard alone silently
        print("mathpaste: no math found in the selection — clipboard left as-is.",
              file=sys.stderr)
        return 3

    if check_only:
        print(out_html)
        return 0

    write_clipboard(out_html, out_text)
    plural = "equation" if n_math == 1 else "equations"
    print(f"mathpaste: {n_math} {plural} ready — paste into Word.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
