const fs = require("fs");
const { Packer, Paragraph, TextRun, AlignmentType, paragraph, heading, bullet, pageBreak, table, figure, document } = require("./report_helpers");
const data = JSON.parse(fs.readFileSync("../outputs/report_data.json", "utf8"));
const c = data.counts;

const rows = [
  ["Chart entries", c.processed_chart_entries.toLocaleString()],
  ["Dates and snapshots", `${c.distinct_dates} dates; ${c.snapshots} snapshots`],
  ["Song titles and recording proxies", `${c.unique_song_titles_raw} titles; ${c.unique_recording_proxies} proxies`],
  ["Artist-credit observations", c.artist_credit_observations.toLocaleString()],
  ["Collaboration share", `${data.collaboration.entry_share_pct}% entries; ${data.collaboration.recording_proxy_share_pct}% proxies`],
  ["Period-wide Top-5 artist-credit share", `${data.concentration.period_wide_full_credit.top_5_share_pct}%`],
  ["Median fractional-entry snapshot HHI", data.concentration.snapshot_fractional.median_hhi],
  ["Mean effective artists per snapshot", data.diversity.mean_effective_number_of_artists],
  ["Explicit chart-entry share", `${data.explicit.overall_pct.Explicit}%`],
  ["Average duration", data.duration.mean_mm_ss],
];

const children = [
  new Paragraph({ text: "UK Top 50 Playlist Executive Summary", style: "Title" }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 }, children: [new TextRun({
    text: "Portfolio case study for an Atlantic Recording Corporation business scenario", size: 22, italics: true, color: "555555" })] }),
  paragraph("Completed with Unified Mentor Pvt. Ltd. as a Data Analyst Intern from 25 April 2026 to 25 July 2026, this Entertainment-category project was submitted on 25 April 2026 and rated 8/10 (Excellent) on 5 August 2026. Atlantic Recording Corporation is only the business scenario, not the employer, client or an official engagement. This summary is the post-evaluation remediated portfolio version."),
  heading("Executive Overview"),
  paragraph(`The corrected analysis covers ${c.processed_chart_entries.toLocaleString()} chart entries across ${c.snapshots} reconstructed Top-50 snapshots. One date, 2025-03-01, contains two legitimate snapshots. The project now separates chart entries, song titles, recording proxies and artist credits, so repeated appearances are no longer described as unique tracks.`),
  paragraph(`The period-wide top-five full-credit artist share is ${data.concentration.period_wide_full_credit.top_5_share_pct}%, while median fractional-entry snapshot HHI is ${data.concentration.snapshot_fractional.median_hhi}. Collaboration represents ${data.collaboration.entry_share_pct}% of chart entries but ${data.collaboration.recording_proxy_share_pct}% of recording proxies. These measures describe different analytical units and should not be combined into causal claims.`),
  heading("Key metrics"),
  table(rows),
  heading("What changed"),
  bullet("Calendar dates and snapshots are now separate; March 1 is reconstructed as two complete position sets."),
  bullet("The earlier period-length-sensitive Diversity Score and custom Content Variety Index were removed. Snapshot entropy and effective artist count replace them."),
  bullet("Top 5, Top 10 and Top 20 are cumulative metrics. Comparisons between non-overlapping positions use 1-5, 6-10, 11-20 and 21-50."),
  bullet("Collaboration pair tables show both repeated co-credited chart appearances and unique collaborative recording proxies."),
  bullet("Recording-proxy attributes use the earliest observed metadata row after sorting by date and source row; this deterministic first-observed rule also determines the proxy collaboration share."),
  bullet("Artist shares are available as full artist-credit and fractional chart-entry measures."),
  ...figure("../outputs/figures/02_concentration_curve.png", "Period-wide cumulative artist-credit concentration.", 570, 360),
  heading("Interpretation and action"),
  paragraph("Observation: international, explicit, collaborative and release-format shares vary by chart position. Interpretation: the differences identify useful segments for further investigation. Business implication: use them to define campaign tests rather than assuming a release or collaboration tactic will change rank. Limitation: the data are observational and lack campaign spend, promotion treatment and counterfactual outcomes."),
  bullet("Review artist strategy with both period-wide persistence and typical-snapshot concentration in view."),
  bullet("Evaluate collaborations at unique-recording level before interpreting recurring chart appearances as catalogue breadth."),
  bullet("Test release format, clean versions and cross-border promotion with campaign-level outcomes."),
  heading("Data quality and limitations"),
  paragraph(`Validation status is ${data.data_quality.status}. All critical checks pass. Warnings cover four missing dates, inferred snapshot reconstruction, 12 exact cross-snapshot duplicates, title collisions, metadata changes and a ${data.nationality.artist_credit_share_pct.Unclassified}% unclassified nationality share.`),
  bullet("No native track ID or snapshot timestamp is available."),
  bullet("Nationality mapping is manual and lacks citations in the supplied repository."),
  bullet("The dataset was supplied by Unified Mentor Pvt. Ltd. as part of the Data Analyst internship project materials for this Entertainment-category case study. The supplied materials do not identify the original upstream provider, collection URL, collection methodology, or formal upstream dataset license."),
  bullet("No causal effect can be inferred from rank-band associations."),
];

Packer.toBuffer(document(children)).then(buffer => {
  fs.writeFileSync("../reports/UK_Top50_Executive_Summary.docx", buffer);
  console.log("Executive summary written");
});
