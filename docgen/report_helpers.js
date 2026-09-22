const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  ImageRun, PageBreak, VerticalAlign,
} = require("docx");

const NAVY = "0B1F3A";
const LIGHT = "F3F6FA";
const BORDER = "D9D9D9";

function paragraph(text, options = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ text: String(text), size: options.size || 22, bold: !!options.bold,
      italics: !!options.italics, color: options.color || "000000" })],
  });
}
function heading(text, level = 1) {
  return new Paragraph({ text, heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
    spacing: { before: level === 1 ? 340 : 240, after: 130 } });
}
function bullet(text) {
  return new Paragraph({ bullet: { level: 0 }, spacing: { after: 100, line: 260 },
    children: [new TextRun({ text: String(text), size: 21 })] });
}
function pageBreak() { return new Paragraph({ children: [new PageBreak()] }); }
function table(rows, headers = ["Metric", "Value"], widths = null) {
  const borders = { top: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    left: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    right: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: BORDER },
    insideVertical: { style: BorderStyle.SINGLE, size: 4, color: BORDER } };
  const makeCell = (value, header, index) => new TableCell({
    width: { size: widths ? widths[index] : 100 / headers.length, type: WidthType.PERCENTAGE },
    shading: { fill: header ? NAVY : "FFFFFF", type: ShadingType.CLEAR },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 100, bottom: 100, left: 120, right: 120 },
    children: [new Paragraph({ alignment: index === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
      children: [new TextRun({ text: String(value), size: 19, bold: header, color: header ? "FFFFFF" : "000000" })] })],
  });
  const outputRows = [new TableRow({ tableHeader: true, children: headers.map((h, i) => makeCell(h, true, i)) })];
  rows.forEach(row => outputRows.push(new TableRow({ children: row.map((v, i) => makeCell(v, false, i)) })));
  return new Table({ width: { size: 100, type: WidthType.PERCENTAGE }, borders, rows: outputRows });
}
function pngDimensions(data) {
  const pngSignature = "89504e470d0a1a0a";
  if (data.length < 24 || data.subarray(0, 8).toString("hex") !== pngSignature) {
    throw new Error("figure() currently expects a valid PNG image");
  }
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) };
}
function figure(path, caption, maxWidth = 600, maxHeight = 330) {
  const data = fs.readFileSync(path);
  const source = pngDimensions(data);
  const scale = Math.min(maxWidth / source.width, maxHeight / source.height);
  const width = Math.max(1, Math.round(source.width * scale));
  const height = Math.max(1, Math.round(source.height * scale));
  const name = path.split(/[\\/]/).pop() || "figure.png";
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 180, after: 80 },
      children: [new ImageRun({
        data, type: "png", transformation: { width, height },
        altText: { name, title: caption, description: caption },
      })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 220 },
      children: [new TextRun({ text: caption, size: 18, italics: true, color: "555555" })] }),
  ];
}
function document(children) {
  return new Document({
    styles: { default: { document: { run: { font: "Aptos", size: 22, color: "000000" } } },
      paragraphStyles: [
        { id: "Title", name: "Title", basedOn: "Normal", next: "Normal",
          run: { font: "Aptos Display", size: 40, bold: true, color: "000000" },
          paragraph: { alignment: AlignmentType.CENTER, spacing: { before: 360, after: 220 } } },
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: "Aptos Display", size: 30, bold: true, color: "000000" },
          paragraph: { spacing: { before: 340, after: 130 }, keepNext: true } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: "Aptos Display", size: 24, bold: true, color: "000000" },
          paragraph: { spacing: { before: 240, after: 110 }, keepNext: true } },
      ] },
    sections: [{ properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 900, right: 900, bottom: 900, left: 900 } } }, children }],
  });
}

module.exports = { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, NAVY,
  paragraph, heading, bullet, pageBreak, table, figure, document };
