"""
Build a print-quality PDF of docs/REPORTS.md.

Pipeline:
  1. Render the Markdown to HTML with python-markdown (tables + fenced code).
  2. Wrap in an Inter / JetBrains Mono print stylesheet.
  3. Use Playwright (headless Chromium) to print to PDF at A4.

Output: docs/MADS_Reports.pdf

Usage:
    python scripts/build_reports_pdf.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import markdown
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "REPORTS.md"
OUT = ROOT / "docs" / "MADS_Reports.pdf"
HTML_OUT = ROOT / "docs" / "MADS_Reports.html"   # kept as a side-artifact

# ---------------------------------------------------------------------------
# Print stylesheet — Inter for prose, JetBrains Mono for code, generous
# margins, soft page-break rules so headings don't strand at the foot of
# a page.
# ---------------------------------------------------------------------------
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

html { font-size: 10.8pt; }

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    color: var(--ink);
    line-height: 1.55;
    margin: 0;
    -webkit-font-smoothing: antialiased;
}

/* Cover header is the first H1 */
h1 {
    font-size: 24pt;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0 0 0.3em 0;
    line-height: 1.15;
    page-break-after: avoid;
}

h1:not(:first-of-type) {
    margin-top: 1.2em;
    padding-top: 0.6em;
    border-top: 2px solid var(--accent);
    page-break-before: always;
}

h2 {
    font-size: 16pt;
    font-weight: 600;
    color: var(--ink);
    letter-spacing: -0.01em;
    margin: 1.4em 0 0.5em 0;
    padding-bottom: 0.25em;
    border-bottom: 1px solid var(--rule);
    page-break-after: avoid;
}

h3 {
    font-size: 12.5pt;
    font-weight: 600;
    color: var(--ink-2);
    margin: 1.2em 0 0.4em 0;
    page-break-after: avoid;
}

h4 {
    font-size: 11pt;
    font-weight: 600;
    color: var(--ink-2);
    margin: 0.9em 0 0.25em 0;
    page-break-after: avoid;
}

p {
    margin: 0 0 0.65em 0;
}

strong { color: var(--ink); font-weight: 600; }
em { color: var(--ink-2); }

a, a:visited {
    color: var(--link);
    text-decoration: none;
    border-bottom: 1px solid var(--link);
}

ul, ol {
    margin: 0 0 0.7em 1.2em;
    padding: 0;
}
li { margin: 0.18em 0; }

blockquote {
    margin: 0.6em 0;
    padding: 0.5em 0.9em;
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
    padding: 10px 14px;
    overflow-x: auto;
    margin: 0.6em 0;
    page-break-inside: avoid;
}

pre code {
    background: transparent;
    padding: 0;
    font-size: 9pt;
    line-height: 1.5;
    color: var(--ink-2);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.7em 0;
    font-size: 9.6pt;
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
    font-size: 9pt;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

td code, th code { font-size: 0.92em; }

hr {
    border: none;
    border-top: 1px solid var(--rule);
    margin: 1.5em 0;
}

/* Page-break helpers used by the renderer. */
.page-break { page-break-after: always; }

/* Cover-meta block (rendered from the leading paragraph). */
.cover-meta {
    margin: 0 0 1.5em 0;
    padding: 12px 16px;
    background: var(--bg-soft);
    border: 1px solid var(--rule);
    border-radius: 6px;
    font-size: 9.5pt;
    color: var(--ink-2);
}
.cover-meta strong { color: var(--ink); }
"""

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>MADS — Engineering Reports</title>
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

    # Render to PDF with headless Chromium.
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(HTML_OUT.as_uri(), wait_until="networkidle")
        # Give web fonts an extra beat to land before printing.
        page.wait_for_timeout(800)
        page.pdf(
            path=str(OUT),
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "16mm", "right": "16mm"},
            display_header_footer=True,
            header_template="<span></span>",  # blank, but enables footer
            footer_template=(
                '<div style="width:100%;font-family:Inter,sans-serif;'
                'font-size:8.5pt;color:#888;padding:0 16mm;display:flex;'
                'justify-content:space-between;">'
                '<span>MADS — Engineering Reports</span>'
                '<span class="pageNumber"></span> / <span class="totalPages"></span>'
                '</div>'
            ),
        )
        browser.close()

    print(f"-> {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(render())
