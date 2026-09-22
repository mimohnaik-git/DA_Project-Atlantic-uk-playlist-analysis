"""Build canonical processed data, outputs, figures, and DOCX reports."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import analytics as an
from data_prep import RAW_PATH, canonical_recordings, load_raw, run
from data_quality import validate_all
from export_report_data import write_report_data


def write_quality_report(report):
    output = ROOT / "outputs"
    output.mkdir(exist_ok=True)
    (output / "data_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    rows = ["name,status,value,detail"]
    for check in report["checks"]:
        rows.append(",".join('"' + str(check[key]).replace('"', '""') + '"' for key in ("name", "status", "value", "detail")))
    (output / "data_quality_report.csv").write_text("\n".join(rows) + "\n", encoding="utf-8")


def build(skip_charts=False, skip_reports=False):
    raw = load_raw(ROOT / RAW_PATH)
    entries, credits, _ = run(ROOT / RAW_PATH)
    recordings = canonical_recordings(entries)
    quality = validate_all(raw, entries, credits, recordings)
    if quality["status"] != "PASS":
        raise RuntimeError("Canonical data validation failed")
    processed = ROOT / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    entries.to_parquet(processed / "clean_playlist.parquet", index=False)
    credits.to_parquet(processed / "exploded_artists.parquet", index=False)
    recordings.to_parquet(processed / "recordings.parquet", index=False)
    write_quality_report(quality)
    report_data = write_report_data(entries, credits, recordings, quality, ROOT / "outputs" / "report_data.json")
    an.artist_appearances(credits).rename("artist_credit_appearances").reset_index().to_csv(ROOT / "outputs" / "artist_appearance_counts.csv", index=False)
    (ROOT / "outputs" / "analytics_output.txt").write_text("\n".join(["=== CANONICAL KPI SUMMARY ===", *[f"{k}: {v}" for k, v in report_data["kpi_summary"].items()]]) + "\n", encoding="utf-8")
    if not skip_charts:
        subprocess.run([sys.executable, "src/make_charts.py"], cwd=ROOT, check=True)
    if not skip_reports:
        subprocess.run(["node", "build_paper.js"], cwd=ROOT / "docgen", check=True)
        subprocess.run(["node", "build_exec_summary.js"], cwd=ROOT / "docgen", check=True)
    manifest = {"raw_rows": len(raw), "processed_rows": len(entries), "dates": int(entries.date.nunique()), "snapshots": int(entries.snapshot_id.nunique()), "quality_status": quality["status"], "charts_generated": not skip_charts, "reports_generated": not skip_reports}
    (ROOT / "outputs" / "build_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-charts", action="store_true")
    parser.add_argument("--skip-reports", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.skip_charts, args.skip_reports), indent=2))
