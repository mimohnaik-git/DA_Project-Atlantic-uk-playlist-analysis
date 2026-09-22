const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, TableOfContents, Header, Footer, PageNumber,
  NumberFormat, LevelFormat, convertInchesToTwip, VerticalAlign,
} = require("docx");

const data = JSON.parse(fs.readFileSync("../outputs/report_data.json", "utf-8"));

// ---- Brand palette ----
const NAVY = "0B1F3A";
const RED = "E4572E";
const GOLD = "D9A441";
const TEAL = "2C7873";
const GREY = "8A94A6";
const LIGHT_GREY = "F2F4F7";

function img(path, widthPx, heightPx, maxWidthIn = 6.3) {
  const buf = fs.readFileSync(path);
  const ratio = heightPx / widthPx;
  const widthIn = maxWidthIn;
  const heightIn = widthIn * ratio;
  return new ImageRun({
    data: buf,
    type: "png",
    transformation: { width: Math.round(widthIn * 96), height: Math.round(heightIn * 96) },
  });
}

function figure(path, widthPx, heightPx, caption, maxWidthIn = 6.3) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 200, after: 80 },
      children: [img(path, widthPx, heightPx, maxWidthIn)],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 240 },
      children: [new TextRun({ text: caption, italics: true, size: 19, color: "555555" })],
    }),
  ];
}

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 200 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 300, after: 160 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 240, after: 120 } });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 180, line: 276 },
    children: [new TextRun({ text, size: 22, ...opts })],
  });
}
function bullet(text, level = 0) {
  return new Paragraph({
    bullet: { level },
    spacing: { after: 100 },
    children: [new TextRun({ text, size: 22 })],
  });
}

function kpiTable(rows, headers = ["Metric", "Value"]) {
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map(htext => new TableCell({
      width: { size: 50, type: WidthType.PERCENTAGE },
      shading: { fill: NAVY, type: ShadingType.CLEAR, color: "auto" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 100, bottom: 100, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: htext, bold: true, color: "FFFFFF", size: 20 })] })],
    })),
  });
  const bodyRows = rows.map((r, i) => new TableRow({
    children: r.map(cell => new TableCell({
      width: { size: 50, type: WidthType.PERCENTAGE },
      shading: { fill: i % 2 === 0 ? "FFFFFF" : LIGHT_GREY, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ children: [new TextRun({ text: String(cell), size: 20 })] })],
    })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    rows: [headerRow, ...bodyRows],
  });
}

function calloutBox(text, color = TEAL) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color },
      bottom: { style: BorderStyle.SINGLE, size: 4, color },
      left: { style: BorderStyle.SINGLE, size: 4, color },
      right: { style: BorderStyle.SINGLE, size: 4, color },
    },
    rows: [new TableRow({
      children: [new TableCell({
        shading: { fill: LIGHT_GREY, type: ShadingType.CLEAR, color: "auto" },
        margins: { top: 160, bottom: 160, left: 200, right: 200 },
        children: [new Paragraph({ children: [new TextRun({ text, size: 21, italics: true })] })],
      })],
    })],
  });
}

// ---------------------------------------------------------------------------
// Build KPI table rows
// ---------------------------------------------------------------------------
const kpiRows = Object.entries(data.kpi_summary).map(([k, v]) => [k, String(v)]);

const top15Rows = Object.entries(data.top_20_artists).slice(0, 15).map(([a, c], i) => [String(i + 1), a, String(c)]);

const collabPairRows = data.top_collab_pairs.slice(0, 10).map((r, i) =>
  [String(i + 1), r.artist_a, r.artist_b, String(r.weight)]);

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", run: { size: 32, bold: true, color: NAVY, font: "Calibri" }, paragraph: { spacing: { before: 400, after: 200 } } },
      { id: "Heading2", name: "Heading 2", run: { size: 26, bold: true, color: RED, font: "Calibri" } },
      { id: "Heading3", name: "Heading 3", run: { size: 23, bold: true, color: NAVY, font: "Calibri" } },
    ],
  },
  sections: [
    // ------------------------------------------------------------------
    // TITLE PAGE
    // ------------------------------------------------------------------
    {
      properties: { page: { size: { width: 11906, height: 16838 } } }, // A4
      children: [
        new Paragraph({ spacing: { before: 1600 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "ATLANTIC RECORDING CORPORATION", bold: true, size: 24, color: RED, allCaps: true })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 300, after: 300 },
          children: [new TextRun({ text: "United Kingdom Top 50 Playlist", bold: true, size: 52, color: NAVY })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 600 },
          children: [new TextRun({ text: "Market Structure, Artist Diversity & Content Localization Analysis", bold: true, size: 32, color: RED })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 100 },
          children: [new TextRun({ text: "Research Paper", size: 26, italics: true, color: GREY })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 800, after: 60 },
          children: [new TextRun({ text: `Analysis period: ${data.date_min} – ${data.date_max}`, size: 22 })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { after: 60 },
          children: [new TextRun({ text: `${data.n_rows.toLocaleString()} playlist entries · ${data.n_unique_artists} unique artists · ${data.n_unique_songs} unique songs`, size: 22 })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER, spacing: { before: 1200 },
          children: [new TextRun({ text: "Prepared for Atlantic Recording Corporation by Unified Mentor", size: 20, color: GREY })],
        }),
        new Paragraph({ children: [new PageBreak()] }),

        // Table of Contents (static — renders reliably everywhere, unlike a
        // TOC field which requires the user to manually "Update Field" in
        // Word before it populates, and shows blank otherwise).
        h1("Table of Contents"),
        ...[
          "Executive Overview",
          "1. Background & Context",
          "     1.1 Problem Statement",
          "2. Data & Methodology",
          "     2.1 Dataset",
          "     2.2 Data Validation & Standardization",
          "     2.3 Nationality Classification (UK / Domestic vs. International)",
          "     2.4 Metric Definitions",
          "3. Findings",
          "     3.1 Artist Dominance & Diversity",
          "     3.2 Domestic (UK) vs. International Artist Representation",
          "     3.3 Collaboration Structure",
          "     3.4 Content Explicitness",
          "     3.5 Album Structure & Release Strategy",
          "     3.6 Track Duration & Format",
          "     3.7 Market Structure Metrics — KPI Summary",
          "4. Strategic Recommendations",
          "     4.1 Artist Signing Strategy",
          "     4.2 UK-Specific Marketing Decisions",
          "     4.3 Release Format Optimization",
          "     4.4 Cross-Border Promotion Planning",
          "5. Limitations",
          "6. Conclusion",
          "Appendix A: Dataset Field Reference",
        ].map(t => new Paragraph({
          spacing: { after: 90 },
          children: [new TextRun({ text: t, size: 22, color: t.startsWith("     ") ? "444444" : NAVY, bold: !t.startsWith("     ") })],
        })),
        new Paragraph({ children: [new PageBreak()] }),

        // ------------------------------------------------------------------
        // EXECUTIVE OVERVIEW
        // ------------------------------------------------------------------
        h1("Executive Overview"),
        p(`This research paper analyzes ${data.n_rows.toLocaleString()} daily UK Top 50 playlist entries collected between ${data.date_min} and ${data.date_max} (${data.n_days} distinct playlist snapshots), covering ${data.n_unique_songs} unique songs by ${data.n_unique_artists} unique artists. The objective is to give Atlantic Recording Corporation a structural, culturally-grounded understanding of the UK market — distinct from a US-style popularity-trend analysis — to inform artist signing, UK-specific marketing, release-format strategy, and cross-border promotion planning.`),
        p("Five headline findings emerge from the data:"),
        bullet(`The UK Top 50 is a low-concentration, high-diversity market. The top five artists account for only ${data.concentration_top5.top_n_share_pct}% of all chart appearances (HHI = ${data.concentration_top5.hhi}), and ${data.n_unique_artists} distinct artists cycled through the chart over the eighteen-month window — evidence against a "hits factory" model dominated by a small artist roster.`),
        bullet(`International artists outweigh UK/domestic artists roughly two-to-one. International acts account for ${data.domestic_vs_intl["International"]}% of chart appearances versus ${data.domestic_vs_intl["UK / Domestic"]}% for UK/domestic artists — and the international skew is even sharper inside the Top 10 (${data.domestic_vs_intl_by_rank["International"]["Top 10"]}% international) than in positions 21-50 (${data.domestic_vs_intl_by_rank["International"]["21-50"]}% international).`),
        bullet(`Collaboration is a top-of-chart phenomenon. ${data.collab_ratio_pct}% of all entries are collaborations, but the collaboration rate peaks in the Top 10 (${data.collab_by_rank["Top 10"]}%) and is lowest in the Top 5 and the tail of the chart (positions 21-50), pointing to collaboration as a mid-chart breakthrough mechanic more than a top-of-chart guarantee.`),
        bullet(`UK listeners lean clean, but explicit content over-indexes at the top. ${data.explicit_share["Clean"]}% of entries are clean-rated overall, yet the explicit share is highest in the Top 10 (${data.explicit_by_rank["Top 10"]}%) and lowest in positions 21-50 (${data.explicit_by_rank["21-50"]}%).`),
        bullet(`Albums out-place singles on the chart, but singles dominate the very top. Album cuts account for ${data.album_type_share["album"]}% of all entries versus ${data.album_type_share["single"]}% for singles — yet inside the Top 5, singles are the majority format at ${data.release_format_by_rank["single"]["Top 5"]}%.`),
        p("Section 4 translates these findings into concrete recommendations for artist signing, marketing, and release-format strategy. Section 5 documents methodology limitations and data-quality caveats that should inform how confidently each finding is used."),
        new Paragraph({ children: [new PageBreak()] }),

        // ------------------------------------------------------------------
        // 1. BACKGROUND & CONTEXT
        // ------------------------------------------------------------------
        h1("1. Background & Context"),
        p("The UK music market is globally influential but structurally distinct from the US market Atlantic's prior analyses have focused on. Four characteristics motivate a UK-specific study:"),
        bullet("Strong domestic artist representation alongside heavy international crossover, in a market with its own broadcast, playlist-curation, and cultural gatekeeping norms (BBC Radio 1, UK-specific editorial playlists)."),
        bullet("A high prevalence of multi-artist collaborations, reflecting the UK's dense grime, drill, and dance/DJ-culture collaboration networks."),
        bullet("Listener and broadcaster sensitivity to explicit content that differs from the US market's norms."),
        bullet("Different album-vs-single consumption behavior than the US, shaped by UK deluxe-edition and \"track-stuffing\" release strategies."),
        p("Without a dedicated structural analysis, UK go-to-market strategy risks being copied wholesale from Atlantic's US playbook — ignoring exactly the cultural differences that determine whether a signing, marketing push, or release format succeeds in the UK. This paper addresses that gap directly, focusing on market structure (who dominates, and how concentrated is dominance), diversity (how many distinct artists cycle through), collaboration dynamics, content composition, and release-format strategy — rather than raw popularity trend-spotting."),

        h2("1.1 Problem Statement"),
        p("Despite daily access to UK Top 50 playlist data, stakeholders at Atlantic lacked clear answers to five questions, each addressed in Section 3 of this paper:"),
        bullet("How is artist dominance distributed in the UK market — is the chart concentrated in a handful of acts, or fragmented across many?"),
        bullet("Do UK charts favor domestic (UK) or international artists, and does that balance shift by chart position?"),
        bullet("How do collaborations influence chart presence, and at what rank tier do they matter most?"),
        bullet("Does explicit content perform differently in the UK than a US-style analysis would assume?"),
        bullet("How does album structure — single vs. album, and album size — affect chart success?"),

        // ------------------------------------------------------------------
        // 2. DATA & METHODOLOGY
        // ------------------------------------------------------------------
        h1("2. Data & Methodology"),
        h2("2.1 Dataset"),
        p(`The source dataset (Atlantic_United_Kingdom.csv) contains ${data.n_rows.toLocaleString()} daily UK Top 50 playlist snapshot rows spanning ${data.date_min} to ${data.date_max} (${data.n_days} distinct dates). Each row records: snapshot date, chart position (1-50), song title, credited artist(s), an Atlantic-API popularity score, track duration, album type (single/album/compilation), the parent album's total track count, an explicit-content flag, and an album artwork URL.`),

        h2("2.2 Data Validation & Standardization"),
        p("Validation confirmed the dataset is complete and well-formed: zero missing values across all fields, and all chart positions fall within the valid 1-50 range. Twelve exact-duplicate rows were identified and are flagged for exclusion in any strict deduplication pass, though they were left in place for this analysis since they do not materially change any reported share or ranking (well under 0.1% of rows)."),
        p("Two data-quality issues required active correction before any artist-level analysis could be trusted, both stemming from naive parsing of the multi-artist `artist` field:"),
        h3("Issue 1 — Band/duo names containing the collaboration delimiter"),
        p("The brief specifies splitting collaborations on the '&' delimiter. Applied naively, this incorrectly fractures act names that legitimately contain an ampersand — most consequentially \"Chase & Status\", a UK drum & bass duo. Before correction, \"Chase\" and \"Status\" appeared as two separate \"artists\" with identical appearance counts (482 each) in every single case — a statistical signature confirming they are one act, not two independent collaborators. A protected-name list (also covering \"Tyler, The Creator\", \"Earth, Wind & Fire\", \"Richy Mitch & The Coal Miners\", and \"Bobby \\\"Boris\\\" Pickett & The Crypt-Kickers\") shields these names from splitting while still correctly splitting genuine multi-artist credits such as \"Chase & Status & Stormzy\" into [\"Chase & Status\", \"Stormzy\"]."),
        h3("Issue 2 — Inconsistent capitalization of the same artist"),
        p("Some artists appear under multiple capitalizations of the same name (e.g. \"Charli xcx\" and \"Charli XCX\"), which would otherwise fragment one artist's chart footprint across two rows in any leaderboard. A canonicalization pass maps every lowercase-equivalent name variant to its single most frequently used exact casing across the full dataset."),
        calloutBox("Analytical impact: correcting these two issues changed the unique-artist count from an inflated 361 to a true 359, and moved \"Chase & Status\" from two phantom mid-table entries into a single top-11 act — directly affecting the artist dominance leaderboard in Section 3.1.", TEAL),
        p(""),
        p("The collaboration field is split on '&' as the primary delimiter and ',' as a secondary delimiter (several entries chain more than two collaborators using a comma, e.g. \"Baddiel, Skinner & Lightning Seeds\"), producing a clean per-collaborator list used for all artist-level (as opposed to entry-level) metrics."),

        h2("2.3 Nationality Classification (UK / Domestic vs. International)"),
        p(`To answer whether UK charts favor domestic or international artists, every act was classified as "UK / Domestic" or "International" based on its publicly known country of origin (not label, chart territory, or residence). This classification covered ${(100 - 0.7).toFixed(1)}% of all chart appearances; the remaining 0.7% — soundtrack/media credits (e.g. "Wicked Movie Cast"), novelty or ambience entries, and a small number of genuinely unverifiable act names — are reported as their own transparent "Unclassified" category rather than folded into either bucket.`),

        h2("2.4 Metric Definitions"),
        bullet("Artist Concentration Index (Top-5 share): the percentage of total artist-appearances (post-collaboration-split) accounted for by the five most-appearing artists."),
        bullet("Herfindahl-Hirschman Index (HHI): sum of squared artist appearance-shares, scaled 0-10,000; conventionally, HHI < 1,500 indicates a low-concentration/competitive market, 1,500-2,500 indicates moderate concentration, and > 2,500 indicates high concentration."),
        bullet("Diversity Score: unique artists ÷ total playlist entries — a higher score indicates more turnover/variety in who occupies the chart."),
        bullet("Collaboration Ratio: share of playlist entries credited to more than one collaborator."),
        bullet("Content Variety Index: a composite 0-100 score blending artist-name diversity, album-format entropy (single/album/compilation mix), and explicit/clean balance, used as a single \"market balance\" figure in Section 3.7."),
        bullet("Rank groups used throughout: Top 5, Top 10, Top 20, and 21-50."),

        new Paragraph({ children: [new PageBreak()] }),

        // ------------------------------------------------------------------
        // 3. FINDINGS
        // ------------------------------------------------------------------
        h1("3. Findings"),

        h2("3.1 Artist Dominance & Diversity"),
        p(`Across the full eighteen-month window, ${data.n_unique_artists} unique artists appeared in the UK Top 50. The market is notably fragmented: the top five artists — Taylor Swift, Sabrina Carpenter, Billie Eilish, Olivia Rodrigo, and Chappell Roan — together account for only ${data.concentration_top5.top_n_share_pct}% of all chart appearances, and the resulting HHI of ${data.concentration_top5.hhi} sits far below the 1,500 threshold conventionally associated with a concentrated market. The top ten artists extend to just ${data.concentration_top10.top_n_share_pct}% of appearances.`),
        ...figure("../outputs/figures/01_top_artists.png", 1416, 1059, "Figure 3.1 — Top 15 dominating artists by chart appearances (entry-days)."),
        p("Taylor Swift is a clear outlier at 2,093 appearances — roughly double the next-closest artist (Sabrina Carpenter, 965) — reflecting an unusually long, multi-era chart residency rather than a single campaign. Beyond the top two, appearance counts decline smoothly, with no other single artist approaching the same scale of dominance."),
        ...figure("../outputs/figures/02_concentration_curve.png", 1238, 1060, "Figure 3.2 — Cumulative concentration curve: the closer the curve sits to the diagonal, the more evenly chart presence is distributed across artists."),
        kpiTable(top15Rows, ["Rank", "Artist", "Chart appearances"]),
        p(""),
        calloutBox(`Strategic read: the UK Top 50 rewards a wide artist base rather than a small "hits factory" roster. A diversity score of ${data.kpi_summary["Diversity Score (unique artists / entries)"]} (unique artists ÷ entries) confirms meaningful week-to-week turnover in who occupies the chart, which argues for a broad, portfolio-style UK signing strategy over concentrating investment in a handful of superstar bets.`, TEAL),

        h2("3.2 Domestic (UK) vs. International Artist Representation"),
        p(`International artists substantially outweigh UK/domestic artists on the UK Top 50: ${data.domestic_vs_intl["International"]}% of chart appearances go to international acts versus ${data.domestic_vs_intl["UK / Domestic"]}% to UK/domestic acts (${data.domestic_vs_intl["Unclassified"]}% unclassified). This is a market genuinely open to international crossover, not a chart insulated by domestic-artist preference.`),
        ...figure("../outputs/figures/13_domestic_vs_international.png", 896, 732, "Figure 3.3 — UK/Domestic vs. International share of chart appearances.", 4.2),
        p(`The international skew is not uniform by chart position — it is more pronounced at the very top of the chart than further down. International artists hold ${data.domestic_vs_intl_by_rank["International"]["Top 5"]}% of Top 5 appearances and ${data.domestic_vs_intl_by_rank["International"]["Top 10"]}% of Top 10 appearances, compared to a less lopsided ${data.domestic_vs_intl_by_rank["International"]["Top 20"]}% in the Top 20 and ${data.domestic_vs_intl_by_rank["International"]["21-50"]}% in positions 21-50 — meaning UK/domestic artists' strongest relative foothold is actually in the Top 20 tier, not the very top or the long tail.`),
        ...figure("../outputs/figures/14_domestic_intl_by_rank.png", 1414, 878, "Figure 3.4 — UK/Domestic vs. International share by chart-position tier."),
        ...figure("../outputs/figures/16_domestic_intl_trend.png", 1597, 880, "Figure 3.5 — UK/Domestic vs. International share over time (quarterly)."),
        calloutBox("Strategic read: UK marketing plans should not assume a home-turf advantage for domestic signings at the very top of the chart — that tier is the most internationally competitive. UK artist development may see the clearest incremental payoff in building acts toward sustained Top 20 presence, where domestic representation is comparatively strongest.", TEAL),

        h2("3.3 Collaboration Structure"),
        p(`${data.collab_ratio_pct}% of all playlist entries are credited to more than one artist (${data.solo_vs_collab["Collaboration"].toLocaleString()} of ${(data.solo_vs_collab["Solo"] + data.solo_vs_collab["Collaboration"]).toLocaleString()} entries), averaging ${data.avg_collaborators} collaborators per song across the full dataset.`),
        ...figure("../outputs/figures/03_solo_vs_collab.png", 836, 877, "Figure 3.6 — Solo vs. collaborative track share.", 3.6),
        p(`Collaboration prevalence is not flat across the chart — it peaks in the Top 10 (${data.collab_by_rank["Top 10"]}%) and Top 20 (${data.collab_by_rank["Top 20"]}%), and is comparatively lower in the Top 5 (${data.collab_by_rank["Top 5"]}%) and in positions 21-50 (${data.collab_by_rank["21-50"]}%). This pattern positions collaboration as a mid-chart breakthrough mechanic — pairing artists appears especially effective for pushing into and through the middle of the Top 50 — rather than a prerequisite for reaching the very top or a fallback strategy for lower-charting tracks.`),
        ...figure("../outputs/figures/04_collab_by_rank.png", 1238, 878, "Figure 3.7 — Collaboration share by chart-position tier."),
        p("The chart below ranks the most frequent artist pairings by number of tracks co-credited together. UK drill/rap (Central Cee × Dave, 392 tracks), UK garage/pop (D-Block Europe × RAYE × cassö, 348 tracks per pair), and UK drum & bass (Chase & Status × Bou × Flowdan, 196 tracks per pair) dominate the top of the list — evidence of dense, genre-specific collaboration ecosystems rather than one homogenous UK collaboration culture. Most of these top pairings recur within a small, tight-knit group of collaborators rather than reflecting one-off features, consistent with the genre-cluster pattern described above."),
        ...figure("../outputs/figures/05_collab_network.png", 1995, 2073, "Figure 3.8 — Top 25 artist collaborator pairs by number of tracks co-credited together.", 5.4),
        kpiTable(collabPairRows, ["Rank", "Artist A", "Artist B", "Co-occurrences"]),
        p(""),
        calloutBox("Strategic read: genre-aligned pairing (signing or brokering collaborations within an artist's existing genre cluster, e.g. UK drill or UK dance/DnB) appears more likely to sustain chart presence than cross-genre pairing for its own sake — the network shows collaboration density concentrated within, not across, genre communities.", TEAL),

        h2("3.4 Content Explicitness"),
        p(`${data.explicit_share["Clean"]}% of UK Top 50 entries are clean-rated versus ${data.explicit_share["Explicit"]}% explicit — confirming the brief's premise of UK listener/broadcaster sensitivity to explicit content, at least in terms of overall chart composition.`),
        ...figure("../outputs/figures/06_explicit_share.png", 836, 877, "Figure 3.9 — Explicit vs. clean content share.", 3.6),
        p(`However, explicit content does not under-perform at the top of the chart — the opposite is true. Explicit share is highest in the Top 10 (${data.explicit_by_rank["Top 10"]}%) and Top 5 (${data.explicit_by_rank["Top 5"]}%), and lowest in positions 21-50 (${data.explicit_by_rank["21-50"]}%). Read together with the overall clean-leaning composition, this suggests explicit tracks face a higher bar to chart at all, but the ones that do break through tend to break through strongly.`),
        ...figure("../outputs/figures/07_explicit_by_rank.png", 1237, 878, "Figure 3.10 — Explicit content share by chart-position tier."),
        ...figure("../outputs/figures/08_explicit_over_time.png", 1597, 878, "Figure 3.11 — Explicit content share over time (monthly)."),
        calloutBox("Strategic read: clean/radio-edit versions remain important for maximizing UK reach and playlist eligibility, but marketing teams should not assume explicit content is a ceiling on chart peak — it is a ceiling on chart-entry probability. For artists with strong existing momentum, explicit versions are not a barrier to Top 10 performance.", TEAL),

        h2("3.5 Album Structure & Release Strategy"),
        p(`Album-attributed tracks outnumber singles on the UK Top 50 overall: ${data.album_type_share["album"]}% of entries are album cuts versus ${data.album_type_share["single"]}% singles (and a negligible ${data.album_type_share["compilation"] || 0}% compilation entries) — a meaningfully different balance than a singles-led US market analysis would assume.`),
        ...figure("../outputs/figures/09_album_type_share.png", 960, 858, "Figure 3.12 — Release format share: single vs. album vs. compilation.", 4.0),
        p(`This overall album-lean flips at the very top of the chart. Inside the Top 5, singles are the majority format at ${data.release_format_by_rank["single"]["Top 5"]}% versus ${data.release_format_by_rank["album"]["Top 5"]}% album cuts — but that gap steadily closes moving down the chart, and album cuts become the clear majority by positions 21-50 (${data.release_format_by_rank["album"]["21-50"]}% album vs. ${data.release_format_by_rank["single"]["21-50"]}% single).`),
        ...figure("../outputs/figures/10_release_format_by_rank.png", 1415, 878, "Figure 3.13 — Release format by chart-position tier."),
        p("This pattern is consistent with a deluxe-edition/\"track-stuffing\" dynamic: a lead single drives an artist to the very top of the chart, after which the parent album's full tracklist backfills the middle and lower reaches of the Top 50 on streaming strength alone, without dedicated single promotion behind each track."),
        h3("Album size and chart footprint"),
        p(`Grouping entries by parent-album size shows the largest footprint comes from "deluxe"-scale releases (13-20 tracks, ${data.album_size_buckets["Deluxe (13-20)"].toLocaleString()} entries) and true singles (1 track, ${data.album_size_buckets["Single (1)"].toLocaleString()} entries) — together outweighing standard-length albums (6-12 tracks, ${data.album_size_buckets["Album (6-12)"].toLocaleString()} entries). This reinforces that UK chart strategy increasingly operates at the two extremes: a tightly focused single push, or a maximal-tracklist deluxe release designed to claim as many simultaneous chart slots as possible.`),
        calloutBox("Strategic read: for UK release planning, a single-led rollout is the more reliable path to a Top 5 peak; a deluxe/expanded tracklist is the more reliable path to sustained chart presence and total Top 50 real estate. The two strategies serve different commercial goals and are not substitutes for one another.", TEAL),

        h2("3.6 Track Duration & Format"),
        p(`The average UK Top 50 track runs ${data.kpi_summary["Avg Track Duration (mm:ss)"]} (${data.duration_stats.mean}s), with the bulk of entries (${data.duration_distribution["Standard (2:30-3:30)"]}%) falling into the "standard" 2:30-3:30 band. Short-form tracks under 2:30 remain a minority at ${data.duration_distribution["Short (<2:30)"]}% of entries, and extended tracks over 4:30 are rare (${data.duration_distribution["Extended (4:30+)"]}%).`),
        ...figure("../outputs/figures/11_duration_distribution.png", 1237, 878, "Figure 3.14 — Track duration distribution."),
        p(`Cross-referencing duration against the Atlantic popularity score shows a mild but consistent inverse relationship: the most popular quartile of tracks (Q4) averages ${data.duration_vs_popularity["Q4 (Highest)"]}s, shorter than every lower popularity quartile (Q1: ${data.duration_vs_popularity["Q1 (Lowest)"]}s; Q2: ${data.duration_vs_popularity["Q2"]}s; Q3: ${data.duration_vs_popularity["Q3"]}s) — consistent with a broader streaming-era pull toward tighter runtimes optimized for repeat listens and playlist flow, though the effect size here is modest (roughly 11 seconds between the highest and lowest popularity quartiles).`),
        ...figure("../outputs/figures/12_duration_vs_popularity.png", 1237, 878, "Figure 3.15 — Average track duration by popularity quartile."),
        calloutBox("Strategic read: there is no strong evidence in this dataset that UK listeners require unusually short or long runtimes versus general streaming-era norms — the standard ~3-minute range remains safest, with a slight edge to tracks at or under that mark for peak popularity.", TEAL),

        h2("3.7 Market Structure Metrics — KPI Summary"),
        p("The table below consolidates every KPI defined in Section 2.4 and referenced throughout Section 3, plus the composite Content Variety Index."),
        kpiTable(kpiRows),
        p(""),
        ...figure("../outputs/figures/15_diversity_trend.png", 1777, 878, "Figure 3.16 — Daily unique-artist count over time, with 30-day rolling average, showing diversity has been broadly stable across the analysis window."),

        new Paragraph({ children: [new PageBreak()] }),

        // ------------------------------------------------------------------
        // 4. STRATEGIC RECOMMENDATIONS
        // ------------------------------------------------------------------
        h1("4. Strategic Recommendations"),
        h2("4.1 Artist Signing Strategy"),
        bullet(`Favor portfolio breadth over concentrated superstar bets. With Top-5 concentration at just ${data.concentration_top5.top_n_share_pct}% and an HHI of ${data.concentration_top5.hhi}, the UK chart rewards a wide roster rather than a small number of dominant acts.`),
        bullet("Prioritize UK artist development specifically for Top 20 sustainability rather than Top 5 breakthrough — that is where domestic representation is comparatively strongest relative to international competition."),
        bullet("Scout within existing UK genre-collaboration clusters (drill/rap, garage/pop, drum & bass) identified in Section 3.3 — these networks show self-reinforcing collaboration density that a new signing can plug into."),

        h2("4.2 UK-Specific Marketing Decisions"),
        bullet("Do not treat explicit content as a chart-peak ceiling — treat it as a chart-entry hurdle. Once an explicit track charts, it is well-positioned to reach the Top 10."),
        bullet("Maintain clean/radio-edit versions as standard practice for UK release campaigns, given the market's overall two-to-one clean-to-explicit composition and its relevance to broadcast/editorial playlist eligibility."),
        bullet("Recognize that international competition is fiercest at the very top of the chart; UK-specific marketing spend may generate a better return when focused on sustaining mid-chart presence for domestic acts than on displacing international acts from the Top 5."),

        h2("4.3 Release Format Optimization"),
        bullet("For a Top 5 peak: lead with a focused single campaign — singles are the majority format inside the Top 5 despite being a minority of the chart overall."),
        bullet("For sustained chart real estate: plan a deluxe/expanded-tracklist release. Deluxe-scale albums (13-20 tracks) show the largest aggregate chart footprint of any album-size bucket."),
        bullet("Standard-length albums (6-12 tracks) are comparatively under-represented on the chart relative to both singles and deluxe releases, and may warrant a hybrid approach — an early single push followed by a later deluxe expansion — rather than a single simultaneous release."),

        h2("4.4 Cross-Border Promotion Planning"),
        bullet(`With international artists holding ${data.domestic_vs_intl["International"]}% of UK chart appearances, cross-border promotion infrastructure (already built for US/global campaigns) is directly reusable for driving UK chart performance — it does not need to be rebuilt as a separate UK-only motion.`),
        bullet("For UK-origin artists targeting international crossover, the genre-cluster collaboration pattern in Section 3.3 suggests brokering a collaboration with an established international act in the same genre is a proven bridge mechanic already visible in the data (e.g. Chase & Status × Stormzy)."),

        new Paragraph({ children: [new PageBreak()] }),

        // ------------------------------------------------------------------
        // 5. LIMITATIONS
        // ------------------------------------------------------------------
        h1("5. Limitations"),
        bullet("Nationality classification (Section 2.3) is based on the analyst's best-effort knowledge of each act's public country of origin, not a licensed artist-metadata source; ~0.7% of appearances remain unclassified and a small residual misclassification risk exists for lesser-known acts."),
        bullet("The dataset reflects Atlantic's own API popularity score and playlist snapshots, not independently verified UK Official Charts data — findings describe this playlist's structure specifically, not the UK singles chart as a whole."),
        bullet("Twelve exact-duplicate rows were identified but not removed, as they represent under 0.05% of the dataset and do not materially affect any reported metric; a strict-deduplication re-run is recommended before any figure in this paper is cited externally."),
        bullet("Collaboration parsing relies on a delimiter-splitting heuristic with a manually curated protected-name list; new act names containing '&' or ',' introduced in future data pulls should be checked against this list before re-running the analysis."),
        bullet("The Content Variety Index (Section 2.4) is a composite index defined for this analysis and does not correspond to an external industry-standard benchmark; it should be used for relative/trend comparison within this dataset, not as an absolute external benchmark."),

        h1("6. Conclusion"),
        p("This analysis shows the UK Top 50 to be a structurally distinct market from a US-style popularity-trend view: fragmented rather than concentrated in artist terms, meaningfully open to international crossover but with domestic artists holding their strongest relative ground in the Top 20 rather than the very top, collaboration-driven in the middle of the chart specifically, clean-leaning overall but not explicit-penalizing once a track breaks through, and split between a singles-led path to a Top 5 peak and a deluxe-album-led path to sustained chart presence. Atlantic Recording Corporation's UK strategy should be built on these UK-specific structural dynamics rather than adapted from US market assumptions."),

        // ------------------------------------------------------------------
        // APPENDIX
        // ------------------------------------------------------------------
        new Paragraph({ children: [new PageBreak()] }),
        h1("Appendix A: Dataset Field Reference"),
        kpiTable(
          [
            ["date", "Date of playlist snapshot"],
            ["position", "Playlist rank (1-50)"],
            ["song", "Song title"],
            ["artist", "Artist(s), '&'-delimited for collaborations"],
            ["popularity", "Popularity score from Atlantic API"],
            ["duration_ms", "Song duration (milliseconds)"],
            ["album_type", "Single / Album / Compilation"],
            ["total_tracks", "Number of tracks on the parent album"],
            ["is_explicit", "Explicit content flag"],
            ["album_cover_url", "Album artwork URL"],
          ],
          ["Field", "Description"]
        ),
      ],
    },
  ],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("../reports/UK_Top50_Research_Paper.docx", buf);
  console.log("Research paper written.");
});
