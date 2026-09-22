import math
import analytics as an


def test_top5_artist_credit_share(prepared):
    _, _, exploded, *_ = prepared
    assert an.artist_concentration_index(exploded, 5)["top_n_share_pct"] == 15.29


def test_period_full_credit_hhi(prepared):
    _, _, exploded, *_ = prepared
    assert an.artist_concentration_index(exploded, 5)["hhi"] == 116.2


def test_collaboration_entry_share(prepared):
    _, clean, *_ = prepared
    assert round(an.collaboration_ratio(clean) * 100, 2) == 17.75


def test_average_artists_per_entry(prepared):
    _, clean, *_ = prepared
    assert an.avg_collaborators_per_entry(clean) == 1.241


def test_recording_collaboration_share(prepared):
    _, _, _, recordings, _ = prepared
    assert round((recordings["n_collaborators"] > 1).mean() * 100, 2) == 15.61


def test_average_artists_per_recording_proxy(prepared):
    _, _, _, recordings, _ = prepared
    assert round(recordings["n_collaborators"].mean(), 3) == 1.197


def test_explicit_share(prepared):
    _, clean, *_ = prepared
    assert an.explicit_share(clean).to_dict() == {"Explicit": 32.06, "Clean": 67.94}


def test_explicit_exclusive_rank_bands(prepared):
    _, clean, *_ = prepared
    got = an.explicit_by_rank(clean).to_dict()
    assert got == {"1-5": 40.0, "6-10": 40.79, "11-20": 33.35, "21-50": 28.85}


def test_collaboration_exclusive_rank_bands(prepared):
    _, clean, *_ = prepared
    got = an.collab_by_rank_group(clean).to_dict()
    assert got == {"1-5": 15.79, "6-10": 21.01, "11-20": 20.74, "21-50": 16.53}


def test_release_format_share(prepared):
    _, clean, *_ = prepared
    got = an.album_type_share(clean).to_dict()
    assert got == {"album": 59.96, "single": 39.76, "compilation": 0.28}


def test_nationality_share(prepared):
    _, _, exploded, *_ = prepared
    got = an.domestic_vs_international(exploded).to_dict()
    assert got == {"International": 64.61, "UK / Domestic": 34.68, "Unclassified": 0.7}


def test_collaboration_edges_schema(prepared):
    _, clean, *_ = prepared
    edges = an.collaboration_edges(clean)
    assert ["artist_a", "artist_b", "co_credited_appearances", "unique_collaborative_tracks"] == list(edges.columns[:4])
    assert "weight" in edges.columns
    assert len(edges) > 0


def test_collaboration_edges_sorted_descending(prepared):
    _, clean, *_ = prepared
    edges = an.collaboration_edges(clean)
    assert edges["co_credited_appearances"].is_monotonic_decreasing


def test_heatmap_uses_exclusive_rank_bands(prepared):
    _, clean, *_ = prepared
    heat = an.explicit_heatmap_by_rank_and_time(clean)
    assert list(heat.index) == ["1-5", "6-10", "11-20", "21-50"]
    assert heat.shape[1] >= 2


def test_release_format_by_rank_sums_to_100(prepared):
    _, clean, *_ = prepared
    tab = an.release_format_by_rank(clean)
    assert ((tab.sum(axis=1) - 100).abs() < 0.02).all()

def test_snapshot_market_metrics_regression(prepared):
    _, _, credits, *_ = prepared
    snapshot = an.snapshot_market_metrics(credits)
    assert len(snapshot) == 556
    assert round(float(snapshot["unique_artists"].mean()), 2) == 48.53
    assert round(float(snapshot["artist_credit_uniqueness_ratio"].mean()), 3) == 0.781
    assert round(float(snapshot["shannon_entropy"].mean()), 3) == 3.585
    assert round(float(snapshot["effective_number_of_artists"].mean()), 2) == 37.67
    assert round(float(snapshot["fractional_hhi"].mean()), 1) == 474.1
    assert round(float(snapshot["fractional_hhi"].median()), 1) == 338.0
    assert (snapshot["artist_credit_uniqueness_ratio"] <= 1.0).all()


def test_snapshot_effective_artists_matches_exp_entropy(prepared):
    import numpy as np

    _, _, credits, *_ = prepared
    snapshot = an.snapshot_market_metrics(credits)
    error = (
        snapshot["effective_number_of_artists"]
        - np.exp(snapshot["shannon_entropy"])
    ).abs().max()
    assert float(error) < 1e-12
