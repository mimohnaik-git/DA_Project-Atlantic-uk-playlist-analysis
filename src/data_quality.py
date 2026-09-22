"""Source and analytical-layer validation for the UK Top 50 case study."""
from __future__ import annotations

from typing import Any
import numpy as np
import pandas as pd

from artist_nationality import classify, UNK

REQUIRED_COLUMNS = [
    "date", "position", "song", "artist", "popularity", "duration_ms",
    "album_type", "total_tracks", "is_explicit", "album_cover_url",
]
EXPECTED_ROWS = 27800


def _check(name: str, status: str, value: Any, detail: str) -> dict:
    return {"name": name, "status": status, "value": value, "detail": detail}


def validate_all(raw: pd.DataFrame, clean: pd.DataFrame, exploded: pd.DataFrame, recordings: pd.DataFrame) -> dict:
    checks: list[dict] = []

    missing_cols = [c for c in REQUIRED_COLUMNS if c not in raw.columns]
    checks.append(_check("required_columns", "PASS" if not missing_cols else "FAIL", missing_cols,
                         "All required source fields must be present."))

    checks.append(_check("raw_row_count", "PASS" if len(raw) == EXPECTED_ROWS else "WARNING", int(len(raw)),
                         f"Supplied project extract is expected to contain {EXPECTED_ROWS:,} rows."))

    required_present = [c for c in REQUIRED_COLUMNS if c in raw.columns]
    nulls = int(raw[required_present].isna().sum().sum()) if required_present else int(raw.isna().sum().sum())
    checks.append(_check("required_value_nulls", "PASS" if nulls == 0 else "FAIL", nulls,
                         "Null cells across required source fields."))

    parsed = pd.to_datetime(raw["date"], format="%d-%m-%Y", errors="coerce") if "date" in raw else pd.Series(dtype="datetime64[ns]")
    parse_fail = int(parsed.isna().sum())
    checks.append(_check("date_parsing", "PASS" if parse_fail == 0 else "FAIL", parse_fail,
                         "Rows whose date could not be parsed."))

    observed_dates = pd.DatetimeIndex(sorted(clean["date"].dropna().unique()))
    full_dates = pd.date_range(observed_dates.min(), observed_dates.max(), freq="D") if len(observed_dates) else pd.DatetimeIndex([])
    missing_dates = [d.strftime("%Y-%m-%d") for d in full_dates.difference(observed_dates)]
    checks.append(_check("calendar_date_coverage", "WARNING" if missing_dates else "PASS", missing_dates,
                         "Missing dates are reported; they are not imputed."))

    per_date = clean.groupby("date")["snapshot_id"].nunique()
    multi = {d.strftime("%Y-%m-%d"): int(n) for d, n in per_date[per_date > 1].items()}
    checks.append(_check("multiple_snapshots_per_date", "WARNING" if multi else "PASS", multi,
                         "Snapshot boundaries are inferred from source-order resets to position 1."))

    march = clean.loc[clean["date"].eq(pd.Timestamp("2025-03-01"))]
    march_counts = march.groupby("snapshot_id")["position"].nunique().to_dict()
    march_complete = [sid for sid, n in march_counts.items() if n == 50]
    march_status = "PASS" if len(march_complete) == 2 and len(march) == 100 else "FAIL"
    checks.append(_check("march_1_reconstruction", march_status, march_complete,
                         "The 100-row date must reconstruct as two complete Top-50 snapshots."))

    invalid_pos = int((~clean["position"].between(1, 50)).sum())
    checks.append(_check("position_domain", "PASS" if invalid_pos == 0 else "FAIL", invalid_pos,
                         "Positions must be integers from 1 to 50."))

    snapshot_rows = clean.groupby("snapshot_id").size()
    bad_counts = {k: int(v) for k, v in snapshot_rows[snapshot_rows != 50].items()}
    checks.append(_check("snapshot_row_counts", "PASS" if not bad_counts else "FAIL", bad_counts,
                         "Each valid snapshot must contain 50 rows."))

    dup_positions = int(clean.duplicated(["snapshot_id", "position"]).sum())
    checks.append(_check("duplicate_snapshot_positions", "PASS" if dup_positions == 0 else "FAIL", dup_positions,
                         "Each expected position may occur once per snapshot."))

    missing_positions: dict[str, list[int]] = {}
    expected = set(range(1, 51))
    for sid, group in clean.groupby("snapshot_id"):
        miss = sorted(expected.difference(set(group["position"].astype(int))))
        if miss:
            missing_positions[str(sid)] = miss
    checks.append(_check("missing_snapshot_positions", "PASS" if not missing_positions else "FAIL", missing_positions,
                         "Missing ranks within reconstructed snapshots."))

    source_cols = [c for c in REQUIRED_COLUMNS if c in raw.columns]
    # Count repeated observations beyond their first occurrence.  The supplied
    # extract contains 12 such repeats, all cross-snapshot rather than within a
    # reconstructed Top-50 state.
    repeated_rows = int(raw.duplicated(source_cols).sum()) if source_cols else 0
    checks.append(_check("exact_source_duplicates", "WARNING" if repeated_rows else "PASS", repeated_rows,
                         "Repeated complete source rows are retained when they belong to different inferred snapshots."))

    dup_recordings = int(clean.duplicated(["snapshot_id", "recording_proxy_id"]).sum())
    checks.append(_check("duplicate_recordings_within_snapshot", "PASS" if dup_recordings == 0 else "WARNING", dup_recordings,
                         "Repeated recording proxies inside one snapshot require review."))

    bad_album = sorted(set(clean["album_type"].dropna()) - {"album", "single", "compilation"})
    checks.append(_check("album_type_domain", "PASS" if not bad_album else "FAIL", bad_album,
                         "Unexpected release-format values."))

    bad_explicit = sorted(set(clean["is_explicit"].dropna().map(type)) - {bool, np.bool_}, key=str)
    checks.append(_check("explicit_content_domain", "PASS" if not bad_explicit else "FAIL", [t.__name__ for t in bad_explicit],
                         "Explicit flag must be boolean."))

    bad_duration = int((pd.to_numeric(clean["duration_ms"], errors="coerce") <= 0).sum())
    checks.append(_check("positive_duration", "PASS" if bad_duration == 0 else "FAIL", bad_duration,
                         "Zero or negative duration values."))

    bad_tracks = int((pd.to_numeric(clean["total_tracks"], errors="coerce") <= 0).sum())
    checks.append(_check("positive_total_tracks", "PASS" if bad_tracks == 0 else "FAIL", bad_tracks,
                         "Invalid parent-release track counts."))

    popularity = pd.to_numeric(clean["popularity"], errors="coerce")
    bad_pop = int((~popularity.between(0, 100)).sum())
    checks.append(_check("popularity_bounds", "PASS" if bad_pop == 0 else "FAIL", bad_pop,
                         "Popularity must be between 0 and 100."))

    parse_issues = int(exploded["artist_name"].isna().sum())
    checks.append(_check("artist_parsing", "PASS" if parse_issues == 0 else "FAIL", parse_issues,
                         "Entries with no parsed credited artist."))

    empty_collabs = int(clean["collaborators"].apply(lambda x: not isinstance(x, list) or len(x) == 0).sum())
    checks.append(_check("empty_collaborator_arrays", "PASS" if empty_collabs == 0 else "FAIL", empty_collabs,
                         "Chart entries without a credited-artist array."))

    nationalities = exploded["artist_name"].apply(classify)
    unclassified_pct = round(float(nationalities.eq(UNK).mean() * 100), 2)
    checks.append(_check("nationality_coverage", "WARNING" if unclassified_pct > 0 else "PASS", unclassified_pct,
                         "Manual nationality mapping is incomplete by design; unclassified artists remain explicit."))

    # Stability diagnostics at recording-proxy grain.
    grouped = clean.groupby("recording_proxy_id", observed=True)
    credited_set = clean.assign(_credited=clean["collaborators"].apply(lambda x: tuple(x)))
    credited_counts = credited_set.groupby("recording_proxy_id")["_credited"].nunique()
    stability = {
        "song": int((grouped["song"].nunique() > 1).sum()),
        "credited_artist_set": int((credited_counts > 1).sum()),
        "duration_ms": int((grouped["duration_ms"].nunique() > 1).sum()),
        "album_type": int((grouped["album_type"].nunique() > 1).sum()),
        "total_tracks": int((grouped["total_tracks"].nunique() > 1).sum()),
        "is_explicit": int((grouped["is_explicit"].nunique() > 1).sum()),
        "credited_artist_set_on_title_duration_key": int((credited_counts > 1).sum()),
    }
    checks.append(_check("recording_metadata_stability", "WARNING" if any(stability.values()) else "PASS", stability,
                         "Recording-proxy metadata can legitimately vary across repeated chart observations; the proxy identity remains title + exact duration."))

    title_collisions = int((clean.groupby("song_norm")["duration_ms"].nunique() > 1).sum())
    checks.append(_check("title_collisions", "WARNING" if title_collisions else "PASS", title_collisions,
                         "Normalised song titles associated with multiple exact durations."))

    credit_sums = exploded.groupby("source_row_id")["fractional_entry_weight"].sum()
    weight_error = round(float((credit_sums - 1.0).abs().max()), 12) if len(credit_sums) else 0.0
    checks.append(_check("fractional_artist_weights", "PASS" if weight_error <= 1e-10 else "FAIL", weight_error,
                         "Fractional artist weights for each chart entry must reconcile to 1.0."))

    consistency = {
        "raw": int(len(raw)),
        "processed": int(len(clean)),
        "artist_credits": int(len(exploded)),
        "recordings": int(len(recordings)),
    }
    status = "PASS" if len(raw) == len(clean) and len(recordings) == clean["recording_proxy_id"].nunique() else "FAIL"
    checks.append(_check("output_row_consistency", status, consistency,
                         "Raw and processed row counts must reconcile; derived grains are reported separately."))

    return {"status": "PASS" if not any(c["status"] == "FAIL" for c in checks) else "FAIL", "checks": checks}
