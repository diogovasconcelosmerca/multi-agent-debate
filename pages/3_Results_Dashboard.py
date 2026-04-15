"""
Results Dashboard -- charts, radar, and export.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.config import EVALUATION_DIMENSIONS
from core.storage import load_summary_df
from core.theme import (
    C,
    favicon_uri,
    inject_premium_css,
    metric_card,
    page_header,
    radar_chart_html,
    section_header,
)

st.set_page_config(page_title="MADS -- Dashboard", page_icon=favicon_uri(), layout="wide")
inject_premium_css()

PL = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color=C["text_3"], size=12),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color=C["text_3"])),
    xaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"]),
    yaxis=dict(gridcolor=C["border"], zerolinecolor=C["border"]),
)

COL_B = C["accent"]
COL_D = C["agent_c"]

page_header("Results Dashboard", "Analyse and export experiment data.")

df = load_summary_df()

if df.empty:
    st.markdown(f'''
    <div class="m-empty">
        <div class="m-empty-title">No experiments yet</div>
        <div class="m-empty-sub">Run experiments first, then return here.</div>
    </div>
    ''', unsafe_allow_html=True)
    st.stop()

# Filters
with st.sidebar:
    st.markdown(f'<div style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:{C["text_3"]};margin:12px 0 6px 0;">Filters</div>', unsafe_allow_html=True)
    if "model" in df.columns:
        opts = ["All"] + sorted(df["model"].dropna().unique().tolist())
        sel = st.selectbox("Model", opts, key="dm")
        if sel != "All":
            df = df[df["model"] == sel]
    if "domain" in df.columns:
        opts = ["All"] + sorted(df["domain"].dropna().unique().tolist())
        sel = st.selectbox("Domain", opts, key="dd")
        if sel != "All":
            df = df[df["domain"] == sel]

if df.empty:
    st.warning("No results match filters.")
    st.stop()

# Overview metrics
scb = [f"baseline_{d}" for d in EVALUATION_DIMENSIONS]
scd = [f"debate_{d}" for d in EVALUATION_DIMENSIONS]
avg_b = df[scb].mean().mean()
avg_d = df[scd].mean().mean()
delta = avg_d - avg_b
ds = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

m1, m2, m3, m4 = st.columns(4)
with m1:
    metric_card("Experiments", str(len(df)), color=C["accent"])
with m2:
    metric_card("Avg Baseline", f"{avg_b:.1f}", color=COL_B)
with m3:
    metric_card("Avg Debate", f"{avg_d:.1f}", color=COL_D)
with m4:
    metric_card("Avg Delta", ds, delta=ds)

# Radar chart of average scores
section_header("Average Score Profile", "radar comparison")
col_radar, col_bar = st.columns([2, 3])

with col_radar:
    avg_b_scores = {d: round(df[f"baseline_{d}"].mean(), 1) for d in EVALUATION_DIMENSIONS}
    avg_d_scores = {d: round(df[f"debate_{d}"].mean(), 1) for d in EVALUATION_DIMENSIONS}
    st.markdown(radar_chart_html(avg_b_scores, avg_d_scores), unsafe_allow_html=True)

with col_bar:
    means_b = df[scb].mean()
    means_d = df[scd].mean()
    labels = [d.replace("_", " ").title() for d in EVALUATION_DIMENSIONS]

    fig = go.Figure()
    fig.add_trace(go.Bar(name="Baseline", x=labels, y=list(means_b.values), marker_color=COL_B, marker_cornerradius=5))
    fig.add_trace(go.Bar(name="Debate", x=labels, y=list(means_d.values), marker_color=COL_D, marker_cornerradius=5))
    fig.update_layout(**PL, barmode="group", yaxis_range=[0, 5.5], yaxis_title="Score", height=320, bargap=0.3)
    st.plotly_chart(fig, use_container_width=True)

# Box plots
section_header("Distributions")
rows_list = []
for dim in EVALUATION_DIMENSIONS:
    lab = dim.replace("_", " ").title()
    for v in df[f"baseline_{dim}"].dropna():
        rows_list.append({"Dimension": lab, "Score": v, "Mode": "Baseline"})
    for v in df[f"debate_{dim}"].dropna():
        rows_list.append({"Dimension": lab, "Score": v, "Mode": "Debate"})
if rows_list:
    fig2 = px.box(
        pd.DataFrame(rows_list), x="Dimension", y="Score", color="Mode",
        color_discrete_map={"Baseline": COL_B, "Debate": COL_D},
    )
    fig2.update_layout(**PL, height=360)
    st.plotly_chart(fig2, use_container_width=True)

# Latency
if "baseline_time" in df.columns and "debate_time" in df.columns:
    tdf = df[["experiment_id", "baseline_time", "debate_time"]].dropna()
    if not tdf.empty:
        section_header("Latency")
        abt, adt = tdf["baseline_time"].mean(), tdf["debate_time"].mean()
        ratio = adt / max(abt, 0.01)
        t1, t2, t3 = st.columns(3)
        with t1:
            metric_card("Avg Baseline", f"{abt:.1f}s", color=COL_B)
        with t2:
            metric_card("Avg Debate", f"{adt:.1f}s", color=COL_D)
        with t3:
            metric_card("Ratio", f"{ratio:.1f}x", color=C["warning"])

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="Baseline", x=list(range(len(tdf))), y=tdf["baseline_time"], marker_color=COL_B, marker_cornerradius=3))
        fig3.add_trace(go.Bar(name="Debate", x=list(range(len(tdf))), y=tdf["debate_time"], marker_color=COL_D, marker_cornerradius=3))
        fig3.update_layout(**PL, barmode="group", yaxis_title="Seconds", xaxis_title="Experiment", height=300)
        st.plotly_chart(fig3, use_container_width=True)

# Data table
section_header("All Experiments")
display = [c for c in df.columns if c != "experiment_id"]
st.dataframe(df[display] if display else df, use_container_width=True, hide_index=True, height=380)

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
st.download_button(
    "Download CSV",
    df.to_csv(index=False).encode("utf-8"),
    "mads_results.csv",
    "text/csv",
    use_container_width=True,
)
