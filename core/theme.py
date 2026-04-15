"""
MADS Design System v2

Palette: Orange (#E8733A) + Charcoal (#111113).
Effects: Glass-morphism, fade-in animations, hover micro-interactions.
Typography: Inter. No emojis.
"""

import base64
import streamlit as st

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
C = {
    "bg_app":       "#111113",
    "bg_surface":   "#1C1C1E",
    "bg_elevated":  "#232326",
    "bg_hover":     "#2A2A2E",
    "bg_input":     "#19191B",
    "bg_glass":     "rgba(28, 28, 30, 0.65)",
    "accent":       "#E8733A",
    "accent_hover": "#F08044",
    "accent_muted": "#E8733A20",
    "agent_a":      "#E8733A",
    "agent_b":      "#8E8E9A",
    "agent_c":      "#D4A054",
    "success":      "#5CB87A",
    "warning":      "#D4A054",
    "error":        "#D45454",
    "text_1":       "#E8E8EC",
    "text_2":       "#A0A0A8",
    "text_3":       "#636368",
    "text_4":       "#45454A",
    "border":       "#2A2A2E",
    "border_light": "#333338",
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

def page_header(title: str, subtitle: str = ""):
    sub = f'<p class="m-page-sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<div class="m-page-header"><h1 class="m-page-title">{title}</h1>{sub}</div>', unsafe_allow_html=True)


def section_header(title: str, subtitle: str = ""):
    sub = f'<span class="m-section-sub"> — {subtitle}</span>' if subtitle else ""
    st.markdown(f'<div class="m-section"><h2 class="m-section-title">{title}{sub}</h2></div>', unsafe_allow_html=True)


def sidebar_brand():
    uri = _b64(_LOGO_SVG_RAW)
    st.markdown(f'''
    <div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px 0;">
        <img src="{uri}" width="28" height="28" />
        <div>
            <div style="font-size:15px;font-weight:700;color:{C["text_1"]};letter-spacing:-0.5px;line-height:1.2;">MADS</div>
            <div style="font-size:10px;color:{C["text_3"]};line-height:1.3;">Multi-Agent Debate System</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def sidebar_status(connected: bool):
    c = C["success"] if connected else C["error"]
    t = "Connected" if connected else "Offline"
    st.markdown(f'<div style="font-size:11px;color:{c};margin-bottom:12px;">&#9679; {t}</div>', unsafe_allow_html=True)


def chat_message(agent_name: str, role: str, content: str, time_s: float | None = None, align: str = "left"):
    """Render a chat-bubble style message with fade-in animation."""
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"], "You": C["text_2"]}
    color = color_map.get(agent_name, C["accent"])
    initial = agent_name[0] if agent_name else "?"
    time_html = f'<span class="m-chat-time">{time_s:.1f}s</span>' if time_s is not None else ""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    align_cls = "m-chat-right" if align == "right" else ""

    st.markdown(f'''
    <div class="m-chat-msg m-fadein {align_cls}">
        <div class="m-chat-avatar" style="background:{color}15;color:{color};border:1px solid {color}25;">{initial}</div>
        <div class="m-chat-bubble">
            <div class="m-chat-meta">
                <span class="m-chat-name" style="color:{color};">{agent_name}</span>
                <span class="m-chat-role">{role}</span>
                {time_html}
            </div>
            <div class="m-chat-text">{safe}</div>
        </div>
    </div>
    ''', unsafe_allow_html=True)


def agent_message(agent_name: str, role: str, content: str, time_s: float | None = None):
    """Legacy card-style message for expanders."""
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"]}
    color = color_map.get(agent_name, C["accent"])
    initial = agent_name[-1] if agent_name else "?"
    time_html = f'<span class="m-agent-time">{time_s:.1f}s</span>' if time_s is not None else ""
    safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
    st.markdown(f'''
    <div class="m-agent m-fadein" style="border-left-color:{color};">
        <div class="m-agent-head">
            <div class="m-agent-avatar" style="background:{color}18;color:{color};">{initial}</div>
            <div class="m-agent-meta">
                <span class="m-agent-name" style="color:{color};">{agent_name}</span>
                <span class="m-agent-role">{role}</span>
            </div>
            {time_html}
        </div>
        <div class="m-agent-body">{safe}</div>
    </div>
    ''', unsafe_allow_html=True)


def typing_indicator(agent_name: str, action: str = "is thinking"):
    """Show a pulsing typing indicator."""
    color_map = {"Agent A": C["agent_a"], "Agent B": C["agent_b"], "Agent C": C["agent_c"]}
    color = color_map.get(agent_name, C["accent"])
    st.markdown(f'''
    <div class="m-typing">
        <div class="m-typing-dots">
            <span style="background:{color};"></span>
            <span style="background:{color};"></span>
            <span style="background:{color};"></span>
        </div>
        <span class="m-typing-text" style="color:{color};">{agent_name} {action}...</span>
    </div>
    ''', unsafe_allow_html=True)


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
    st.markdown(f'''
    <div class="m-metric m-glass">
        <div class="m-metric-label">{label}</div>
        <div class="m-metric-value" style="color:{color or C["text_1"]};">{value}</div>
        {d_html}
    </div>
    ''', unsafe_allow_html=True)


def winner_banner(winner: str):
    configs = {
        "debate":   ("m-banner-win",  "Multi-agent debate produced a higher-rated response"),
        "baseline": ("m-banner-base", "Single-agent baseline was rated higher"),
        "tie":      ("m-banner-tie",  "Both approaches scored equally"),
    }
    cls, text = configs.get(winner, configs["tie"])
    st.markdown(f'<div class="m-banner {cls} m-fadein"><span>{text}</span></div>', unsafe_allow_html=True)


def radar_chart_html(baseline_scores: dict, debate_scores: dict) -> str:
    """Generate an SVG radar chart comparing baseline vs debate scores."""
    import math
    dims = list(baseline_scores.keys())
    n = len(dims)
    cx, cy, r = 120, 120, 85
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
        grid += f'<polygon points="{" ".join(ring_pts)}" fill="none" stroke="{C["border"]}" stroke-width="0.5"/>'

    # Axis lines
    axes = ""
    for i in range(n):
        x = cx + r * math.cos(angles[i])
        y = cy - r * math.sin(angles[i])
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{C["border"]}" stroke-width="0.5"/>'

    # Labels
    labels = ""
    for i, dim in enumerate(dims):
        label = dim.replace("_", " ").title()
        lx = cx + (r + 18) * math.cos(angles[i])
        ly = cy - (r + 18) * math.sin(angles[i])
        anchor = "middle"
        if lx < cx - 10: anchor = "end"
        elif lx > cx + 10: anchor = "start"
        labels += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" dominant-baseline="middle" fill="{C["text_3"]}" font-size="9" font-family="Inter">{label}</text>'

    b_pts = points(baseline_scores, r)
    d_pts = points(debate_scores, r)

    return f'''
    <svg viewBox="0 0 240 260" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:320px;display:block;margin:0 auto;">
        {grid}{axes}
        <polygon points="{b_pts}" fill="{C["accent"]}15" stroke="{C["accent"]}" stroke-width="1.5" opacity="0.7"/>
        <polygon points="{d_pts}" fill="{C["agent_c"]}15" stroke="{C["agent_c"]}" stroke-width="1.5" opacity="0.7"/>
        {labels}
        <g transform="translate(50, 245)">
            <rect width="8" height="8" rx="2" fill="{C["accent"]}" opacity="0.7"/>
            <text x="12" y="8" fill="{C["text_3"]}" font-size="9" font-family="Inter">Baseline</text>
            <rect x="70" width="8" height="8" rx="2" fill="{C["agent_c"]}" opacity="0.7"/>
            <text x="82" y="8" fill="{C["text_3"]}" font-size="9" font-family="Inter">Debate</text>
        </g>
    </svg>
    '''


# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;450;500;600;700&display=swap');

/* === Base === */
.stApp {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: {C["bg_app"]};
}}
#MainMenu, header, footer {{ visibility: hidden; }}
.stDeployButton {{ display: none; }}

/* === Animations === */
@keyframes fadeInUp {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulse {{
    0%, 80%, 100% {{ opacity: 0.3; transform: scale(0.8); }}
    40% {{ opacity: 1; transform: scale(1); }}
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
section[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: {C["bg_input"]}; border: 1px solid {C["border"]};
    border-radius: 8px; color: {C["text_1"]}; font-size: 13px;
}}
section[data-testid="stSidebar"] .stTextInput > div > div > input {{
    background: {C["bg_input"]}; border: 1px solid {C["border"]};
    border-radius: 8px; color: {C["text_1"]}; font-size: 13px;
}}

/* Sidebar nav links */
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {{
    border-radius: 8px; padding: 6px 12px; margin: 1px 0;
    font-size: 13px; font-weight: 500; color: {C["text_2"]};
    transition: all 0.15s;
}}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:hover {{
    background: {C["bg_hover"]}; color: {C["text_1"]};
}}
section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"][aria-current="page"] {{
    background: {C["accent"]}12; color: {C["accent"]};
    border-left: 2px solid {C["accent"]};
}}

/* === Layout === */
.main .block-container {{ max-width: 1100px; padding: 2rem 2.5rem; }}

/* === Page Header === */
.m-page-header {{ margin-bottom: 1.75rem; }}
.m-page-title {{
    font-size: 1.4rem; font-weight: 700; letter-spacing: -0.03em;
    color: {C["text_1"]}; margin: 0; line-height: 1.3;
}}
.m-page-sub {{
    font-size: 0.84rem; color: {C["text_3"]}; margin: 0.2rem 0 0 0; line-height: 1.5;
}}

/* === Section === */
.m-section {{
    margin: 1.75rem 0 0.85rem 0; padding-bottom: 0.5rem;
    border-bottom: 1px solid {C["border"]};
}}
.m-section-title {{
    font-size: 0.95rem; font-weight: 600; color: {C["text_1"]};
    letter-spacing: -0.01em; margin: 0; display: inline;
}}
.m-section-sub {{ font-size: 0.75rem; color: {C["text_3"]}; font-weight: 400; }}

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
    border-radius: 12px; padding: 10px 14px;
    max-width: 85%; min-width: 200px;
    transition: border-color 0.15s;
}}
.m-chat-bubble:hover {{ border-color: {C["border_light"]}; }}
.m-chat-meta {{
    display: flex; align-items: center; gap: 6px; margin-bottom: 4px;
}}
.m-chat-name {{ font-weight: 600; font-size: 12px; }}
.m-chat-role {{ font-size: 10px; color: {C["text_3"]}; }}
.m-chat-time {{
    font-size: 10px; color: {C["text_4"]}; margin-left: auto;
    font-variant-numeric: tabular-nums;
}}
.m-chat-text {{
    font-size: 13px; line-height: 1.7; color: {C["text_2"]};
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
    border-radius: 10px; padding: 14px 12px; text-align: center;
    transition: transform 0.15s, border-color 0.15s;
}}
.m-metric:hover {{ transform: translateY(-1px); border-color: {C["border_light"]}; }}
.m-metric-label {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.08em; color: {C["text_3"]}; margin-bottom: 5px;
}}
.m-metric-value {{ font-size: 22px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; }}
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
}}
.m-score-table tr:hover td {{ background: {C["bg_elevated"]}; }}
.m-pos {{ color: {C["success"]}; font-weight: 600; }}
.m-neg {{ color: {C["error"]}; font-weight: 600; }}
.m-neu {{ color: {C["text_3"]}; }}

/* === Hero === */
.m-hero {{ padding: 3.5rem 1rem 2rem 1rem; text-align: center; }}
.m-hero img {{ margin: 0 auto; }}
.m-hero-title {{
    font-size: 2rem; font-weight: 700; letter-spacing: -0.04em;
    color: {C["text_1"]}; margin: 0.6rem 0 0 0; line-height: 1.15;
}}
.m-hero-accent {{ color: {C["accent"]}; }}
.m-hero-sub {{
    font-size: 0.9rem; color: {C["text_3"]}; max-width: 520px;
    margin: 0.6rem auto 0 auto; line-height: 1.6;
}}

/* === Features === */
.m-features {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 2rem 0; }}
.m-feat {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 12px; padding: 20px 18px;
    transition: border-color 0.15s, transform 0.15s, box-shadow 0.15s;
}}
.m-feat:hover {{
    border-color: {C["accent"]}40; transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}}
.m-feat-bar {{ width: 24px; height: 3px; border-radius: 2px; margin-bottom: 12px; }}
.m-feat-title {{ font-size: 13px; font-weight: 600; color: {C["text_1"]}; margin-bottom: 4px; }}
.m-feat-desc {{ font-size: 12px; color: {C["text_3"]}; line-height: 1.55; }}

/* === Flow === */
.m-flow {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 12px; padding: 24px; margin: 1.5rem 0;
}}
.m-flow-label {{
    font-size: 9px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.1em; color: {C["text_4"]}; margin-bottom: 16px;
}}
.m-flow-step {{ display: flex; align-items: center; gap: 12px; padding: 6px 0; }}
.m-flow-num {{
    width: 28px; height: 28px; border-radius: 7px;
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
    padding: 7px 12px; background: {C["bg_surface"]};
    border-radius: 8px; margin: 4px 0; border: 1px solid {C["border"]};
    font-size: 13px; transition: border-color 0.15s;
}}
.m-result-row:hover {{ border-color: {C["border_light"]}; }}
.m-rr-q {{ flex: 1; color: {C["text_2"]}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.m-rr-badge {{ font-size: 10px; font-weight: 500; padding: 1px 6px; border-radius: 4px; }}
.m-rr-time {{ font-size: 10px; color: {C["text_3"]}; font-variant-numeric: tabular-nums; }}

/* === Empty === */
.m-empty {{
    text-align: center; padding: 48px 16px;
    background: {C["bg_surface"]}; border: 1px solid {C["border"]}; border-radius: 12px;
}}
.m-empty-title {{ font-size: 14px; font-weight: 500; color: {C["text_1"]}; margin-bottom: 4px; }}
.m-empty-sub {{ font-size: 13px; color: {C["text_3"]}; }}

/* === Inputs === */
.stTextArea textarea {{
    background: {C["bg_surface"]}; border: 1px solid {C["border"]};
    border-radius: 10px; font-size: 14px; font-family: 'Inter', sans-serif;
    padding: 12px 14px; color: {C["text_1"]}; transition: border-color 0.15s;
}}
.stTextArea textarea:focus {{
    border-color: {C["accent"]}; box-shadow: 0 0 0 2px {C["accent"]}18;
}}
.stTextArea textarea::placeholder {{ color: {C["text_4"]}; }}

/* === Buttons === */
div.stButton > button[kind="primary"] {{
    background: {C["accent"]}; color: #fff; border: none;
    border-radius: 8px; font-weight: 500; font-size: 13px;
    padding: 8px 18px; transition: all 0.15s;
}}
div.stButton > button[kind="primary"]:hover {{
    background: {C["accent_hover"]}; box-shadow: 0 2px 12px {C["accent"]}35;
    transform: translateY(-1px);
}}
div.stButton > button {{
    border-radius: 8px; border: 1px solid {C["border"]};
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
    transition: all 0.15s;
}}
div.stButton > button:hover {{
    border-color: {C["accent"]}50; color: {C["text_1"]}; transform: translateY(-1px);
}}

/* === Expander === */
.streamlit-expanderHeader {{
    background: {C["bg_surface"]}; border-radius: 8px;
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
}}

/* === Progress === */
.stProgress > div > div {{ background: {C["accent"]}; border-radius: 8px; }}

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
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {C["border"]}; border-radius: 3px; }}

/* === Download === */
.stDownloadButton > button {{
    border-radius: 8px; border: 1px solid {C["border"]};
    font-weight: 500; font-size: 13px; color: {C["text_2"]};
}}
.stDownloadButton > button:hover {{ border-color: {C["accent"]}50; color: {C["text_1"]}; }}

/* === Dataframe === */
.stDataFrame {{ border-radius: 10px; overflow: hidden; }}
.stSlider [data-testid="stThumbValue"] {{ color: {C["accent"]}; }}
</style>
"""
