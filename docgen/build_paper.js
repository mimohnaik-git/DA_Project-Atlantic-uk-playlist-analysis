const fs = require("fs");
const { Packer, Paragraph, TextRun, AlignmentType, paragraph, heading, bullet, pageBreak, table, figure, document } = require("./report_helpers");
const data = JSON.parse(fs.readFileSync("../outputs/report_data.json", "utf8"));
const c = data.counts;
const fmt = x => Number(x).toFixed(2);
const titleCollisionCount = data.data_quality.checks.find(x => x.name === "title_collisions").value;
const qualityFindings = [
  "Four calendar dates are absent; no observations are imputed.",
  "The position reset on 2025-03-01 reconstructs two complete Top-50 snapshots.",
  "Twelve exact source duplicates occur across those separate snapshots and are retained.",
  `Unclassified nationality accounts for ${data.nationality.artist_credit_share_pct.Unclassified}% of full artist credits.`,
  "Observed metadata changes affect 3 song labels, 48 album types, 59 total-track values, 11 explicit flags and 25 apparent credited-artist sets.",
  `${titleCollisionCount} normalised titles map to more than one exact-duration recording proxy, confirming that title alone is not a safe track identifier.`,
];

const children = [
  new Paragraph({ text: "UK Top 50 Playlist Market Structure Research Paper", style: "Title" }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 }, children: [new TextRun({
    text: "A portfolio case study prepared around an Atlantic Recording Corporation business scenario", size: 23, italics: true, color: "555555" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 460 }, children: [new TextRun({
    text: `${data.date_range.min} to ${data.date_range.max}`, size: 20 })] }),
  paragraph("Completed with Unified Mentor Pvt. Ltd. as a Data Analyst Intern from 25 April 2026 to 25 July 2026, this Entertainment-category project was submitted on 25 April 2026 and rated 8/10 (Excellent) on 5 August 2026. Atlantic Recording Corporation is only the business scenario, not the employer, client or an official engagement. This report is the post-evaluation remediated portfolio version."),
  heading("Executive summary"),
  paragraph(`This snapshot-aware analysis covers ${c.processed_chart_entries.toLocaleString()} chart entries across ${c.distinct_dates} dates and ${c.snapshots} reconstructed Top-50 snapshots. It distinguishes ${c.unique_song_titles_raw} raw song titles from ${c.unique_recording_proxies} dataset-local recording proxies and ${c.artist_credit_observations.toLocaleString()} artist-credit observations.`),
  paragraph(`Period-wide full-credit artist concentration is ${data.concentration.period_wide_full_credit.top_5_share_pct}% for the five most frequent artists, with HHI ${data.concentration.period_wide_full_credit.hhi}. A typical snapshot has median fractional-credit HHI ${data.concentration.snapshot_fractional.median_hhi} and a mean effective artist count of ${data.diversity.mean_effective_number_of_artists}. The measures are reported separately because long-run appearance persistence is not the same as concentration within one snapshot.`),
  paragraph(`Collaborations account for ${data.collaboration.entry_share_pct}% of chart entries and ${data.collaboration.recording_proxy_share_pct}% of unique recording proxies. Explicit entries are ${data.explicit.overall_pct.Explicit}% of observations. International artists account for ${data.nationality.artist_credit_share_pct.International}% of full artist credits, while the fractional-entry method gives ${data.nationality.fractional_entry_share_pct.International}%. These are descriptive associations and do not establish causal effects.`),
  pageBreak(),
  heading("1 Project objective and analytical units"),
  paragraph("The project examines artist presence, collaboration, content explicitness, release format, duration and nationality within the supplied UK Top 50 dataset. The analysis is a portfolio case study, not evidence of an official engagement."),
  table(Object.entries(data.analytical_units).map(([a,b]) => [a.replaceAll("_", " "), b]), ["Unit", "Definition"], [28,72]),
  heading("2 Data preparation and quality"),
  heading("2.1 Snapshot reconstruction", 2),
  paragraph("A snapshot is one ordered ranking, not one calendar date. Source row order is preserved. Within a date, a later reset to position 1 starts a new deterministic snapshot sequence. This rule reconstructs 2025-03-01 as two complete snapshots, 2025-03-01__1 and 2025-03-01__2."),
  heading("2.2 Duplicate policy", 2),
  paragraph("Twelve exact source duplicates occur across the two legitimate March 1 snapshots. They are retained because they represent observations in different inferred snapshots. Only an exact repeated source row inside the same snapshot would be removed from processed analytical data; no row meets that rule."),
  heading("2.3 Recording proxy", 2),
  paragraph("No Spotify track ID, ISRC or other native recording identifier is present. The recording_proxy_id is a deterministic dataset-local key formed from a conservative normalised title and exact duration in milliseconds. Artist credits are excluded from identity because 25 identical title-duration combinations show changing billed credits. Title alone merges distinct-duration recordings, while a two-second tolerance introduces an arbitrary merge rule. For proxy-level attributes, the canonical recording table keeps the earliest observed row after sorting by date and source_row_id. This first-observed rule is deterministic and is also used for the recording-proxy collaboration share; it is not a claim that the first observed metadata is a globally authoritative recording record."),
  heading("2.4 Artist parsing, weighting and rank semantics", 2),
  paragraph("Protected act names are parsed before general collaborator delimiters, then casing variants are canonicalised deterministically. Full-credit measures give every credited artist one unit; fractional measures divide each chart entry equally across its credited artists. Top 5, Top 10 and Top 20 are cumulative thresholds, while 1-5, 6-10, 11-20 and 21-50 are mutually exclusive bands."),
  heading("2.5 Quality findings", 2),
  ...qualityFindings.map(bullet),
  heading("3 Artist presence diversity and concentration"),
  paragraph(`The dataset contains ${c.unique_artists} parsed artists and ${c.artist_credit_observations.toLocaleString()} full artist-credit observations. Full credit gives every credited artist one appearance. Fractional credit divides each chart entry equally among its credited artists so every entry sums to one.`),
  ...figure("../outputs/figures/01_top_artists.png", "Figure 1. Leading artists by repeated full artist-credit appearances."),
  ...figure("../outputs/figures/02_concentration_curve.png", "Figure 2. Period-wide cumulative artist-credit concentration."),
  paragraph(`Across snapshots, mean unique credited artists are ${data.diversity.mean_snapshot_unique_artists}; mean bounded artist-credit uniqueness is ${data.diversity.mean_artist_credit_uniqueness_ratio}; mean fractional-weight Shannon entropy is ${data.diversity.mean_shannon_entropy}; and mean effective artist count is ${data.diversity.mean_effective_number_of_artists}. The uniqueness ratio divides distinct credited artists by artist-credit observations, so collaboration cannot push it above one. Effective count is calculated per snapshot as exp(H), then averaged; it is not exp(mean H).`),
  ...figure("../outputs/figures/15_diversity_trend.png", "Figure 3. Snapshot artist variety over time."),
  heading("4 Collaboration"),
  paragraph(`Collaborative chart entries represent ${data.collaboration.entry_share_pct}% of repeated observations, compared with ${data.collaboration.recording_proxy_share_pct}% of distinct recording proxies. The average is ${data.collaboration.average_collaborators_per_entry} credited artists per chart entry and ${data.collaboration.average_collaborators_per_recording_proxy} per recording proxy.`),
  ...figure("../outputs/figures/03_solo_vs_collab.png", "Figure 4. Solo and collaborative chart-entry observations."),
  ...figure("../outputs/figures/04_collab_by_rank.png", "Figure 5. Collaboration share by mutually exclusive rank band."),
  paragraph("Pair counts distinguish co-credited chart-entry appearances from unique collaborative recording proxies. For example, a pair recurring across many snapshots can have a large appearance count even when it represents only one recording proxy."),
  table(data.collaboration.top_pairs.slice(0,10).map((x,i) => [i+1, x.artist_a, x.artist_b, x.co_credited_appearances, x.unique_collaborative_tracks]),
    ["Rank", "Artist A", "Artist B", "Chart appearances", "Recording proxies"], [8,25,25,21,21]),
  heading("5 Content release format duration and nationality"),
  heading("5.1 Explicit content", 2),
  paragraph(`Explicit content is ${data.explicit.overall_pct.Explicit}% of chart-entry observations. Cumulative positions 1-5, 1-10 and 1-20 are ${data.explicit.cumulative_top_n_pct["Top 5"]}%, ${data.explicit.cumulative_top_n_pct["Top 10"]}% and ${data.explicit.cumulative_top_n_pct["Top 20"]}%, respectively. Exclusive-band figures are reported separately.`),
  ...figure("../outputs/figures/07_explicit_by_rank.png", "Figure 6. Explicit share by exclusive rank band."),
  heading("5.2 Release format", 2),
  paragraph(`Album entries are ${data.release_format.overall_pct.album}% and single entries are ${data.release_format.overall_pct.single}% of repeated observations. These shares describe entry composition; they do not estimate the causal effect of releasing an album or single.`),
  ...figure("../outputs/figures/10_release_format_by_rank.png", "Figure 7. Release-format share by exclusive rank band."),
  heading("5.3 Duration", 2),
  paragraph(`Mean duration is ${data.duration.mean_mm_ss} (${data.duration.mean_seconds} seconds). Duration-popularity relationships are observational and include repeated appearances of the same recording proxies.`),
  ...figure("../outputs/figures/11_duration_distribution.png", "Figure 8. Duration distribution across chart-entry observations."),
  heading("5.4 Nationality", 2),
  paragraph(`Under full artist-credit weighting, UK/Domestic share is ${data.nationality.artist_credit_share_pct["UK / Domestic"]}% and international share is ${data.nationality.artist_credit_share_pct.International}%. Under fractional-entry weighting, the values are ${data.nationality.fractional_entry_share_pct["UK / Domestic"]}% and ${data.nationality.fractional_entry_share_pct.International}%. Unclassified artists remain separate.`),
  paragraph("Nationality is a manually curated classification of the billed act's primary origin. Groups follow the billed act rather than individual members; multinational or uncertain acts remain Unclassified. The supplied project contains no structured citations for individual mappings, so the classification requires source review before external publication."),
  ...figure("../outputs/figures/13_domestic_vs_international.png", "Figure 9. Nationality share using full artist-credit weighting."),
  heading("6 Business interpretation"),
  heading("Observation", 2),
  paragraph("Artist, collaboration, explicitness, release-format and nationality shares vary across exclusive rank bands and across the observation period."),
  heading("Interpretation", 2),
  paragraph("The patterns identify segments and recurring artist-credit relationships that merit campaign-level investigation. They are consistent with several plausible mechanisms, but the dataset does not contain treatment assignment, promotion spend, label inputs or counterfactual outcomes."),
  heading("Business implication", 2),
  bullet("Use cumulative Top-5, Top-10 and Top-20 metrics for threshold questions and exclusive bands for comparisons between non-overlapping positions."),
  bullet("Evaluate collaboration hypotheses at both entry and unique-recording level so repeated persistence is not mistaken for a large catalogue of collaborations."),
  bullet("Test clean and explicit versions, single and album sequencing, and domestic or cross-border campaigns with campaign-level outcomes before claiming performance effects."),
  heading("Limitation", 2),
  paragraph("The source is observational and covers a supplied playlist or chart-style dataset rather than a randomized release-strategy experiment."),
  heading("7 Limitations"),
  bullet("Snapshot boundaries are inferred from row order and position resets because no native timestamp or snapshot identifier is present."),
  bullet("The recording proxy is dataset-local and may split or combine recordings differently from a Spotify ID or ISRC."),
  bullet("Four calendar dates are absent and are not imputed."),
  bullet("Nationality mapping is manually curated. The repository contains no source citations for the mappings, so external source review is required before publication."),
  bullet("Artist-credit metadata, release format, total track count and explicit flags can vary over time; the recording table reports these instabilities and uses the documented deterministic first-observed metadata rule."),
  bullet("The analysis is descriptive. Recommendations are hypotheses to test, not demonstrated causal effects."),
  bullet("The dataset was supplied by Unified Mentor Pvt. Ltd. as part of the Data Analyst internship project materials for this Entertainment-category case study. The supplied materials do not identify the original upstream provider, collection URL, collection methodology, or formal upstream dataset license."),
];

Packer.toBuffer(document(children)).then(buffer => {
  fs.writeFileSync("../reports/UK_Top50_Research_Paper.docx", buffer);
  console.log("Research paper written");
});
