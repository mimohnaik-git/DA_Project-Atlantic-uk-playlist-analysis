"""
Atlantic Recording Corporation
UK Top 50 Playlist — Executive Market Structure & Diversity Dashboard

Run with:  streamlit run app.py
"""
import sys
sys.path.insert(0, "src")

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

import analytics as an
from data_prep import run as run_pipeline
from artist_nationality import classify, UK, INTL, UNK

st.set_page_config(
    page_title="Atlantic Recording | UK Top 50 Executive Dashboard",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


ATLANTIC_NAVY = "#0B1F3A"
ATLANTIC_RED = "#E4572E"
ATLANTIC_GOLD = "#D9A441"
ATLANTIC_TEAL = "#2C7873"
ATLANTIC_GREY = "#8A94A6"
ATLANTIC_LIGHT = "#F5F6F8"
PALETTE = [ATLANTIC_NAVY, ATLANTIC_RED, ATLANTIC_GOLD, ATLANTIC_TEAL, ATLANTIC_GREY]
SEQ_BLUES = ["#E8ECF3", "#B9C4D9", "#8A9BBF", "#4C6089", "#0B1F3A"]

# ---------------------------------------------------------------------------
# Global styling
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ---- Streamlit's default header was overlapping the custom hero title
    (it's position:absolute, z-index 999990, spanning y:0-60px). Keep the
    header element itself in the layout (removing it broke Streamlit's own
    sidebar-toggle rendering -- confirmed via testing) and keep its default
    Deploy/menu/status controls visible -- just make the header's own
    background transparent so it can't visually block the title underneath.
    The title clears the header via block-container's top padding. ---- */
    header[data-testid="stHeader"] {background: transparent; box-shadow: none;}
    footer {visibility: hidden;}

    /* ---- Overall canvas: soft tinted gradient instead of flat white ---- */
    .stApp {
        background: linear-gradient(160deg, #F8F9FC 0%, #EEF1F7 45%, #F6F2EA 100%);
        background-attachment: fixed;
    }
    .block-container {padding-top: 2.8rem; padding-bottom: 2rem; padding-left: 2rem; padding-right: 2rem; max-width: 1600px;}

    /* ---- Sidebar: distinct light tone with a brand-colored edge ---- */
    section[data-testid="stSidebar"] {
        width: 290px !important; min-width: 290px !important;
        background: linear-gradient(180deg, #FFFFFF 0%, #F1F4F9 100%);
        border-right: 1px solid #E3E7EF;
    }
    section[data-testid="stSidebar"] .block-container {padding-top: 1.5rem; padding-left: 1rem; padding-right: 1rem;}

    /* ---- Decorative brand-gradient rule under the header ---- */
    .brand-rule {
        height: 4px; width: 220px; border-radius: 10px; margin: 8px 0 24px 0;
        background: linear-gradient(90deg, #0B1F3A 0%, #E4572E 36%, #D9A441 68%, #2C7873 100%);
    }

    /* ---- Hero header: three-tier hierarchy (title / subtitle / description) ---- */
    .hero-title {font-size: 2.05rem; font-weight: 800; color: #0B1F3A; margin-bottom: 0.1rem; letter-spacing:-0.4px; line-height:1.25;}
    .hero-subtitle {font-size: 1.3rem; font-weight: 700; color: #334155; margin-bottom: 0.35rem; line-height:1.25;}
    .hero-description {font-size: 0.96rem; color: #64748B; margin-bottom: 0.2rem; line-height:1.4;}
    .section-narrative {color:#3d4450; font-size:0.98rem; line-height:1.65; margin-bottom:0.9rem; max-width: 1100px;}

    /* ---- Tab panels behave like white cards floating on the tinted canvas ---- */
    .stTabs [data-baseweb="tab-panel"] {
        background: #FCFCFE; border-radius: 12px; padding: 26px 28px 12px 28px; margin-top: 8px;
        box-shadow: 0 4px 16px rgba(15,23,42,0.07); border: 1px solid #EDEFF3;
    }
    .stTabs [data-baseweb="tab-list"] {gap: 4px; flex-wrap: nowrap; background: transparent;}
    .stTabs [data-baseweb="tab"] {padding: 10px 16px; font-size: 0.92rem; background: transparent; border-radius: 8px 8px 0 0;}
    .stTabs [aria-selected="true"] {background: #FFF9F0;}

    /* ---- KPI cards ---- */
    .kpi-card {
        background: linear-gradient(160deg, #ffffff 0%, #fbfcfe 100%);
        border-left: 5px solid #0B1F3A; border-radius: 10px;
        padding: 18px 18px 16px 18px; box-shadow: 0 2px 8px rgba(16,24,40,0.08); height: 100%; min-height: 116px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(16,24,40,0.12);}
    .kpi-icon {font-size: 1.4rem; line-height:1;}
    .kpi-value {font-size: 1.65rem; font-weight: 800; color:#0B1F3A; line-height:1.2; margin-top:4px;}
    .kpi-label {font-size: 0.74rem; color:#6b7280; text-transform:uppercase; letter-spacing:0.04em; margin-top:2px;}

    .insight-card {
        background: linear-gradient(135deg, #FBF8F1 0%, #F5F6F8 100%);
        border-left: 5px solid #D9A441; border-radius: 10px; padding: 16px 20px; margin: 0.4rem 0 1.1rem 0;
    }
    .insight-title {font-weight:750; color:#0B1F3A; font-size:0.98rem; margin-bottom:3px;}
    .insight-text {color:#3d4450; font-size:0.9rem; line-height:1.55;}

    .finding-card {
        background: linear-gradient(160deg, #ffffff 0%, #fbfcfe 100%);
        border:1px solid #E5E7EB; border-top:5px solid #0B1F3A; border-radius:10px;
        padding:16px 20px; height:100%; box-shadow: 0 2px 6px rgba(16,24,40,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .finding-card:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(16,24,40,0.1);}
    .finding-title {font-weight:750; color:#0B1F3A; font-size:0.95rem; margin-bottom:6px;}
    .finding-text {color:#4b5262; font-size:0.86rem; line-height:1.5;}

    .rec-card {
        background: linear-gradient(160deg, #ffffff 0%, #fbfcfe 100%);
        border:1px solid #E5E7EB; border-top:5px solid #2C7873; border-radius:10px;
        padding:18px 20px; height:100%; box-shadow: 0 2px 6px rgba(16,24,40,0.06);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .rec-card:hover {transform: translateY(-2px); box-shadow: 0 6px 16px rgba(16,24,40,0.1);}
    .rec-title {font-weight:800; color:#0B1F3A; font-size:1.02rem; margin-bottom:10px;}
    .rec-title span.badge {
        display:inline-block; color:#ffffff; font-size:0.68rem; font-weight:700;
        padding:3px 9px; border-radius:999px; margin-left:8px; vertical-align:middle; letter-spacing:0.03em;
    }

    div[data-testid="stMetricValue"] {font-size: 1.5rem;}
    .section-spacer {margin-top: 18px;}

    /* ---- Chart & dataframe containers: white cards with a soft border.
    IMPORTANT: no padding directly on this element -- Plotly measures THIS
    element's box to size its SVG, and padding here caused the SVG to be
    drawn ~13px wider than the visible content box (confirmed via bounding-
    box inspection), clipping the right edge of wide charts like the
    treemap. overflow:hidden + border-radius gives the same rounded-card
    look without touching the box Plotly measures. ---- */
    div[data-testid="stPlotlyChart"] {
        background: #FFFFFF; border-radius: 12px; overflow: hidden;
        border: 1px solid #EEF0F4; box-shadow: 0 1px 4px rgba(16,24,40,0.05);
    }
    div[data-testid="stDataFrame"] {
        background: #FFFFFF; border-radius: 12px; padding: 12px;
        border: 1px solid #EEF0F4; box-shadow: 0 1px 4px rgba(16,24,40,0.05);
    }
</style>
""", unsafe_allow_html=True)


def kpi_card(col, icon, label, value, accent=ATLANTIC_NAVY):
    col.markdown(f"""
    <div class="kpi-card" style="border-left-color:{accent};">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
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
        <ul style="padding-left:1.1rem; color:#3d4450; font-size:0.87rem; line-height:1.45; margin-bottom:0;">{items}</ul>
    </div>""", unsafe_allow_html=True)


def section_narrative(text):
    st.markdown(f'<div class="section-narrative">{text}</div>', unsafe_allow_html=True)


CHART_FONT = "Segoe UI, Arial, sans-serif"


def style_fig(fig, height=None, legend=True, margin=None):
    """Single source of truth for chart styling -- every chart in the
    dashboard should be passed through this so typography, background, and
    spacing stay consistent across all 20+ charts."""
    layout_kwargs = dict(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(color="#3d4450", size=12.5, family=CHART_FONT),
        legend=dict(font=dict(size=11, family=CHART_FONT)),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family=CHART_FONT,
                         bordercolor="#E5E7EB"),
        margin=margin or dict(l=10, r=10, t=48, b=10),
        showlegend=legend,
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
    fig.update_xaxes(showgrid=True, gridcolor="#EEF0F3")
    fig.update_yaxes(showgrid=True, gridcolor="#EEF0F3")
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
        text=f"<b>{value_pct:.0f}%</b><br><span style='font-size:11px;color:#6b7280'>{label}</span>",
        showarrow=False, font=dict(size=20, color=ATLANTIC_NAVY, family=CHART_FONT),
    )
    return fig


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner="Loading and cleaning UK Top 50 data...")
def load_data():
    clean_df, exploded, report = run_pipeline("data/Atlantic_United_Kingdom.csv")
    exploded = exploded.copy()
    exploded["nationality"] = exploded["artist_name"].apply(classify)
    return clean_df, exploded, report


df_full, exploded_full, validation_report = load_data()

# ---------------------------------------------------------------------------
# Sidebar — Filters
# ---------------------------------------------------------------------------

st.sidebar.markdown("### 🎧 Atlantic Recording Corporation")
st.sidebar.caption("UK Top 50 Market Structure Dashboard")
st.sidebar.markdown("---")
st.sidebar.markdown("#### 🎛️ Filters")

min_date, max_date = df_full["date"].min().date(), df_full["date"].max().date()
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

artist_options = sorted(exploded_full["artist_name"].unique())
selected_artists = st.sidebar.multiselect(
    "Artist",
    options=artist_options,
    help="Leave empty to include all artists",
)

collab_toggle = st.sidebar.radio(
    "Solo vs. Collaboration",
    options=["All tracks", "Solo only", "Collaborations only"],
    index=0,
)

album_types = sorted(df_full["album_type"].unique())
selected_album_types = st.sidebar.multiselect(
    "Release Type",
    options=album_types,
    help="Leave empty to include all release types",
)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"Dataset: {validation_report['n_rows_raw']:,} raw entries · "
    f"{validation_report['duplicate_rows']} duplicate rows detected · "
    f"0 missing values"
)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

mask = (df_full["date"].dt.date >= start_date) & (df_full["date"].dt.date <= end_date)
df = df_full[mask].copy()

if collab_toggle == "Solo only":
    df = df[~df["is_collaboration"]]
elif collab_toggle == "Collaborations only":
    df = df[df["is_collaboration"]]

if selected_album_types:
    df = df[df["album_type"].isin(selected_album_types)]

if selected_artists:
    sel_set = set(selected_artists)
    df = df[df["collaborators"].apply(lambda names: len(sel_set.intersection(names)) > 0)]

# Rebuild the exploded (one-row-per-collaborator) view from the filtered df
# so every downstream chart/metric reflects the active filters consistently.
# NOTE: df.explode() repeats the original row's index for every collaborator
# it creates, producing a non-unique index. pd.crosstab (used in
# analytics.domestic_vs_international_by_rank) can raise "cannot reindex on
# an axis with duplicate labels" on that in newer pandas versions -- reset
# to a fresh unique index to avoid it.
exploded = df.explode("collaborators").rename(columns={"collaborators": "artist_name"})
exploded = exploded[exploded["artist_name"].notna()].reset_index(drop=True).copy()
exploded["nationality"] = exploded["artist_name"].apply(classify)

if len(df) == 0:
    st.warning("No playlist entries match the selected filters. Try widening your date range or filters.")
    st.stop()

filters_active = (
    (start_date, end_date) != (min_date, max_date)
    or bool(selected_artists)
    or collab_toggle != "All tracks"
    or bool(selected_album_types)
)

# ---------------------------------------------------------------------------
# Hero header
# ---------------------------------------------------------------------------

st.markdown("""
<div class="hero-title">
🎧 UK Top 50 Playlist
</div>

<div class="hero-subtitle">
Executive Market Structure Dashboard
</div>

<div class="hero-description">
Atlantic Recording Corporation &nbsp;·&nbsp; UK Music Market Intelligence
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-rule"></div>', unsafe_allow_html=True)

if filters_active:
    st.caption("🔎 Filters active — every figure below reflects your current filter selection.")

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

conc = an.artist_concentration_index(exploded, top_n=5)
dom_intl = an.domestic_vs_international(exploded)
es_top = an.explicit_share(df)
sc_top = an.solo_vs_collab(df)

kpi_row1 = st.columns(3)
kpi_card(kpi_row1[0], "📋", "Playlist entries", f"{len(df):,}", ATLANTIC_NAVY)
kpi_card(kpi_row1[1], "🎤", "Unique artists", f"{exploded['artist_name'].nunique():,}", ATLANTIC_NAVY)
kpi_card(kpi_row1[2], "🏆", "Top-5 concentration", f"{conc['top_n_share_pct']:.1f}%", ATLANTIC_RED)

st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

kpi_row2 = st.columns(3)
kpi_card(kpi_row2[0], "🤝", "Collaboration ratio", f"{an.collaboration_ratio(df)*100:.1f}%", ATLANTIC_TEAL)
kpi_card(kpi_row2[1], "🔞", "Explicit share", f"{es_top['Explicit']:.1f}%", ATLANTIC_GOLD)
kpi_card(kpi_row2[2], "🇬🇧", "UK / domestic share", f"{dom_intl.get('UK / Domestic', 0):.1f}%", ATLANTIC_NAVY)

st.markdown('<div style="margin-top:26px;"></div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_overview, tab_dom, tab_collab, tab_explicit, tab_album, tab_duration, tab_market, tab_reco = st.tabs([
    "📋 Overview",
    "🏆 Artists",
    "🤝 Collaboration",
    "🎙️ Content",
    "💿 Formats",
    "⏱️ Duration",
    "📈 Health",
    "💡 Strategy",
])

# =============================================================================
# TAB 0: EXECUTIVE OVERVIEW
# =============================================================================
with tab_overview:
    section_narrative(
        "This dashboard analyzes the structural composition of the UK Top 50 playlist — who dominates it, how "
        "concentrated that dominance is, how collaboration and explicit content shape chart position, and how "
        "release-format strategy differs by chart tier — to give Atlantic Recording Corporation UK-specific "
        "intelligence for artist signing, marketing, and release planning, rather than a US-style popularity-trend view."
    )

    by_rank_ov = an.domestic_vs_international_by_rank(df, exploded)
    collab_by_rank_ov = an.collab_by_rank_group(df)
    explicit_by_rank_ov = an.explicit_by_rank(df)
    release_by_rank_ov = an.release_format_by_rank(df)

    f1, f2, f3 = st.columns(3)
    finding_card(
        f1, "🏆", "A fragmented, broad-based market",
        f"The top 5 artists hold just <b>{conc['top_n_share_pct']:.1f}%</b> of chart appearances "
        f"(HHI {conc['hhi']:.0f}), across <b>{exploded['artist_name'].nunique()}</b> unique artists — "
        "evidence against a small-roster \"hits factory\" model.",
        ATLANTIC_NAVY,
    )
    finding_card(
        f2, "🌍", "International artists lead, especially at the top",
        f"International acts hold <b>{dom_intl.get('International', 0):.1f}%</b> of appearances vs. "
        f"<b>{dom_intl.get('UK / Domestic', 0):.1f}%</b> for UK/domestic acts — and the gap is widest inside "
        f"the Top 10 ({by_rank_ov.get(INTL, pd.Series()).get('Top 10', float('nan')):.1f}% international).",
        ATLANTIC_RED,
    )
    finding_card(
        f3, "🤝", "Collaboration peaks mid-chart",
        f"<b>{an.collaboration_ratio(df)*100:.1f}%</b> of entries are collaborations, peaking around the "
        f"Top 10–20 ({collab_by_rank_ov.get('Top 10', float('nan')):.1f}% / "
        f"{collab_by_rank_ov.get('Top 20', float('nan')):.1f}%) rather than at the very top.",
        ATLANTIC_TEAL,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    f4, f5, f6 = st.columns(3)
    finding_card(
        f4, "🎙️", "UK leans clean, but explicit charts high",
        f"<b>{es_top['Clean']:.1f}%</b> of entries are clean-rated overall, yet explicit share is highest in "
        f"the Top 10 ({explicit_by_rank_ov.get('Top 10', float('nan')):.1f}%) — explicit tracks that chart "
        "tend to chart strongly.",
        ATLANTIC_GOLD,
    )
    single_top5 = release_by_rank_ov["single"].get("Top 5", float("nan")) if "single" in release_by_rank_ov else float("nan")
    finding_card(
        f5, "💿", "Singles win the top; albums win volume",
        f"Album cuts are <b>{an.album_type_share(df).get('album', 0):.1f}%</b> of all entries vs. "
        f"<b>{an.album_type_share(df).get('single', 0):.1f}%</b> singles — but singles are the majority "
        f"format inside the Top 5 ({single_top5:.1f}%).",
        ATLANTIC_RED,
    )
    finding_card(
        f6, "📊", "Market balance",
        f"Content Variety Index: <b>{an.content_variety_index(df):.1f}</b> / 100, blending artist diversity, "
        "album-format mix, and explicit/clean balance into one market-composition figure.",
        ATLANTIC_TEAL,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.caption(
        "💡 Explore each dimension in depth using the tabs above, or jump straight to **Strategy** for the "
        "recommendations. Every chart respects the filters in the sidebar."
    )

# =============================================================================
# TAB 1: ARTIST LANDSCAPE
# =============================================================================
with tab_dom:
    section_narrative(
        "How concentrated is the UK Top 50 in a handful of artists, and how does that concentration break down "
        "between UK/domestic and international acts?"
    )
    insight_card(
        "🏆", "Market concentration read",
        f"The top 5 artists account for <b>{conc['top_n_share_pct']:.1f}%</b> of chart appearances, with an "
        f"HHI of <b>{conc['hhi']:.0f}</b> — well below the 1,500 threshold conventionally associated with a "
        "concentrated market. This is a fragmented, broad-based artist landscape.",
    )

    left, right = st.columns([2, 1])
    with left:
        n_top = st.slider("Show top N artists", 5, 40, 15, key="dom_n")
        top_artists = an.top_dominating_artists(exploded, n_top).sort_values()
        fig = px.bar(
            top_artists, orientation="h",
            labels={"value": "Chart appearances", "artist_name": "Artist"},
            color=top_artists.values, color_continuous_scale=SEQ_BLUES,
        )
        fig.update_layout(showlegend=False, coloraxis_showscale=False, title="Artist Dominance Leaderboard")
        fig.update_layout(height=max(450, n_top * 24))
        st.plotly_chart(style_fig(fig, legend=False), width="stretch")

    with right:
        st.markdown("**Market Concentration**")
        st.metric("Top-5 artist share of appearances", f"{conc['top_n_share_pct']:.1f}%")
        st.metric("Herfindahl-Hirschman Index (HHI)", f"{conc['hhi']:.0f}")
        st.metric("Unique artist count", f"{conc['total_unique_artists']:,}")
        st.metric("Diversity score (unique artists / entries)", f"{an.diversity_score(df, exploded):.4f}")
        st.caption(
            "HHI below ~1,500 indicates a low-concentration, competitive market. A low HHI here signals the "
            "UK Top 50 is fragmented across artists rather than dominated by a handful of acts."
        )

    st.markdown("#### Concentration Curve")
    st.caption(
        "How evenly is chart presence spread across artists? The closer the curve sits to the diagonal, the "
        "more evenly distributed; the more it bows toward the top-left, the more concentrated the market."
    )
    curve = an.concentration_curve(exploded)
    fig_curve = go.Figure()
    fig_curve.add_trace(go.Scatter(
        x=curve["artist_rank_pct"], y=curve["cumulative_share_pct"], mode="lines",
        line=dict(color=ATLANTIC_RED, width=3), fill="tozeroy", fillcolor="rgba(228,87,46,0.08)",
        name="Actual", hovertemplate="Top %{x:.1f}% of artists<br>= %{y:.1f}% of appearances<extra></extra>",
    ))
    fig_curve.add_trace(go.Scatter(
        x=[0, 100], y=[0, 100], mode="lines", line=dict(color=ATLANTIC_GREY, dash="dash", width=1.5),
        name="Perfectly even market",
    ))
    fig_curve.update_layout(
        xaxis_title="Cumulative % of artists (ranked by dominance)",
        yaxis_title="Cumulative % of chart appearances",
        legend=dict(orientation="h", y=1.1),
    )
    curve_col, stat_col = st.columns([3, 2])
    with curve_col:
        st.plotly_chart(style_fig(fig_curve, height=380), width="stretch")
    with stat_col:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.metric("Top 5 artists hold", f"{conc['top_n_share_pct']:.1f}% of appearances")
        st.metric("Top 10 artists hold", f"{an.artist_concentration_index(exploded, 10)['top_n_share_pct']:.1f}% of appearances")
        st.metric("Herfindahl-Hirschman Index", f"{conc['hhi']:.0f}")
        st.caption("HHI < 1,500 = low concentration (fragmented, competitive market).")

    st.markdown("#### Artist Landscape Treemap")
    st.caption("Box size = chart appearances. A quick visual read on how much of the chart each artist occupies.")
    tm_n = 30
    tm_data = an.top_dominating_artists(exploded, tm_n).reset_index()
    tm_data.columns = ["artist_name", "appearances"]
    fig_tm = px.treemap(
        tm_data, path=["artist_name"], values="appearances",
        color="appearances", color_continuous_scale=SEQ_BLUES,
    )
    fig_tm.update_layout(coloraxis_showscale=False, title="Top 30 Artists by Chart Appearances")
    fig_tm.update_traces(textinfo="label+value", textfont_size=13)
    st.plotly_chart(style_fig(fig_tm, height=450, margin=dict(l=4, r=4, t=48, b=4)), width="stretch")

    st.markdown("#### UK / Domestic vs. International Artists")
    c1, c2 = st.columns(2)
    with c1:
        pie = px.pie(
            values=dom_intl.reindex([UK, INTL, UNK]).fillna(0).values,
            names=[UK, INTL, UNK],
            color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_RED, ATLANTIC_GREY],
            hole=DONUT_HOLE,
        )
        pie.update_traces(textinfo="percent")
        donut_center(pie, dom_intl.get(UK, 0), "UK / Domestic")
        pie.update_layout(title="Share of Appearances")
        st.plotly_chart(style_donut(pie), width="stretch")
    with c2:
        by_rank = an.domestic_vs_international_by_rank(df, exploded)
        fig2 = px.bar(
            by_rank[[UK, INTL]], barmode="group",
            color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_RED],
            labels={"value": "Share (%)", "rank_group": "Chart position"},
        )
        fig2.update_layout(title="Share by Chart Position")
        st.plotly_chart(style_fig(fig2, height=DONUT_HEIGHT), width="stretch")

# =============================================================================
# TAB 2: COLLABORATION DYNAMICS
# =============================================================================
with tab_collab:
    section_narrative(
        "How much of the UK Top 50 is collaborative, at what chart tier does collaboration matter most, and "
        "which artist pairings recur most often?"
    )
    cbr = an.collab_by_rank_group(df)
    peak_tier = cbr.idxmax() if len(cbr.dropna()) else "N/A"
    insight_card(
        "🤝", "Collaboration is a mid-chart mechanic",
        f"<b>{an.collaboration_ratio(df)*100:.1f}%</b> of entries are collaborations, peaking in the "
        f"<b>{peak_tier}</b> tier ({cbr.max():.1f}%) — pairing artists looks like an effective way to break "
        "into the middle of the chart more than a top-of-chart requirement.",
        ATLANTIC_TEAL,
    )

    c1, c2, c3, c4 = st.columns(4)
    sc = an.solo_vs_collab(df)
    c1.metric("Solo tracks", f"{sc.get('Solo', 0):,}")
    c2.metric("Collaborative tracks", f"{sc.get('Collaboration', 0):,}")
    c3.metric("Collaboration ratio", f"{an.collaboration_ratio(df)*100:.1f}%")
    c4.metric("Avg. collaborators / song", f"{an.avg_collaborators_per_song(df):.2f}")

    left, right = st.columns(2)
    with left:
        fig = px.bar(cbr, labels={"value": "Collaboration share (%)", "rank_group": "Chart position"},
                     color_discrete_sequence=[ATLANTIC_TEAL])
        fig.update_layout(showlegend=False, title="Collaboration Frequency by Rank Group")
        st.plotly_chart(style_fig(fig, legend=False, height=DONUT_HEIGHT), width="stretch")
    with right:
        sc_fig = px.pie(values=sc.values, names=sc.index,
                         color_discrete_sequence=[ATLANTIC_TEAL, ATLANTIC_RED], hole=DONUT_HOLE)
        sc_fig.update_traces(textinfo="percent")
        collab_pct = an.collaboration_ratio(df) * 100
        donut_center(sc_fig, collab_pct, "Collaboration")
        sc_fig.update_layout(title="Solo vs. Collaboration Share")
        st.plotly_chart(style_donut(sc_fig), width="stretch")

    st.markdown("#### Top Collaborator Pairs")
    st.caption("Ranked by number of tracks the pair was co-credited on together.")
    edges = an.collaboration_edges(exploded)
    if len(edges) == 0:
        st.info("No collaborations found in the current filter selection.")
    else:
        top_n_pairs = st.slider("Number of top pairs to show", 5, min(40, len(edges)), 15, key="pairs_n")
        top_edges = edges.head(top_n_pairs).copy()
        top_edges["pair_label"] = top_edges["artist_a"] + "  ×  " + top_edges["artist_b"]
        top_edges = top_edges.sort_values("weight")
        fig_pairs = px.bar(
            top_edges, x="weight", y="pair_label", orientation="h",
            color="weight", color_continuous_scale=[ATLANTIC_NAVY, ATLANTIC_RED],
            labels={"weight": "Tracks co-credited together", "pair_label": ""},
        )
        fig_pairs.update_layout(coloraxis_showscale=False, height=max(360, top_n_pairs * 30),
                                 title="Top Collaborator Pairs")
        st.plotly_chart(style_fig(fig_pairs, legend=False), width="stretch")

        with st.expander("🔍 Explore as an interactive network graph"):
            max_edges = st.slider("Number of top collaborator pairs to display", 10, min(60, len(edges)), 30)
            net_edges = edges.head(max_edges)
            G = nx.Graph()
            for _, row in net_edges.iterrows():
                G.add_edge(row["artist_a"], row["artist_b"], weight=row["weight"])
            pos = nx.spring_layout(G, k=0.8, seed=42, weight="weight")

            edge_x, edge_y = [], []
            for u, v in G.edges():
                x0, y0 = pos[u]; x1, y1 = pos[v]
                edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1, color=ATLANTIC_GREY),
                                     hoverinfo="none", mode="lines")

            degrees = dict(G.degree())
            node_x = [pos[n][0] for n in G.nodes()]
            node_y = [pos[n][1] for n in G.nodes()]
            node_trace = go.Scatter(
                x=node_x, y=node_y, mode="markers+text",
                text=list(G.nodes()), textposition="top center", textfont=dict(size=9, family=CHART_FONT),
                marker=dict(size=[12 + degrees[n] * 4 for n in G.nodes()],
                            color=ATLANTIC_RED, line=dict(width=1, color="white")),
                hovertext=[f"{n} ({degrees[n]} collaborators)" for n in G.nodes()],
                hoverinfo="text",
            )
            net_fig = go.Figure(data=[edge_trace, node_trace])
            net_fig.update_layout(
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
            )
            st.caption(
                "This view is interactive (zoom/pan/hover) so overlapping labels at a glance are less of a "
                "concern than in a static chart — zoom into any cluster for detail."
            )
            st.plotly_chart(
                style_fig(net_fig, height=600, legend=False, margin=dict(l=15, r=15, t=10, b=20)),
                width="stretch",
            )

# =============================================================================
# TAB 3: CONTENT MIX (EXPLICIT VS CLEAN)
# =============================================================================
with tab_explicit:
    section_narrative(
        "Does the UK Top 50 favor clean content overall, and does that preference hold at every chart tier and "
        "point in time?"
    )
    ebr = an.explicit_by_rank(df)
    insight_card(
        "🎙️", "Clean-leaning overall, but explicit charts high",
        f"<b>{es_top['Clean']:.1f}%</b> of entries are clean-rated, yet explicit share is highest in the "
        f"Top 10 ({ebr.get('Top 10', float('nan')):.1f}%) and lowest in positions 21-50 "
        f"({ebr.get('21-50', float('nan')):.1f}%) — explicit tracks face a higher bar to chart at all, but "
        "the ones that do break through tend to break through strongly.",
        ATLANTIC_GOLD,
    )

    es = an.explicit_share(df)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(values=es.values, names=es.index,
                      color_discrete_sequence=[ATLANTIC_RED, ATLANTIC_TEAL], hole=DONUT_HOLE)
        fig.update_traces(textinfo="percent")
        donut_center(fig, es["Explicit"], "Explicit")
        fig.update_layout(title="Explicit vs. Clean Share")
        st.plotly_chart(style_donut(fig), width="stretch")
    with c2:
        fig2 = px.bar(ebr, labels={"value": "Explicit share (%)", "rank_group": "Chart position"},
                       color_discrete_sequence=[ATLANTIC_RED])
        fig2.update_layout(showlegend=False, title="Explicit Content by Chart Position")
        st.plotly_chart(style_fig(fig2, legend=False, height=DONUT_HEIGHT), width="stretch")

    eot = an.explicit_over_time(df)
    fig3 = px.line(eot, markers=True, labels={"value": "Explicit share (%)", "date": "Month"},
                    color_discrete_sequence=[ATLANTIC_RED])
    fig3.update_layout(showlegend=False, title="Explicit Content Share Over Time")
    st.plotly_chart(style_fig(fig3, legend=False), width="stretch")

    st.markdown("#### Explicit Share Heatmap: Chart Position × Time")
    st.caption("Has the explicit/clean balance at each chart tier shifted over the analysis window?")
    heat = an.explicit_heatmap_by_rank_and_time(df)
    if heat.shape[0] >= 2:
        fig_heat = px.imshow(
            heat.T, aspect="auto", color_continuous_scale=[ATLANTIC_TEAL, "#FFFFFF", ATLANTIC_RED],
            labels=dict(x="Quarter", y="Chart position", color="Explicit %"),
            zmin=0, zmax=100,
        )
        fig_heat.update_xaxes(tickformat="%b %Y")
        fig_heat.update_layout(height=320, title="Explicit Share (%) by Chart Tier and Quarter")
        st.plotly_chart(style_fig(fig_heat, legend=False), width="stretch")
    else:
        st.info("Not enough time range in the current filter selection to build a heatmap.")

    st.caption(
        "Cultural read: roughly two-thirds of UK Top 50 entries are clean-rated. Explicit content is more "
        "prevalent inside the Top 10 than in positions 21-50, suggesting explicit tracks that do break "
        "through tend to break through strongly, consistent with UK radio/media's more conservative default "
        "posture toward explicit content."
    )

# =============================================================================
# TAB 4: FORMAT STRATEGY (ALBUM TYPE)
# =============================================================================
with tab_album:
    section_narrative(
        "Do singles or albums dominate the UK Top 50, does that balance shift by chart tier, and does a "
        "bigger (deluxe) release actually help or hurt a track's individual popularity?"
    )
    ats = an.album_type_share(df)
    rfr = an.release_format_by_rank(df)
    single_top5_v = rfr["single"].get("Top 5", float("nan")) if "single" in rfr else float("nan")
    insight_card(
        "💿", "Singles win the top; albums win volume",
        f"Album cuts are <b>{ats.get('album', 0):.1f}%</b> of all entries vs. <b>{ats.get('single', 0):.1f}%</b> "
        f"singles overall — but inside the Top 5, singles are the majority format at <b>{single_top5_v:.1f}%</b>, "
        "consistent with a lead-single-to-the-top, deluxe-album-for-volume release strategy.",
        ATLANTIC_RED,
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(values=ats.values, names=[i.title() for i in ats.index],
                     color_discrete_sequence=PALETTE, hole=DONUT_HOLE)
        fig.update_traces(textinfo="percent")
        donut_center(fig, ats.get("album", 0), "Album")
        fig.update_layout(title="Release Format Share")
        st.plotly_chart(style_donut(fig), width="stretch")
    with c2:
        fig2 = px.bar(rfr, barmode="stack",
                      color_discrete_sequence=[ATLANTIC_RED, ATLANTIC_NAVY, ATLANTIC_GOLD],
                      labels={"value": "Share (%)", "rank_group": "Chart position"})
        fig2.update_layout(title="Release Format by Chart Position")
        st.plotly_chart(style_fig(fig2, height=DONUT_HEIGHT), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("#### Album Size vs. Playlist Inclusion")
        bucket_counts = an.album_size_vs_inclusion(df)
        fig3 = px.bar(bucket_counts, labels={"value": "Playlist entries", "index": "Album size (tracks)"},
                      color_discrete_sequence=[ATLANTIC_TEAL])
        fig3.update_layout(showlegend=False, title="Chart Footprint by Album Size")
        st.plotly_chart(style_fig(fig3, legend=False, height=360), width="stretch")
    with c4:
        st.markdown("#### Album Size vs. Average Popularity")
        pop_by_size = an.album_size_vs_popularity(df)
        fig4 = px.bar(pop_by_size, labels={"value": "Avg. popularity score", "album_size_bucket": "Album size (tracks)"},
                      color_discrete_sequence=[ATLANTIC_GOLD])
        fig4.update_layout(showlegend=False, title="Per-Track Popularity by Album Size")
        st.plotly_chart(style_fig(fig4, legend=False, height=360), width="stretch")
        st.caption(
            "Bigger isn't automatically better on a per-track basis: extended/deluxe releases (20+ tracks) "
            "tend to average slightly lower per-track popularity than tighter releases, even though they "
            "generate more total chart entries."
        )

# =============================================================================
# TAB 5: DURATION PATTERNS
# =============================================================================
with tab_duration:
    section_narrative(
        "Is there a UK-specific sweet spot for track length, and does duration relate to how popular a track "
        "becomes?"
    )
    dvp = an.duration_vs_popularity(df)
    dd = an.duration_distribution(df)
    insight_card(
        "⏱️", "A mild pull toward tighter runtimes",
        f"The average UK Top 50 track runs <b>{an.kpi_summary(df, exploded)['Avg Track Duration (mm:ss)']}</b>, "
        f"with <b>{dd.get('Standard (2:30-3:30)', 0):.1f}%</b> of entries in the 2:30–3:30 \"standard\" band. "
        "The most popular quartile of tracks runs slightly shorter on average than the least popular quartile — "
        "a modest but consistent effect.",
        ATLANTIC_TEAL,
    )

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(dd, labels={"value": "Share of entries (%)", "duration_bucket": "Duration"},
                     color_discrete_sequence=[ATLANTIC_GOLD])
        fig.update_layout(showlegend=False, title="Duration Distribution")
        st.plotly_chart(style_fig(fig, legend=False, height=360), width="stretch")
    with c2:
        fig2 = px.bar(dvp, labels={"value": "Avg duration (sec)", "popularity_bucket": "Popularity quartile"},
                      color_discrete_sequence=[ATLANTIC_TEAL])
        fig2.update_layout(showlegend=False, title="Duration vs. Popularity Quartile")
        st.plotly_chart(style_fig(fig2, legend=False, height=360), width="stretch")

    st.markdown("#### Duration vs. Popularity (Track-Level)")
    st.caption("Each point is one playlist entry. A gentle downward trend would mirror the quartile-bucket finding above.")
    scatter_df = df.sample(min(3000, len(df)), random_state=42) if len(df) > 3000 else df
    fig_scatter = px.scatter(
        scatter_df, x="duration_sec", y="popularity", color="is_explicit",
        color_discrete_map={True: ATLANTIC_RED, False: ATLANTIC_TEAL},
        opacity=0.45,
        labels={"duration_sec": "Duration (seconds)", "popularity": "Popularity score", "is_explicit": "Explicit"},
        trendline="ols" if len(scatter_df) > 5 else None,
    )
    fig_scatter.update_layout(height=440, title="Duration vs. Popularity, colored by Explicit Flag")
    st.plotly_chart(style_fig(fig_scatter), width="stretch")

    stats = an.duration_summary_stats(df)
    st.markdown("**Summary statistics (seconds)**")
    st.dataframe(stats.to_frame("duration_sec").T, width="stretch")

# =============================================================================
# TAB 6: MARKET HEALTH
# =============================================================================
with tab_market:
    section_narrative(
        "A consolidated view of every market-structure KPI, how key metrics relate to one another, and how "
        "much fresh artist turnover the chart sees over time."
    )
    kpis = an.kpi_summary(df, exploded)
    insight_card(
        "📈", "Overall market composition",
        f"Content Variety Index of <b>{an.content_variety_index(df):.1f}</b>/100 blends artist diversity, "
        f"album-format mix, and explicit/clean balance into one figure — use it to track whether the market's "
        "overall composition is becoming more or less varied as new data comes in.",
        ATLANTIC_NAVY,
    )

    st.markdown("#### KPI Summary")
    kpi_items = list(kpis.items())
    n_cols = 4
    for row_start in range(0, len(kpi_items), n_cols):
        row_items = kpi_items[row_start:row_start + n_cols]
        cols = st.columns(n_cols)
        for col, (label, value) in zip(cols, row_items):
            col.metric(label, value)

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.markdown("#### Diversity Trend Over Time")
    uapd = an.unique_artists_per_day(exploded)
    fig = px.line(uapd, labels={"value": "Unique artists that day", "date": "Date"},
                  color_discrete_sequence=[ATLANTIC_NAVY])
    fig.update_layout(showlegend=False, title="Daily Unique Artist Count")
    st.plotly_chart(style_fig(fig, legend=False, height=360), width="stretch")

    st.markdown("#### UK / Domestic vs. International Trend")
    try:
        dit = an.domestic_vs_international_trend(exploded)
        fig2 = px.line(dit[[UK, INTL]], markers=True,
                       labels={"value": "Share of appearances (%)", "date": "Quarter"},
                       color_discrete_sequence=[ATLANTIC_NAVY, ATLANTIC_RED])
        fig2.update_layout(title="Domestic vs. International Share Over Time")
        st.plotly_chart(style_fig(fig2, height=360), width="stretch")
    except Exception:
        st.info("Not enough data in the current filter window to compute a trend.")

# =============================================================================
# TAB 7: RECOMMENDATIONS
# =============================================================================
with tab_reco:
    section_narrative(
        "Strategic implications drawn from the full analysis — artist signing, UK marketing, release-format "
        "planning, and cross-border promotion. These recommendations reflect patterns across the complete "
        "dataset; use the sidebar filters elsewhere in this dashboard to stress-test them against specific "
        "artists, time windows, or content types."
    )

    r1, r2 = st.columns(2)
    rec_card(
        r1, "🏆", "Artist Signing Strategy", "PORTFOLIO",
        [
            f"Favor portfolio breadth over concentrated superstar bets — Top-5 concentration is just "
            f"{conc['top_n_share_pct']:.1f}% (HHI {conc['hhi']:.0f}), rewarding a wide roster.",
            "Prioritize UK artist development for <b>Top 20 sustainability</b> rather than Top 5 breakthrough — "
            "that's where domestic representation is comparatively strongest.",
            "Scout within existing UK genre-collaboration clusters (drill/rap, garage/pop, drum &amp; bass) — "
            "these networks show self-reinforcing collaboration density a new signing can plug into.",
        ],
        ATLANTIC_NAVY,
    )
    rec_card(
        r2, "📣", "UK-Specific Marketing", "CONTENT",
        [
            "Treat explicit content as a chart-<i>entry</i> hurdle, not a chart-<i>peak</i> ceiling — once an "
            "explicit track charts, it's well-positioned to reach the Top 10.",
            "Maintain clean/radio-edit versions as standard practice, given the market's roughly two-to-one "
            "clean-to-explicit composition and its relevance to broadcast/editorial playlist eligibility.",
            "International competition is fiercest at the very top of the chart — UK marketing spend may see "
            "better returns sustaining mid-chart presence for domestic acts than displacing the Top 5.",
        ],
        ATLANTIC_GOLD,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    r3, r4 = st.columns(2)
    rec_card(
        r3, "💿", "Release Format Optimization", "STRATEGY",
        [
            "For a <b>Top 5 peak</b>: lead with a focused single campaign — singles are the majority format "
            "inside the Top 5 despite being a minority of the chart overall.",
            "For <b>sustained chart real estate</b>: plan a deluxe/expanded-tracklist release — deluxe-scale "
            "albums (13-20 tracks) show the largest aggregate chart footprint of any album-size bucket.",
            "Standard-length albums (6-12 tracks) are comparatively under-represented — consider a hybrid: "
            "early single push, followed by a later deluxe expansion.",
        ],
        ATLANTIC_RED,
    )
    rec_card(
        r4, "🌍", "Cross-Border Promotion", "GLOBAL",
        [
            f"With international artists holding {dom_intl.get('International', 0):.1f}% of UK chart "
            "appearances, existing US/global cross-border promotion infrastructure is directly reusable for "
            "UK chart performance.",
            "For UK-origin artists targeting international crossover, brokering a collaboration with an "
            "established international act in the same genre is a proven bridge mechanic already visible in "
            "the data (e.g. Chase &amp; Status × Stormzy).",
            "Track the UK/domestic vs. international trend over time (Health tab) to catch shifts in "
            "how open the UK market is to crossover acts before they show up in signing outcomes.",
        ],
        ATLANTIC_TEAL,
    )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    st.caption(
        "📄 These recommendations are grounded in the companion research paper, which documents complete "
        "methodology, data-cleaning decisions, and section-by-section findings by chart-position tier."
    )

st.markdown("---")
st.caption(
    "Data: Atlantic Recording Corporation daily UK Top 50 playlist snapshots "
    f"({validation_report['n_rows_raw']:,} raw rows, "
    f"{df_full['date'].min().date()} – {df_full['date'].max().date()}). "
    "Artist collaborations parsed on the '&' delimiter with protection for act names "
    "that legitimately contain '&' or ',' (e.g. Chase & Status, Tyler, The Creator). "
    "Nationality classification is based on publicly known artist origin; "
    "unclassified acts are shown as their own transparent category."
)



