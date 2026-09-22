"""Export report-ready metrics from canonical analytical dataframes."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import analytics as an
from artist_nationality import INTL, UK, UNK, classify


def _round_map(series: pd.Series) -> dict[str, float]:
    return {str(k): round(float(v), 2) for k, v in series.items()}



def write_report_data(entries: pd.DataFrame, credits: pd.DataFrame, recordings: pd.DataFrame, quality: dict, path: str | Path) -> dict:
    """Write the one canonical report-data payload consumed by DOCX generators."""
    credits = credits.copy()
    credits["nationality"] = credits["artist_name"].apply(classify)
    snapshot = an.snapshot_market_metrics(credits)
    full = an.artist_concentration_index(credits, 5)
    fractional = credits.groupby("artist_name")["fractional_entry_weight"].sum()
    fractional = fractional / fractional.sum()
    full_nat = credits["nationality"].value_counts(normalize=True).mul(100)
    frac_nat = credits.groupby("nationality")["fractional_entry_weight"].sum()
    frac_nat = frac_nat / frac_nat.sum() * 100
    duration = float(entries["duration_sec"].mean())
    formats = an.album_type_share(entries)
    data = {
        "methodology_version": "2.0-snapshot-aware",
        "analytical_units": {"chart_entry": "one observed rank within one reconstructed snapshot", "snapshot": "one complete ordered Top-50 ranking; boundaries inferred from resets to position 1", "artist_credit": "one credited artist on one chart entry", "song_title": "the raw textual song value; not a track identifier", "recording_proxy": "normalised title + exact duration_ms; dataset-local and not a global ID", "recording_proxy_metadata": "one canonical row per proxy using the earliest observed metadata after sorting by date and source_row_id; this deterministic first-observed rule is also used for proxy-level collaboration attributes"},
        "counts": {"processed_chart_entries": int(len(entries)), "distinct_dates": int(entries.date.nunique()), "snapshots": int(entries.snapshot_id.nunique()), "unique_song_titles_raw": int(entries.song.nunique()), "unique_song_titles_normalized": int(entries.song_norm.nunique()), "unique_recording_proxies": int(len(recordings)), "unique_artists": int(credits.artist_name.nunique()), "artist_credit_observations": int(len(credits))},
        "date_range": {"min": str(entries.date.min().date()), "max": str(entries.date.max().date())},
        "concentration": {"period_wide_full_credit": {"top_5_share_pct": full["top_n_share_pct"], "top_10_share_pct": an.artist_concentration_index(credits, 10)["top_n_share_pct"], "top_20_share_pct": an.artist_concentration_index(credits, 20)["top_n_share_pct"], "hhi": full["hhi"]}, "period_wide_fractional": {"top_5_share_pct": round(float(fractional.nlargest(5).sum() * 100), 2), "hhi": round(float(fractional.pow(2).sum() * 10_000), 1)}, "snapshot_fractional": {"mean_hhi": round(float(snapshot.fractional_hhi.mean()), 1), "median_hhi": round(float(snapshot.fractional_hhi.median()), 1), "min_hhi": round(float(snapshot.fractional_hhi.min()), 1), "max_hhi": round(float(snapshot.fractional_hhi.max()), 1)}},
        "diversity": {"mean_snapshot_unique_artists": round(float(snapshot.unique_artists.mean()), 2), "mean_artist_credit_uniqueness_ratio": round(float(snapshot.artist_credit_uniqueness_ratio.mean()), 3), "mean_shannon_entropy": round(float(snapshot.shannon_entropy.mean()), 3), "mean_effective_number_of_artists": round(float(snapshot.effective_number_of_artists.mean()), 2)},
        "collaboration": {"entry_share_pct": round(float(an.collaboration_ratio(entries) * 100), 2), "recording_proxy_share_pct": round(float(recordings.is_collaboration.mean() * 100), 2), "average_collaborators_per_entry": an.avg_collaborators_per_entry(entries), "average_collaborators_per_recording_proxy": round(float(recordings.n_collaborators.mean()), 3), "entry_counts": an.solo_vs_collab(entries).to_dict(), "exclusive_rank_bands_pct": _round_map(an.collab_by_rank_group(entries)), "top_pairs": an.collaboration_edges(entries).head(20).drop(columns="weight").to_dict("records")},
        "explicit": {"overall_pct": _round_map(an.explicit_share(entries)), "exclusive_rank_bands_pct": _round_map(an.explicit_by_rank(entries)), "cumulative_top_n_pct": {f"Top {n}": round(float(entries.loc[entries.position <= n, "is_explicit"].mean() * 100), 2) for n in (5, 10, 20)}},
        "release_format": {"overall_pct": _round_map(formats), "exclusive_rank_bands_pct": {str(k): _round_map(v) for k, v in an.release_format_by_rank(entries).items()}},
        "nationality": {"artist_credit_share_pct": {label: round(float(full_nat.get(label, 0)), 2) for label in [UK, INTL, UNK]}, "fractional_entry_share_pct": {label: round(float(frac_nat.get(label, 0)), 2) for label in [UK, INTL, UNK]}},
        "duration": {"mean_seconds": round(duration, 1), "mean_mm_ss": f"{int(duration // 60)}:{int(duration % 60):02d}", "distribution_pct": _round_map(an.duration_distribution(entries)), "by_popularity_quartile_seconds": _round_map(an.duration_vs_popularity(entries)), "summary_seconds": {str(k): float(v) for k, v in an.duration_summary_stats(entries).items()}},
        "data_quality": quality,
    }
    data["kpi_summary"] = {"Raw/processed chart entries": data["counts"]["processed_chart_entries"], "Distinct dates": data["counts"]["distinct_dates"], "Snapshots": data["counts"]["snapshots"], "Unique recording proxies": data["counts"]["unique_recording_proxies"], "Artist-credit observations": data["counts"]["artist_credit_observations"], "Collaboration share — chart entries (%)": data["collaboration"]["entry_share_pct"], "Collaboration share — recording proxies (%)": data["collaboration"]["recording_proxy_share_pct"], "Period-wide Top-5 artist-credit share (%)": full["top_n_share_pct"], "Period-wide artist-credit HHI": full["hhi"], "Mean effective number of artists": data["diversity"]["mean_effective_number_of_artists"], "Explicit chart-entry share (%)": data["explicit"]["overall_pct"]["Explicit"], "Album chart-entry share (%)": round(float(formats.get("album", 0)), 2), "Single chart-entry share (%)": round(float(formats.get("single", 0)), 2), "Compilation chart-entry share (%)": round(float(formats.get("compilation", 0)), 2), "UK/Domestic artist-credit share (%)": data["nationality"]["artist_credit_share_pct"][UK], "International artist-credit share (%)": data["nationality"]["artist_credit_share_pct"][INTL], "Nationality unclassified artist-credit rate (%)": data["nationality"]["artist_credit_share_pct"][UNK], "Average duration (mm:ss)": data["duration"]["mean_mm_ss"]}
    Path(path).write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    return data
