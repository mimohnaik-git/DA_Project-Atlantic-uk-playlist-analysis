"""Data preparation for the UK Top 50 playlist market-intelligence case study.

The source has one row per observed chart position.  It does not provide a
native snapshot identifier or recording identifier, so this module reconstructs
both deterministically while preserving all 27,800 source rows.
"""
from __future__ import annotations

from collections import Counter
import re
from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = "data/Atlantic_United_Kingdom.csv"

PROTECTED_ACT_NAMES = [
    "Chase & Status",
    "Richy Mitch & The Coal Miners",
    "Earth, Wind & Fire",
    'Bobby "Boris" Pickett & The Crypt-Kickers',
    "Tyler, The Creator",
]
_PLACEHOLDER_TEMPLATE = "\u0001PROTECTED{i}\u0001"

RANK_ORDER = ["1-5", "6-10", "11-20", "21-50"]
DURATION_ORDER = [
    "Short (<2:30)",
    "Standard (2:30-3:30)",
    "Long (3:30-4:30)",
    "Extended (4:30+)",
]
ALBUM_SIZE_ORDER = ["Single (1)", "EP (2-5)", "Album (6-12)", "Deluxe (13-20)", "Extended (20+)"]


def load_raw(path: str | Path = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def normalize_artist_name(name: str) -> str:
    return re.sub(r"\s+", " ", str(name).strip())


def normalize_song_title(title: str) -> str:
    """Dataset-local title normalization used only for recording proxies."""
    return re.sub(r"\s+", " ", str(title).strip()).casefold()


def split_collaborators(artist_field) -> list[str]:
    """Split the supplied artist credit while protecting known act names.

    The project material uses ``&`` as the primary collaboration delimiter and
    contains a small number of comma-separated multi-credit strings.  Named
    entities that legitimately contain ``&`` or a comma are protected first.
    """
    if pd.isna(artist_field):
        return []

    text = str(artist_field)
    placeholders: dict[str, str] = {}
    for i, name in enumerate(PROTECTED_ACT_NAMES):
        if name in text:
            token = _PLACEHOLDER_TEMPLATE.format(i=i)
            placeholders[token] = name
            text = text.replace(name, token)

    parts: list[str] = []
    for chunk in text.split(","):
        parts.extend(chunk.split("&"))

    restored: list[str] = []
    for part in parts:
        part = normalize_artist_name(part)
        for token, name in placeholders.items():
            part = part.replace(token, name)
        if part:
            restored.append(part)
    return restored


def _canonicalize_artist_casing(series: pd.Series) -> pd.Series:
    variant_counts: dict[str, Counter] = {}
    for names in series:
        for name in names:
            variant_counts.setdefault(name.casefold(), Counter())[name] += 1
    canonical = {
        key: counts.most_common(1)[0][0]
        for key, counts in variant_counts.items()
    }
    return series.apply(lambda names: [canonical[n.casefold()] for n in names])


def _rank_band(position: int) -> str:
    if position <= 5:
        return "1-5"
    if position <= 10:
        return "6-10"
    if position <= 20:
        return "11-20"
    return "21-50"


def _duration_bucket(seconds: float) -> str:
    if seconds < 150:
        return "Short (<2:30)"
    if seconds < 210:
        return "Standard (2:30-3:30)"
    if seconds < 270:
        return "Long (3:30-4:30)"
    return "Extended (4:30+)"


def _album_size_bucket(total_tracks: float) -> str:
    if pd.isna(total_tracks):
        return np.nan
    n = float(total_tracks)
    if n <= 1:
        return "Single (1)"
    if n <= 5:
        return "EP (2-5)"
    if n <= 12:
        return "Album (6-12)"
    if n <= 20:
        return "Deluxe (13-20)"
    return "Extended (20+)"


def _reconstruct_snapshots(df: pd.DataFrame) -> pd.Series:
    """Infer a snapshot index within each date from source-order rank resets."""
    seq = pd.Series(index=df.index, dtype="int64")
    for _, idx in df.groupby("date", sort=False).groups.items():
        positions = df.loc[idx, "position"]
        resets = positions.eq(1).cumsum()
        # Defensive fallback: a malformed date without a rank-1 row still gets
        # deterministic 50-row chunks instead of collapsing all rows together.
        if resets.max() == 0:
            resets = pd.Series(np.arange(len(idx)) // 50 + 1, index=idx)
        seq.loc[idx] = resets.astype(int)
    return seq.astype(int)


def validate(df: pd.DataFrame) -> dict:
    parsed_dates = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    return {
        "n_rows_raw": int(len(df)),
        "required_value_nulls": int(df[[
            "date", "position", "song", "artist", "popularity", "duration_ms",
            "album_type", "total_tracks", "is_explicit"
        ]].isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "positions_out_of_range": int((~df["position"].between(1, 50)).sum()),
        "date_parse_failures": int(parsed_dates.isna().sum()),
    }


def clean(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["source_row_id"] = np.arange(len(out), dtype=int)
    out["date"] = pd.to_datetime(out["date"], format="%d-%m-%Y", errors="raise")
    out["song"] = out["song"].astype(str).str.strip()
    out["song_norm"] = out["song"].map(normalize_song_title)
    out["artist_raw"] = out["artist"].astype(str).str.strip()

    if out["is_explicit"].dtype != bool:
        explicit = out["is_explicit"].astype(str).str.upper().map(
            {"TRUE": True, "FALSE": False, "1": True, "0": False}
        )
        out["is_explicit"] = explicit.fillna(False).astype(bool)
    else:
        out["is_explicit"] = out["is_explicit"].astype(bool)

    out["album_type"] = out["album_type"].astype(str).str.strip().str.lower()
    out["collaborators"] = _canonicalize_artist_casing(out["artist_raw"].apply(split_collaborators))
    out["n_collaborators"] = out["collaborators"].apply(len).astype(int)
    out["is_collaboration"] = out["n_collaborators"].gt(1)
    out["primary_artist"] = out["collaborators"].apply(lambda x: x[0] if x else np.nan)

    out["duration_sec"] = pd.to_numeric(out["duration_ms"], errors="coerce") / 1000.0
    out["duration_min"] = out["duration_sec"] / 60.0
    out["rank_band"] = out["position"].map(_rank_band)
    # Backward-compatible name retained for old scripts, but now uses exclusive bands.
    out["rank_group"] = out["rank_band"]
    out["duration_bucket"] = out["duration_sec"].map(_duration_bucket)
    out["album_size_bucket"] = out["total_tracks"].map(_album_size_bucket)

    # Stable quartile labels. Duplicated popularity values can make qcut edges
    # ambiguous, so rank first to guarantee four bins deterministically.
    ranks = out["popularity"].rank(method="first")
    out["popularity_bucket"] = pd.qcut(
        ranks, 4, labels=["Q1 (Lowest)", "Q2", "Q3", "Q4 (Highest)"]
    )

    out["snapshot_seq"] = _reconstruct_snapshots(out)
    out["snapshot_id"] = (
        out["date"].dt.strftime("%Y-%m-%d") + "__" + out["snapshot_seq"].astype(str)
    )

    # Dataset-local identity only: no ISRC is available in the supplied data.
    out["recording_proxy_id"] = out["song_norm"] + "||" + out["duration_ms"].astype(str)
    return out


def explode_artists(df: pd.DataFrame) -> pd.DataFrame:
    ex = df.explode("collaborators").rename(columns={"collaborators": "artist_name"})
    ex = ex.loc[ex["artist_name"].notna()].reset_index(drop=True).copy()
    ex["artist_credit_weight"] = 1.0
    ex["fractional_entry_weight"] = 1.0 / ex["n_collaborators"].clip(lower=1)
    return ex


def canonical_recordings(df: pd.DataFrame) -> pd.DataFrame:
    """One deterministic row per dataset-local recording proxy.

    The first observed metadata row is kept.  This intentionally avoids using
    the credited-artist set as part of the identity because 25 title-duration
    proxies change credited sets across the observation period.
    """
    if df.empty:
        return df.copy()
    if "recording_proxy_id" not in df.columns:
        work = df.copy()
        work["song_norm"] = work["song"].map(normalize_song_title)
        work["recording_proxy_id"] = work["song_norm"] + "||" + work["duration_ms"].astype(str)
    else:
        work = df
    return (
        work.sort_values(["date", "source_row_id"] if "source_row_id" in work.columns else ["date"])
        .drop_duplicates("recording_proxy_id", keep="first")
        .reset_index(drop=True)
        .copy()
    )


def run(path: str | Path = RAW_PATH):
    raw = load_raw(path)
    base_report = validate(raw)
    clean_df = clean(raw)
    exploded = explode_artists(clean_df)
    report = {
        **base_report,
        "n_rows_processed": int(len(clean_df)),
        "n_dates": int(clean_df["date"].nunique()),
        "n_snapshots": int(clean_df["snapshot_id"].nunique()),
        "n_artist_credits": int(len(exploded)),
        "n_recording_proxies": int(clean_df["recording_proxy_id"].nunique()),
    }
    return clean_df, exploded, report


if __name__ == "__main__":
    clean_df, exploded, report = run()
    print(report)
