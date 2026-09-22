# United Kingdom Top 50 Playlist Market Structure Artist Diversity and Content Localization Analysis

![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white)
![Internship evaluation](https://img.shields.io/badge/Internship%20evaluation-8%2F10-brightgreen)

A reproducible music-market analytics portfolio project covering artist presence, collaboration, content, release format, duration and geographic representation across a supplied UK Top 50 dataset.

## Project Context

This project was originally completed with Unified Mentor Pvt. Ltd. as part of a Data Analyst Intern placement from 25 April 2026 to 25 July 2026. Interns were offered multiple project options across different domains, and this project was selected from the Entertainment category. The analysis is structured around an Atlantic Recording Corporation business scenario and is presented here as a portfolio case study, not as evidence that Atlantic was the employer or client or that this was an official Atlantic engagement.

The current repository is an improved post-evaluation version of the original internship submission. Its business scope, dashboard and core visual framework are preserved, while analytical definitions, data quality, reproducibility, testing and methodology documentation have been strengthened.

## Internship Project Evaluation

| Field | Original evaluation record |
|---|---|
| Status | Evaluated |
| Rating | 8/10 |
| Evaluation | Excellent |
| Company | Unified Mentor Pvt. Ltd. |
| Role | Data Analyst Intern |
| Internship period | 25 April 2026 - 25 July 2026 |
| Category | Entertainment |
| Submitted | 25 April 2026 |
| Evaluated | 5 August 2026 |

The evaluator described the original submission as a well-developed, highly interactive project examining the structure and behaviour of the UK music market through more than 27,000 playlist entries and 359 artists. The feedback highlighted artist concentration, collaborations, explicit and clean content, release formats, track duration, market diversity, and UK/domestic versus international representation. It cited approximately 15.3% Top-5 concentration, a roughly 17% collaboration ratio, 32% explicit content and approximately 34% UK/domestic artist share.

The evaluator also recommended greater methodological transparency for the Content Variety Index, HHI, diversity score, nationality classification and collaboration metrics. The original feedback referred to 803 “unique songs,” reflecting the submitted methodology. The current project instead distinguishes 803 raw song titles, 798 normalized titles and 833 dataset-local recording proxies. The historical record is preserved in [`docs/internship_evaluation.md`](docs/internship_evaluation.md).

## Improvements After Evaluation

The repository demonstrates the feedback loop **submission → evaluation → methodology review → remediation → validation**. The post-evaluation version:

- separates 555 dates from 556 reconstructed chart snapshots;
- distinguishes chart entries, song titles, recording proxies and artist credits;
- separates cumulative Top-5/10/20 thresholds from exclusive rank bands;
- separates repeated collaboration appearances from unique collaborative recordings;
- supports full-credit and fractional-entry artist weighting;
- replaces the period-length-sensitive diversity score and removes the arbitrary Content Variety Index;
- adds snapshot entropy, effective artists and explicit full/fractional HHI definitions;
- documents nationality methodology and preserves an Unclassified category;
- adds deterministic validation, automated tests, CI and one-command builds;
- regenerates all figures and reports from one analytics layer; and
- frames business findings as descriptive evidence and testable hypotheses rather than causal conclusions.

## Business Objective and Analytical Scope

The case study examines market structure and content composition within the supplied UK Top 50 observations. It covers artist presence and concentration, collaboration, explicit content, release formats, duration, nationality classification and changes across chart position bands and time.

## Dataset and Provenance

The dataset was supplied by Unified Mentor Pvt. Ltd. as part of the Data Analyst internship project materials for this Entertainment-category case study. The supplied materials do not identify the original upstream provider, collection URL, collection methodology, or formal upstream dataset license.

The raw file remains at `data/Atlantic_United_Kingdom.csv` and is treated as immutable. Processed outputs are generated under `data/processed/`. No formal redistribution license is claimed; code licensing and dataset usage rights are separate questions.

## Analytical Units

- **Chart entry:** one observed position in one reconstructed snapshot.
- **Snapshot:** one complete ordered Top-50 ranking; a calendar date is not automatically one snapshot.
- **Song title:** raw `song` text, not a recording identifier.
- **Recording proxy:** dataset-local key formed from normalized title and exact duration. It is not a Spotify ID, ISRC or global identifier.
- **Artist credit:** one artist credited on one chart entry. Full weighting gives each artist one credit; fractional weighting divides one entry across all credited artists.

## Methodology

- **Snapshots:** source order is preserved and a later reset to position 1 starts another deterministic snapshot sequence within the date.
- **Artist parsing:** protected act names are applied before general collaborator delimiters, followed by deterministic casing normalization.
- **Recording identity:** normalized title plus exact duration produces 833 proxies while avoiding 25 splits caused by changing artist credits. Proxy-level metadata uses the earliest observed row after sorting by date and source row; this deterministic first-observed rule also determines proxy-level collaboration attributes.
- **Ranks:** Top 5, Top 10 and Top 20 are cumulative; `1-5`, `6-10`, `11-20` and `21-50` are exclusive bands.
- **Collaboration:** chart-entry appearances and distinct collaborative proxies are reported separately.
- **Weighting:** full artist-credit and fractional chart-entry measures are both available.
- **Diversity:** snapshot unique artists, bounded artist-credit uniqueness, fractional Shannon entropy and effective artists replace the original custom score.
- **Concentration:** period-wide full-credit HHI is separated from fractional snapshot HHI. Alternate weighting views remain in report data.
- **Nationality:** UK / Domestic, International and Unclassified are reported; uncertain acts are not guessed.

## Key Corrected Findings

| Metric | Corrected value |
|---|---:|
| Raw and processed chart entries | 27,800 |
| Dates / reconstructed snapshots | 555 / 556 |
| Raw / normalized titles / recording proxies | 803 / 798 / 833 |
| Parsed artists / artist-credit observations | 359 / 34,492 |
| Collaboration share, entries / proxies | 17.75% / 15.61% |
| Period-wide Top-5 full-credit share | 15.29% |
| Period-wide full-credit HHI | 116.2 |
| Mean / median fractional snapshot HHI | 474.1 / 338.0 |
| Mean unique artists per snapshot | 48.53 |
| Mean artist-credit uniqueness ratio | 0.781 |
| Mean Shannon entropy / effective artists | 3.585 / 37.67 |
| Explicit chart-entry share | 32.06% |
| UK / International / Unclassified full-credit share | 34.68% / 64.61% / 0.70% |
| Mean chart-entry duration | 3:17 |

## Dashboard

The Streamlit dashboard retains eight sections: Overview, Artists, Collaboration, Content, Formats, Duration, Health and Strategy. The Health section exposes validation status and source-quality findings while executive sections use denominator-specific business labels.

```powershell
streamlit run app.py
```

## Project Architecture

```text
Immutable source CSV
        ↓
Source validation and snapshot reconstruction
        ↓
Deterministic cleaning, artist parsing and recording proxies
        ↓
Canonical entries, artist credits and recording tables
        ↓
Data-quality validation and canonical analytics
   ↙            ↓              ↘
Dashboard    CSV / JSON      Figures
                                  ↓
                            DOCX reports
```

## Repository Structure

```text
.
├── app.py
├── data/Atlantic_United_Kingdom.csv
├── data/processed/
├── src/
├── scripts/
├── tests/
├── outputs/figures/
├── docgen/
├── reports/
├── docs/
├── .github/workflows/ci.yml
└── requirements.txt
```

## Data Quality

`src/data_quality.py` reports `PASS`, `WARNING` and `FAIL`. Critical schema, parsing, domain, position, snapshot and reconciliation defects stop the build. Missing dates, inferred snapshot boundaries, cross-snapshot repeated rows, metadata changes, title collisions and incomplete nationality sourcing remain visible warnings rather than silent repairs.

The March 1, 2025 anomaly is retained as two complete snapshots. Four absent dates are reported and not imputed. Current reports are written to `outputs/data_quality_report.json` and `.csv`.

## Testing and CI

The pytest suite covers parsing, snapshots, duplicates, recording identity, rank logic, collaboration, weighting, direct snapshot Shannon/effective-artist/HHI regressions, and real-dataset integration. GitHub Actions uses Python 3.12, compiles the project, runs pytest, validation and methodology verification, installs Node dependencies with `npm ci`, then builds canonical processed data, figures and DOCX reports. It does not require secrets.

Recommended remote settings: require the CI workflow on pull requests, require one review, block force pushes and restrict direct pushes to `main`.

## Setup

Python 3.12 is the tested version.

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Push-Location docgen
npm ci
Pop-Location
```

## Run Analysis

```powershell
python -m pytest -q --tb=short
python scripts/validate.py
python scripts/build_all.py
```

## Build Reports

```powershell
Push-Location docgen
npm run build
Pop-Location
```

Generated reports are stored in `reports/` and consume canonical values from `outputs/report_data.json`.

## Limitations

- Snapshot boundaries are inferred because the source lacks native timestamps or snapshot IDs.
- Recording proxies remain dataset-local and may differ from native platform identifiers. Proxy-level metadata is the earliest observed row for each proxy, not a modal or inferred canonical truth.
- Four calendar dates are missing and are not imputed.
- Artist credits and other metadata can change over time.
- Nationality classification is manually curated and lacks per-artist source citations.
- The supplied coverage is a playlist/chart-style dataset and is not established as the official UK Singles Chart.
- Dataset licensing and third-party redistribution terms are not documented.
- Observational associations do not establish causal release-strategy effects.

## Original Submission Links

These confirmed working links point to the original internship submission. They are distinct from the current post-evaluation remediated portfolio version in this repository.

- [Code](https://github.com/mimohnaik-git/Atlantic-uk-playlist-analysis)
- [Report](https://drive.google.com/file/d/1gWT_Mc9cw9j6JKibKmkkua_q7trmI9bm/view?usp=sharing)
- [Live Project Material](https://drive.google.com/file/d/18ZdTJypzPweQa78qbFkkIg50_yatizUx/view?usp=sharing)
- [Streamlit](https://atlantic-uk-playlist-analysis-xnlekfzl2sx8padpthqvme.streamlit.app/)

## Suggested Repository Metadata

**Description:** Post-evaluation Data Analyst internship case study analyzing UK Top 50 market structure, artist diversity, collaborations and content localization.

**Topics:** `data-analysis`, `python`, `pandas`, `streamlit`, `music-analytics`, `data-visualization`, `analytics-dashboard`, `data-quality`, `pytest`, `portfolio-project`

---

### Metric methodology

The headline concentration and diversity measures are defined explicitly so that the dashboard can be reproduced and interpreted at the correct analytical grain.

- **HHI:** `10,000 × Σ(pᵢ²)`, where `pᵢ` is an artist's share. **Period-wide HHI** uses full artist-credit shares across the selected period. **Snapshot HHI** uses fractional entry weights so every chart entry contributes a total artist weight of 1 across its credited artists.
- **Shannon diversity:** `H = -Σ(pᵢ × ln pᵢ)` using fractional artist shares within each reconstructed Top-50 snapshot.
- **Effective artist count:** `exp(H)`. This converts Shannon entropy into the equivalent number of equally represented artists and is calculated for each snapshot before averaging.
- **Collaboration:** reported separately at chart-entry grain and recording-proxy grain. Repeated co-credited appearances are not treated as additional unique collaborations.
- **Nationality:** manually curated from the billed act's primary origin. Multinational or uncertain acts remain **Unclassified**. Full artist-credit and fractional-entry weighting are distinguished where relevant.

A fuller calculation note is available in `docs/metric_methodology.md`.

#### Retired legacy measures

The earlier **Diversity Score** and custom **Content Variety Index** are not used for headline reporting.

The Diversity Score was sensitive to the length of the observation window, while the Content Variety Index combined artist variety, release-format mix, and explicit/clean balance into a custom composite.

The final analysis instead uses snapshot-level unique artists, Shannon diversity, effective artist count, and HHI.
