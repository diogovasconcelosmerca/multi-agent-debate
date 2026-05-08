"""
MADS Design System v3

Palette: Orange (#E8733A) + Charcoal (#111113).
Effects: Glass-morphism, fade-in animations, hover micro-interactions.
Typography: Inter. No emojis.
"""

import base64

import streamlit as st


def _html(markup: str) -> None:
    """
    Emit raw HTML, bypassing the Markdown processor entirely.

    `st.markdown(..., unsafe_allow_html=True)` first runs the string
    through a Markdown renderer, which can mangle deeply-indented HTML
    (treating it as <code>). `st.html` (added in Streamlit 1.33) is the
    dedicated raw-HTML API; we fall back to markdown for older runtimes.
    """
    if hasattr(st, "html"):
        st.html(markup)
    else:
        st.markdown(markup, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
C = {
    "bg_app":       "#0F0F11",
    "bg_surface":   "#17171A",
    "bg_elevated":  "#1F1F23",
    "bg_hover":     "#27272B",
    "bg_input":     "#131316",
    "bg_glass":     "rgba(23, 23, 26, 0.72)",
    "accent":       "#E8733A",
    "accent_hover": "#F08044",
    "accent_muted": "#E8733A20",
    "agent_a":      "#E8733A",
    "agent_b":      "#8E8E9A",
    "agent_c":      "#D4A054",
    "success":      "#4DBB7A",
    "warning":      "#D4A054",
    "error":        "#D45454",
    "text_1":       "#EEEEF1",
    "text_2":       "#A0A0A8",
    "text_3":       "#636368",
    "text_4":       "#3F3F44",
    "border":       "#26262A",
    "border_light": "#33333A",
}

# ---------------------------------------------------------------------------
# Logo
# ---------------------------------------------------------------------------
_LOGO_SVG_RAW = '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><rect width="32" height="32" rx="8" fill="#E8733A"/><path d="M7 22V10.5L11.5 18.5L16 10.5L20.5 18.5L25 10.5V22" stroke="#111113" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'
_LOGO_SVG_48 = '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48"><rect width="48" height="48" rx="12" fill="#E8733A"/><path d="M10 34V15L16.5 28L23 15L29.5 28L38 15V34" stroke="#111113" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>'


def _b64(svg: str) -> str:
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"


def logo_img(size: int = 32) -> str:
    uri = _b64(_LOGO_SVG_RAW if size <= 32 else _LOGO_SVG_48)
    return f'<img src="{uri}" width="{size}" height="{size}" style="display:block;" />'


def favicon_uri() -> str:
    return _b64(_LOGO_SVG_RAW)


# ---------------------------------------------------------------------------
# CSS injection
# ---------------------------------------------------------------------------
def inject_premium_css():
    st.markdown(_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

def page_header(title: str, subtitle: str = "", eyebrow: str = ""):
    eb = f'<div class="m-eyebrow">{eyebrow}</div>' if eyebrow else ""
    sub = f'<p class="m-page-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="m-page-header">{eb}<h1 class="m-page-title">{title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )


def section_header(title: str, subtitle: str = ""):
    sub = f'<span class="m-section-sub"> — {subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div class="m-section"><h2 class="m-section-title">{title}{sub}</h2></div>',
        unsafe_allow_html=True,
    )


def sidebar_brand():
    uri = _b64(_LOGO_SVG_RAW)
    html = (
        f'<div class="m-sb-brand">'
        f'<img src="{uri}" width="28" height="28" />'
        f'<div>'
        f'<div class="m-sb-brand-title">MADS</div>'
        f'<div class="m-sb-brand-sub">Multi-Agent Debate System</div>'
        f'</div>'
        f'</div>'
    )
    _html(html)


def top_brand():
    """Compact MADS logo + name strip for the top of every sub-page.

    Calling this once near the top of each page gives the user a
    persistent visual anchor — the same identity in the same place,
    no matter where they navigated from.
    """
    uri = _b64(_LOGO_SVG_RAW)
    html = (
        f'<a href="/" target="_self" class="m-top-brand">'
        f'<img src="{uri}" width="22" height="22" alt="MADS" />'
        f'<span class="m-top-brand-name">MADS</span>'
        f'<span class="m-top-brand-sub">Multi-Agent Debate System</span>'
        f'</a>'
    )
    _html(html)


def sidebar_label(text: str):
    """Tiny uppercase eyebrow used as a sidebar section divider."""
    st.markdown(
        f'<div class="m-sb-label">{text}</div>',
        unsafe_allow_html=True,
    )


def sidebar_status(connected: bool, label: str = ""):
    """Connection pill — green dot + 'Connected · <backend>' / red dot + 'Offline'."""
    if connected:
        cls, dot, txt = "m-status-ok", "&#9679;", f"Connected{' · ' + label if label else ''}"
    else:
        cls, dot, txt = "m-status-err", "&#9679;", f"Offline{' · ' + label if label else ''}"
    st.markdown(
        f'<div class="m-status-pill {cls}"><span class="m-status-dot">{dot}</span>{txt}</div>',
        unsafe_allow_html=True,
    )


def sidebar_hint(text: str):
    """Small grey hint text under the connection pill."""
    st.markdown(
        f'<div class="m-sb-hint">{text}</div>',
        unsafe_allow_html=True,
    )


def chat_message(agent_name: str, role: str, content: str, time_s: float | None = None, align: str = "left"):
    """Render a chat-bubble style message with fade-in animation.

    The HTML below is emitted at column 0 deliberately — Streamlit's
    Markdown processor treats 4-space-indented blocks as <code>, which
    would render the bubble's HTML as raw text.
    """
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"], "You": C["text_2"]}
    color = color_map.get(agent_name, C["accent"])
    initial = agent_name[0] if agent_name else "?"
    time_html = f'<span class="m-chat-time">{time_s:.1f}s</span>' if time_s is not None else ""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    align_cls = "m-chat-right" if align == "right" else ""

    html = (
        f'<div class="m-chat-msg m-fadein {align_cls}">'
        f'<div class="m-chat-avatar" style="background:{color}15;color:{color};border:1px solid {color}25;">{initial}</div>'
        f'<div class="m-chat-bubble">'
        f'<div class="m-chat-meta">'
        f'<span class="m-chat-name" style="color:{color};">{agent_name}</span>'
        f'<span class="m-chat-role">{role}</span>'
        f'{time_html}'
        f'</div>'
        f'<div class="m-chat-text">{safe}</div>'
        f'</div>'
        f'</div>'
    )
    _html(html)


def agent_message(agent_name: str, role: str, content: str, time_s: float | None = None):
    """Legacy card-style message for expanders."""
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"]}
    color = color_map.get(agent_name, C["accent"])
    initial = agent_name[-1] if agent_name else "?"
    time_html = f'<span class="m-agent-time">{time_s:.1f}s</span>' if time_s is not None else ""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    html = (
        f'<div class="m-agent m-fadein" style="border-left-color:{color};">'
        f'<div class="m-agent-head">'
        f'<div class="m-agent-avatar" style="background:{color}18;color:{color};">{initial}</div>'
        f'<div class="m-agent-meta">'
        f'<span class="m-agent-name" style="color:{color};">{agent_name}</span>'
        f'<span class="m-agent-role">{role}</span>'
        f'</div>'
        f'{time_html}'
        f'</div>'
        f'<div class="m-agent-body">{safe}</div>'
        f'</div>'
    )
    _html(html)


def typing_indicator(agent_name: str, action: str = "is thinking"):
    """Show a pulsing typing indicator."""
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"]}
    color = color_map.get(agent_name, C["accent"])
    html = (
        f'<div class="m-typing">'
        f'<div class="m-typing-dots">'
        f'<span style="background:{color};"></span>'
        f'<span style="background:{color};"></span>'
        f'<span style="background:{color};"></span>'
        f'</div>'
        f'<span class="m-typing-text" style="color:{color};">{agent_name} {action}...</span>'
        f'</div>'
    )
    _html(html)


def step_indicator(steps: list[str], active: int = -1, completed: int = -1):
    """Render a horizontal step progress bar."""
    items = ""
    for i, label in enumerate(steps):
        if i < completed:
            cls = "m-step-done"
        elif i == active:
            cls = "m-step-active"
        else:
            cls = "m-step-pending"
        items += f'<div class="m-step {cls}"><div class="m-step-dot"></div><div class="m-step-label">{label}</div></div>'
        if i < len(steps) - 1:
            line_cls = "m-step-line-done" if i < completed else ""
            items += f'<div class="m-step-line {line_cls}"></div>'

    st.markdown(f'<div class="m-stepper">{items}</div>', unsafe_allow_html=True)


def metric_card(label: str, value: str, delta: str = "", color: str = ""):
    d_html = ""
    if delta:
        dc = C["success"] if delta.startswith("+") else C["error"] if delta.startswith("-") else C["text_3"]
        d_html = f'<div class="m-metric-delta" style="color:{dc};">{delta}</div>'
    val_color = color or C["text_1"]
    html = (
        f'<div class="m-metric m-glass">'
        f'<div class="m-metric-label">{label}</div>'
        f'<div class="m-metric-value" style="color:{val_color};">{value}</div>'
        f'{d_html}'
        f'</div>'
    )
    _html(html)


def winner_banner(winner: str):
    configs = {
        "debate":   ("m-banner-win",  "Multi-agent debate produced a higher-rated response"),
        "baseline": ("m-banner-base", "Single-agent baseline was rated higher"),
        "tie":      ("m-banner-tie",  "Both approaches scored equally"),
    }
    cls, text = configs.get(winner, configs["tie"])
    st.markdown(f'<div class="m-banner {cls} m-fadein"><span>{text}</span></div>', unsafe_allow_html=True)


def info_banner(text: str, variant: str = "base"):
    """Inline notice used on the home page when no backend is connected."""
    cls = {
        "base":  "m-banner-base",
        "warn":  "m-banner-warn",
        "ok":    "m-banner-win",
    }.get(variant, "m-banner-base")
    st.markdown(
        f'<div class="m-banner {cls}"><span>{text}</span></div>',
        unsafe_allow_html=True,
    )


def radar_chart_html(baseline_scores: dict, debate_scores: dict) -> str:
    """Generate an SVG radar chart comparing baseline vs debate scores."""
    import math
    dims = list(baseline_scores.keys())
    n = len(dims)
    # Wide viewBox with horizontal padding so long labels ("Reasoning
    # Depth", "Completeness") render without clipping when the SVG is
    # scaled to a narrow column.
    vb_w, vb_h = 440, 300
    cx, cy, r = vb_w / 2, 130, 88
    angles = [math.pi / 2 + 2 * math.pi * i / n for i in range(n)]

    def points(scores, radius):
        pts = []
        for i, dim in enumerate(dims):
            val = scores[dim] / 5.0
            x = cx + radius * val * math.cos(angles[i])
            y = cy - radius * val * math.sin(angles[i])
            pts.append(f"{x:.1f},{y:.1f}")
        return " ".join(pts)

    # Grid rings
    grid = ""
    for level in [1, 2, 3, 4, 5]:
        ring_pts = []
        for i in range(n):
            x = cx + r * (level / 5) * math.cos(angles[i])
            y = cy - r * (level / 5) * math.sin(angles[i])
            ring_pts.append(f"{x:.1f},{y:.1f}")
        grid += f'<polygon points="{" ".join(ring_pts)}" fill="none" stroke="{C["border"]}" stroke-width="0.6"/>'

    # Axis lines
    axes = ""
    for i in range(n):
        x = cx + r * math.cos(angles[i])
        y = cy - r * math.sin(angles[i])
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{C["border"]}" stroke-width="0.6"/>'

    # Labels — use short forms so they fit narrow columns without clipping
    short = {
        "coherence": "Coherence",
        "reasoning_depth": "Reasoning",
        "completeness": "Completeness",
        "clarity": "Clarity",
    }
    labels = ""
    for i, dim in enumerate(dims):
        label = short.get(dim, dim.replace("_", " ").title())
        lx = cx + (r + 20) * math.cos(angles[i])
        ly = cy - (r + 20) * math.sin(angles[i])
        anchor = "middle"
        if lx < cx - 12:
            anchor = "end"
        elif lx > cx + 12:
            anchor = "start"
        labels += (
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
            f'dominant-baseline="middle" fill="{C["text_2"]}" font-size="10.5" '
            f'font-family="Inter" font-weight="500">{label}</text>'
        )

    b_pts = points(baseline_scores, r)
    d_pts = points(debate_scores, r)

    legend_y = vb_h - 22
    legend_x_base = cx - 70

    return f'''
    <svg viewBox="0 0 {vb_w} {vb_h}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:440px;display:block;margin:0 auto;" overflow="visible">
        {grid}{axes}
        <polygon points="{b_pts}" fill="{C["accent"]}1F" stroke="{C["accent"]}" stroke-width="1.6" opacity="0.85"/>
        <polygon points="{d_pts}" fill="{C["agent_c"]}1F" stroke="{C["agent_c"]}" stroke-width="1.6" opacity="0.85"/>
        {labels}
        <g transform="translate({legend_x_base}, {legend_y})">
            <rect width="9" height="9" rx="2" fill="{C["accent"]}" opacity="0.85"/>
            <text x="14" y="9" fill="{C["text_2"]}" font-size="10" font-family="Inter">Baseline</text>
            <rect x="76" width="9" height="9" rx="2" fill="{C["agent_c"]}" opacity="0.85"/>
            <text x="90" y="9" fill="{C["text_2"]}" font-size="10" font-family="Inter">Debate</text>
        </g>
    </svg>
    '''


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;450;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* === Base === */
.stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background:
        radial-gradient(1200px 600px at 80% -10%, {C["accent"]}10, transparent 60%),
        radial-gradient(900px 500px at -10% 110%, {C["agent_c"]}0A, transparent 60%),
        {C["bg_app"]};
    color: {C["text_1"]};
}}
/* Streamlit chrome — surgical hides only.

   The toolbar (header right side) contains BOTH the deploy button AND
   the sidebar-expand button. Hiding the whole toolbar — as an earlier
   version of this stylesheet did — also hid the only way to reopen
   the sidebar once collapsed. We now hide the individual leaves we
   don't want and leave everything else rendered. */
footer {{ display: none !important; }}
[data-testid="stMainMenu"] {{ display: none !important; }}
[data-testid="stAppDeployButton"] {{ display: none !important; }}
.stDeployButton {{ display: none !important; }}

/* Keep the header rendered so the sidebar-collapse and sidebar-expand
   buttons keep their layout slot. Just make the header transparent so
   it visually disappears against the page gradient. */
header[data-testid="stHeader"] {{
    background: transparent !important;
    box-shadow: none !important;
}}

/* Belt-and-braces: force the sidebar controls visible. The expand
   button (Streamlit 1.33+) has a dedicated testid; the collapse
   button lives inside the sidebar header. */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stSidebarHeader"] button {{
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}}
section[data-testid="stSidebar"] {{
    visibility: visible !important;
}}

code, kbd, pre {{
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, monospace;
    font-size: 12px;
}}

/* === Animations === */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulse {{
    0%, 80%, 100% {{ opacity: 0.3; transform: scale(0.8); }}
    40% {{ opacity: 1; transform: scale(1); }}
}}
@keyframes pulseDot {{
    0% {{ box-shadow: 0 0 0 0 rgba(77,187,122,0.55); }}
    70% {{ box-shadow: 0 0 0 6px rgba(77,187,122,0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(77,187,122,0); }}
}}
@keyframes slideIn {{
    from {{ opacity: 0; transform: translateX(-8px); }}
    to {{ opacity: 1; transform: translateX(0); }}
}}
.m-fadein {{
    animation: fadeInUp 0.35s ease-out both;
}}

/* === Glass-morphism === */
.m-glass {{
    background: {C["bg_glass"]};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.04);
}}

/* === Sidebar === */
section[data-testid="stSidebar"] {{
    background: {C["bg_surface"]};
    border-right: 1px solid {C["border"]};
}}
section[data-testid="stSidebar"] label {{
    font-size: 10px !important; font-weight: 600 !important;
    color: {C["text_3"]} !important; text-transform: uppercase;
    letter-spacing: 0.08em;
}}
section[data-testid="stSidebar"] .stSelectbox > div > div,
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background: {C["bg_input"]}; border: 1px solid {C["border"]};
    border-radius: 8px; color: {C["text_1"]}; font-size: 13px;
}}
section[data-testid="stSidebar"] .stSelectbox > div > div:hover,
section[data-testid="stSidebar"] .stTextInput > div > div > input:hover {{
    border-color: {C["border_light"]};
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {{
    border-color: {C["accent"]}; box-shadow: 0 0 0 2px {C["accent"]}22;
}}
/* Backend selector — vertical stacked buttons, no labels truncated */
section[data-testid="stSidebar"] .stRadio > div {{
    flex-direction: column !important;
    gap: 4px !important;
    background: transparent;
    border: 0;
    padding: 0;
}}
section[data-testid="stSidebar"] .stRadio > div > label {{
    width: 100%;
    display: flex !important; align-items: center !important;
    padding: 9px 12px;
    background: {C["bg_input"]};
    border: 1px solid {C["border"]};
    border-radius: 9px;
    cursor: pointer;
    font-size: 12.5px !important; font-weight: 500 !important;
    color: {C["text_2"]} !important; text-transform: none !important;
    letter-spacing: 0 !important; transition: all 0.15s;
    white-space: nowrap;
}}
section[data-testid="stSidebar"] .stRadio > div > label:hover {{
    border-color: {C["border_light"]};
    color: {C["text_1"]} !important;
    background: {C["bg_elevated"]};
}}
section[data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {{
    background: {C["accent"]}1A;
    border-color: {C["accent"]};
    color: {C["accent"]} !important;
    box-shadow: 0 0 0 1px {C["accent"]}33 inset;
}}
/* Hide the native radio dot — we use the whole row as the button */
section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {{
    display: none;
}}

/* Hide Streamlit's auto-discovered sidebar nav (built from filenames).
   We render our own anchor-based `.m-nav` below the brand so the layout
   order is: brand → links → backend → … */
section[data-testid="stSidebar"] [data-testid="stSidebarNav"],
section[data-testid="stSidebar"] [data-testid="stSidebarNavSeparator"] {{
    display: none !important;
}}

/* Custom anchor-based sidebar nav. Plain <a> instead of st.page_link
   so the entry-script name (Home.py / app.py / streamlit_app.py)
   doesn't matter; navigation is done via Streamlit's URL router. */
section[data-testid="stSidebar"] .m-nav {{
    display: flex; flex-direction: column; gap: 2px;
    margin: 4px 0 14px 0;
}}
section[data-testid="stSidebar"] .m-nav .m-nav-item,
section[data-testid="stSidebar"] .m-nav .m-nav-item:visited {{
    display: block;
    padding: 8px 12px;
    border-radius: 8px;
    border-left: 2px solid transparent;
    font-size: 13px; font-weight: 500;
    color: {C["text_2"]};
    text-decoration: none !important;
    transition: background 0.15s, color 0.15s, border-color 0.15s;
}}
section[data-testid="stSidebar"] .m-nav .m-nav-item:hover {{
    background: {C["bg_hover"]};
    color: {C["text_1"]};
    text-decoration: none !important;
}}
section[data-testid="stSidebar"] .m-nav .m-nav-active {{
    background: {C["accent"]}14 !important;
    color: {C["accent"]} !important;
    border-left-color: {C["accent"]} !important;
}}

/* Sidebar custom blocks */
.m-sb-brand {{
    display: flex; align-items: center; gap: 10px;
    padding: 4px 0 14px 0;
    border-bottom: 1px solid {C["border"]};
    margin-bottom: 14px;
}}
.m-sb-brand-title {{
    font-size: 15px; font-weight: 700; color: {C["text_1"]};
    letter-spacing: -0.5px; line-height: 1.2;
}}
.m-sb-brand-sub {{
    font-size: 10px; color: {C["text_3"]}; line-height: 1.3;
}}
.m-sb-label {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; color: {C["text_3"]};
    margin: 14px 0 6px 0;
}}
.m-sb-tagline {{
    font-size: 10.5px; color: {C["text_3"]};
    margin: 6px 2px 0 2px; line-height: 1.4;
    letter-spacing: 0.01em;
}}
.m-sb-hint {{
    font-size: 10.5px; color: {C["text_3"]};
    line-height: 1.5; margin-top: 4px;
}}
.m-sb-hint code {{
    background: {C["bg_input"]}; padding: 1px 4px; border-radius: 3px;
    font-size: 10.5px; color: {C["text_2"]};
}}
.m-sb-footer {{
    margin-top: 18px; padding-top: 12px;
    border-top: 1px solid {C["border"]};
    font-size: 10px; color: {C["text_4"]};
    text-align: center; letter-spacing: 0.04em;
}}

/* Status pill */
.m-status-pill {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 500;
    padding: 4px 10px; border-radius: 999px;
    margin-bottom: 6px;
}}
.m-status-dot {{ font-size: 8px; line-height: 1; }}
.m-status-ok {{
    background: {C["success"]}14; color: {C["success"]};
    border: 1px solid {C["success"]}30;
}}
.m-status-ok .m-status-dot {{
    color: {C["success"]};
    border-radius: 999px;
    animation: pulseDot 2.2s infinite;
}}
.m-status-err {{
    background: {C["error"]}14; color: {C["error"]};
    border: 1px solid {C["error"]}30;
}}

/* === Layout === */
.main .block-container {{ max-width: 1100px; padding: 2rem 2.5rem 3rem 2.5rem; }}

/* === Page Header === */
.m-page-header {{ margin-bottom: 1.75rem; }}
.m-eyebrow {{
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.16em; color: {C["accent"]};
    margin-bottom: 6px;
}}
.m-page-title {{
    font-size: 1.6rem; font-weight: 700; letter-spacing: -0.03em;
    color: {C["text_1"]}; margin: 0; line-height: 1.25;
}}
.m-page-sub {{
    font-size: 0.88rem; color: {C["text_3"]}; margin: 0.35rem 0 0 0; line-height: 1.55;
    max-width: 720px;
}}

/* === Section === */
.m-section {{
    margin: 1.85rem 0 0.95rem 0; padding-bottom: 0.5rem;
    border-bottom: 1px solid {C["border"]};
    position: relative;
}}
.m-section::after {{
    content: ""; position: absolute; left: 0; bottom: -1px;
    width: 36px; height: 2px;
    background: {C["accent"]}; border-radius: 2px;
}}
.m-section-title {{
    font-size: 0.98rem; font-weight: 600; color: {C["text_1"]};
    letter-spacing: -0.01em; margin: 0; display: inline;
}}
.m-section-sub {{ font-size: 0.78rem; color: {C["text_3"]}; font-weight: 400; }}

/* === Chat Messages === */
.m-chat-msg {{
    display: flex; gap: 10px; padding: 8px 0;
    animation: fadeInUp 0.35s ease-out both;
}}
.m-chat-right {{ flex-direction: row-reverse; }}
.m-chat-avatar {{
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 12px; flex-shrink: 0;
    margin-top: 2px;
}}
.m-chat-bubble {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 14px; padding: 11px 15px;
    max-width: 85%;
    transition: border-color 0.15s, transform 0.15s;
}}
.m-chat-bubble:hover {{ border-color: {C["border_light"]}; }}
.m-chat-meta {{
    display: flex; align-items: center; gap: 6px; margin-bottom: 4px;
}}
.m-chat-name {{ font-weight: 600; font-size: 12px; }}
.m-chat-role {{
    font-size: 10px; color: {C["text_3"]};
    background: {C["bg_elevated"]};
    padding: 1px 6px; border-radius: 4px;
}}
.m-chat-time {{
    font-size: 10px; color: {C["text_4"]}; margin-left: auto;
    font-variant-numeric: tabular-nums;
}}
.m-chat-text {{
    font-size: 13.5px; line-height: 1.7; color: {C["text_2"]};
}}

/* === Typing Indicator === */
.m-typing {{
    display: flex; align-items: center; gap: 8px; padding: 8px 0;
    animation: fadeInUp 0.2s ease-out;
}}
.m-typing-dots {{ display: flex; gap: 3px; }}
.m-typing-dots span {{
    width: 6px; height: 6px; border-radius: 50%; display: block;
    animation: pulse 1.2s infinite;
}}
.m-typing-dots span:nth-child(2) {{ animation-delay: 0.15s; }}
.m-typing-dots span:nth-child(3) {{ animation-delay: 0.3s; }}
.m-typing-text {{ font-size: 12px; font-weight: 500; }}

/* === Step Indicator === */
.m-stepper {{
    display: flex; align-items: center; justify-content: center;
    gap: 0; padding: 16px 0; margin: 8px 0;
}}
.m-step {{
    display: flex; flex-direction: column; align-items: center; gap: 5px;
    min-width: 60px;
}}
.m-step-dot {{
    width: 10px; height: 10px; border-radius: 50%;
    background: {C["border_light"]}; transition: all 0.3s;
}}
.m-step-label {{
    font-size: 9px; font-weight: 500; color: {C["text_4"]};
    text-transform: uppercase; letter-spacing: 0.05em;
    transition: color 0.3s;
}}
.m-step-line {{
    width: 40px; height: 2px; background: {C["border"]};
    margin: 0 2px; margin-bottom: 18px; transition: background 0.3s;
}}
.m-step-done .m-step-dot {{ background: {C["success"]}; box-shadow: 0 0 6px {C["success"]}40; }}
.m-step-done .m-step-label {{ color: {C["success"]}; }}
.m-step-line-done {{ background: {C["success"]}; }}
.m-step-active .m-step-dot {{
    background: {C["accent"]}; box-shadow: 0 0 8px {C["accent"]}50;
    animation: pulse 1.5s infinite;
}}
.m-step-active .m-step-label {{ color: {C["accent"]}; }}

/* === Agent Card (for expanders) === */
.m-agent {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-left: 3px solid; border-radius: 10px;
    padding: 14px 16px; margin: 6px 0;
    transition: transform 0.15s, border-color 0.15s;
}}
.m-agent:hover {{ transform: translateY(-1px); }}
.m-agent-head {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
.m-agent-avatar {{
    width: 28px; height: 28px; border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 11px; flex-shrink: 0;
}}
.m-agent-meta {{ flex: 1; }}
.m-agent-name {{ font-weight: 600; font-size: 12px; display: block; line-height: 1.2; }}
.m-agent-role {{ font-size: 10px; color: {C["text_3"]}; }}
.m-agent-time {{
    font-size: 10px; color: {C["text_3"]}; background: {C["bg_elevated"]};
    padding: 2px 7px; border-radius: 4px; font-variant-numeric: tabular-nums;
}}
.m-agent-body {{ font-size: 13px; line-height: 1.7; color: {C["text_2"]}; }}

/* === Metric === */
.m-metric {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 12px; padding: 14px 12px; text-align: center;
    transition: transform 0.15s, border-color 0.15s;
}}
.m-metric:hover {{ transform: translateY(-1px); border-color: {C["border_light"]}; }}
.m-metric-label {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: {C["text_3"]}; margin-bottom: 5px;
}}
.m-metric-value {{
    font-size: 22px; font-weight: 700; letter-spacing: -0.02em;
    line-height: 1.2; font-variant-numeric: tabular-nums;
}}
.m-metric-delta {{ font-size: 11px; font-weight: 500; margin-top: 2px; }}

/* === Banner === */
.m-banner {{
    border-radius: 10px; padding: 12px 16px;
    display: flex; align-items: center; gap: 8px;
    font-size: 13px; font-weight: 500; margin: 12px 0;
}}
.m-banner-win {{ background: {C["success"]}0C; border: 1px solid {C["success"]}30; color: {C["success"]}; }}
.m-banner-base {{ background: {C["accent"]}0C; border: 1px solid {C["accent"]}30; color: {C["accent"]}; }}
.m-banner-tie {{ background: {C["text_3"]}0C; border: 1px solid {C["text_3"]}30; color: {C["text_2"]}; }}
.m-banner-warn {{ background: {C["warning"]}0E; border: 1px solid {C["warning"]}30; color: {C["warning"]}; }}

/* === Score Table === */
.m-score-table {{
    width: 100%; border-collapse: separate; border-spacing: 0;
    border: 1px solid {C["border"]}; border-radius: 10px; overflow: hidden;
}}
.m-score-table th {{
    background: {C["bg_elevated"]}; padding: 8px 14px;
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: {C["text_3"]}; text-align: left;
}}
.m-score-table td {{
    padding: 8px 14px; font-size: 13px; color: {C["text_2"]};
    border-top: 1px solid {C["border"]}; background: {C["bg_surface"]};
    transition: background 0.1s;
    font-variant-numeric: tabular-nums;
}}
.m-score-table tr:hover td {{ background: {C["bg_elevated"]}; }}
.m-pos {{ color: {C["success"]}; font-weight: 600; }}
.m-neg {{ color: {C["error"]}; font-weight: 600; }}
.m-neu {{ color: {C["text_3"]}; }}

/* === Hero === */
.m-hero {{
    padding: 3.2rem 1rem 1.4rem 1rem; text-align: center;
    position: relative;
}}
.m-hero img {{ margin: 0 auto; }}
.m-hero-eyebrow {{
    margin-top: 18px;
    font-size: 11px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.22em;
    color: {C["text_3"]};
}}
.m-hero-title {{
    font-size: 2.6rem; font-weight: 700; letter-spacing: -0.04em;
    color: {C["text_1"]}; margin: 0.5rem 0 0 0; line-height: 1.08;
}}
.m-hero-accent {{
    color: {C["accent"]};
    background: linear-gradient(135deg, {C["accent"]} 0%, {C["agent_c"]} 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-style: italic;
    font-weight: 700;
}}
.m-hero-sub {{
    font-size: 0.98rem; color: {C["text_3"]}; max-width: 580px;
    margin: 0.85rem auto 0 auto; line-height: 1.65;
}}
.m-hero-meta {{
    display: inline-flex; gap: 8px;
    margin-top: 18px; flex-wrap: wrap; justify-content: center;
}}
.m-hero-meta code {{
    background: transparent; padding: 0; color: inherit;
    font-size: 11px;
}}
.m-tag {{
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 500;
    padding: 4px 10px; border-radius: 999px;
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    color: {C["text_2"]};
}}
.m-tag-dot {{
    width: 6px; height: 6px; border-radius: 50%; display: inline-block;
}}

/* === Features (clickable cards) === */
.m-features {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 2rem 0 0.6rem 0; }}
.m-feat {{
    display: block;
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 14px; padding: 22px 20px 18px 20px;
    transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
    position: relative; overflow: hidden;
    text-decoration: none;
    color: inherit;
    cursor: pointer;
}}
.m-feat::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0;
    height: 1px; background: linear-gradient(90deg, transparent, {C["accent"]}55, transparent);
    opacity: 0; transition: opacity 0.2s;
}}
.m-feat:hover {{
    border-color: {C["accent"]}40; transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0,0,0,0.32);
    text-decoration: none;
}}
.m-feat:hover::before {{ opacity: 1; }}
.m-feat:hover .m-feat-cta {{ color: {C["accent"]}; transform: translateX(2px); }}
/* Streamlit's <a> rule beats a single-class selector even with
   !important. Stack class selectors to win on specificity. */
.m-features a.m-feat,
.m-features a.m-feat:hover,
.m-features a.m-feat:visited,
.m-features a.m-feat *,
.m-features a.m-feat:hover * {{
    text-decoration: none !important;
    text-decoration-line: none !important;
    border-bottom: none !important;
}}
.m-feat-bar {{ width: 26px; height: 3px; border-radius: 2px; margin-bottom: 14px; }}
.m-feat-title {{
    font-size: 13.5px; font-weight: 600; color: {C["text_1"]};
    margin-bottom: 5px; text-decoration: none;
}}
.m-feat-desc {{
    font-size: 12px; color: {C["text_3"]}; line-height: 1.6;
    text-decoration: none;
}}
.m-feat-cta {{
    margin-top: 12px; font-size: 11px; font-weight: 600;
    color: {C["text_3"]}; letter-spacing: 0.02em;
    transition: color 0.15s, transform 0.15s;
    display: inline-block;
}}

/* === Top-brand strip (persistent header on sub-pages) === */
.m-top-brand {{
    display: inline-flex; align-items: center; gap: 8px;
    padding: 4px 10px 4px 4px;
    margin: -0.5rem 0 1.2rem 0;
    border-radius: 999px;
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    text-decoration: none;
    transition: border-color 0.15s, transform 0.15s;
}}
.m-top-brand:hover {{
    border-color: {C["accent"]}50; transform: translateY(-1px);
    text-decoration: none;
}}
.m-top-brand img {{ display: block; border-radius: 6px; }}
.m-top-brand-name {{
    font-size: 12px; font-weight: 700; color: {C["text_1"]};
    letter-spacing: -0.01em;
}}
.m-top-brand-sub {{
    font-size: 10.5px; color: {C["text_3"]};
    border-left: 1px solid {C["border_light"]};
    padding-left: 8px; margin-left: 2px;
}}

@media (max-width: 720px) {{
    .m-features {{ grid-template-columns: 1fr; }}
    .m-hero-title {{ font-size: 1.85rem; }}
}}

/* === Flow === */
.m-flow {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 14px; padding: 22px 24px; margin: 1.4rem 0;
}}
.m-flow-label {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.12em; color: {C["text_4"]}; margin-bottom: 14px;
}}
.m-flow-step {{ display: flex; align-items: center; gap: 12px; padding: 6px 0; }}
.m-flow-num {{
    width: 28px; height: 28px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 11px; flex-shrink: 0;
}}
.m-flow-text {{ font-size: 13px; color: {C["text_2"]}; }}
.m-flow-text strong {{ color: {C["text_1"]}; font-weight: 600; }}
.m-flow-line {{ width: 1px; height: 12px; margin-left: 13px; background: {C["border_light"]}; }}

/* === Comparison === */
.m-comp-head {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 10px; padding: 10px 14px;
    display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}}
.m-comp-icon {{
    width: 24px; height: 24px; border-radius: 6px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 10px;
}}
.m-comp-label {{ font-size: 13px; font-weight: 600; color: {C["text_1"]}; }}
.m-comp-sub {{ font-size: 11px; color: {C["text_3"]}; margin-left: auto; }}

/* === Result Row === */
.m-result-row {{
    display: flex; align-items: center; gap: 10px;
    padding: 8px 12px; background: {C["bg_surface"]};
    border-radius: 8px; margin: 4px 0; border: 1px solid {C["border"]};
    font-size: 13px; transition: border-color 0.15s;
}}
.m-result-row:hover {{ border-color: {C["border_light"]}; }}
.m-rr-q {{ flex: 1; color: {C["text_2"]}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.m-rr-badge {{ font-size: 10px; font-weight: 500; padding: 1px 7px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.04em; }}
.m-rr-time {{ font-size: 10px; color: {C["text_3"]}; font-variant-numeric: tabular-nums; }}

/* === Empty === */
.m-empty {{
    text-align: center; padding: 48px 16px;
    background: {C["bg_surface"]}; border: 1px dashed {C["border_light"]}; border-radius: 14px;
}}
.m-empty-title {{ font-size: 14px; font-weight: 500; color: {C["text_1"]}; margin-bottom: 4px; }}
.m-empty-sub {{ font-size: 13px; color: {C["text_3"]}; }}

/* === Inputs === */
.stTextArea textarea {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 12px; font-size: 14px; font-family: 'Inter', sans-serif;
    padding: 13px 15px; color: {C["text_1"]}; transition: border-color 0.15s;
}}
.stTextArea textarea:focus {{
    border-color: {C["accent"]}; box-shadow: 0 0 0 2px {C["accent"]}1F;
    outline: none;
}}
.stTextArea textarea::placeholder {{ color: {C["text_4"]}; }}

/* === Buttons === */
div.stButton > button[kind="primary"] {{
    background: {C["accent"]}; color: #fff; border: none;
    border-radius: 10px; font-weight: 600; font-size: 13px;
    padding: 9px 18px; transition: all 0.15s;
    box-shadow: 0 1px 0 rgba(255,255,255,0.06) inset;
}}
div.stButton > button[kind="primary"]:hover {{
    background: {C["accent_hover"]}; box-shadow: 0 4px 16px {C["accent"]}40;
    transform: translateY(-1px);
}}
div.stButton > button[kind="primary"]:active {{
    transform: translateY(0); box-shadow: 0 1px 4px {C["accent"]}40;
}}
div.stButton > button {{
    border-radius: 10px; border: 1px solid {C["border"]};
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
    background: {C["bg_surface"]};
    transition: all 0.15s;
}}
div.stButton > button:hover {{
    border-color: {C["accent"]}50; color: {C["text_1"]}; transform: translateY(-1px);
    background: {C["bg_elevated"]};
}}

/* === Expander === */
.streamlit-expanderHeader {{
    background: {C["bg_surface"]}; border-radius: 8px;
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
}}

/* === Status (st.status) === */
div[data-testid="stStatusWidget"] {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 10px;
}}

/* === Progress === */
.stProgress > div > div {{
    background: linear-gradient(90deg, {C["accent"]}, {C["agent_c"]});
    border-radius: 8px;
}}
.stProgress > div {{ background: {C["bg_input"]}; border-radius: 8px; }}

/* === Tabs === */
.stTabs [data-baseweb="tab-list"] {{
    gap: 0; border-bottom: 1px solid {C["border"]};
}}
.stTabs [data-baseweb="tab"] {{
    font-size: 13px; font-weight: 500; color: {C["text_3"]};
    padding: 8px 16px; transition: color 0.15s;
}}
.stTabs [aria-selected="true"] {{ color: {C["accent"]} !important; }}
.stTabs [data-baseweb="tab-highlight"] {{ background-color: {C["accent"]} !important; }}

/* === Scrollbar === */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {C["border"]}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {C["border_light"]}; }}

/* === Download === */
.stDownloadButton > button {{
    border-radius: 10px; border: 1px solid {C["border"]};
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
    background: {C["bg_surface"]};
}}
.stDownloadButton > button:hover {{ border-color: {C["accent"]}50; color: {C["text_1"]}; }}

/* === Dataframe === */
.stDataFrame {{ border-radius: 10px; overflow: hidden; }}
.stSlider [data-testid="stThumbValue"] {{ color: {C["accent"]}; }}

/* === Toast === */
div[data-testid="stToast"] {{
    background: {C["bg_elevated"]}; border: 1px solid {C["border_light"]};
    border-radius: 10px;
}}
</style>
"""
