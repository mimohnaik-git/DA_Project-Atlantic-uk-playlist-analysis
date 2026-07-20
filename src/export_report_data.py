"""
Exports every metric used in the research paper / executive summary to
outputs/report_data.json, so the docgen/ Node scripts always build reports
from real, reproducible numbers rather than hand-typed figures.

Run from the project root: python3 src/export_report_data.py
"""
import sys
import json
sys.path.insert(0, "src")
import pandas as pd
import analytics as an
from artist_nationality import classify

df = pd.read_parquet("data/clean_playlist.parquet")
exploded = pd.read_parquet("data/exploded_artists.parquet")
exploded["nationality"] = exploded["artist_name"].apply(classify)

out = {}
out["kpi_summary"] = an.kpi_summary(df, exploded)
out["top_20_artists"] = an.top_dominating_artists(exploded, 20).to_dict()
out["concentration_top5"] = an.artist_concentration_index(exploded, 5)
out["concentration_top10"] = an.artist_concentration_index(exploded, 10)
out["solo_vs_collab"] = an.solo_vs_collab(df).to_dict()
out["collab_ratio_pct"] = round(an.collaboration_ratio(df) * 100, 2)
out["avg_collaborators"] = an.avg_collaborators_per_song(df)
out["collab_by_rank"] = an.collab_by_rank_group(df).to_dict()
out["top_collab_pairs"] = an.collaboration_edges(exploded).head(10).to_dict("records")
out["explicit_share"] = an.explicit_share(df).to_dict()
out["explicit_by_rank"] = an.explicit_by_rank(df).to_dict()
out["album_type_share"] = an.album_type_share(df).to_dict()
out["release_format_by_rank"] = an.release_format_by_rank(df).to_dict()
out["duration_distribution"] = an.duration_distribution(df).to_dict()
out["duration_vs_popularity"] = {str(k): v for k, v in an.duration_vs_popularity(df).to_dict().items()}
out["duration_stats"] = an.duration_summary_stats(df).to_dict()
out["domestic_vs_intl"] = an.domestic_vs_international(exploded).to_dict()
out["domestic_vs_intl_by_rank"] = an.domestic_vs_international_by_rank(df, exploded).to_dict()
out["content_variety_index"] = an.content_variety_index(df)
out["n_rows"] = len(df)
out["n_unique_songs"] = int(df["song"].nunique())
out["n_unique_artists"] = int(exploded["artist_name"].nunique())
out["date_min"] = str(df["date"].min().date())
out["date_max"] = str(df["date"].max().date())
out["n_days"] = int(df["date"].nunique())
out["album_size_buckets"] = an.album_size_vs_inclusion(df).to_dict()

with open("outputs/report_data.json", "w") as f:
    json.dump(out, f, indent=2, default=str)

print("Saved outputs/report_data.json")
