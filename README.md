# UK Top 50 Playlist — Market Structure, Artist Diversity & Content Localization Analysis

**Client:** Atlantic Recording Corporation
**Prepared via:** Unified Mentor
**Dataset:** Daily UK Top 50 playlist snapshots, 18 May 2024 – 27 Nov 2025 (27,800 raw entries)

This project analyzes the structural composition of the UK Top 50 playlist —
artist dominance, collaboration dynamics, explicit-content prevalence, release
format strategy, and track duration patterns — to give Atlantic Recording
Corporation region-specific intelligence for UK artist signing, marketing, and
release strategy, distinct from a US-style popularity-trend analysis.

## Project Structure

```
atlantic-uk-playlist-analysis/
├── app.py                        # Streamlit dashboard (main entry point)
├── requirements.txt
├── .streamlit/config.toml        # Dashboard theme
├── data/
│   └── Atlantic_United_Kingdom.csv   # Raw source data
├── src/
│   ├── data_prep.py               # Validation, cleaning, artist-name splitting
│   ├── artist_nationality.py      # UK / International classification
│   ├── analytics.py               # All KPIs & metrics
│   └── make_charts.py             # Generates static PNG charts for reports
├── outputs/
│   ├── figures/                   # 16 generated chart PNGs
│   └── analytics_output.txt       # Full console KPI dump
└── reports/
    ├── UK_Top50_Research_Paper.docx
    └── UK_Top50_Executive_Summary.docx
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run the dashboard

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## Reproduce the analysis / regenerate charts

```bash
python3 src/data_prep.py     # cleans data -> data/clean_playlist.parquet, data/exploded_artists.parquet
python3 src/analytics.py     # prints full KPI report to console
python3 src/make_charts.py   # regenerates all PNGs in outputs/figures/
```

## Regenerate the Word reports

```bash
# 1. Re-export the metrics JSON the report scripts read from (after any analytics change)
python3 src/export_report_data.py

cd docgen
npm install
node build_paper.js          # -> reports/UK_Top50_Research_Paper.docx
node build_exec_summary.js   # -> reports/UK_Top50_Executive_Summary.docx
```

## Key Data-Cleaning Decisions (see research paper §2 for full detail)

- **Collaboration parsing:** the `artist` field is split on the `&` delimiter
  per the brief, with `,` treated as a secondary delimiter. A small
  **protected-name list** prevents genuine act names that contain `&` or `,`
  (e.g. *Chase & Status*, *Tyler, The Creator*, *Earth, Wind & Fire*) from
  being incorrectly fractured into separate "collaborators" — verified by
  confirming e.g. "Chase" and "Status" appeared only ever in lock-step
  counts before the fix.
- **Casing normalization:** artist name variants that differ only in
  capitalization (e.g. "Charli xcx" vs "Charli XCX") are merged to the
  most frequently used casing.
- **Nationality classification:** UK/Domestic vs. International is based on
  each act's publicly known country of origin. Acts that could not be
  confidently classified (~0.7% of appearances — soundtrack/media credits,
  novelty entries, or genuinely obscure acts) are reported as their own
  transparent "Unclassified" category rather than guessed.

## Deliverables

1. **Research paper** (`reports/UK_Top50_Research_Paper.docx`) — full EDA,
   methodology, findings, and strategic recommendations.
2. **Streamlit dashboard** (`app.py`) — a polished executive dashboard with
   8 tabs: an Overview (headline findings), Artists (leaderboard,
   concentration curve, treemap, domestic/international split), Collaboration
   (top-pairs chart + optional interactive network), Content (explicit/clean,
   including a rank-tier × time heatmap), Formats (single vs. album, including
   per-track popularity by album size), Duration (including a
   duration-vs-popularity scatter), Health (KPI grid + diversity/domestic
   trends), and Strategy (recommendation cards for signing, marketing,
   release format, and cross-border promotion). All 4 filters apply across
   every tab.
3. **Executive summary** (`reports/UK_Top50_Executive_Summary.docx`) —
   condensed, government-stakeholder-facing summary of findings and
   recommendations.

## User Capabilities in the Dashboard

- Date range selector
- Artist filter (multi-select)
- Solo vs. collaboration toggle
- Album type filter
# Atlantic-uk-playlist-analysis
