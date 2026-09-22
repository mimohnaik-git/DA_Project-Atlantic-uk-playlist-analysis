"""Validate canonical data without generating figures or reports."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from data_prep import RAW_PATH, canonical_recordings, load_raw, run
from data_quality import validate_all

raw = load_raw(ROOT / RAW_PATH)
entries, credits, _ = run(ROOT / RAW_PATH)
report = validate_all(raw, entries, credits, canonical_recordings(entries))
print(json.dumps(report, indent=2, default=str))
if report["status"] != "PASS":
    raise SystemExit("Validation failed")
