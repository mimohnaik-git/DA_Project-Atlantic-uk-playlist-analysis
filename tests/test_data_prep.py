import pandas as pd
from data_prep import normalize_song_title, split_collaborators


def test_source_row_count(prepared):
    raw, *_ = prepared
    assert len(raw) == 27800


def test_processed_row_count(prepared):
    _, clean, *_ = prepared
    assert len(clean) == 27800


def test_distinct_dates(prepared):
    _, clean, *_ = prepared
    assert clean["date"].nunique() == 555


def test_snapshot_count(prepared):
    _, clean, *_ = prepared
    assert clean["snapshot_id"].nunique() == 556


def test_march_first_reconstructs_two_complete_snapshots(prepared):
    _, clean, *_ = prepared
    march = clean[clean["date"] == pd.Timestamp("2025-03-01")]
    assert len(march) == 100
    assert march.groupby("snapshot_id").size().tolist() == [50, 50]
    assert march.groupby("snapshot_id")["position"].nunique().tolist() == [50, 50]


def test_all_snapshot_positions_are_unique(prepared):
    _, clean, *_ = prepared
    assert clean.duplicated(["snapshot_id", "position"]).sum() == 0


def test_all_snapshots_have_50_rows(prepared):
    _, clean, *_ = prepared
    assert clean.groupby("snapshot_id").size().eq(50).all()


def test_normalized_title_count(prepared):
    _, clean, *_ = prepared
    assert clean["song_norm"].nunique() == 798


def test_recording_proxy_count(prepared):
    _, clean, _, recordings, _ = prepared
    assert clean["recording_proxy_id"].nunique() == 833
    assert len(recordings) == 833


def test_recording_proxy_is_title_plus_duration(prepared):
    _, clean, *_ = prepared
    expected = clean["song_norm"] + "||" + clean["duration_ms"].astype(str)
    assert expected.equals(clean["recording_proxy_id"])


def test_artist_credit_count(prepared):
    _, _, exploded, *_ = prepared
    assert len(exploded) == 34492


def test_unique_artist_count(prepared):
    _, _, exploded, *_ = prepared
    assert exploded["artist_name"].nunique() == 359


def test_fractional_artist_weights_reconcile(prepared):
    _, _, exploded, *_ = prepared
    sums = exploded.groupby("source_row_id")["fractional_entry_weight"].sum()
    assert (sums - 1.0).abs().max() < 1e-12


def test_protected_artist_name_is_not_split():
    assert split_collaborators("Chase & Status") == ["Chase & Status"]


def test_multi_artist_credit_is_split():
    assert split_collaborators("Calvin Harris & Ellie Goulding") == ["Calvin Harris", "Ellie Goulding"]


def test_title_normalization_is_case_insensitive():
    assert normalize_song_title("  Song   Name ") == "song name"
