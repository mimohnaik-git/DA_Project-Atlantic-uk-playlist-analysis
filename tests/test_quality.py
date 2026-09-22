from data_quality import validate_all


def _report(prepared):
    raw, clean, exploded, recordings, _ = prepared
    return validate_all(raw, clean, exploded, recordings)


def _by_name(report):
    return {c["name"]: c for c in report["checks"]}


def test_quality_has_no_failures(prepared):
    report = _report(prepared)
    assert report["status"] == "PASS"
    assert not [c for c in report["checks"] if c["status"] == "FAIL"]


def test_calendar_gap_count(prepared):
    c = _by_name(_report(prepared))["calendar_date_coverage"]
    assert c["status"] == "WARNING"
    assert c["value"] == ["2025-03-14", "2025-03-25", "2025-07-11", "2025-08-13"]


def test_multiple_snapshots_warning(prepared):
    c = _by_name(_report(prepared))["multiple_snapshots_per_date"]
    assert c["value"] == {"2025-03-01": 2}


def test_exact_source_repeat_count(prepared):
    c = _by_name(_report(prepared))["exact_source_duplicates"]
    assert c["status"] == "WARNING"
    assert c["value"] == 12


def test_nationality_unclassified_rate(prepared):
    c = _by_name(_report(prepared))["nationality_coverage"]
    assert c["status"] == "WARNING"
    assert c["value"] == 0.7


def test_recording_metadata_stability_counts(prepared):
    c = _by_name(_report(prepared))["recording_metadata_stability"]
    assert c["value"]["song"] == 3
    assert c["value"]["credited_artist_set"] == 25
    assert c["value"]["duration_ms"] == 0
    assert c["value"]["album_type"] == 48
    assert c["value"]["total_tracks"] == 59
    assert c["value"]["is_explicit"] == 11


def test_title_collision_count(prepared):
    c = _by_name(_report(prepared))["title_collisions"]
    assert c["value"] == 33


def test_output_reconciliation(prepared):
    c = _by_name(_report(prepared))["output_row_consistency"]
    assert c["status"] == "PASS"
    assert c["value"] == {"raw": 27800, "processed": 27800, "artist_credits": 34492, "recordings": 833}
