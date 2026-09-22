"""
UK Top 50 Playlist — Music Market Intelligence Dashboard
Entertainment analytics portfolio case study using an Atlantic Recording Corporation business scenario.

Run with:  streamlit run app.py
"""
import sys
from pathlib import Path
from typing import Any, cast
sys.path.insert(0, "src")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

import analytics as an
from data_prep import run as run_pipeline, canonical_recordings, load_raw
from data_quality import validate_all
from artist_nationality import classify, UK, INTL, UNK


DATA_PATH = Path("data/Atlantic_United_Kingdom.csv")
DATA_VERSION = DATA_PATH.stat().st_mtime_ns if DATA_PATH.exists() else 0


st.set_page_config(
    page_title="UK Top 50 | Music Market Intelligence",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


ATLANTIC_BLACK = "#0B0B0B"  # Structural UI ink only; never used as the default quantitative mark.
# Olive comparison palette: restrained, editorial, and tuned to the warm off-white canvas.
# The variable names remain backward-compatible with the existing chart code.
ATLANTIC_NAVY = "#5E6849"       # Deep olive: primary quantitative series.
ATLANTIC_RED = "#737D52"        # Olive accent: emphasis / selected / explicit series.
ATLANTIC_GOLD = "#968C67"       # Warm khaki: secondary comparative series.
ATLANTIC_TEAL = "#7C876E"       # Sage olive: collaboration / tertiary series.
ATLANTIC_GREY = "#9C998D"       # Warm neutral fallback / unclassified category.
PALETTE = [ATLANTIC_NAVY, ATLANTIC_RED, ATLANTIC_GOLD, ATLANTIC_TEAL, ATLANTIC_GREY]

FORMAT_COLORS = {
    "album": "#5E6849",
    "single": "#9A8F67",
    "compilation": "#B9B7A7",
}
COLLAB_COLORS = {
    "Solo chart entries": "#B8B8AA",
    "Collaborative chart entries": "#66734C",
}
EXPLICIT_SCATTER_COLORS = {
    "Clean": "#7C876E",
    "Explicit": "#596447",
}

# Magnitude scales remain readable on the yellowish off-white chart surface.
BAR_SCALE = ["#B7B99E", "#A4AA87", "#8D9670", "#747F59", "#566044"]
TREEMAP_SCALE = ["#C9C9AD", "#B2B794", "#99A079", "#7E8963", "#616D4E"]
SEQ_BLUES = TREEMAP_SCALE  # Backward-compatible alias used by existing chart code.

# Olive sequential heatmap: low values remain warm-off-white; high values become deep olive.
HEATMAP_SCALE = [
    [0.00, "#F4F0E5"],
    [0.25, "#DADCC2"],
    [0.50, "#B7BD91"],
    [0.75, "#899466"],
    [1.00, "#596447"],
]

# ---------------------------------------------------------------------------
# Global styling — final olive / warm-off-white dashboard system
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    :root {
        --black:#0B0B0B;
        --graphite:#242422;
        --ink:#151513;
        --muted:#5E5E59;
        --canvas:#EEE9DC;
        --sidebar:#E7E1D2;
        --surface:#F5F1E7;
        --surface-raised:#FAF7EF;
        --surface-soft:#EAE4D7;
        --line:#C9C1AF;
        --line-strong:#AAA18C;
        --accent:#737D52;
        --sand:#968C67;
        --sage:#7C876E;
        --shadow:rgba(11,11,11,0.10);
    }

    html, body, [class*="css"] {
        font-family: Inter, "Helvetica Neue", Arial, sans-serif;
    }
    header[data-testid="stHeader"] {background:transparent; box-shadow:none;}
    footer {visibility:hidden;}

    /* One continuous warm-concrete canvas. */
    .stApp {
        background:
            radial-gradient(circle at 88% 4%, rgba(255,255,255,0.18), transparent 25rem),
            linear-gradient(180deg, #F4F0E5 0%, var(--canvas) 56%, #E7E0D0 100%);
        background-attachment:fixed;
        color:var(--ink);
    }
    .block-container {
        padding-top:2.55rem; padding-bottom:2.1rem; padding-left:2rem; padding-right:2rem;
        max-width:1580px;
    }

    /* Sidebar belongs to the same material family as the canvas. */
    section[data-testid="stSidebar"] {
        width:300px !important; min-width:300px !important;
        background:linear-gradient(180deg,#ECE6D8 0%,#E2DCCB 100%);
        border-right:1px solid var(--line);
        box-shadow:7px 0 22px rgba(11,11,11,0.055);
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top:1.35rem; padding-left:1rem; padding-right:1rem;
    }
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h4 {color:var(--ink);}
    section[data-testid="stSidebar"] [data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div,
    section[data-testid="stSidebar"] input {
        background:var(--surface-soft) !important;
        border-color:var(--line) !important;
        color:var(--ink) !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    section[data-testid="stSidebar"] [data-baseweb="input"] > div:hover {
        border-color:var(--line-strong) !important;
    }
    section[data-testid="stSidebar"] hr {border-color:var(--line);}

    .sidebar-brand {
        background:var(--black);
        color:#F2EFEA; border-radius:14px; padding:15px 16px 14px 16px;
        box-shadow:0 9px 22px rgba(11,11,11,0.20); margin-bottom:0.9rem;
        border:1px solid #2D2B28;
    }
    .sidebar-kicker {
        font-size:0.67rem; letter-spacing:0.12em; font-weight:800; text-transform:uppercase;
        color:#98A173; margin-bottom:0.35rem;
    }
    .sidebar-title {font-size:1.12rem; font-weight:850; line-height:1.18; color:#F5F2EE;}
    .sidebar-subtitle {font-size:0.80rem; color:#C9C4BD; margin-top:0.28rem; line-height:1.35;}
    .sidebar-context {
        margin-top:0.72rem; padding-top:0.68rem; border-top:1px solid #35322F;
        color:#AAA49D; font-size:0.69rem; line-height:1.45;
    }

    /* Black editorial hero; no competing accent rainbow. */
    .hero-shell {
        position:relative; overflow:hidden;
        background:linear-gradient(118deg,#080808 0%,#10100F 58%,#181715 100%);
        border-radius:18px; padding:26px 28px 24px 28px; margin-bottom:18px;
        box-shadow:0 13px 34px rgba(11,11,11,0.22);
        border:1px solid #292725;
    }
    .hero-shell:after {
        content:""; position:absolute; width:330px; height:330px; right:-135px; top:-175px;
        border-radius:50%; border:42px solid rgba(255,255,255,0.025);
        box-shadow:0 0 0 42px rgba(240,90,58,0.024), 0 0 0 84px rgba(255,255,255,0.014);
        pointer-events:none;
    }
    .hero-eyebrow {
        color:#98A173; font-size:0.70rem; font-weight:800; letter-spacing:0.14em;
        text-transform:uppercase; margin-bottom:0.45rem;
    }
    .hero-title {
        font-size:2.25rem; font-weight:900; color:#F7F4F0; margin:0; letter-spacing:-0.6px; line-height:1.13;
    }
    .hero-subtitle {
        font-size:1.12rem; font-weight:650; color:#DDD8D1; margin-top:0.38rem; line-height:1.35;
    }
    .hero-description {font-size:0.86rem; color:#ABA59E; margin-top:0.55rem; line-height:1.45;}
    .hero-rule {
        width:188px; height:4px; border-radius:999px; margin-top:0.95rem;
        background:var(--accent);
    }
    .hero-chips {display:flex; flex-wrap:wrap; gap:7px; margin-top:0.95rem;}
    .hero-chip {
        display:inline-flex; align-items:center; border:1px solid #3A3733;
        background:#1A1918; color:#E8E4DE; border-radius:999px;
        padding:4px 9px; font-size:0.69rem; font-weight:680; letter-spacing:0.01em;
    }

    .section-narrative {
        color:#4B4B47; font-size:0.96rem; line-height:1.65; margin-bottom:0.95rem; max-width:1120px;
    }


    /* All information cards share one surface and one border language. */
    .kpi-card,
    .insight-card,
    .finding-card,
    .rec-card,
    .evidence-card,
    .grain-card,
    div[data-testid="stMetric"] {
        background:var(--surface-raised);
        border-color:var(--line);
        box-shadow:0 3px 10px rgba(11,11,11,0.055);
    }
    .kpi-card {
        border-left:5px solid var(--black); border-radius:12px;
        padding:17px 18px 16px 18px; height:100%; min-height:112px;
        border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line);
        transition:transform 0.15s ease,box-shadow 0.15s ease,border-color 0.15s ease;
    }
    .kpi-card:hover {transform:translateY(-2px); box-shadow:0 8px 20px rgba(11,11,11,0.095);}
    .kpi-icon {
        display:inline-flex; align-items:center; justify-content:center;
        min-width:30px; height:30px; padding:0 7px; border-radius:8px;
        background:#ECE9DC; border:1px solid #C6BEAB; color:var(--black);
        font-size:0.92rem; font-weight:850; line-height:1; letter-spacing:-0.01em;
    }
    .kpi-value {font-size:1.62rem; font-weight:900; color:var(--black); line-height:1.2; margin-top:7px;}
    .kpi-label {font-size:0.72rem; color:#5E5E59; text-transform:uppercase; letter-spacing:0.055em; margin-top:3px;}
    .kpi-help {
        display:inline-flex; align-items:center; justify-content:center; margin-left:5px;
        width:15px; height:15px; border-radius:50%; border:1px solid #918A83;
        color:#69635D; font-size:0.60rem; font-weight:800; vertical-align:1px;
        cursor:help; text-transform:none; letter-spacing:0;
    }

    .insight-card {
        border-left:5px solid var(--sand); border-radius:11px; padding:15px 19px; margin:0.45rem 0 1.05rem 0;
        border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line);
        transition:transform 0.15s ease,box-shadow 0.15s ease;
    }
    .finding-card {
        border:1px solid var(--line); border-top:4px solid var(--black); border-radius:11px;
        padding:16px 19px; height:100%; transition:transform 0.15s ease,box-shadow 0.15s ease;
    }
    .rec-card {
        border:1px solid var(--line); border-top:4px solid var(--sage); border-radius:11px;
        padding:18px 20px; height:100%; transition:transform 0.15s ease,box-shadow 0.15s ease;
    }
    .evidence-card {
        border:1px solid var(--line); border-top:4px solid var(--black); border-radius:12px;
        padding:17px 19px; height:100%;
    }
    .grain-card {
        border:1px solid var(--line); border-radius:11px; padding:12px 14px;
    }
    @media (hover:hover) and (pointer:fine) {
        .insight-card:hover,.finding-card:hover,.rec-card:hover {transform:translateY(-1px); box-shadow:0 7px 17px rgba(11,11,11,0.085);}
    }
    .insight-title,.finding-title,.rec-title,.evidence-title,.grain-card-title {color:var(--black); font-weight:850;}
    .insight-title {font-size:0.96rem; margin-bottom:4px;}
    .finding-title {font-size:0.94rem; margin-bottom:6px;}
    .rec-title {font-size:1rem; margin-bottom:9px;}
    .evidence-title {font-size:0.96rem; margin-bottom:0.65rem;}
    .grain-card-title {font-size:0.82rem; margin-bottom:3px;}
    .insight-text,.finding-text,.evidence-text {color:#494945;}
    .insight-text {font-size:0.89rem; line-height:1.56;}
    .finding-text {font-size:0.85rem; line-height:1.52;}
    .evidence-text {font-size:0.86rem; line-height:1.52;}
    .evidence-label {
        font-size:0.66rem; letter-spacing:0.07em; text-transform:uppercase; font-weight:800;
        color:#79736D; margin-top:0.55rem; margin-bottom:0.15rem;
    }
    .grain-grid {
        display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:10px;
        margin:0.15rem 0 0.35rem 0;
    }
    .grain-card-text {color:#666661; font-size:0.72rem; line-height:1.4;}
    .footer-meta {color:#686863; font-size:0.74rem; line-height:1.55; margin-top:0.35rem;}
    .rec-title span.badge {
        display:inline-block; color:#F6F2ED; font-size:0.66rem; font-weight:800;
        padding:3px 8px; border-radius:999px; margin-left:7px; vertical-align:middle; letter-spacing:0.045em;
    }

    div[data-testid="stMetric"] {
        border:1px solid var(--line); border-radius:11px; padding:11px 13px;
        transition:transform 0.15s ease,box-shadow 0.15s ease;
    }
    @media (hover:hover) and (pointer:fine) {
        div[data-testid="stMetric"]:hover {transform:translateY(-1px); box-shadow:0 6px 14px rgba(11,11,11,0.08);}
    }
    div[data-testid="stMetricValue"] {font-size:1.48rem; color:var(--black);}
    div[data-testid="stMetricLabel"] {color:#5E5E59;}
    .section-spacer {margin-top:18px;}

    /* Charts, modebar, tables, expanders, and alerts all use the same surface. */
    div[data-testid="stPlotlyChart"] {
        background:var(--surface); border-radius:13px; overflow:hidden; border:1px solid var(--line);
        box-shadow:0 2px 8px rgba(11,11,11,0.045); transition:border-color 0.15s ease,box-shadow 0.15s ease;
    }
    div[data-testid="stPlotlyChart"] .modebar {opacity:0.26; transition:opacity 0.15s ease;}
    div[data-testid="stPlotlyChart"] .modebar-btn path {fill:#4B4742 !important;}
    @media (hover:hover) and (pointer:fine) {
        div[data-testid="stPlotlyChart"]:hover {border-color:var(--line-strong); box-shadow:0 7px 18px rgba(11,11,11,0.075);}
        div[data-testid="stPlotlyChart"]:hover .modebar {opacity:0.72;}
    }
    div[data-testid="stDataFrame"], div[data-testid="stTable"] {
        background:var(--surface); border-radius:12px; border:1px solid var(--line);
        box-shadow:0 2px 8px rgba(11,11,11,0.045);
    }
    div[data-testid="stDataFrame"] {padding:10px;}
    div[data-testid="stTable"] table {font-size:0.85rem; background:var(--surface);}
    div[data-testid="stTable"] th {background:#D9DEC4; color:#303520; font-weight:850;}
    div[data-testid="stTable"] td {background:#F8F4EA; color:#38372F;}
    div[data-testid="stTable"] tbody tr td {transition:background 0.12s ease;}
    @media (hover:hover) and (pointer:fine) {
        div[data-testid="stTable"] tbody tr:hover td {background:#E9EAD8 !important;}
    }
    details[data-testid="stExpander"] {
        background:var(--surface); border:1px solid var(--line); border-radius:11px;
    }
    div[data-testid="stAlert"] {
        background:#ECE8DA; border:1px solid var(--line); color:var(--ink);
    }

    .stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4 {
        color:var(--black); font-weight:900; letter-spacing:-0.018em;
    }
    .stMarkdown h4 {margin-top:1.15rem;}
    .stCaptionContainer, [data-testid="stCaptionContainer"] {color:#6A645E;}

    @media (max-width:1100px) {
        .grain-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
    }

    @media (max-width:900px) {
        section[data-testid="stSidebar"] {width:270px !important; min-width:270px !important;}
        .block-container {padding-left:1rem; padding-right:1rem;}
        .hero-shell {padding:22px 20px;}
        .hero-title {font-size:1.82rem;}
        .hero-subtitle {font-size:1rem;}
    }
    /* Sidebar controls use the same neutral material system -- no cold-white islands. */
    section[data-testid="stSidebar"] div[data-baseweb="base-input"],
    section[data-testid="stSidebar"] div[data-baseweb="input"],
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
    section[data-testid="stSidebar"] [data-testid="stDateInput"] div[data-baseweb="base-input"] {
        background:#F5F1E7 !important;
        border-color:#C9C1AF !important;
        box-shadow:none !important;
    }
    section[data-testid="stSidebar"] input {
        background:transparent !important; color:#1B1B19 !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {
        background:#1A1A19 !important; color:#F3F3EF !important; border-color:#1A1A19 !important;
    }
    section[data-testid="stSidebar"] svg {color:#4F4F4B !important; fill:currentColor;}
    section[data-testid="stSidebar"] [role="radiogroup"] label {color:#222220 !important;}

    /* Selected Streamlit controls use the same olive accent as the dashboard. */
    section[data-testid="stSidebar"] input[type="radio"] {accent-color:var(--accent) !important;}
    section[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        border-color:var(--line-strong) !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="radio"] input:checked + div,
    section[data-testid="stSidebar"] [data-baseweb="radio"] [aria-checked="true"] {
        border-color:var(--accent) !important;
        background:var(--accent) !important;
    }
    div[data-testid="stSlider"] [role="slider"] {
        background:var(--accent) !important;
        border-color:var(--accent) !important;
    }
    div[data-testid="stSlider"] [data-testid="stTickBarMin"],
    div[data-testid="stSlider"] [data-testid="stTickBarMax"] {color:#625F53 !important;}
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {background:var(--accent) !important;}

    /* Consistent heading rhythm and no accidental blue link treatment. */
    .editorial-section-title {
        color:var(--black); font-size:1.48rem; font-weight:900; letter-spacing:-0.02em;
        margin:1.35rem 0 0.8rem 0; line-height:1.2;
    }


    /* Dashboard section navigation */
    .st-key-dashboard_section {
        margin:0.2rem 0 1.05rem 0 !important;
        padding:0.38rem !important;
        background:#E5E3D3 !important;
        border:1px solid var(--line) !important;
        border-radius:12px !important;
        box-shadow:0 2px 8px rgba(11,11,11,0.04) !important;
    }

    .st-key-dashboard_section [data-testid="stPills"] {
        gap:0.32rem !important;
    }

    .st-key-dashboard_section button {
        min-height:38px !important;
        padding:0.42rem 0.82rem !important;
        border:1px solid transparent !important;
        border-radius:8px !important;
        background:transparent !important;
        color:#4E4E49 !important;
        font-size:0.84rem !important;
        font-weight:720 !important;
        box-shadow:none !important;
        transition:background .15s ease, border-color .15s ease, color .15s ease !important;
    }

    .st-key-dashboard_section button p {
        color:inherit !important;
        font-weight:inherit !important;
    }

    @media (hover:hover) and (pointer:fine) {
        .st-key-dashboard_section button:hover {
            background:#EFEBDE !important;
            border-color:#C0C0BB !important;
            color:var(--black) !important;
        }
    }

    .st-key-dashboard_section button[aria-pressed="true"] {
        background:var(--black) !important;
        border-color:var(--black) !important;
        color:#F5F2EE !important;
    }

    .st-key-artist_comparison_main {
        max-width:760px;
        margin:0.2rem 0 1rem 0;
    }

    @media (max-width:900px) {
        .st-key-dashboard_section button {
            padding:0.38rem 0.62rem !important;
            font-size:0.78rem !important;
        }
    }


    /* Strong current-view treatment, independent of Streamlit's default theme. */
    .active-view-strip {
        display:flex; align-items:center; gap:10px; margin:0.15rem 0 1rem 0;
        padding:9px 12px; border-left:4px solid var(--accent); border-radius:8px;
        background:#EFEBDE; color:#4D4D49; font-size:0.78rem;
    }
    .active-view-strip .label {
        text-transform:uppercase; letter-spacing:0.08em; font-size:0.64rem; font-weight:850; color:#74736D;
    }
    .active-view-strip .value {font-weight:900; color:var(--black); font-size:0.86rem;}
    .active-view-strip .desc {color:#66635E;}

    /* Streamlit segmented-control states. */
    .st-key-dashboard_section [data-testid="stBaseButton-segmented_control"] {
        background:transparent !important; border-color:transparent !important; color:#4E4E49 !important;
        min-height:39px !important; font-weight:760 !important;
    }
    .st-key-dashboard_section [data-testid="stBaseButton-segmented_controlActive"],
    .st-key-dashboard_section button[aria-pressed="true"],
    .st-key-dashboard_section button[aria-selected="true"] {
        background:#66734C !important;
        border-color:#66734C !important;
        color:#FBF8EF !important;
        box-shadow:inset 0 -3px 0 var(--accent) !important;
        font-weight:850 !important;
    }
    .st-key-dashboard_section [data-testid="stBaseButton-segmented_controlActive"] p,
    .st-key-dashboard_section button[aria-pressed="true"] p,
    .st-key-dashboard_section button[aria-selected="true"] p {
        color:#FBF8EF !important;
    }

    /* Deliberate, readable static tables. */
    .professional-table-wrap {
        width:100%; overflow-x:auto; border:1px solid var(--line); border-radius:12px;
        background:var(--surface-raised); box-shadow:0 2px 8px rgba(11,11,11,0.045); margin:0.45rem 0 1rem;
    }
    table.professional-table {
        width:100%; border-collapse:collapse; border-spacing:0; font-size:0.80rem; color:#30302D;
    }
    table.professional-table th {
        position:sticky; top:0; z-index:1; text-align:left; padding:10px 11px;
        background:#D8DDC2; color:#303520; font-size:0.70rem; text-transform:uppercase;
        letter-spacing:0.045em; font-weight:850; border-bottom:1px solid #C6BEAB; white-space:nowrap;
    }
    table.professional-table td {
        padding:9px 11px; border-bottom:1px solid #D4D4D0; vertical-align:top; line-height:1.42;
        background:#F9F5EA;
    }
    table.professional-table tbody tr:nth-child(even) td {background:#F1EEE1;}
    table.professional-table tbody tr:last-child td {border-bottom:none;}
    table.professional-table tbody tr:hover td {background:#E6E8D3;}
    table.professional-table td:first-child {font-weight:780;}
    .quality-table td:nth-child(1) {width:104px; white-space:nowrap; text-transform:uppercase; letter-spacing:0.045em; font-size:0.68rem;}
    .quality-table td:nth-child(2) {min-width:180px; font-weight:720;}
    .quality-table td:nth-child(3) {min-width:210px; color:#4C4A46;}
    .quality-table td:nth-child(4) {min-width:320px; white-space:normal; color:#5B5751;}
    .status-badge {display:inline-flex; align-items:center; border-radius:999px; padding:3px 8px; font-size:0.64rem; font-weight:850; letter-spacing:0.045em; border:1px solid transparent;}
    .status-pass {background:#E1E6D4; color:#48513A; border-color:#C7CFB4;}
    .status-review {background:#EEE7D5; color:#665B42; border-color:#D6C9A9;}
    .status-fail {background:#E9DDD8; color:#6E4F48; border-color:#D3BBB3;}
    .null-value {color:#7B7770; font-style:italic; font-weight:650;}
    .artist-table td:first-child {min-width:160px;}

    /* Explicit open/close panels replace inconsistent expander behavior. */
    [class*="st-key-toggle_"] {
        margin:0.35rem 0 0.75rem 0 !important;
    }
    [class*="st-key-toggle_"] button {
        width:100% !important; justify-content:flex-start !important; min-height:42px !important;
        border:1px solid #C2C2BD !important; border-radius:10px !important;
        background:rgba(245,241,231,0.82) !important; color:#242421 !important; font-weight:760 !important;
        box-shadow:0 1px 3px rgba(11,11,11,0.025) !important; padding:0.55rem 0.8rem !important;
    }
    [class*="st-key-toggle_"] button:hover {
        background:#ECE9DC !important; border-color:#B8B09C !important;
    }


    /* Open panel content: one soft card, no separator-rule effect. */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color:#C7C7C2 !important;
        border-radius:11px !important;
        background:rgba(250,247,239,0.78) !important;
        box-shadow:none !important;
    }

        /* Structured portfolio footer instead of a dense one-line disclaimer. */
    .portfolio-footer {margin-top:1.15rem; padding-top:0.20rem; border-top:none;}
    .portfolio-footer-title {font-size:1.02rem; font-weight:900; color:var(--black); margin-bottom:0.65rem;}
    .footer-grid {display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin-top:0.25rem;}
    .footer-card {background:#EFEBDE; border:1px solid var(--line); border-radius:10px; padding:12px 13px;}
    .footer-card-title {font-size:0.68rem; text-transform:uppercase; letter-spacing:0.065em; font-weight:850; color:#6A6761; margin-bottom:5px;}
    .footer-card-text {font-size:0.78rem; line-height:1.48; color:#494944;}
    .footer-note {font-size:0.70rem; color:#77736D; line-height:1.5; margin-top:0.55rem; padding:0 2px;}

    @media (max-width:900px) {
        .footer-grid {grid-template-columns:1fr;}
        .active-view-strip {align-items:flex-start; flex-direction:column; gap:3px;}
    }



    /* Native Streamlit theme fallbacks for active controls. */
    .stApp {
        --primary-color:#737D52 !important;
        --primary-color-background:#E3E6D4 !important;
        --primary-color-border:#737D52 !important;
    }

    /* FINAL_OLIVE_CONTROL_STATES */
    /* Force Streamlit/BaseWeb active controls into the same olive system. */
    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) > div:first-child,
    section[data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) > div:first-child,
    section[data-testid="stSidebar"] [role="radio"][aria-checked="true"] {
        background:var(--accent) !important;
        border-color:var(--accent) !important;
        box-shadow:inset 0 0 0 1px var(--accent) !important;
    }

    section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) svg,
    section[data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) svg {
        color:#FBF8EF !important;
        fill:#FBF8EF !important;
    }


    section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) > div:first-child > div {
        background:#737D52 !important;
        border-color:#737D52 !important;
    }

    div[data-testid="stSlider"] [role="slider"],
    div[data-testid="stSlider"] [role="slider"] > div {
        background:var(--accent) !important;
        border-color:var(--accent) !important;
    }

    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child {
        background:var(--accent) !important;
    }

    section[data-testid="stSidebar"] button[aria-pressed="true"],
    section[data-testid="stSidebar"] button[aria-selected="true"] {
        border-color:var(--accent) !important;
        box-shadow:inset 0 0 0 1px var(--accent) !important;
    }

    section[data-testid="stSidebar"] input:focus,
    section[data-testid="stSidebar"] [data-baseweb="select"] > div:focus-within,
    section[data-testid="stSidebar"] [data-baseweb="base-input"]:focus-within {
        border-color:var(--accent) !important;
        box-shadow:0 0 0 1px var(--accent) !important;
    }

</style>
""", unsafe_allow_html=True)


def kpi_card(col, icon, label, value, accent=ATLANTIC_NAVY, help_text=None):
    help_html = (
        f'<span class="kpi-help" title="{help_text}">i</span>'
        if help_text else ""
    )
    col.markdown(f"""
    <div class="kpi-card" style="border-left-color:{accent};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}{help_html}</div>
    </div>""", unsafe_allow_html=True)


def insight_card(icon, title, text, accent=ATLANTIC_GOLD):
    st.markdown(f"""
    <div class="insight-card" style="border-left-color:{accent};">
        <div class="insight-title">{icon}&nbsp; {title}</div>
        <div class="insight-text">{text}</div>
    </div>""", unsafe_allow_html=True)


def finding_card(col, icon, title, text, accent=ATLANTIC_NAVY):
    col.markdown(f"""
    <div class="finding-card" style="border-top-color:{accent};">
        <div class="finding-title">{icon}&nbsp; {title}</div>
        <div class="finding-text">{text}</div>
    </div>""", unsafe_allow_html=True)


def rec_card(col, icon, title, badge, points, accent=ATLANTIC_TEAL):
    items = "".join(f"<li style='margin-bottom:7px;'>{p}</li>" for p in points)
    col.markdown(f"""
    <div class="rec-card" style="border-top-color:{accent};">
        <div class="rec-title">{icon}&nbsp; {title}<span class="badge" style="background:{accent};">{badge}</span></div>
        <ul style="padding-left:1.1rem; color:#3A3A37; font-size:0.87rem; line-height:1.45; margin-bottom:0;">{items}</ul>
    </div>""", unsafe_allow_html=True)


def section_narrative(text):
    st.markdown(f'<div class="section-narrative">{text}</div>', unsafe_allow_html=True)


def render_static_table(frame, table_class="professional-table", formats=None, status_column=None):
    """Render a clear, read-only HTML table with predictable wrapping and no hidden column menu."""
    from html import escape

    display = frame.copy()
    for column, formatter in (formats or {}).items():
        if column in display.columns:
            display[column] = display[column].map(lambda value: formatter(value) if not pd.isna(value) else "null")

    for column in display.columns:
        display[column] = display[column].map(lambda value: "null" if pd.isna(value) else escape(str(value)))

    if status_column and status_column in display.columns:
        status_class = {"Pass": "status-pass", "Review": "status-review", "Fail": "status-fail"}
        display[status_column] = display[status_column].map(
            lambda value: f'<span class="status-badge {status_class.get(value, "")}">{value}</span>'
        )

    for column in display.columns:
        if column != status_column:
            display[column] = display[column].map(
                lambda value: '<span class="null-value">null</span>' if value == "null" else value
            )

    html = display.to_html(index=False, border=0, escape=False, classes=table_class)
    st.markdown(f'<div class="professional-table-wrap">{html}</div>', unsafe_allow_html=True)


def toggle_panel(label, key, default=False):
    """Reliable open/close control used instead of st.expander."""
    state_key = f"_{key}_open"
    if state_key not in st.session_state:
        st.session_state[state_key] = default
    is_open = bool(st.session_state[state_key])
    arrow = "▴" if is_open else "▾"
    if st.button(f"{arrow}  {label}", key=f"toggle_{key}", width="stretch"):
        st.session_state[state_key] = not is_open
        st.rerun()
    return bool(st.session_state[state_key])


def explicit_share_within_positions(entries, upper_position=10):
    """Return explicit share for positions 1..upper_position without failing on empty/nullable subsets."""
    if entries.empty or "position" not in entries.columns or "is_explicit" not in entries.columns:
        return None

    positions = pd.to_numeric(entries["position"], errors="coerce")
    subset = entries.loc[positions.between(1, upper_position), "is_explicit"].dropna()
    if subset.empty:
        return None

    if pd.api.types.is_bool_dtype(subset.dtype) or str(subset.dtype) == "boolean":
        values = subset.astype("boolean")
    else:
        values = (
            subset.astype(str).str.strip().str.lower()
            .map({"true": True, "false": False, "1": True, "0": False})
            .dropna()
        )
        if values.empty:
            return None

    return float(values.astype(float).mean() * 100)


def fmt_pct(value, decimals=1):
    """Human-readable percent text for nullable metrics."""
    try:
        if value is None or pd.isna(value):
            return "N/A"
        return f"{float(value):.{decimals}f}%"
    except (TypeError, ValueError):
        return "N/A"



RANK_ORDER = ["1-5", "6-10", "11-20", "21-50"]


def safe_mode(series, default="N/A"):
    values = pd.Series(series).dropna()
    if values.empty:
        return default
    mode = values.mode()
    return str(mode.iloc[0]) if not mode.empty else str(values.iloc[0])


def snapshot_count(entries):
    key = "snapshot_id" if "snapshot_id" in entries.columns else "date"
    return int(entries[key].nunique()) if not entries.empty else 0



def recording_collaboration_share(recordings):
    if recordings.empty:
        return None
    if "is_collaboration" in recordings.columns:
        values = recordings["is_collaboration"].dropna()
        return float(values.astype(float).mean() * 100) if not values.empty else None
    if "n_collaborators" in recordings.columns:
        return float((pd.to_numeric(recordings["n_collaborators"], errors="coerce") > 1).mean() * 100)
    if "collaborators" in recordings.columns:
        return float(recordings["collaborators"].apply(lambda x: len(x) > 1 if isinstance(x, (list, tuple, set)) else False).mean() * 100)
    return None


def recording_avg_collaborators(recordings):
    if recordings.empty:
        return None
    if "n_collaborators" in recordings.columns:
        values = pd.to_numeric(recordings["n_collaborators"], errors="coerce").dropna()
        return float(values.mean()) if not values.empty else None
    if "collaborators" in recordings.columns:
        values = recordings["collaborators"].apply(lambda x: len(x) if isinstance(x, (list, tuple, set)) else np.nan).dropna()
        return float(values.mean()) if not values.empty else None
    return None


def artist_entry_subset(entries, artist):
    if "collaborators" not in entries.columns:
        return entries.iloc[0:0].copy()
    mask = entries["collaborators"].apply(
        lambda names: artist in names if isinstance(names, (list, tuple, set)) else False
    )
    return entries.loc[mask].copy()


def artist_profile_table(artists, entries, artist_credits):
    rows = []
    for artist in artists:
        a_entries = artist_entry_subset(entries, artist)
        a_credits = artist_credits[artist_credits["artist_name"] == artist]
        if a_entries.empty and a_credits.empty:
            continue
        proxy_count = len(canonical_recordings(a_entries)) if not a_entries.empty else 0
        rows.append({
            "Artist": artist,
            "Artist-credit appearances": int(len(a_credits)),
            "Artist-credit share (%)": round(len(a_credits) / max(len(artist_credits), 1) * 100, 2),
            "Recording proxies": int(proxy_count),
            "Best observed position": int(pd.to_numeric(a_entries["position"], errors="coerce").min()) if not a_entries.empty else np.nan,
            "Median position": round(float(pd.to_numeric(a_entries["position"], errors="coerce").median()), 1) if not a_entries.empty else np.nan,
            "Collab share (%)": round(float(a_entries["is_collaboration"].astype(float).mean() * 100), 2) if "is_collaboration" in a_entries.columns and not a_entries.empty else np.nan,
            "Explicit share (%)": round(float(a_entries["is_explicit"].astype(float).mean() * 100), 2) if "is_explicit" in a_entries.columns and not a_entries.empty else np.nan,
            "Primary release format": safe_mode(a_entries["album_type"]) if "album_type" in a_entries.columns else "N/A",
            "Nationality": classify(artist),
        })
    return pd.DataFrame(rows)


def format_duration(seconds):
    if seconds is None or pd.isna(seconds):
        return "N/A"
    seconds = int(round(float(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def ordered_bar_colors(count, scale=BAR_SCALE):
    """Return a quiet light-to-dark sequence for ordered magnitude bars.

    Charts remain readable on the warm-grey canvas while the largest values
    receive visual emphasis without pure-black marks or neon accents.
    """
    if count <= 0:
        return []
    if count == 1:
        return [scale[-2]]
    positions = np.linspace(0, len(scale) - 1, count)
    return [scale[int(round(pos))] for pos in positions]


def evidence_card(col, title, evidence, implication, question, accent=ATLANTIC_NAVY):
    col.markdown(
        f"""<div class="evidence-card" style="border-top-color:{accent};">
            <div class="evidence-title">{title}</div>
            <div class="evidence-label">Evidence</div>
            <div class="evidence-text">{evidence}</div>
            <div class="evidence-label">Observed implication</div>
            <div class="evidence-text">{implication}</div>
            <div class="evidence-label">Decision question</div>
            <div class="evidence-text">{question}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def render_data_quality(quality_report, validation_report):
    checks = pd.DataFrame(quality_report["checks"])

    q1, q2, q3, q4 = st.columns(4)
    q1.metric("Raw rows", f"{validation_report['n_rows_raw']:,}")
    q2.metric("Processed rows", f"{validation_report['n_rows_processed']:,}")
    q3.metric("Distinct dates", f"{validation_report['n_dates']:,}")
    q4.metric("Snapshots", f"{validation_report['n_snapshots']:,}")

    quality_labels = {
        "required_columns": "Required columns",
        "raw_row_count": "Source row count",
        "required_value_nulls": "Required-value completeness",
        "date_parsing": "Date parsing",
        "calendar_date_coverage": "Calendar date coverage",
        "multiple_snapshots_per_date": "Multiple snapshots on one date",
        "march_1_reconstruction": "March 1 reconstruction",
        "position_domain": "Chart-position validity",
        "snapshot_row_counts": "Snapshot completeness",
        "duplicate_snapshot_positions": "Duplicate chart positions",
        "missing_snapshot_positions": "Missing chart positions",
        "exact_source_duplicates": "Repeated source rows",
        "duplicate_recordings_within_snapshot": "Duplicate recordings within snapshot",
        "album_type_domain": "Release-format validity",
        "explicit_content_domain": "Explicit-content validity",
        "positive_duration": "Duration validity",
        "positive_total_tracks": "Release track-count validity",
        "popularity_bounds": "Popularity range",
        "artist_parsing": "Artist-credit parsing",
        "empty_collaborator_arrays": "Artist-credit completeness",
        "nationality_coverage": "Nationality coverage",
        "recording_metadata_stability": "Recording metadata changes",
        "title_collisions": "Song-title collisions",
        "fractional_artist_weights": "Fractional artist weights",
        "output_row_consistency": "Output reconciliation",
    }

    def quality_result(row: pd.Series) -> str:
        key = str(row["name"])
        value: Any = row["value"]
        if value is None or (isinstance(value, (list, tuple, set, dict)) and len(value) == 0) or (isinstance(value, str) and not value.strip()):
            return "null"
        if key == "required_columns": return "All required fields present"
        if key == "raw_row_count": return f"{int(value):,} rows"
        if key == "required_value_nulls": return "No missing required values" if value == 0 else f"{value} missing values"
        if key == "date_parsing": return "All dates parsed" if value == 0 else f"{value} invalid dates"
        if key == "calendar_date_coverage": return f"{len(value)} dates missing"
        if key == "multiple_snapshots_per_date": return ", ".join(f"{date}: {count} snapshots" for date, count in value.items())
        if key == "march_1_reconstruction": return f"{len(value)} complete Top-50 snapshots"
        if key == "position_domain": return "All positions valid" if value == 0 else f"{value} invalid positions"
        if key == "snapshot_row_counts": return "All snapshots contain 50 rows" if not value else str(value)
        if key == "duplicate_snapshot_positions": return "No duplicate positions" if value == 0 else f"{value} duplicates"
        if key == "missing_snapshot_positions": return "No missing positions" if not value else str(value)
        if key == "exact_source_duplicates": return f"{value} retained across separate snapshots"
        if key == "duplicate_recordings_within_snapshot": return "None detected" if value == 0 else str(value)
        if key in {"album_type_domain", "explicit_content_domain"}: return "All values valid" if not value else str(value)
        if key == "positive_duration": return "All durations valid" if value == 0 else f"{value} invalid durations"
        if key == "positive_total_tracks": return "All release track counts valid" if value == 0 else f"{value} invalid values"
        if key == "popularity_bounds": return "All values within 0-100" if value == 0 else f"{value} out-of-range values"
        if key == "artist_parsing": return "All artist credits parsed" if value == 0 else f"{value} parsing issues"
        if key == "empty_collaborator_arrays": return "None detected" if value == 0 else str(value)
        if key == "nationality_coverage": return f"{float(value):.2f}% unclassified"
        if key == "recording_metadata_stability":
            return (
                f"Song labels: {value.get('song', 0)} | Artist-credit sets: {value.get('credited_artist_set', 0)} | "
                f"Album types: {value.get('album_type', 0)} | Release track counts: {value.get('total_tracks', 0)} | "
                f"Explicit flags: {value.get('is_explicit', 0)}"
            )
        if key == "title_collisions": return f"{value} normalised titles"
        if key == "fractional_artist_weights": return "All chart entries reconcile to 1.0" if float(value) == 0 else str(value)
        if key == "output_row_consistency":
            return (
                f"Raw: {value.get('raw', 0):,} | Processed: {value.get('processed', 0):,} | "
                f"Artist credits: {value.get('artist_credits', 0):,} | Recordings: {value.get('recordings', 0):,}"
            )
        return str(value)

    quality_display = checks.copy()
    quality_display["Observed result"] = quality_display.apply(quality_result, axis=1)
    quality_display["Validation check"] = quality_display["name"].map(quality_labels).fillna(quality_display["name"])
    quality_display["Assessment"] = quality_display["status"].replace({"PASS": "Pass", "WARNING": "Review", "FAIL": "Fail"})
    quality_display["Interpretation"] = quality_display["detail"]
    render_static_table(
        quality_display[["Assessment", "Validation check", "Observed result", "Interpretation"]],
        table_class="professional-table quality-table",
        status_column="Assessment",
    )


CHART_FONT = "Segoe UI, Arial, sans-serif"


def plotly_traces(fig: go.Figure) -> tuple[Any, ...]:
    """Return Plotly traces with a stable type for static analysis."""
    return cast(tuple[Any, ...], fig.data)


def style_fig(fig, height=None, legend=True, margin=None):
    """Single source of truth for chart styling -- every chart in the
    dashboard should be passed through this so typography, background, and
    spacing stay consistent across all 20+ charts."""
    layout_kwargs = dict(
        plot_bgcolor="#F5F1E7", paper_bgcolor="#F5F1E7",
        font=dict(color="#242422", size=12.5, family=CHART_FONT),
        legend=dict(font=dict(size=11, color="#333330", family=CHART_FONT)),
        hoverlabel=dict(
            bgcolor="#FAF7EF", font_color="#171715", font_size=12,
            font_family=CHART_FONT, bordercolor="#B8B09C"
        ),
        margin=margin or dict(l=10, r=10, t=48, b=10),
        showlegend=legend,
        hovermode="closest",
    )
    # Only style the title font if the figure actually has title text set.
    # Confirmed via testing: in Plotly 6.x, setting title_font on a figure
    # with no title.text renders the literal string "undefined" where the
    # title would go (a real Plotly rendering bug, not a Streamlit one --
    # reproduced with a minimal isolated repro). Charts that rely on an
    # external st.markdown() heading instead of a Plotly-native title (like
    # the concentration curve) must not have title_font applied.
    has_title = bool(fig.layout.title and fig.layout.title.text)
    if has_title:
        layout_kwargs["title_font"] = dict(size=15, color=ATLANTIC_NAVY, family=CHART_FONT)
    fig.update_layout(**layout_kwargs)
    if height:
        fig.update_layout(height=height)
    fig.update_xaxes(showgrid=True, gridcolor="#D8D1C1", zerolinecolor="#C3BAA8", tickfont=dict(color="#615F54"), title_font=dict(color="#666354"))
    fig.update_yaxes(showgrid=True, gridcolor="#D8D1C1", zerolinecolor="#C3BAA8", tickfont=dict(color="#615F54"), title_font=dict(color="#666354"))
    for trace in plotly_traces(fig):
        if getattr(trace, "type", None) == "bar":
            trace.update(marker_line_color="#7E8068", marker_line_width=0.35, opacity=0.94)
    return fig


DONUT_HOLE = 0.62
DONUT_HEIGHT = 380


def style_donut(fig, height=DONUT_HEIGHT):
    """Consistent treatment for every pie/donut chart: fixed height so it
    matches whatever bar/line chart sits next to it in the same row, a
    horizontal legend below the chart (rather than Plotly's default
    vertical side legend, which leaves a lot of dead space in a wide
    column), and tight margins so the donut fills its card properly."""
    fig.update_traces(textposition="inside", textfont=dict(size=12, family=CHART_FONT))
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5,
                     font=dict(size=11.5, family=CHART_FONT)),
        margin=dict(l=20, r=20, t=48, b=10),
    )
    return style_fig(fig, height=height)


def donut_center(fig, value_pct, label):
    """Adds a centered KPI-style annotation inside the donut hole, tying the
    chart back to the headline number it illustrates."""
    fig.add_annotation(
        text=f"<b>{value_pct:.0f}%</b><br><span style='font-size:11px;color:#62625E'>{label}</span>",
        showarrow=False, font=dict(size=20, color=ATLANTIC_NAVY, family=CHART_FONT),
    )
    return fig


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(
    show_spinner="Loading UK Top 50 data...",
    persist="disk",
    max_entries=2,
)
def load_data(data_version):
    """Load the cleaned analytical base once and persist it across reruns.

    data_version is deliberately part of the cache key so replacing the source
    CSV invalidates the cached result automatically.
    """
    clean_df, exploded, report = run_pipeline(str(DATA_PATH))
    exploded = exploded.copy()
    exploded["nationality"] = exploded["artist_name"].apply(classify)
    return clean_df, exploded, report


@st.cache_data(show_spinner="Validating source data...", persist="disk", max_entries=2)
def load_quality_report(data_version):
    """Heavy source validation is loaded only when the Health section is opened."""
    clean_df, exploded, _ = load_data(data_version)
    return validate_all(
        load_raw(str(DATA_PATH)),
        clean_df,
        exploded,
        canonical_recordings(clean_df),
    )


@st.cache_data(show_spinner=False, persist="disk", max_entries=2)
def full_recording_count(data_version):
    """Dataset-wide recording-proxy count for provenance/footer display."""
    clean_df, _, _ = load_data(data_version)
    return int(len(canonical_recordings(clean_df)))


df_full, exploded_full, validation_report = load_data(DATA_VERSION)
FULL_RECORDING_COUNT = full_recording_count(DATA_VERSION)

# ---------------------------------------------------------------------------
# Sidebar — Filters
# ---------------------------------------------------------------------------


st.sidebar.markdown(
    """
    <div class="sidebar-brand">
        <div class="sidebar-kicker">Portfolio Case Study</div>
        <div class="sidebar-title">UK Top 50 Playlist</div>
        <div class="sidebar-subtitle">Music Market Intelligence</div>
        <div class="sidebar-context">
            Entertainment-category Data Analyst project<br>
            Dataset supplied by Unified Mentor Pvt. Ltd.<br>
            Atlantic Recording Corporation used as the business scenario
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.markdown("#### Market Filters")

min_date, max_date = (
    df_full["date"].min().date(),
    df_full["date"].max().date(),
)

date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

collab_toggle = st.sidebar.radio(
    "Solo vs. Collaboration",
    options=["All chart entries", "Solo entries only", "Collaborative entries only"],
    index=0,
)

album_types = sorted(df_full["album_type"].dropna().astype(str).unique())
selected_album_types = st.sidebar.pills(
    "Release Type",
    options=album_types,
    selection_mode="multi",
    default=None,
    format_func=lambda value: str(value).title(),
    key="release_type_filter",
    help="Select one or more formats. Leave all unselected to include every release type.",
    width="stretch",
) or []

st.sidebar.markdown("---")

# ---------------------------------------------------------------------------
# Apply filters — cached by the small, hashable filter state
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False, max_entries=32)
def build_filtered_views(start_iso, end_iso, collaboration_mode, album_types_key, data_version):
    start = pd.Timestamp(start_iso).date()
    end = pd.Timestamp(end_iso).date()

    mask = (df_full["date"].dt.date >= start) & (df_full["date"].dt.date <= end)
    filtered = df_full.loc[mask].copy()

    if collaboration_mode == "Solo entries only":
        filtered = filtered.loc[~filtered["is_collaboration"]].copy()
    elif collaboration_mode == "Collaborative entries only":
        filtered = filtered.loc[filtered["is_collaboration"]].copy()

    if album_types_key:
        filtered = filtered.loc[filtered["album_type"].isin(album_types_key)].copy()

    credits = filtered.explode("collaborators").rename(columns={"collaborators": "artist_name"})
    credits = credits.loc[credits["artist_name"].notna()].reset_index(drop=True).copy()
    credits["artist_credit_weight"] = 1.0
    credits["fractional_entry_weight"] = 1.0 / credits["n_collaborators"].clip(lower=1)

    # Reuse the already-classified full artist layer instead of calling classify()
    # for every artist on every widget interaction.
    nationality_map = (
        exploded_full.drop_duplicates("artist_name")
        .set_index("artist_name")["nationality"]
        .to_dict()
    )
    credits["nationality"] = credits["artist_name"].map(nationality_map).fillna(UNK)

    recording_view = canonical_recordings(filtered).copy()
    snapshot_view = an.snapshot_market_metrics(credits)
    return filtered, credits, recording_view, snapshot_view


df, exploded, recordings, snapshot_health = build_filtered_views(
    str(start_date),
    str(end_date),
    collab_toggle,
    tuple(selected_album_types),
    DATA_VERSION,
)

if len(df) == 0:
    st.warning("No playlist entries match the selected filters. Try widening your date range or filters.")
    st.stop()

filters_active = (
    (start_date, end_date) != (min_date, max_date)
    or collab_toggle != "All chart entries"
    or bool(selected_album_types)
)
# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hero-shell">
    <div class="hero-eyebrow">UK MUSIC MARKET · PORTFOLIO INTELLIGENCE</div>
    <div class="hero-title">UK Top 50 Playlist</div>
    <div class="hero-subtitle">Market Structure, Artist Landscape & Release Intelligence</div>
    <div class="hero-description">
        Entertainment analytics case study · Dataset supplied by Unified Mentor Pvt. Ltd. · Atlantic Recording Corporation used as a business scenario
    </div>
    <div class="hero-rule"></div>
    <div class="hero-chips">
        <span class="hero-chip">A&amp;R Landscape</span>
        <span class="hero-chip">Collaboration</span>
        <span class="hero-chip">Content Mix</span>
        <span class="hero-chip">Release Strategy</span>
        <span class="hero-chip">Market Health</span>
    </div>
</div>
""", unsafe_allow_html=True)

if filters_active:
    st.caption("🔎 Global filters active — date, collaboration, and release-type filters apply across the dashboard.")

# ---------------------------------------------------------------------------
# Dashboard navigation
# ---------------------------------------------------------------------------

DASHBOARD_SECTIONS = [
    "Overview",
    "Artists",
    "Collaboration",
    "Content",
    "Formats",
    "Duration",
    "Health",
    "Strategy",
]

active_view = st.segmented_control(
    "Dashboard section",
    DASHBOARD_SECTIONS,
    selection_mode="single",
    default="Overview",
    key="dashboard_section",
    label_visibility="collapsed",
    width="stretch",
) or "Overview"

VIEW_DESCRIPTIONS = {
    "Overview": "Executive market summary",
    "Artists": "Artist presence, concentration & nationality",
    "Collaboration": "Partnership structure & recurring co-credits",
    "Content": "Explicit-content mix by rank and time",
    "Formats": "Release-format footprint & recording proxies",
    "Duration": "Runtime distribution & popularity context",
    "Health": "Snapshot diversity, concentration & data quality",
    "Strategy": "Evidence-led decision questions",
}
st.markdown(
    f'''<div class="active-view-strip">
        <span class="label">Current view</span>
        <span class="value">{active_view}</span>
        <span class="desc">{VIEW_DESCRIPTIONS[active_view]}</span>
    </div>''',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

conc = an.artist_concentration_index(exploded, top_n=5)
dom_intl = an.domestic_vs_international(exploded)
es_top = an.explicit_share(df)
explicit_top10_pct = explicit_share_within_positions(df, 10)
current_snapshot_count = snapshot_count(df)
current_recording_count = len(recordings)
recording_collab_pct = recording_collaboration_share(recordings)
recording_avg_collabs = recording_avg_collaborators(recordings)

# Scale: explain what the filtered market contains before interpreting it.
scale_row = st.columns(4)
kpi_card(scale_row[0], "#", "Chart entries", f"{len(df):,}", ATLANTIC_NAVY,
         "One playlist position observed in one reconstructed snapshot after the active global filters.")
kpi_card(scale_row[1], "▦", "Snapshots in view", f"{current_snapshot_count:,}", ATLANTIC_NAVY,
         "Distinct reconstructed snapshot IDs represented after global filters. Filtered snapshots may contain fewer than 50 visible entries.")
kpi_card(scale_row[2], "A", "Credited artists", f"{exploded['artist_name'].nunique():,}", ATLANTIC_TEAL,
         "Distinct credited artists represented in the filtered artist-credit layer.")
kpi_card(scale_row[3], "♪", "Recording proxies", f"{current_recording_count:,}", ATLANTIC_GOLD,
         "Dataset-local recording identities based on normalized title plus exact duration; not ISRCs or global recording IDs.")

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

# Structure: market composition and concentration.
structure_row = st.columns(4)
kpi_card(structure_row[0], "★", "Top-5 artist-credit share", f"{conc['top_n_share_pct']:.1f}%", ATLANTIC_RED,
         "Share of period-wide full artist-credit appearances held by the five most frequent credited artists.")
kpi_card(structure_row[1], "↔", "Collaborative entries", f"{an.collaboration_ratio(df)*100:.1f}%", ATLANTIC_TEAL,
         "Share of chart entries with more than one credited artist.")
kpi_card(structure_row[2], "18+", "Explicit entries", f"{es_top['Explicit']:.1f}%", ATLANTIC_GOLD,
         "Share of chart-entry observations marked explicit in the supplied data.")
kpi_card(structure_row[3], "UK", "UK / domestic artist-credit share", f"{dom_intl.get('UK / Domestic', 0):.1f}%", ATLANTIC_NAVY,
         "Share of full artist credits manually classified as UK / Domestic; unclassified artists remain unclassified.")


# =============================================================================
# SECTION 0: OVERVIEW
# =============================================================================
if active_view == "Overview":
    section_narrative(
        "An executive read of the filtered UK Top 50 market. The dashboard separates chart-entry, artist-credit, "
        "recording-proxy, and snapshot measures so repeated chart appearances are not mistaken for unique tracks or typical daily structure."
    )

    mean_effective = snapshot_health["effective_number_of_artists"].mean() if not snapshot_health.empty else np.nan
    mean_unique = snapshot_health["unique_artists"].mean() if not snapshot_health.empty else np.nan
    median_hhi = snapshot_health["fractional_hhi"].median() if not snapshot_health.empty else np.nan

    s1, s2, s3 = st.columns(3)
    finding_card(
        s1, "🏆", "Artist concentration",
        f"Top-5 artists account for <b>{conc['top_n_share_pct']:.1f}%</b> of period-wide full artist-credit appearances "
        f"(HHI <b>{conc['hhi']:.0f}</b>). This is a long-run persistence measure, not a typical-snapshot HHI.",
        ATLANTIC_NAVY,
    )
    finding_card(
        s2, "▦", "Typical snapshot",
        f"A filtered snapshot averages <b>{mean_unique:.1f}</b> unique credited artists and "
        f"<b>{mean_effective:.1f}</b> effective artists. Median fractional snapshot HHI is <b>{median_hhi:.0f}</b>.",
        ATLANTIC_TEAL,
    )
    finding_card(
        s3, "♪", "Recording layer",
        f"The current market view contains <b>{current_recording_count:,}</b> dataset-local recording proxies across "
        f"<b>{len(df):,}</b> chart entries. Recording proxies use the project's validated title-duration identity rule.",
        ATLANTIC_GOLD,
    )

    st.markdown("#### Structure by chart position")
    st.caption("Four observed market signals compared on the same exclusive rank bands. Percentages are descriptive, not causal effects.")
    by_rank_ov = an.domestic_vs_international_by_rank(df, exploded)
    collab_by_rank_ov = an.collab_by_rank_group(df)
    explicit_by_rank_ov = an.explicit_by_rank(df)
    release_by_rank_ov = an.release_format_by_rank(df)

    rank_profile = pd.DataFrame(index=RANK_ORDER)
    rank_profile["Collaborative entries"] = collab_by_rank_ov.reindex(RANK_ORDER)
    rank_profile["Explicit entries"] = explicit_by_rank_ov.reindex(RANK_ORDER)
    rank_profile["International artist-credit share"] = by_rank_ov.get(INTL, pd.Series(dtype=float)).reindex(RANK_ORDER)
    rank_profile["Single-format entries"] = (
        release_by_rank_ov["single"].reindex(RANK_ORDER)
        if "single" in release_by_rank_ov.columns else np.nan
    )
    rank_long = rank_profile.rename_axis("Rank band").reset_index().melt(
        id_vars="Rank band", var_name="Signal", value_name="Share (%)"
    )
    fig_rank = px.line(
        rank_long, x="Rank band", y="Share (%)", color="Signal", markers=True,
        category_orders={"Rank band": RANK_ORDER}, color_discrete_sequence=PALETTE,
    )
    fig_rank.update_traces(hovertemplate="<b>%{fullData.name}</b><br>Rank band: %{x}<br>Share: %{y:.2f}%<extra></extra>")
    fig_rank.update_layout(
        title=None,
        legend=dict(
            orientation="h", yanchor="bottom", y=1.08,
            xanchor="center", x=0.5, title_text="",
            bgcolor="rgba(0,0,0,0)"
        ),
        margin=dict(l=10, r=10, t=56, b=10),
    )
    st.plotly_chart(style_fig(fig_rank, height=345), width="stretch")

    st.markdown('<div class="editorial-section-title">Analytical units</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="grain-grid">
            <div class="grain-card">
                <div class="grain-card-title">Chart Entries</div>
                <div class="grain-card-text">Rank · content · release format</div>
            </div>
            <div class="grain-card">
                <div class="grain-card-title">Artist Credits</div>
                <div class="grain-card-text">Dominance · nationality · collaboration</div>
            </div>
            <div class="grain-card">
                <div class="grain-card-title">Recording Proxies</div>
                <div class="grain-card-text">Track-level comparisons</div>
            </div>
            <div class="grain-card">
                <div class="grain-card-title">Snapshots</div>
                <div class="grain-card-text">Diversity · concentration</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if toggle_panel("How measures are defined", "measure_definitions"):
        with st.container(border=True):
            st.markdown(
                """
                **Chart entry** — one playlist position observed in one reconstructed Top-50 snapshot.
                **Artist credit** — one credited artist attached to a chart entry; collaborations contribute multiple credits.
                **Recording proxy** — dataset-local recording identity based on normalized title plus exact duration; it is not an ISRC or global recording ID.
                **Snapshot** — one reconstructed 50-position chart state. Snapshot diversity and HHI are calculated on comparable Top-50 states.

                **Artist concentration (HHI)** — measures how concentrated artist presence is. Lower values mean artist presence is more distributed; higher values mean a smaller group accounts for more of the chart.

                **Snapshot diversity** — measures both how many artists appear and how evenly chart presence is distributed within each reconstructed Top-50 snapshot.

                **Effective artists** — translates diversity into the equivalent number of equally represented artists. Across this dataset the average snapshot is equivalent to about **37.7 equally represented artists**.

                Exact formulas and weighting rules are documented in `docs/metric_methodology.md`.

                **Legacy measures** — the earlier Diversity Score and custom Content Variety Index are retired from headline reporting because the former changes with observation-window length and the latter combines unlike dimensions into a custom composite. Snapshot unique artists, Shannon diversity, effective artist count, and HHI are used instead.
                """
            )

# =============================================================================
# SECTION 1: ARTISTS
# =============================================================================
if active_view == "Artists":
    section_narrative(
        "A&R-oriented artist intelligence: long-run artist-credit presence, snapshot concentration, nationality mix, and optional artist-level drill-down."
    )

    artist_options = sorted(exploded["artist_name"].dropna().unique())
    if "artist_comparison_main" in st.session_state:
        current_artist_selection = st.session_state.get("artist_comparison_main") or []
        st.session_state["artist_comparison_main"] = [
            artist for artist in current_artist_selection if artist in artist_options
        ]

    selected_artists = st.multiselect(
        "Artist comparison",
        options=artist_options,
        key="artist_comparison_main",
        placeholder="Search and select artists",
        max_selections=6,
        help=(
            "Select one artist for a detailed intelligence profile or multiple "
            "artists for side-by-side comparison. This control affects only "
            "the Artists section."
        ),
    )

    if selected_artists:
        st.caption(
            f"Comparing {len(selected_artists)} selected artist"
            f"{'s' if len(selected_artists) != 1 else ''}."
        )

    if selected_artists:
        profiles = artist_profile_table(selected_artists, df, exploded)
        if len(profiles) == 1:
            row = profiles.iloc[0]
            st.markdown(f"#### Artist Intelligence · {row['Artist']}")
            a1, a2, a3, a4 = st.columns(4)
            a1.metric("Artist-credit appearances", f"{int(row['Artist-credit appearances']):,}")
            a2.metric("Recording proxies", f"{int(row['Recording proxies']):,}")
            a3.metric("Best observed position", f"#{int(row['Best observed position'])}")
            a4.metric("Median position", f"{row['Median position']:.1f}")
            a5, a6, a7, a8 = st.columns(4)
            a5.metric("Credit share", f"{row['Artist-credit share (%)']:.2f}%")
            a6.metric("Collab share", f"{row['Collab share (%)']:.1f}%")
            a7.metric("Explicit share", f"{row['Explicit share (%)']:.1f}%")
            a8.metric("Nationality", row["Nationality"])

            artist_name = row["Artist"]
            artist_credits = exploded[exploded["artist_name"] == artist_name].copy()
            artist_entries = artist_entry_subset(df, artist_name)
            c1, c2 = st.columns([3, 2])
            with c1:
                trend = (
                    artist_credits.set_index("date").resample("ME").size().rename("appearances").reset_index()
                    if not artist_credits.empty else pd.DataFrame(columns=["date", "appearances"])
                )
                fig_artist_trend = px.line(
                    trend, x="date", y="appearances", markers=True,
                    color_discrete_sequence=[ATLANTIC_RED], title="Monthly Artist-Credit Appearances",
                )
                fig_artist_trend.update_traces(hovertemplate="<b>%{x|%b %Y}</b><br>Appearances: %{y:,.0f}<extra></extra>")
                st.plotly_chart(style_fig(fig_artist_trend, legend=False, height=360), width="stretch")
            with c2:
                fmt = (artist_entries["album_type"].value_counts(normalize=True) * 100).round(2)
                fig_artist_fmt = px.pie(
                    values=fmt.values, names=[str(x).title() for x in fmt.index], hole=DONUT_HOLE,
                    color_discrete_sequence=PALETTE,
                )
                fig_artist_fmt.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>Share: %{value:.2f}%<extra></extra>")
                fig_artist_fmt.update_layout(title="Observed Release Mix")
                st.plotly_chart(style_donut(fig_artist_fmt, height=360), width="stretch")
        else:
            st.markdown("#### Selected Artist Comparison")
            st.caption("Comparison is scoped to this tab; market-wide visuals elsewhere remain unchanged.")
            show_cols = [
                "Artist", "Artist-credit appearances", "Artist-credit share (%)", "Recording proxies",
                "Best observed position", "Median position", "Collab share (%)", "Explicit share (%)", "Nationality"
            ]
            artist_table = profiles[show_cols].rename(columns={
                "Artist-credit appearances": "Appearances",
                "Artist-credit share (%)": "Credit share",
                "Best observed position": "Best rank",
                "Median position": "Median rank",
                "Collab share (%)": "Collaboration",
                "Explicit share (%)": "Explicit",
            })
            render_static_table(
                artist_table,
                table_class="professional-table artist-table",
                formats={
                    "Appearances": lambda v: f"{int(v):,}",
                    "Credit share": lambda v: f"{float(v):.2f}%",
                    "Recording proxies": lambda v: f"{int(v):,}",
                    "Best rank": lambda v: f"#{int(v)}",
                    "Median rank": lambda v: f"{float(v):.1f}",
                    "Collaboration": lambda v: f"{float(v):.1f}%",
                    "Explicit": lambda v: f"{float(v):.1f}%",
                },
            )
            fig_selected = px.bar(
                profiles.sort_values("Artist-credit appearances"), x="Artist-credit appearances", y="Artist",
                orientation="h", color_discrete_sequence=[ATLANTIC_GOLD],
                custom_data=["Artist-credit share (%)", "Recording proxies", "Best observed position"],
                title="Selected Artist Presence",
            )
            fig_selected.update_layout(showlegend=False, height=max(340, len(profiles) * 42))
            fig_selected.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>Artist-credit appearances: %{x:,.0f}<br>"
                    "Credit share: %{customdata[0]:.2f}%<br>Recording proxies: %{customdata[1]:,.0f}<br>"
                    "Best observed position: #%{customdata[2]:.0f}<extra></extra>"
                )
            )
            st.plotly_chart(style_fig(fig_selected, legend=False), width="stretch")

    insight_card(
        "🏆", "Market concentration read",
        f"Top-5 artists account for <b>{conc['top_n_share_pct']:.1f}%</b> of period-wide full artist-credit appearances. "
        f"Median fractional snapshot HHI is <b>{snapshot_health['fractional_hhi'].median():.0f}</b>; the measures answer different questions.",
        ATLANTIC_NAVY,
    )

    left, right = st.columns([2, 1])
    with left:
        n_top = st.slider("Show top N artists", 5, 40, 15, key="dom_n")
        top_artists = an.top_dominating_artists(exploded, n_top).sort_values()
        fig = px.bar(
            top_artists, orientation="h",
            labels={"value": "Artist-credit appearances", "artist_name": "Artist"},
            color_discrete_sequence=[ATLANTIC_GOLD],
        )
        bar_colors = ordered_bar_colors(len(top_artists), BAR_SCALE)
        fig.update_traces(marker_color=bar_colors, marker_line_width=0)
        fig.update_layout(showlegend=False, title="Artist Dominance Leaderboard")
        fig.update_traces(hovertemplate="<b>%{y}</b><br>Artist-credit appearances: %{x:,.0f}<extra></extra>")
        fig.update_layout(height=max(450, n_top * 24))
        st.plotly_chart(style_fig(fig, legend=False), width="stretch")
    with right:
        st.metric("Top-5 credit share", f"{conc['top_n_share_pct']:.1f}%")
        st.metric("Period full-credit HHI", f"{conc['hhi']:.0f}")
        st.metric("Mean effective artists / snapshot", f"{snapshot_health['effective_number_of_artists'].mean():.1f}")
        st.metric("Mean unique artists / snapshot", f"{snapshot_health['unique_artists'].mean():.1f}")
        st.caption("Period-wide credit concentration and snapshot concentration are intentionally reported separately.")

    st.markdown("#### Artist Landscape Treemap")
    tm_data = an.top_dominating_artists(exploded, 30).reset_index()
    tm_data.columns = ["artist_name", "appearances"]
    tm_data["artist_credit_share_pct"] = tm_data["appearances"] / max(len(exploded), 1) * 100
    fig_tm = px.treemap(
        tm_data, path=["artist_name"], values="appearances", color="appearances",
        color_continuous_scale=TREEMAP_SCALE, custom_data=["artist_credit_share_pct"],
    )
    fig_tm.update_layout(coloraxis_showscale=False, title="Top 30 Artists by Artist-Credit Appearances")
    fig_tm.update_traces(
        textinfo="label+value", textfont_size=13,
        hovertemplate="<b>%{label}</b><br>Artist-credit appearances: %{value:,.0f}<br>Credit share: %{customdata[0]:.2f}%<extra></extra>",
        marker_line_color="#EEE9DC", marker_line_width=1.2,
    )
    st.plotly_chart(style_fig(fig_tm, height=450, margin=dict(l=4, r=4, t=48, b=4)), width="stretch")

    st.markdown("#### UK / Domestic vs. International Artist Credits")
    c1, c2 = st.columns(2)
    with c1:
        pie = px.pie(
            values=dom_intl.reindex([UK, INTL, UNK]).fillna(0).values,
            names=[UK, INTL, UNK], color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_GOLD, ATLANTIC_GREY], hole=DONUT_HOLE,
        )
        pie.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>Artist-credit share: %{value:.2f}%<extra></extra>")
        donut_center(pie, dom_intl.get(UK, 0), "UK / Domestic")
        pie.update_layout(title="Period-Wide Artist-Credit Share")
        st.plotly_chart(style_donut(pie), width="stretch")
    with c2:
        by_rank = an.domestic_vs_international_by_rank(df, exploded)
        fig2 = px.bar(
            by_rank[[UK, INTL]], barmode="group", color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_GOLD],
            labels={"value": "Share (%)", "rank_band": "Exclusive rank band"},
        )
        fig2.update_layout(title="Nationality Mix by Rank Band")
        for trace in plotly_traces(fig2):
            trace.update(hovertemplate=f"<b>{trace.name}</b><br>Rank band: %{{x}}<br>Artist-credit share: %{{y:.2f}}%<extra></extra>")
        st.plotly_chart(style_fig(fig2, height=DONUT_HEIGHT), width="stretch")

# =============================================================================
# SECTION 2: COLLABORATION
# =============================================================================
if active_view == "Collaboration":
    section_narrative(
        "Separate repeated chart-entry collaboration from recording-proxy collaboration, then inspect where collaboration appears and which partnerships recur."
    )
    cbr = an.collab_by_rank_group(df)
    sc = an.solo_vs_collab(df)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Collaborative entries", f"{an.collaboration_ratio(df)*100:.2f}%")
    c2.metric("Collaborative recording proxies", fmt_pct(recording_collab_pct, 2))
    c3.metric("Avg credited artists / entry", f"{an.avg_collaborators_per_entry(df):.2f}")
    c4.metric("Avg credited artists / proxy", f"{recording_avg_collabs:.2f}" if recording_avg_collabs is not None else "N/A")

    left, right = st.columns(2)
    with left:
        fig = px.bar(
            cbr.reindex(RANK_ORDER), labels={"value": "Collaboration share (%)", "rank_band": "Exclusive rank band"},
            color_discrete_sequence=[ATLANTIC_TEAL],
        )
        fig.update_layout(showlegend=False, title="Collaboration Share by Rank Band")
        fig.update_traces(hovertemplate="<b>Rank band %{x}</b><br>Collaborative entries: %{y:.2f}%<extra></extra>")
        st.plotly_chart(style_fig(fig, legend=False, height=DONUT_HEIGHT), width="stretch")
    with right:
        collab_order = ["Solo chart entries", "Collaborative chart entries"]
        sc_display = sc.reindex(collab_order).dropna()
        sc_fig = px.pie(
            values=sc_display.values, names=sc_display.index,
            color=sc_display.index, color_discrete_map=COLLAB_COLORS,
            hole=DONUT_HOLE,
        )
        sc_fig.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>Chart entries: %{value:,.0f}<br>Share: %{percent}<extra></extra>")
        donut_center(sc_fig, an.collaboration_ratio(df) * 100, "Collaboration")
        sc_fig.update_layout(title="Entry-Level Collaboration Mix")
        st.plotly_chart(style_donut(sc_fig), width="stretch")

    st.markdown("#### Recurring Artist Partnerships")
    st.caption("Bars use co-credited chart-entry appearances; hover also reports distinct collaborative recording proxies.")
    edges = an.collaboration_edges(df)
    if len(edges) == 0:
        st.info("No collaborations found in the current filter selection.")
    else:
        pair_max = min(40, len(edges))
        if pair_max <= 5:
            top_n_pairs = pair_max
            st.caption(f"Showing all {top_n_pairs} available collaborator pair{'s' if top_n_pairs != 1 else ''}.")
        else:
            top_n_pairs = st.slider("Number of top pairs", 5, pair_max, min(15, pair_max), key="pairs_n")
        top_edges = edges.head(top_n_pairs).copy()
        top_edges["pair_label"] = top_edges["artist_a"] + "  ×  " + top_edges["artist_b"]
        top_edges = top_edges.sort_values("co_credited_appearances")
        fig_pairs = px.bar(
            top_edges, x="co_credited_appearances", y="pair_label", orientation="h",
            color_discrete_sequence=[ATLANTIC_TEAL],
            custom_data=["unique_collaborative_tracks"],
            labels={"co_credited_appearances": "Co-credited chart-entry appearances", "pair_label": ""},
        )
        pair_colors = ordered_bar_colors(len(top_edges), BAR_SCALE)
        fig_pairs.update_layout(showlegend=False, height=max(360, top_n_pairs * 30), title="Top Collaborator Pairs")
        fig_pairs.update_traces(
            marker_color=pair_colors, marker_line_width=0,
            hovertemplate="<b>%{y}</b><br>Co-credited appearances: %{x:,.0f}<br>Distinct recording proxies: %{customdata[0]:,.0f}<extra></extra>"
        )
        st.plotly_chart(style_fig(fig_pairs, legend=False), width="stretch")


# =============================================================================
# SECTION 3: CONTENT
# =============================================================================
if active_view == "Content":
    section_narrative(
        "Content mix is shown at chart-entry level, with exclusive rank bands and quarter-by-quarter context so aggregate percentages do not hide structural variation."
    )
    ebr = an.explicit_by_rank(df).reindex(RANK_ORDER)
    lower_band = ebr.get("21-50", np.nan)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Explicit entries", f"{es_top['Explicit']:.2f}%")
    c2.metric("Clean entries", f"{es_top['Clean']:.2f}%")
    c3.metric("Explicit share · positions 1–10", fmt_pct(explicit_top10_pct, 2))
    c4.metric("Explicit share · positions 21–50", fmt_pct(lower_band, 2))

    left, right = st.columns(2)
    with left:
        fig_rank_content = px.bar(
            ebr, labels={"value": "Explicit share (%)", "rank_band": "Exclusive rank band"},
            color_discrete_sequence=[ATLANTIC_RED],
        )
        fig_rank_content.update_layout(showlegend=False, title="Explicit Share by Rank Band")
        fig_rank_content.update_traces(hovertemplate="<b>Rank band %{x}</b><br>Explicit share: %{y:.2f}%<extra></extra>")
        st.plotly_chart(style_fig(fig_rank_content, legend=False, height=360), width="stretch")
    with right:
        es = an.explicit_share(df)
        fig_mix = px.pie(values=es.values, names=es.index, color_discrete_sequence=[ATLANTIC_RED, ATLANTIC_TEAL], hole=DONUT_HOLE)
        fig_mix.update_traces(textinfo="percent", hovertemplate="<b>%{label}</b><br>Share: %{value:.2f}%<extra></extra>")
        donut_center(fig_mix, es["Explicit"], "Explicit")
        fig_mix.update_layout(title="Explicit vs. Clean")
        st.plotly_chart(style_donut(fig_mix, height=360), width="stretch")

    eot = an.explicit_over_time(df)
    fig_time = px.line(eot, markers=True, labels={"value": "Explicit share (%)", "date": "Month"}, color_discrete_sequence=[ATLANTIC_RED])
    fig_time.update_layout(showlegend=False, title="Explicit Share Over Time")
    fig_time.update_traces(hovertemplate="<b>%{x|%b %Y}</b><br>Explicit share: %{y:.2f}%<extra></extra>")
    st.plotly_chart(style_fig(fig_time, legend=False, height=340), width="stretch")

    st.markdown("#### Rank Band × Quarter Heatmap")
    rank_col = "rank_band" if "rank_band" in df.columns else "rank_group"
    heat_src = df[["date", rank_col, "is_explicit"]].dropna().copy()
    heat_src["Quarter"] = heat_src["date"].dt.to_period("Q").astype(str)
    heat = (
        heat_src.groupby([rank_col, "Quarter"], observed=True)["is_explicit"].mean().mul(100).unstack("Quarter")
        .reindex(RANK_ORDER)
    )
    counts = heat_src.groupby([rank_col, "Quarter"], observed=True).size().unstack("Quarter", fill_value=0).reindex(index=RANK_ORDER, columns=heat.columns, fill_value=0)
    if heat.shape[1] >= 2:
        change = heat.diff(axis=1)
        change_text = change.apply(lambda col: col.map(lambda x: "Baseline" if pd.isna(x) else f"{x:+.1f} pp"))
        custom = np.empty((heat.shape[0], heat.shape[1], 2), dtype=object)
        custom[:, :, 0] = counts.values
        custom[:, :, 1] = change_text.values
        fig_heat = go.Figure(go.Heatmap(
            z=heat.values, x=heat.columns, y=heat.index, customdata=custom,
            zmin=0, zmax=100, colorscale=HEATMAP_SCALE,
            colorbar=dict(title="Explicit %", outlinecolor="#AAA18C", outlinewidth=1, tickfont=dict(color="#5F5C50")),
            hovertemplate=(
                "<b>Rank band: %{y}</b><br>Quarter: %{x}<br>Explicit share: %{z:.2f}%<br>"
                "Chart entries: %{customdata[0]:,.0f}<br>Change vs previous quarter: %{customdata[1]}<extra></extra>"
            ),
        ))
        fig_heat.update_layout(title="Explicit Share by Rank Band and Quarter", height=340, xaxis_title="Quarter", yaxis_title="Exclusive rank band")
        st.plotly_chart(style_fig(fig_heat, legend=False), width="stretch")
    else:
        st.info("Select a date range spanning at least two quarters to build the heatmap.")

# =============================================================================
# SECTION 4: FORMATS
# =============================================================================
if active_view == "Formats":
    section_narrative(
        "Release strategy separates chart-entry footprint from recording-proxy composition. A release with many charting tracks can dominate entry counts without representing the same number of unique recordings."
    )
    ats = an.album_type_share(df)
    rfr = an.release_format_by_rank(df)
    rec_format = (
        recordings["album_type"].value_counts(normalize=True).mul(100).round(2)
        if "album_type" in recordings.columns and not recordings.empty else pd.Series(dtype=float)
    )
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Album share · entries", f"{ats.get('album', 0):.2f}%")
    f2.metric("Single share · entries", f"{ats.get('single', 0):.2f}%")
    f3.metric("Compilation share · entries", f"{ats.get('compilation', 0):.2f}%")
    f4.metric("Recording proxies", f"{len(recordings):,}")

    format_names = sorted(set(ats.index.astype(str)).union(set(rec_format.index.astype(str))))
    format_compare = pd.DataFrame({
        "Release format": format_names,
        "Chart-entry share": [float(ats.get(x, 0)) for x in format_names],
        "Recording-proxy share": [float(rec_format.get(x, 0)) for x in format_names],
    }).melt(id_vars="Release format", var_name="Grain", value_name="Share (%)")
    fig_format_compare = px.bar(
        format_compare, x="Release format", y="Share (%)", color="Grain", barmode="group",
        color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_GOLD], title="Release Format: Entry Share vs Recording-Proxy Share",
    )
    fig_format_compare.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.2f}%<extra></extra>")
    st.plotly_chart(style_fig(fig_format_compare, height=380), width="stretch")

    c1, c2 = st.columns(2)
    with c1:
        release_order = [c for c in ["album", "single", "compilation"] if c in rfr.columns]
        fig_rank_fmt = px.bar(
            rfr.reindex(RANK_ORDER)[release_order], barmode="stack",
            labels={"value": "Share (%)", "rank_band": "Exclusive rank band"}, title="Release Format by Rank Band",
        )
        for trace in plotly_traces(fig_rank_fmt):
            trace.update(
                marker_color=FORMAT_COLORS.get(str(trace.name).lower(), ATLANTIC_GREY),
                hovertemplate=f"<b>{trace.name.title()}</b><br>Rank band: %{{x}}<br>Share: %{{y:.2f}}%<extra></extra>",
            )
        st.plotly_chart(style_fig(fig_rank_fmt, height=380), width="stretch")
    with c2:
        bucket_counts = an.album_size_vs_inclusion(df)
        fig_footprint = px.bar(
            bucket_counts, labels={"value": "Chart entries", "index": "Parent release size"},
            color_discrete_sequence=[ATLANTIC_TEAL], title="Chart Footprint by Parent Release Size",
        )
        fig_footprint.update_layout(showlegend=False)
        fig_footprint.update_traces(hovertemplate="<b>%{x}</b><br>Chart entries: %{y:,.0f}<extra></extra>")
        st.plotly_chart(style_fig(fig_footprint, legend=False, height=380), width="stretch")

    st.markdown("#### Popularity by Parent Release Size")
    if "album_size_bucket" in recordings.columns and "popularity" in recordings.columns:
        proxy_pop = recordings.groupby("album_size_bucket", observed=True)["popularity"].mean().dropna()
        title = "Average Popularity by Release Size · Recording Proxies"
        caption = "One observation per dataset-local recording proxy."
    else:
        proxy_pop = an.album_size_vs_popularity(df)
        title = "Average Popularity by Release Size · Chart Entries"
        caption = "Recording-level bucket fields were unavailable, so this view remains chart-entry weighted."
    fig_pop = px.bar(proxy_pop, labels={"value": "Average popularity", "album_size_bucket": "Parent release size"}, color_discrete_sequence=[ATLANTIC_GOLD])
    fig_pop.update_layout(showlegend=False, title=title)
    fig_pop.update_traces(hovertemplate="<b>%{x}</b><br>Average popularity: %{y:.2f}<extra></extra>")
    st.plotly_chart(style_fig(fig_pop, legend=False, height=360), width="stretch")
    st.caption(caption)

# =============================================================================
# SECTION 5: DURATION
# =============================================================================
if active_view == "Duration":
    section_narrative(
        "Track-duration relationships are presented at both chart-entry and recording-proxy grain. The recording-proxy scatter reduces repeated-chart weighting for tracks that remained in the Top 50 for long periods."
    )
    avg_duration = pd.to_numeric(df["duration_sec"], errors="coerce").mean()
    median_duration = pd.to_numeric(recordings["duration_sec"], errors="coerce").median() if "duration_sec" in recordings.columns else pd.to_numeric(df["duration_sec"], errors="coerce").median()
    dd = an.duration_distribution(df)
    d1, d2, d3, d4 = st.columns(4)
    d1.metric("Average entry duration", format_duration(avg_duration))
    d2.metric("Median recording duration", format_duration(median_duration))
    d3.metric("Standard 2:30–3:30 · entries", f"{dd.get('Standard (2:30-3:30)', 0):.2f}%")
    d4.metric("Recording proxies", f"{len(recordings):,}")

    c1, c2 = st.columns(2)
    with c1:
        fig_dist = px.bar(dd, labels={"value": "Share of entries (%)", "duration_bucket": "Duration"}, color_discrete_sequence=[ATLANTIC_TEAL])
        fig_dist.update_layout(showlegend=False, title="Duration Distribution · Chart Entries")
        fig_dist.update_traces(hovertemplate="<b>%{x}</b><br>Share of chart entries: %{y:.2f}%<extra></extra>")
        st.plotly_chart(style_fig(fig_dist, legend=False, height=360), width="stretch")
    with c2:
        dvp = an.duration_vs_popularity(df)
        fig_quartile = px.bar(dvp, labels={"value": "Avg duration (sec)", "popularity_bucket": "Popularity quartile"}, color_discrete_sequence=[ATLANTIC_TEAL])
        fig_quartile.update_layout(showlegend=False, title="Duration by Popularity Quartile · Chart Entries")
        fig_quartile.update_traces(hovertemplate="<b>%{x}</b><br>Average duration: %{y:.1f} sec<extra></extra>")
        st.plotly_chart(style_fig(fig_quartile, legend=False, height=360), width="stretch")

    st.markdown("#### Duration vs Popularity · Recording Proxies")
    if {"duration_sec", "popularity"}.issubset(recordings.columns):
        scatter_source = recordings.copy()
    elif "recording_proxy_id" in df.columns:
        # Preserve recording-proxy grain even when the canonical proxy table lacks a plotting field.
        agg_spec = {"duration_sec": "median", "popularity": "mean"}
        for optional in ["is_explicit", "song", "artist_raw", "artist", "album_type"]:
            if optional in df.columns:
                agg_spec[optional] = "first"
        scatter_source = df.groupby("recording_proxy_id", as_index=False, observed=True).agg(agg_spec)
    else:
        scatter_source = df.drop_duplicates(subset=["song_norm", "duration_ms"]).copy() if {"song_norm", "duration_ms"}.issubset(df.columns) else df.copy()
    scatter_source = scatter_source.dropna(subset=["duration_sec", "popularity"]).copy()
    if "is_explicit" in scatter_source.columns:
        scatter_source["Content type"] = np.where(
            scatter_source["is_explicit"].astype(bool),
            "Explicit",
            "Clean",
        )
    song_col = next((c for c in ["song", "track_name", "title"] if c in scatter_source.columns), None)
    artist_col = next((c for c in ["artist_raw", "artist", "primary_artist"] if c in scatter_source.columns), None)
    custom_cols = [c for c in [song_col, artist_col, "album_type"] if c]
    fig_scatter = px.scatter(
        scatter_source, x="duration_sec", y="popularity", render_mode="webgl",
        color="Content type" if "Content type" in scatter_source.columns else None,
        color_discrete_map=EXPLICIT_SCATTER_COLORS, opacity=0.50,
        category_orders={"Content type": ["Clean", "Explicit"]},
        custom_data=custom_cols if custom_cols else None,
        labels={"duration_sec": "Duration (seconds)", "popularity": "Popularity score"},
        trendline="ols" if len(scatter_source) > 5 else None,
        title="Recording-Level Duration vs Popularity",
    )
    for trace in plotly_traces(fig_scatter):
        if "markers" in (getattr(trace, "mode", "") or ""):
            trace.update(marker=dict(size=5.2, line=dict(width=0)))
            lines = ["Duration: %{x:.0f} sec", "Popularity: %{y:.0f}"]
            if song_col: lines.insert(0, f"Track: %{{customdata[{custom_cols.index(song_col)}]}}")
            if artist_col: lines.insert(1 if song_col else 0, f"Artist: %{{customdata[{custom_cols.index(artist_col)}]}}")
            trace.update(hovertemplate="<b>" + str(trace.name) + "</b><br>" + "<br>".join(lines) + "<extra></extra>")
        elif "lines" in (getattr(trace, "mode", "") or ""):
            trace.update(line=dict(width=2.0))
        elif getattr(trace, "mode", None) == "lines":
            trace.update(line=dict(width=1.5))
    st.plotly_chart(style_fig(fig_scatter, height=460), width="stretch")

# =============================================================================
# SECTION 6: HEALTH
# =============================================================================
if active_view == "Health":
    section_narrative(
        "Market health focuses on snapshot-comparable artist diversity and concentration. Source data quality is reported separately below rather than mixed into the market KPIs."
    )
    h1, h2, h3, h4 = st.columns(4)
    h1.metric("Mean effective artists / snapshot", f"{snapshot_health['effective_number_of_artists'].mean():.1f}")
    h2.metric("Mean unique artists / snapshot", f"{snapshot_health['unique_artists'].mean():.1f}")
    h3.metric("Median fractional snapshot HHI", f"{snapshot_health['fractional_hhi'].median():.0f}")
    h4.metric("Mean fractional snapshot HHI", f"{snapshot_health['fractional_hhi'].mean():.0f}")

    c1, c2 = st.columns(2)
    with c1:
        fig_div = px.line(
            snapshot_health, x="date", y="effective_number_of_artists",
            labels={"date": "Date", "effective_number_of_artists": "Effective artists"},
            color_discrete_sequence=[ATLANTIC_NAVY], title="Effective Artist Count by Snapshot",
        )
        fig_div.update_traces(hovertemplate="<b>%{x|%d %b %Y}</b><br>Effective artists: %{y:.2f}<extra></extra>")
        st.plotly_chart(style_fig(fig_div, legend=False, height=360), width="stretch")
    with c2:
        fig_hhi = px.line(
            snapshot_health, x="date", y="fractional_hhi",
            labels={"date": "Date", "fractional_hhi": "Fractional HHI"},
            color_discrete_sequence=[ATLANTIC_RED], title="Fractional Snapshot HHI",
        )
        fig_hhi.update_traces(hovertemplate="<b>%{x|%d %b %Y}</b><br>Fractional HHI: %{y:.1f}<extra></extra>")
        st.plotly_chart(style_fig(fig_hhi, legend=False, height=360), width="stretch")

    st.markdown("#### UK / Domestic vs International Trend")
    dit = an.domestic_vs_international_trend(exploded)
    if len(dit) >= 2:
        dit_plot = dit.reindex(columns=[UK, INTL], fill_value=0)
        fig_nat = px.line(
            dit_plot, markers=True, labels={"value": "Artist-credit share (%)", "date": "Quarter"},
            color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_GOLD], title="Nationality Mix Over Time",
        )
        for trace in plotly_traces(fig_nat):
            trace.update(hovertemplate=f"<b>{trace.name}</b><br>Quarter: %{{x|%b %Y}}<br>Artist-credit share: %{{y:.2f}}%<extra></extra>")
        st.plotly_chart(style_fig(fig_nat, height=350), width="stretch")
    else:
        st.info("Select a date range spanning at least two quarters to compute the nationality trend.")

    st.markdown("#### Data Quality")
    st.caption("Validation describes the complete source pipeline, not only the currently filtered dashboard view. Assessment and observed result are separate fields; genuinely empty observed values are shown as null.")
    quality_report = load_quality_report(DATA_VERSION)
    render_data_quality(quality_report, validation_report)

# =============================================================================
# SECTION 7: STRATEGY
# =============================================================================
if active_view == "Strategy":
    section_narrative(
        "Decision support is framed as evidence → observed implication → decision question. The dataset is observational, so the dashboard does not present causal prescriptions."
    )

    by_rank_strategy = an.domestic_vs_international_by_rank(df, exploded)
    release_strategy = an.release_format_by_rank(df)
    ats_strategy = an.album_type_share(df)
    collab_strategy = an.collab_by_rank_group(df)
    explicit_strategy = an.explicit_by_rank(df)
    single_top5 = release_strategy["single"].get("1-5", np.nan) if "single" in release_strategy.columns else np.nan
    intl_top5 = by_rank_strategy.get(INTL, pd.Series(dtype=float)).get("1-5", np.nan)
    collab_peak_band = collab_strategy.idxmax() if not collab_strategy.dropna().empty else "N/A"
    collab_peak_value = collab_strategy.max() if not collab_strategy.dropna().empty else np.nan

    r1, r2 = st.columns(2)
    evidence_card(
        r1, "Artist portfolio",
        f"Top-5 artists hold {conc['top_n_share_pct']:.1f}% of full artist-credit appearances; median fractional snapshot HHI is {snapshot_health['fractional_hhi'].median():.0f}.",
        "Long-run artist presence is distributed across a broad roster, while daily concentration is measured separately.",
        "Which roster segments deserve incremental A&R investment when persistence and snapshot diversity are evaluated together?",
        ATLANTIC_NAVY,
    )
    evidence_card(
        r2, "Release format",
        f"Singles account for {fmt_pct(single_top5)} of positions 1–5 versus {ats_strategy.get('single', 0):.1f}% of chart entries overall.",
        "Singles are disproportionately represented at the very top relative to their overall chart-entry share.",
        "Should lead-single investment be tested against peak-position objectives before expanding album-scale campaigns?",
        ATLANTIC_RED,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    r3, r4 = st.columns(2)
    evidence_card(
        r3, "Collaboration",
        f"Collaborative entries are {an.collaboration_ratio(df)*100:.1f}% overall and peak in the {collab_peak_band} band at {fmt_pct(collab_peak_value)}.",
        "Collaboration prevalence differs by chart tier, but the data do not identify collaboration as the cause of rank performance.",
        "Which collaboration formats or partner networks should be tested prospectively rather than inferred from historical association?",
        ATLANTIC_TEAL,
    )
    evidence_card(
        r4, "Cross-border positioning",
        f"International artists account for {dom_intl.get(INTL, 0):.1f}% of period-wide artist credits and {fmt_pct(intl_top5)} in positions 1–5.",
        "International representation is substantial in the UK Top 50, including at the highest chart tier.",
        "Where should UK-origin and international campaigns use different objectives, creative, or partner strategies?",
        ATLANTIC_GOLD,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.caption(
        "Use date, collaboration, and release-type filters to stress-test whether these patterns persist in different market slices. "
        "Artist comparison remains scoped to the Artists tab."
    )

st.markdown(
    f"""
    <div class="portfolio-footer">
        <div class="portfolio-footer-title">Portfolio context & analytical scope</div>
        <div class="footer-grid">
            <div class="footer-card">
                <div class="footer-card-title">Project context</div>
                <div class="footer-card-text">Entertainment-category Data Analyst portfolio case study. Atlantic Recording Corporation is used only as the business scenario; this is not an official Atlantic engagement.</div>
            </div>
            <div class="footer-card">
                <div class="footer-card-title">Dataset & coverage</div>
                <div class="footer-card-text">Dataset supplied by Unified Mentor Pvt. Ltd. · {validation_report['n_rows_raw']:,} chart entries · {validation_report['n_dates']:,} dates · {validation_report['n_snapshots']:,} reconstructed snapshots · {df_full['date'].min().strftime('%b %Y')}–{df_full['date'].max().strftime('%b %Y')}.</div>
            </div>
            <div class="footer-card">
                <div class="footer-card-title">Analytical units</div>
                <div class="footer-card-text">{exploded_full['artist_name'].nunique():,} credited artists · {FULL_RECORDING_COUNT:,} dataset-local recording proxies. Nationality is manually curated; findings are descriptive, not causal.</div>
            </div>
        </div>
        <div class="footer-note">Upstream source limitation: the supplied project materials do not identify the original provider, collection URL, collection method, or formal upstream license.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if toggle_panel("Methodology & provenance", "methodology_provenance"):
    with st.container(border=True):
        st.markdown(
            f"""
            **Project context** — Entertainment-category Data Analyst portfolio case study using an Atlantic Recording Corporation business scenario.
            **Dataset provenance** — Supplied by Unified Mentor Pvt. Ltd.; the supplied materials do not identify the original upstream provider, collection URL, collection method, or formal upstream license.
            **Coverage** — {validation_report['n_rows_raw']:,} raw chart entries across {validation_report['n_dates']:,} dates and {validation_report['n_snapshots']:,} reconstructed Top-50 snapshots from {df_full['date'].min().date()} to {df_full['date'].max().date()}.
            **Recording proxy** — Dataset-local identity based on normalized title plus exact duration; not an ISRC or global recording identifier.
            **Nationality labels** — Manually curated; unclassified artists remain explicitly unclassified.
            **Interpretation** — Findings are descriptive associations, not causal effects.
            **Status** — This portfolio dashboard does not represent an official Atlantic Recording Corporation engagement.
            """
        )
