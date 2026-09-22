"""Core analytics for the UK Top 50 music-market intelligence case study."""
from __future__ import annotations

from itertools import combinations
import numpy as np
import pandas as pd

RANK_ORDER = ["1-5", "6-10", "11-20", "21-50"]
DURATION_ORDER = ["Short (<2:30)", "Standard (2:30-3:30)", "Long (3:30-4:30)", "Extended (4:30+)"]
ALBUM_SIZE_ORDER = ["Single (1)", "EP (2-5)", "Album (6-12)", "Deluxe (13-20)", "Extended (20+)"]


def unique_artists_per_day(exploded):
    return exploded.groupby("date")["artist_name"].nunique()


def artist_appearances(exploded):
    return exploded.groupby("artist_name").size().sort_values(ascending=False).rename("appearances")


def top_dominating_artists(exploded, n=20):
    return artist_appearances(exploded).head(int(n))


def artist_concentration_index(exploded, top_n=5):
    """Return period-wide full-credit artist concentration.

    HHI is computed as 10,000 * sum(p_i ** 2), where p_i is each artist's
    share of full artist-credit appearances in the supplied selection. This
    period-wide persistence measure is intentionally distinct from the
    fractional snapshot HHI displayed in the dashboard's Health view.
    """
    counts = artist_appearances(exploded)
    total = float(counts.sum())
    if total == 0:
        return {"top_n": top_n, "top_n_share_pct": 0.0, "hhi": 0.0, "total_unique_artists": 0}
    shares = counts / total
    return {
        "top_n": int(top_n),
        "top_n_share_pct": round(float(shares.head(top_n).sum() * 100), 2),
        "hhi": round(float((shares.pow(2).sum()) * 10000), 1),
        "total_unique_artists": int(counts.shape[0]),
    }


def domestic_vs_international(exploded):
    from artist_nationality import classify
    ex = exploded.copy()
    if "nationality" not in ex.columns:
        ex["nationality"] = ex["artist_name"].apply(classify)
    pct = ex["nationality"].value_counts(normalize=True).mul(100)
    return pct.round(2)


def domestic_vs_international_by_rank(df, exploded):
    from artist_nationality import classify, UK, INTL, UNK
    ex = exploded.copy()
    if "nationality" not in ex.columns:
        ex["nationality"] = ex["artist_name"].apply(classify)
    tab = pd.crosstab(ex["rank_band"], ex["nationality"], normalize="index").mul(100)
    return tab.reindex(index=RANK_ORDER, columns=[UK, INTL, UNK]).fillna(0).round(2)


def domestic_vs_international_trend(exploded, freq="QE"):
    from artist_nationality import classify, UK, INTL, UNK
    ex = exploded.copy()
    if "nationality" not in ex.columns:
        ex["nationality"] = ex["artist_name"].apply(classify)
    tab = (
        ex.set_index("date")
        .groupby("nationality")
        .resample(freq)
        .size()
        .unstack(0)
        .fillna(0)
        .reindex(columns=[UK, INTL, UNK], fill_value=0)
    )
    denom = tab.sum(axis=1).replace(0, np.nan)
    return tab.div(denom, axis=0).mul(100).fillna(0).round(2)


def solo_vs_collab(df):
    counts = df["is_collaboration"].value_counts()
    return pd.Series({"Solo chart entries": int(counts.get(False, 0)), "Collaborative chart entries": int(counts.get(True, 0))})


def avg_collaborators_per_entry(df):
    return round(float(df["n_collaborators"].mean()), 3) if len(df) else np.nan


def avg_collaborators_per_song(df):
    return avg_collaborators_per_entry(df)


def collaboration_ratio(df):
    return round(float(df["is_collaboration"].mean()), 6) if len(df) else 0.0


def collab_by_rank_group(df):
    return (df.groupby("rank_band", observed=True)["is_collaboration"].mean().reindex(RANK_ORDER).mul(100)).round(2)


def collaboration_edges(df):
    """Pair-level repeated co-credit appearances and distinct recording proxies.

    Accepts either the cleaned chart-entry layer (preferred) or the historical
    exploded artist-credit layer used by legacy report scripts.
    """
    counts: dict[tuple[str, str], dict[str, object]] = {}

    if "collaborators" in df.columns:
        iterator = (
            (row.collaborators, getattr(row, "recording_proxy_id", None))
            for row in df.itertuples(index=False)
        )
    elif "artist_name" in df.columns:
        group_cols = [c for c in ["snapshot_id", "date", "position", "recording_proxy_id", "song"] if c in df.columns]
        if not group_cols:
            return pd.DataFrame(columns=["artist_a", "artist_b", "co_credited_appearances", "unique_collaborative_tracks", "weight"])
        def _iter():
            for key, group in df.groupby(group_cols, observed=True, sort=False):
                artists = group["artist_name"].dropna().astype(str).tolist()
                if "recording_proxy_id" in group.columns:
                    rec_id = str(group["recording_proxy_id"].iloc[0])
                else:
                    rec_id = str(key)
                yield artists, rec_id
        iterator = _iter()
    else:
        return pd.DataFrame(columns=["artist_a", "artist_b", "co_credited_appearances", "unique_collaborative_tracks", "weight"])

    for artists_raw, recording_id in iterator:
        artists = sorted(set(artists_raw)) if isinstance(artists_raw, (list, tuple, set)) else []
        if len(artists) < 2:
            continue
        for a, b in combinations(artists, 2):
            rec = counts.setdefault((a, b), {"appearances": 0, "recordings": set()})
            rec["appearances"] += 1
            if recording_id is not None:
                rec["recordings"].add(recording_id)

    rows = [
        (a, b, int(v["appearances"]), int(len(v["recordings"])), int(v["appearances"]))
        for (a, b), v in counts.items()
    ]
    if not rows:
        return pd.DataFrame(columns=["artist_a", "artist_b", "co_credited_appearances", "unique_collaborative_tracks", "weight"])
    return (
        pd.DataFrame(rows, columns=["artist_a", "artist_b", "co_credited_appearances", "unique_collaborative_tracks", "weight"])
        .sort_values(["co_credited_appearances", "unique_collaborative_tracks", "artist_a", "artist_b"], ascending=[False, False, True, True])
        .reset_index(drop=True)
    )


def explicit_share(df):
    counts = df["is_explicit"].value_counts(normalize=True).mul(100)
    return pd.Series({"Explicit": round(float(counts.get(True, 0)), 2), "Clean": round(float(counts.get(False, 0)), 2)})


def explicit_by_rank(df):
    return (df.groupby("rank_band", observed=True)["is_explicit"].mean().reindex(RANK_ORDER).mul(100)).round(2)


def explicit_over_time(df, freq="ME"):
    return df.set_index("date").resample(freq)["is_explicit"].mean().mul(100).round(2)


def explicit_heatmap_by_rank_and_time(df, freq="Q"):
    tmp = df.copy()
    tmp["quarter"] = tmp["date"].dt.to_period("Q").astype(str)
    heat = tmp.groupby(["rank_band", "quarter"], observed=True)["is_explicit"].mean().mul(100).unstack("quarter")
    return heat.reindex(RANK_ORDER).round(2)


def album_type_share(df):
    return df["album_type"].value_counts(normalize=True).mul(100).round(2)


def release_format_by_rank(df):
    tab = pd.crosstab(df["rank_band"], df["album_type"], normalize="index").mul(100)
    cols = [c for c in ["album", "compilation", "single"] if c in tab.columns]
    return tab.reindex(index=RANK_ORDER, columns=cols).fillna(0).round(2)


def album_size_vs_inclusion(df):
    if "album_size_bucket" in df.columns:
        series = df["album_size_bucket"]
    else:
        bins = [0, 1, 5, 12, 20, np.inf]
        series = pd.cut(df["total_tracks"], bins=bins, labels=ALBUM_SIZE_ORDER)
    return series.value_counts().reindex(ALBUM_SIZE_ORDER).fillna(0).astype(int)


def album_size_vs_popularity(df):
    if "album_size_bucket" in df.columns:
        work = df
    else:
        work = df.copy()
        work["album_size_bucket"] = pd.cut(work["total_tracks"], bins=[0, 1, 5, 12, 20, np.inf], labels=ALBUM_SIZE_ORDER)
    return work.groupby("album_size_bucket", observed=True)["popularity"].mean().reindex(ALBUM_SIZE_ORDER).round(2)


def duration_distribution(df):
    return df["duration_bucket"].value_counts(normalize=True).mul(100).reindex(DURATION_ORDER).fillna(0).round(2)


def duration_vs_popularity(df):
    order = ["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"]
    return df.groupby("popularity_bucket", observed=True)["duration_sec"].mean().reindex(order).round(1)


def duration_summary_stats(df):
    return df["duration_sec"].describe().round(1)


# Retired legacy Diversity Score / Content Variety Index helpers were removed
# from the active analytics layer. The final project uses snapshot-level
# Shannon entropy, effective artist count, unique artists, and HHI instead.

def concentration_curve(exploded):
    counts = artist_appearances(exploded).sort_values(ascending=False)
    if counts.empty:
        return pd.DataFrame(columns=["artist_rank_pct", "cumulative_share_pct", "artist_name", "appearances"])
    return pd.DataFrame({
        "artist_rank_pct": np.arange(1, len(counts) + 1) / len(counts) * 100,
        "cumulative_share_pct": counts.cumsum().div(counts.sum()).mul(100).values,
        "artist_name": counts.index,
        "appearances": counts.values,
    })


def numeric_correlation_matrix(df):
    cols = [c for c in ["position", "popularity", "duration_sec", "total_tracks", "n_collaborators"] if c in df.columns]
    work = df[cols].copy()
    if "is_explicit" in df.columns:
        work["is_explicit"] = df["is_explicit"].astype(int)
    if "is_collaboration" in df.columns:
        work["is_collaboration"] = df["is_collaboration"].astype(int)
    return work.corr(numeric_only=True)


def monthly_new_artists(exploded):
    first_seen = exploded.groupby("artist_name")["date"].min()
    return first_seen.dt.to_period("M").dt.to_timestamp().value_counts().sort_index()


def snapshot_market_metrics(artist_credits):
    """Calculate snapshot-level diversity and concentration.

    Fractional artist weights ensure each chart entry contributes a total
    weight of 1 even when multiple artists are credited.

    Returns:
        date
        unique_artists
        artist_credit_observations
        artist_credit_uniqueness_ratio
        shannon_entropy
        effective_number_of_artists
        fractional_hhi
    """
    if artist_credits.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "unique_artists",
                "artist_credit_observations",
                "artist_credit_uniqueness_ratio",
                "shannon_entropy",
                "effective_number_of_artists",
                "fractional_hhi",
            ]
        )

    ex = artist_credits.copy()

    key = "snapshot_id" if "snapshot_id" in ex.columns else "date"

    if "fractional_entry_weight" not in ex.columns:
        ex["fractional_entry_weight"] = (
            1.0 / ex["n_collaborators"].clip(lower=1)
        )

    weights = (
        ex.groupby(
            [key, "artist_name"],
            observed=True,
        )["fractional_entry_weight"]
        .sum()
        .rename("artist_weight")
        .reset_index()
    )

    weights["total_weight"] = (
        weights.groupby(key)["artist_weight"]
        .transform("sum")
    )

    weights["share"] = (
        weights["artist_weight"]
        / weights["total_weight"].replace(0, np.nan)
    )

    weights["entropy_term"] = (
        -weights["share"]
        * np.log(weights["share"].clip(lower=1e-15))
    )

    weights["hhi_term"] = (
        weights["share"].pow(2) * 10000
    )

    summary = weights.groupby(
        key,
        observed=True,
    ).agg(
        shannon_entropy=("entropy_term", "sum"),
        fractional_hhi=("hhi_term", "sum"),
    )

    summary["effective_number_of_artists"] = np.exp(
        summary["shannon_entropy"]
    )

    summary["unique_artists"] = (
        ex.groupby(key)["artist_name"].nunique()
    )

    summary["artist_credit_observations"] = (
        ex.groupby(key)["artist_name"].size()
    )

    summary["artist_credit_uniqueness_ratio"] = (
        summary["unique_artists"]
        / summary["artist_credit_observations"].replace(0, np.nan)
    )

    summary["date"] = pd.to_datetime(
        ex.groupby(key)["date"].min()
    )

    return (
        summary.reset_index()
        .sort_values(["date", key])
        .reset_index(drop=True)
    )
