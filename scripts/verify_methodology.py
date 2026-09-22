"""Focused pre-commit audit of recording identity and diversity mathematics."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import analytics as an  # noqa: E402
from data_prep import run  # noqa: E402


EXPECTED = {
    "title_only_proxies": 798,
    "title_duration_proxies": 833,
    "tolerance_proxies": 810,
    "artist_set_duration_proxies": 858,
    "ambiguous_title_duration_groups": 25,
    "snapshots": 556,
    "mean_unique_artists": 48.530575539568346,
    "mean_artist_credit_uniqueness_ratio": 0.7805560544082328,
    "mean_shannon_entropy": 3.584751268990977,
    "mean_effective_artists": 37.672329903980476,
    "mean_fractional_hhi": 474.1,
    "median_fractional_hhi": 338.0,
}


def assert_close(name: str, actual: float, expected: float, tolerance: float = 1e-9) -> None:
    if not math.isclose(float(actual), float(expected), rel_tol=0.0, abs_tol=tolerance):
        raise AssertionError(f"{name}: expected {expected}, got {actual}")


def enforce_regressions(result: dict, diversity: pd.DataFrame) -> None:
    candidates = result["recording_proxy_candidates"]
    exact = candidates["B_title_exact_duration"]
    checks = {
        "title_only_proxies": candidates["A_title_only"]["unique_proxy_count"],
        "title_duration_proxies": exact["unique_proxy_count"],
        "tolerance_proxies": candidates["C_title_duration_2s_tolerance"]["unique_proxy_count"],
        "artist_set_duration_proxies": candidates["D_title_artist_set_exact_duration_previous"]["unique_proxy_count"],
        "ambiguous_title_duration_groups": candidates["same_title_exact_duration_multiple_artist_sets"],
        "snapshots": int(len(diversity)),
    }
    for name, actual in checks.items():
        if actual != EXPECTED[name]:
            raise AssertionError(f"{name}: expected {EXPECTED[name]}, got {actual}")

    assert_close("mean_unique_artists", diversity["unique_artists"].mean(), EXPECTED["mean_unique_artists"])
    assert_close(
        "mean_artist_credit_uniqueness_ratio",
        diversity["artist_credit_uniqueness_ratio"].mean(),
        EXPECTED["mean_artist_credit_uniqueness_ratio"],
    )
    assert_close("mean_shannon_entropy", diversity["shannon_entropy"].mean(), EXPECTED["mean_shannon_entropy"])
    assert_close(
        "mean_effective_artists",
        diversity["effective_number_of_artists"].mean(),
        EXPECTED["mean_effective_artists"],
    )
    assert_close("mean_fractional_hhi", diversity["fractional_hhi"].mean(), EXPECTED["mean_fractional_hhi"], 0.05)
    assert_close("median_fractional_hhi", diversity["fractional_hhi"].median(), EXPECTED["median_fractional_hhi"], 0.05)
    if result["diversity"]["snapshots_above_one"] != 0:
        raise AssertionError("artist-credit uniqueness ratio exceeded 1.0")
    if result["diversity"]["effective_identity_max_abs_error"] > 1e-12:
        raise AssertionError("effective artist count no longer equals exp(Shannon entropy) per snapshot")


def tolerance_clusters(group: pd.DataFrame, tolerance_ms: int = 2_000) -> pd.Series:
    """Cluster durations per title when adjacent observed values differ by <= tolerance."""
    labels: dict[int, int] = {}
    for _, title_group in group.groupby("song_norm", sort=True):
        durations = sorted(title_group["duration_ms"].unique())
        cluster = 0
        previous = None
        duration_label: dict[int, int] = {}
        for duration in durations:
            if previous is not None and duration - previous > tolerance_ms:
                cluster += 1
            duration_label[duration] = cluster
            previous = duration
        for index, duration in title_group["duration_ms"].items():
            labels[index] = duration_label[duration]
    return pd.Series(labels).sort_index()


def candidate_summary(entries: pd.DataFrame, column: str) -> dict:
    grouped = entries.groupby(column, dropna=False)
    title_proxy_counts = entries.groupby("song_norm")[column].nunique()
    artist_sets = grouped["credited_artist_set"].nunique()
    current_proxies = grouped["recording_proxy_id"].nunique()
    selected_splits = entries.groupby("recording_proxy_id")[column].nunique()
    return {
        "unique_proxy_count": int(entries[column].nunique()),
        "titles_split_into_multiple_proxies": int((title_proxy_counts > 1).sum()),
        "candidate_groups_merging_current_proxies": int((current_proxies > 1).sum()),
        "selected_proxy_groups_split_by_candidate": int((selected_splits > 1).sum()),
        "candidate_groups_with_multiple_artist_sets": int((artist_sets > 1).sum()),
        "rows_in_multiple_artist_set_groups": int(entries[column].isin(artist_sets[artist_sets > 1].index).sum()),
    }


def main() -> None:
    entries, credits, _ = run()
    work = entries.copy()
    # Derived only for methodology comparison.
    # The canonical pipeline stores credited artists in `collaborators`.
    # Sort + casefold makes this an order-insensitive credited-artist set.
    work["credited_artist_set"] = work["collaborators"].apply(
        lambda names: " | ".join(
            sorted(
                str(name).strip().casefold()
                for name in names
                if str(name).strip()
            )
        )
    )

    work["candidate_a_title"] = work["song_norm"]
    work["candidate_b_title_duration"] = (
        work["song_norm"] + "|" + work["duration_ms"].astype(str)
    )
    work["duration_tolerance_cluster"] = tolerance_clusters(work)
    work["candidate_c_title_duration_2s"] = (
        work["song_norm"] + "|cluster_" + work["duration_tolerance_cluster"].astype(str)
    )
    work["candidate_d_title_artist_duration"] = (
        work["song_norm"] + "|" + work["credited_artist_set"].str.casefold()
        + "|" + work["duration_ms"].astype(str)
    )

    title_duration_artist_sets = work.groupby(
        ["song_norm", "duration_ms"]
    )["credited_artist_set"].nunique()
    ambiguous = title_duration_artist_sets[title_duration_artist_sets > 1].sort_values(ascending=False)
    examples = []
    for (title, duration), count in ambiguous.head(12).items():
        rows = work[(work.song_norm == title) & (work.duration_ms == duration)]
        examples.append({
            "title_key": title,
            "duration_ms": int(duration),
            "artist_set_count": int(count),
            "artist_sets": sorted(rows.credited_artist_set.unique().tolist()),
            "observations_by_artist_set": {
                key: int(value) for key, value in rows.credited_artist_set.value_counts().items()
            },
            "date_min": str(rows.date.min().date()),
            "date_max": str(rows.date.max().date()),
        })

    diversity = an.snapshot_market_metrics(credits)
    entropy_gap = float(
        diversity["effective_number_of_artists"].mean()
        - math.exp(diversity["shannon_entropy"].mean())
    )
    result = {
        "recording_proxy_candidates": {
            "A_title_only": candidate_summary(work, "candidate_a_title"),
            "B_title_exact_duration": candidate_summary(work, "candidate_b_title_duration"),
            "C_title_duration_2s_tolerance": candidate_summary(work, "candidate_c_title_duration_2s"),
            "D_title_artist_set_exact_duration_previous": candidate_summary(
                work, "candidate_d_title_artist_duration"
            ),
            "same_title_exact_duration_multiple_artist_sets": int(len(ambiguous)),
            "ambiguity_examples": examples,
        },
        "diversity": {
            "unique_artists": diversity["unique_artists"].describe().to_dict(),
            "artist_credit_uniqueness_ratio": diversity[
                "artist_credit_uniqueness_ratio"
            ].describe().to_dict(),
            "snapshots_above_one": int((diversity.artist_credit_uniqueness_ratio > 1).sum()),
            "mean_entropy": float(diversity.shannon_entropy.mean()),
            "mean_effective_artists": float(diversity.effective_number_of_artists.mean()),
            "exp_mean_entropy": float(math.exp(diversity.shannon_entropy.mean())),
            "mean_effective_minus_exp_mean_entropy": entropy_gap,
            "effective_identity_max_abs_error": float(
                (
                    diversity.effective_number_of_artists
                    - diversity.shannon_entropy.map(math.exp)
                ).abs().max()
            ),
            "mean_fractional_hhi": float(diversity.fractional_hhi.mean()),
            "median_fractional_hhi": float(diversity.fractional_hhi.median()),
        },
    }
    enforce_regressions(result, diversity)
    print(json.dumps(result, indent=2, default=float))
    print("METHODOLOGY REGRESSION GATE: PASS")


if __name__ == "__main__":
    main()
