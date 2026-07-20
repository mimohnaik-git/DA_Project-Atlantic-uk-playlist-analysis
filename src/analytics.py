"""
Core analytics for the UK Top 50 Playlist Market Structure, Artist Diversity
& Content Localization Analysis.

Every function returns a small, dashboard/report-ready pandas object.
"""
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# 1. Artist Dominance & Diversity
# ---------------------------------------------------------------------------

def unique_artists_per_day(exploded):
    return exploded.groupby("date")["artist_name"].nunique()


def artist_appearances(exploded):
    """Total chart appearances (entry-days) per unique artist."""
    return (exploded.groupby("artist_name")
            .size()
            .sort_values(ascending=False)
            .rename("appearances"))


def top_dominating_artists(exploded, n=20):
    return artist_appearances(exploded).head(n)


def artist_concentration_index(exploded, top_n=5):
    """
    Herfindahl-style concentration: share of total artist-appearances held by
    the top-N artists (a.k.a. Top-5 Concentration Ratio), plus a full HHI.
    """
    counts = artist_appearances(exploded)
    total = counts.sum()
    shares = counts / total
    top_share = shares.head(top_n).sum()
    hhi = (shares ** 2).sum() * 10000  # standard HHI scaling (0-10000)
    return {
        "top_n": top_n,
        "top_n_share_pct": round(top_share * 100, 2),
        "hhi": round(hhi, 1),
        "total_unique_artists": counts.shape[0],
    }


def diversity_score(df, exploded):
    """Unique artists / total playlist entries."""
    unique_artists = exploded["artist_name"].nunique()
    total_entries = len(df)
    return round(unique_artists / total_entries, 4)


def domestic_vs_international(exploded):
    """UK/Domestic vs. International share of chart appearances."""
    from artist_nationality import classify
    ex = exploded.copy()
    ex["nationality"] = ex["artist_name"].apply(classify)
    counts = ex["nationality"].value_counts()
    pct = (counts / counts.sum() * 100).round(2)
    return pct


def domestic_vs_international_by_rank(df, exploded):
    """Domestic vs International share within each rank group."""
    from artist_nationality import classify, UK, INTL, UNK
    ex = exploded.copy()
    ex["nationality"] = ex["artist_name"].apply(classify)
    order = ["Top 5", "Top 10", "Top 20", "21-50"]
    tab = pd.crosstab(ex["rank_group"], ex["nationality"], normalize="index") * 100
    # Under a narrow filter, not every nationality category may be present
    # (e.g. selecting one artist who only ever collaborates with UK acts) --
    # reindex columns too so UK/International/Unclassified always exist.
    return tab.reindex(index=order, columns=[UK, INTL, UNK]).round(2)


def domestic_vs_international_trend(exploded, freq="QE"):
    from artist_nationality import classify
    ex = exploded.copy()
    ex["nationality"] = ex["artist_name"].apply(classify)
    ex = ex[ex["nationality"] != "Unclassified"]
    tab = (ex.set_index("date")
           .groupby("nationality")
           .resample(freq)
           .size()
           .unstack(0)
           .fillna(0))
    pct = tab.div(tab.sum(axis=1), axis=0) * 100
    return pct.round(2)


# ---------------------------------------------------------------------------
# 2. Collaboration Structure
# ---------------------------------------------------------------------------

def solo_vs_collab(df):
    counts = df["is_collaboration"].value_counts()
    return pd.Series({
        "Solo": int(counts.get(False, 0)),
        "Collaboration": int(counts.get(True, 0)),
    })


def avg_collaborators_per_song(df):
    return round(df["n_collaborators"].mean(), 3)


def collaboration_ratio(df):
    return round(df["is_collaboration"].mean(), 4)


def collab_by_rank_group(df):
    order = ["Top 5", "Top 10", "Top 20", "21-50"]
    tab = (df.groupby("rank_group")["is_collaboration"]
           .mean()
           .reindex(order))
    return (tab * 100).round(2)


def collaboration_edges(exploded):
    """
    Build an edge list (artist_a, artist_b, weight) for the collaboration
    network: every pair of collaborators that appear together on a track.
    """
    from itertools import combinations
    pair_counts = {}
    grouping_cols = ["date", "position", "song"]
    for _, group in exploded.groupby(grouping_cols):
        artists = sorted(set(group["artist_name"]))
        if len(artists) < 2:
            continue
        for a, b in combinations(artists, 2):
            pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    edges = pd.DataFrame(
        [(a, b, w) for (a, b), w in pair_counts.items()],
        columns=["artist_a", "artist_b", "weight"]
    ).sort_values("weight", ascending=False)
    return edges


# ---------------------------------------------------------------------------
# 3. Content Explicitness
# ---------------------------------------------------------------------------

def explicit_share(df):
    counts = df["is_explicit"].value_counts(normalize=True) * 100
    return pd.Series({
        "Explicit": round(counts.get(True, 0), 2),
        "Clean": round(counts.get(False, 0), 2),
    })


def explicit_by_rank(df):
    order = ["Top 5", "Top 10", "Top 20", "21-50"]
    tab = (df.groupby("rank_group")["is_explicit"]
           .mean()
           .reindex(order)) * 100
    return tab.round(2)


def explicit_over_time(df, freq="ME"):
    tab = df.set_index("date").resample(freq)["is_explicit"].mean() * 100
    return tab.round(2)


# ---------------------------------------------------------------------------
# 4. Album Structure & Release Strategy
# ---------------------------------------------------------------------------

def album_type_share(df):
    return (df["album_type"].value_counts(normalize=True) * 100).round(2)


def album_size_vs_inclusion(df):
    """Average playlist appearances grouped by album size bucket."""
    bins = [0, 1, 5, 12, 20, np.inf]
    labels = ["Single (1)", "EP (2-5)", "Album (6-12)", "Deluxe (13-20)", "Extended (20+)"]
    df = df.copy()
    df["album_size_bucket"] = pd.cut(df["total_tracks"], bins=bins, labels=labels)
    return df["album_size_bucket"].value_counts().reindex(labels).fillna(0)


def release_format_by_rank(df):
    order = ["Top 5", "Top 10", "Top 20", "21-50"]
    tab = pd.crosstab(df["rank_group"], df["album_type"], normalize="index") * 100
    return tab.reindex(order).round(2)


# ---------------------------------------------------------------------------
# 5. Track Duration & Format
# ---------------------------------------------------------------------------

def duration_distribution(df):
    order = ["Short (<2:30)", "Standard (2:30-3:30)", "Long (3:30-4:30)", "Extended (4:30+)"]
    return (df["duration_bucket"].value_counts(normalize=True) * 100).reindex(order).round(2)


def duration_vs_popularity(df):
    return df.groupby("popularity_bucket", observed=True)["duration_sec"].mean().round(1)


def duration_summary_stats(df):
    return df["duration_sec"].describe().round(1)


# ---------------------------------------------------------------------------
# 6. Market Structure Metrics / KPI roll-up
# ---------------------------------------------------------------------------

def playlist_concentration_ratio(exploded, top_n=5):
    return artist_concentration_index(exploded, top_n)["top_n_share_pct"]


def content_variety_index(df):
    """
    Composite 0-100 index blending artist diversity, album-format variety,
    and explicit/clean balance -- a single "market balance" figure requested
    by the brief.
    """
    unique_ratio = df["artist"].nunique() / len(df)
    album_entropy = -(df["album_type"].value_counts(normalize=True)
                       .apply(lambda p: p * np.log2(p))).sum()
    max_album_entropy = np.log2(df["album_type"].nunique())
    album_component = album_entropy / max_album_entropy if max_album_entropy else 0

    explicit_p = df["is_explicit"].mean()
    explicit_p = min(max(explicit_p, 1e-9), 1 - 1e-9)
    explicit_entropy = -(explicit_p * np.log2(explicit_p) + (1 - explicit_p) * np.log2(1 - explicit_p))

    index = (0.5 * unique_ratio + 0.3 * album_component + 0.2 * explicit_entropy) * 100
    return round(index, 2)


def kpi_summary(df, exploded):
    conc = artist_concentration_index(exploded, top_n=5)
    dom_intl = domestic_vs_international(exploded)
    return {
        "Artist Concentration Index (Top-5 share, %)": conc["top_n_share_pct"],
        "Artist Concentration (HHI)": conc["hhi"],
        "Unique Artist Count": conc["total_unique_artists"],
        "Diversity Score (unique artists / entries)": diversity_score(df, exploded),
        "Collaboration Ratio (%)": round(collaboration_ratio(df) * 100, 2),
        "Avg Collaborators per Song": avg_collaborators_per_song(df),
        "Explicit Content Share (%)": explicit_share(df)["Explicit"],
        "Single Share (%)": album_type_share(df).get("single", 0),
        "Album Share (%)": album_type_share(df).get("album", 0),
        "Content Variety Index (0-100)": content_variety_index(df),
        "UK/Domestic Artist Share (%)": dom_intl.get("UK / Domestic", 0),
        "International Artist Share (%)": dom_intl.get("International", 0),
        "Avg Track Duration (mm:ss)": f"{int(df['duration_sec'].mean()//60)}:{int(df['duration_sec'].mean()%60):02d}",
        "Total Playlist Entries": len(df),
        "Date Range": f"{df['date'].min().date()} to {df['date'].max().date()}",
        "Unique Songs": df["song"].nunique(),
    }


# ---------------------------------------------------------------------------
# 7. Dashboard-specific extras: concentration curve, correlations, heatmaps
# ---------------------------------------------------------------------------

def concentration_curve(exploded):
    """
    Lorenz-style cumulative concentration curve: for each cumulative % of
    artists (ranked most- to least-dominant), what cumulative % of total
    chart appearances do they hold. A curve close to the diagonal means an
    even/fragmented market; a curve that bows sharply toward the top-left
    means a concentrated market dominated by a few artists.
    """
    counts = artist_appearances(exploded).sort_values(ascending=False)
    cum_share = counts.cumsum() / counts.sum() * 100
    artist_rank_pct = np.arange(1, len(counts) + 1) / len(counts) * 100
    return pd.DataFrame({
        "artist_rank_pct": artist_rank_pct,
        "cumulative_share_pct": cum_share.values,
        "artist_name": counts.index,
        "appearances": counts.values,
    })


def numeric_correlation_matrix(df):
    """Correlation matrix of key numeric/boolean fields, for a market-health
    correlation heatmap (e.g. does explicit content correlate with rank?)."""
    cols = {
        "position": df["position"],
        "popularity": df["popularity"],
        "duration_sec": df["duration_sec"],
        "total_tracks": df["total_tracks"],
        "is_explicit": df["is_explicit"].astype(int),
        "is_collaboration": df["is_collaboration"].astype(int),
        "n_collaborators": df["n_collaborators"],
    }
    corr_df = pd.DataFrame(cols).corr()
    return corr_df


def explicit_heatmap_by_rank_and_time(df, freq="QE"):
    """Explicit-content share (%) by rank group x time period, for a heatmap
    showing whether explicit-content patterns by chart tier have shifted."""
    order = ["Top 5", "Top 10", "Top 20", "21-50"]
    tmp = df.copy()
    tmp["period"] = tmp["date"].dt.to_period(freq[0]).dt.to_timestamp()
    tab = (tmp.groupby(["rank_group", "period"])["is_explicit"]
           .mean().unstack(0) * 100)
    # Under a narrow filter (e.g. a single rare artist), not every rank tier
    # may be present in the filtered data -- reindex rather than direct
    # column selection so this never raises a KeyError.
    return tab.reindex(columns=order).T


def album_size_vs_popularity(df):
    """Average popularity score by album-size bucket, to check whether
    bigger (deluxe) releases under- or over-perform on a per-track basis."""
    bins = [0, 1, 5, 12, 20, np.inf]
    labels = ["Single (1)", "EP (2-5)", "Album (6-12)", "Deluxe (13-20)", "Extended (20+)"]
    d = df.copy()
    d["album_size_bucket"] = pd.cut(d["total_tracks"], bins=bins, labels=labels)
    return d.groupby("album_size_bucket", observed=True)["popularity"].mean().reindex(labels)


def monthly_new_artists(exploded):
    """Count of artists appearing for the FIRST time in the dataset, by
    month -- a proxy for how much fresh artist turnover the chart sees."""
    first_seen = exploded.groupby("artist_name")["date"].min()
    tmp = first_seen.dt.to_period("M").dt.to_timestamp()
    return tmp.value_counts().sort_index()


if __name__ == "__main__":
    df = pd.read_parquet("data/clean_playlist.parquet")
    exploded = pd.read_parquet("data/exploded_artists.parquet")

    print("=== KPI SUMMARY ===")
    for k, v in kpi_summary(df, exploded).items():
        print(f"{k}: {v}")

    print("\n=== TOP 15 DOMINATING ARTISTS ===")
    print(top_dominating_artists(exploded, 15))

    print("\n=== SOLO VS COLLAB ===")
    print(solo_vs_collab(df))

    print("\n=== COLLAB BY RANK GROUP (%) ===")
    print(collab_by_rank_group(df))

    print("\n=== EXPLICIT SHARE ===")
    print(explicit_share(df))

    print("\n=== EXPLICIT BY RANK (%) ===")
    print(explicit_by_rank(df))

    print("\n=== ALBUM TYPE SHARE (%) ===")
    print(album_type_share(df))

    print("\n=== RELEASE FORMAT BY RANK (%) ===")
    print(release_format_by_rank(df))

    print("\n=== DURATION DISTRIBUTION (%) ===")
    print(duration_distribution(df))

    print("\n=== DURATION VS POPULARITY BUCKET (avg sec) ===")
    print(duration_vs_popularity(df))

    print("\n=== DOMESTIC (UK) VS INTERNATIONAL (%) ===")
    print(domestic_vs_international(exploded))

    print("\n=== DOMESTIC VS INTERNATIONAL BY RANK GROUP (%) ===")
    print(domestic_vs_international_by_rank(df, exploded))
