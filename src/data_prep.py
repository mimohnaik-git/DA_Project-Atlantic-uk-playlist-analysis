"""
Data Validation & Standardization
UK Top 50 Playlist Market Structure Analysis - Atlantic Recording Corporation

- Validates daily Top 50 entries
- Normalizes artist names
- Splits multi-artist collaborations using the '&' delimiter
- Produces a clean, analysis-ready dataframe plus an "exploded" per-artist view
"""
import pandas as pd
import numpy as np
import re

RAW_PATH = "data/Atlantic_United_Kingdom.csv"


def load_raw(path=RAW_PATH):
    df = pd.read_csv(path)
    return df


def validate(df):
    """Basic validation checks -- returns (df, report dict)."""
    report = {}
    report["n_rows_raw"] = len(df)
    report["n_nulls"] = int(df.isna().sum().sum())
    report["duplicate_rows"] = int(df.duplicated().shape[0] - df.drop_duplicates().shape[0])

    # position should be within 1-50 for a "Top 50" playlist; flag out-of-range
    report["positions_out_of_range"] = int(((df["position"] < 1) | (df["position"] > 50)).sum())

    return df, report


def normalize_artist_name(name: str) -> str:
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)
    return name


# Some act *names* legitimately contain the '&' delimiter (duos/bands billed
# with an ampersand). Naively splitting on '&' would incorrectly fracture
# these into two "collaborators". Confirmed in this dataset by checking that
# e.g. "Chase" and "Status" only ever appear together, in lock-step counts --
# i.e. they are one duo, not two independent collaborators.
PROTECTED_ACT_NAMES = [
    "Chase & Status",
    "Richy Mitch & The Coal Miners",
    "Earth, Wind & Fire",
    'Bobby "Boris" Pickett & The Crypt-Kickers',
    "Tyler, The Creator",
]

_PLACEHOLDER_TEMPLATE = "\u0001PROTECTED{i}\u0001"


def split_collaborators(artist_field: str):
    """
    Split a multi-artist string on the '&' delimiter (the dataset's stated
    collaboration delimiter). Also treat ',' as a secondary delimiter since a
    number of real-world entries chain more than two collaborators that way.
    Known act names that legitimately contain '&' (PROTECTED_ACT_NAMES) are
    shielded from splitting.
    """
    if pd.isna(artist_field):
        return []

    text = str(artist_field)
    placeholders = {}
    for i, name in enumerate(PROTECTED_ACT_NAMES):
        if name in text:
            token = _PLACEHOLDER_TEMPLATE.format(i=i)
            placeholders[token] = name
            text = text.replace(name, token)

    parts = []
    for chunk in text.split(","):
        parts.extend(chunk.split("&"))

    restored = []
    for p in parts:
        p = normalize_artist_name(p)
        for token, name in placeholders.items():
            p = p.replace(token, name)
        if p != "":
            restored.append(p)
    return restored


def clean(df):
    df = df.copy()

    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")

    df["song"] = df["song"].astype(str).str.strip()
    df["artist_raw"] = df["artist"].astype(str).str.strip()

    df["is_explicit"] = df["is_explicit"].astype(str).str.upper().map(
        {"TRUE": True, "FALSE": False, "1": True, "0": False}
    ).fillna(df["is_explicit"])
    df["is_explicit"] = df["is_explicit"].astype(bool)

    df["album_type"] = df["album_type"].astype(str).str.strip().str.lower()

    df["collaborators"] = df["artist_raw"].apply(split_collaborators)

    # Canonicalize casing across the whole dataset: same artist can appear
    # with different capitalization (e.g. "Charli xcx" vs "Charli XCX"). Map
    # every lowercase variant to its most frequently used exact-case form.
    from collections import Counter
    variant_counts = {}
    for names in df["collaborators"]:
        for n in names:
            key = n.lower()
            variant_counts.setdefault(key, Counter())[n] += 1
    canonical_map = {key: counter.most_common(1)[0][0] for key, counter in variant_counts.items()}
    df["collaborators"] = df["collaborators"].apply(
        lambda names: [canonical_map[n.lower()] for n in names]
    )
    df["n_collaborators"] = df["collaborators"].apply(len)
    df["is_collaboration"] = df["n_collaborators"] > 1
    df["primary_artist"] = df["collaborators"].apply(lambda x: x[0] if len(x) else np.nan)

    df["duration_sec"] = df["duration_ms"] / 1000
    df["duration_min"] = df["duration_sec"] / 60

    def rank_group(pos):
        if pos <= 5:
            return "Top 5"
        elif pos <= 10:
            return "Top 10"
        elif pos <= 20:
            return "Top 20"
        else:
            return "21-50"
    df["rank_group"] = df["position"].apply(rank_group)

    def dur_bucket(minutes):
        if minutes < 2.5:
            return "Short (<2:30)"
        elif minutes < 3.5:
            return "Standard (2:30-3:30)"
        elif minutes < 4.5:
            return "Long (3:30-4:30)"
        else:
            return "Extended (4:30+)"
    df["duration_bucket"] = df["duration_min"].apply(dur_bucket)

    df["popularity_bucket"] = pd.qcut(df["popularity"], 4,
                                       labels=["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"])

    return df


def explode_artists(df):
    """One row per (entry, collaborator) -- for artist-level dominance metrics."""
    ex = df.explode("collaborators").rename(columns={"collaborators": "artist_name"})
    ex = ex[ex["artist_name"].notna()]
    # df.explode() repeats the ORIGINAL row's index for every collaborator it
    # creates, so the result has a non-unique index (e.g. a 2-collaborator
    # row becomes two rows both carrying the same original index value).
    # pd.crosstab (used downstream in analytics.py) can raise "cannot
    # reindex on an axis with duplicate labels" on a non-unique index in
    # newer pandas versions -- reset to a fresh unique index to avoid it.
    return ex.reset_index(drop=True)


def run(path=RAW_PATH):
    raw = load_raw(path)
    raw, report = validate(raw)
    clean_df = clean(raw)
    exploded = explode_artists(clean_df)
    return clean_df, exploded, report


if __name__ == "__main__":
    clean_df, exploded, report = run()
    print("Validation report:", report)
    print(clean_df.shape, exploded.shape)
    clean_df.to_parquet("data/clean_playlist.parquet", index=False)
    exploded.drop(columns=["collaborators"], errors="ignore").to_parquet(
        "data/exploded_artists.parquet", index=False
    )
    print("Saved cleaned datasets to data/")
