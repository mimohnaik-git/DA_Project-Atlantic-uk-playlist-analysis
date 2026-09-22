const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, VerticalAlign,
} = require("docx");

const data = JSON.parse(fs.readFileSync("../outputs/report_data.json", "utf-8"));

const NAVY = "0B1F3A";
const RED = "E4572E";
const TEAL = "2C7873";
const GREY = "8A94A6";
const LIGHT_GREY = "F2F4F7";

function img(path, widthPx, heightPx, maxWidthIn = 6.3) {
  const buf = fs.readFileSync(path);
  const ratio = heightPx / widthPx;
  const widthIn = maxWidthIn;
  const heightIn = widthIn * ratio;
  return new ImageRun({
    data: buf, type: "png",
    transformation: { width: Math.round(widthIn * 96), height: Math.round(heightIn * 96) },
  });
}
function figure(path, widthPx, heightPx, caption, maxWidthIn = 6.3) {
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 }, children: [img(path, widthPx, heightPx, maxWidthIn)] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [new TextRun({ text: caption, italics: true, size: 19, color: "555555" })] }),
  ];
}
function h1(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 380, after: 180 } }); }
function h2(text) { return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 140 } }); }
function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 180, line: 276 }, children: [new TextRun({ text, size: 22, ...opts })] });
}
function bullet(text) {
  return new Paragraph({ bullet: { level: 0 }, spacing: { after: 100 }, children: [new TextRun({ text, size: 22 })] });
}

function statTable(rows, headers) {
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map(ht => new TableCell({
      width: { size: 100 / headers.length, type: WidthType.PERCENTAGE },
      shading: { fill: NAVY, type: ShadingType.CLEAR, color: "auto" },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 100, bottom: 100, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: ht, bold: true, color: "FFFFFF", size: 20 })] })],
    })),
  });
  const bodyRows = rows.map((r, i) => new TableRow({
    children: r.map(cell => new TableCell({
      width: { size: 100 / headers.length, type: WidthType.PERCENTAGE },
      shading: { fill: i % 2 === 0 ? "FFFFFF" : LIGHT_GREY, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({ children: [new TextRun({ text: String(cell), size: 20 })] })],
    })),
  }));
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, rows: [headerRow, ...bodyRows] });
}

function calloutBox(text, color = TEAL) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color }, bottom: { style: BorderStyle.SINGLE, size: 4, color },
      left: { style: BorderStyle.SINGLE, size: 4, color }, right: { style: BorderStyle.SINGLE, size: 4, color },
    },
    rows: [new TableRow({ children: [new TableCell({
      shading: { fill: LIGHT_GREY, type: ShadingType.CLEAR, color: "auto" },
      margins: { top: 160, bottom: 160, left: 200, right: 200 },
      children: [new Paragraph({ children: [new TextRun({ text, size: 21 })] })],
    })] })],
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", run: { size: 30, bold: true, color: NAVY, font: "Calibri" }, paragraph: { spacing: { before: 380, after: 180 } } },
      { id: "Heading2", name: "Heading 2", run: { size: 24, bold: true, color: RED, font: "Calibri" } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 } } },
    children: [
      new Paragraph({ spacing: { before: 800 }, children: [] }),
      new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "ATLANTIC RECORDING CORPORATION", bold: true, size: 22, color: RED, allCaps: true })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 200 }, children: [new TextRun({ text: "UK Top 50 Playlist Market Structure Analysis", bold: true, size: 40, color: NAVY })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 500 }, children: [new TextRun({ text: "Executive Summary", size: 28, italics: true, color: GREY })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 }, children: [new TextRun({ text: `Analysis period: ${data.date_min} – ${data.date_max} · ${data.n_rows.toLocaleString()} playlist entries`, size: 20 })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 900 }, children: [new TextRun({ text: "Prepared for stakeholder briefing", size: 18, color: GREY })] }),
      new Paragraph({ children: [new PageBreak()] }),

      h1("Purpose"),
      p("Atlantic Recording Corporation commissioned this analysis to understand the structural composition of the United Kingdom's Top 50 music playlist — separate from, and not simply copied from, prior US-market analysis. The findings below inform artist signing, UK marketing, release-format, and cross-border promotion decisions, and are shared here at summary level for a general stakeholder audience."),

      h1("What We Analyzed"),
      p(`We examined ${data.n_rows.toLocaleString()} daily UK Top 50 playlist entries recorded between ${data.date_min} and ${data.date_max}, covering ${data.n_unique_songs} unique songs by ${data.n_unique_artists} unique artists. Every entry was checked for completeness (no missing data was found) and cleaned so that artist names and collaborations are counted accurately.`),

      h1("Headline Findings"),

      h2("1. The chart is broad-based, not dominated by a few artists"),
      p(`Just ${data.concentration_top5.top_n_share_pct}% of all chart appearances belong to the five most-featured artists. Over the eighteen-month period, ${data.n_unique_artists} different artists appeared on the chart at some point — indicating a healthy, competitive market rather than one controlled by a small number of acts.`),

      h2("2. International artists outnumber UK artists on the chart, roughly two to one"),
      p(`International acts hold ${data.domestic_vs_intl["International"]}% of chart appearances versus ${data.domestic_vs_intl["UK / Domestic"]}% for UK/domestic acts. This international presence is strongest at the very top of the chart and slightly less pronounced by the Top 20, where UK artists hold comparatively more ground.`),
      ...figure("../outputs/figures/13_domestic_vs_international.png", 896, 732, "UK/Domestic vs. International share of chart appearances.", 3.8),

      h2("3. Artist collaborations are most common in the middle of the chart"),
      p(`${data.collab_ratio_pct}% of chart entries feature more than one artist. Collaboration is most common around the Top 10–20 of the chart, suggesting that pairing artists together is an effective way to break into the middle of the chart, more so than a requirement for reaching the very top.`),

      h2("4. Most UK chart content is clean-rated, but explicit tracks that chart tend to chart high"),
      p(`${data.explicit_share["Clean"]}% of chart entries are clean-rated content, reflecting UK audience and broadcast sensitivity to explicit material. However, explicit tracks that do make the chart are more common in the Top 10 than further down the chart — once an explicit track breaks through, it tends to perform well.`),

      h2("5. Albums generate more total chart entries, but singles win the very top spot"),
      p(`Album tracks make up ${data.album_type_share["album"]}% of chart entries overall, more than singles at ${data.album_type_share["single"]}%. However, within the Top 5 specifically, singles are the majority format (${data.release_format_by_rank["single"]["Top 5"]}%) — showing that a focused single release is the more reliable route to the very top of the chart, while a full album release generates broader, sustained chart presence.`),

      h1("Key Figures at a Glance"),
      statTable(
        [
          ["Top-5 artist concentration", `${data.concentration_top5.top_n_share_pct}%`],
          ["Unique artists on chart", `${data.n_unique_artists}`],
          ["UK / Domestic artist share", `${data.domestic_vs_intl["UK / Domestic"]}%`],
          ["International artist share", `${data.domestic_vs_intl["International"]}%`],
          ["Collaboration rate", `${data.collab_ratio_pct}%`],
          ["Clean-rated content share", `${data.explicit_share["Clean"]}%`],
          ["Album vs. single share", `${data.album_type_share["album"]}% / ${data.album_type_share["single"]}%`],
          ["Average track length", `${data.kpi_summary["Avg Track Duration (mm:ss)"]}`],
        ],
        ["Metric", "Value"]
      ),
      p(""),

      h1("What This Means — Recommendations"),
      bullet("Signing strategy: favor a broad artist portfolio; the UK chart rewards variety, not a small set of dominant acts."),
      bullet("Marketing: maintain clean/radio-edit versions as standard for UK campaigns, while recognizing explicit content is not a barrier to top-chart performance once a track has broken through."),
      bullet("Release format: use a focused single campaign to target a Top 5 peak; use a fuller album or deluxe release to build sustained, broad chart presence."),
      bullet("Cross-border promotion: existing international promotion infrastructure is directly applicable to the UK market, given how open UK charts are to international artists."),

      h1("Methodology Note"),
      p("This summary is drawn from a full research paper that documents complete methodology, data-cleaning steps, all supporting charts, and detailed findings by chart-position tier. Two data-quality corrections were required and are fully documented in that paper: (1) protecting legitimate band/act names that contain the collaboration delimiter (e.g. \"Chase & Status\") from being incorrectly split into separate artists, and (2) merging inconsistent capitalization of the same artist name. Nationality classification (UK vs. International) is based on each act's publicly known country of origin; a small residual share of entries (0.7%) could not be confidently classified and are excluded from the domestic/international comparison rather than guessed."),
      calloutBox("For full methodology, complete figures, chart-position-tier breakdowns, and section-by-section strategic recommendations, refer to the companion Research Paper (UK_Top50_Research_Paper.docx).", TEAL),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("../reports/UK_Top50_Executive_Summary.docx", buf);
  console.log("Executive summary written.");
});
