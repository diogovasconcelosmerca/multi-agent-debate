"""
Build a print-quality PDF of docs/CODEBASE_TOUR.md.

Same pipeline as build_reports_pdf.py, tuned for a longer tutorial
document (more breathing room, slightly larger body type).

Output: docs/MADS_Codebase_Tour.pdf

Usage:
    python scripts/build_codebase_tour_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "CODEBASE_TOUR.md"
OUT = ROOT / "docs" / "MADS_Codebase_Tour.pdf"
HTML_OUT = ROOT / "docs" / "MADS_Codebase_Tour.html"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

@page {
    size: A4;
    margin: 22mm 18mm 22mm 18mm;
}

:root {
    --ink:        #0F0F11;
    --ink-2:      #2B2B2F;
    --muted:      #6E6E76;
    --rule:       #E6E6EA;
    --bg-soft:    #F7F7F9;
    --code-bg:    #F4F3F1;
    --accent:     #D9622A;
    --accent-2:   #B8884A;
    --link:       #B85020;
}

* { box-sizing: border-box; }

html { font-size: 10.6pt; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--ink);
    line-height: 1.6;
    margin: 0;
    -webkit-font-smoothing: antialiased;
}

h1 {
    font-size: 22pt;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0 0 0.3em 0;
    line-height: 1.15;
    page-break-after: avoid;
}

h1:not(:first-of-type) {
    margin-top: 1.4em;
    padding-top: 0.6em;
    border-top: 2px solid var(--accent);
    page-break-before: always;
}

h2 {
    font-size: 15pt;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: -0.01em;
    margin: 1.5em 0 0.55em 0;
    padding-bottom: 0.25em;
    border-bottom: 1px solid var(--rule);
    page-break-after: avoid;
}

h3 {
    font-size: 12pt;
    font-weight: 600;
    color: var(--ink-2);
    margin: 1.2em 0 0.4em 0;
    page-break-after: avoid;
}

h4 {
    font-size: 10.8pt;
    font-weight: 600;
    color: var(--ink-2);
    margin: 1em 0 0.3em 0;
    page-break-after: avoid;
}

p { margin: 0 0 0.7em 0; }
strong { color: var(--ink); font-weight: 600; }
em { color: var(--ink-2); }

a, a:visited {
    color: var(--link);
    text-decoration: none;
    border-bottom: 1px solid var(--link);
}

ul, ol {
    margin: 0 0 0.8em 1.4em;
    padding: 0;
}
li { margin: 0.22em 0; }

blockquote {
    margin: 0.7em 0;
    padding: 0.55em 0.95em;
    border-left: 3px solid var(--accent);
    background: var(--bg-soft);
    color: var(--ink-2);
    font-style: normal;
    border-radius: 0 4px 4px 0;
}
blockquote p { margin: 0.15em 0; }

code {
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-size: 0.86em;
    background: var(--code-bg);
    padding: 0.08em 0.32em;
    border-radius: 3px;
    color: var(--ink);
}

pre {
    background: var(--code-bg);
    border: 1px solid var(--rule);
    border-radius: 6px;
    padding: 11px 14px;
    overflow-x: auto;
    margin: 0.75em 0;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    padding: 0;
    font-size: 8.8pt;
    line-height: 1.55;
    color: var(--ink-2);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.75em 0;
    font-size: 9.4pt;
    page-break-inside: avoid;
}

th, td {
    border-bottom: 1px solid var(--rule);
    padding: 7px 10px;
    text-align: left;
    vertical-align: top;
}

th {
    background: var(--bg-soft);
    font-weight: 600;
    color: var(--ink);
    border-bottom: 1.5px solid var(--ink);
    font-size: 8.8pt;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

td code, th code { font-size: 0.92em; }

hr {
    border: none;
    border-top: 1px solid var(--rule);
    margin: 1.5em 0;
}
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MADS — Codebase Tour</title>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
"""


def render() -> int:
    if not SRC.exists():
        print(f"missing: {SRC}", file=sys.stderr)
        return 2

    md_text = SRC.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )
    html_doc = HTML_TEMPLATE.format(css=CSS, body=html_body)
    HTML_OUT.write_text(html_doc, encoding="utf-8")
    print(f"-> {HTML_OUT.relative_to(ROOT)}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(HTML_OUT.as_uri(), wait_until="networkidle")
        page.wait_for_timeout(900)
        page.pdf(
            path=str(OUT),
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            display_header_footer=True,
            header_template="<span></span>",
            footer_template=(
                '<div style="width:100%;font-family:Inter,sans-serif;'
                'font-size:8.5pt;color:#888;padding:0 16mm;display:flex;'
                'justify-content:space-between;">'
                '<span>MADS — Codebase Tour</span>'
                '<span class="pageNumber"></span> / <span class="totalPages"></span>'
                '</div>'
            ),
        )
        browser.close()

    print(f"-> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(render())
