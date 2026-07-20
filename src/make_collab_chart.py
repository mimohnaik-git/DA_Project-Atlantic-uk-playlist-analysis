"""
Figure 3.8 replacement: horizontal bar chart of the top collaborator pairs
by number of tracks co-credited together.

Why this replaces the network diagram: the underlying data is 16 mostly-
disconnected small clusters (mostly simple 2-artist pairs, a few trios, one
6-artist cluster) with no real large-scale network structure to show. A
node-link diagram is the wrong chart for that shape of data -- it fights
overlap and legibility problems for no analytical payoff versus just ranking
the pairs directly. A sorted horizontal bar chart:
  - has zero overlap risk by construction (it's a simple categorical axis)
  - reads correctly at any embed size, small or large
  - directly answers the question the figure exists to answer: which artists
    collaborate most, and how often
"""
import sys
sys.path.insert(0, "src")
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import analytics as an

ATLANTIC_NAVY = "#0B1F3A"
ATLANTIC_RED = "#E4572E"
ATLANTIC_TEAL = "#2C7873"
ATLANTIC_GREY = "#8A94A6"

exploded = pd.read_parquet("data/exploded_artists.parquet")
edges = an.collaboration_edges(exploded)
top_n = 25
top_edges = edges.head(top_n).copy()
top_edges["pair_label"] = top_edges["artist_a"] + "  ×  " + top_edges["artist_b"]
top_edges = top_edges.sort_values("weight")  # ascending for horizontal barh (largest on top)

fig_h = max(8, top_n * 0.42)
fig, ax = plt.subplots(figsize=(9.5, fig_h))

bars = ax.barh(top_edges["pair_label"], top_edges["weight"], color=ATLANTIC_NAVY, height=0.62)

# Highlight the single highest-weight bar for visual anchoring
bars[-1].set_color(ATLANTIC_RED)

for bar, val in zip(bars, top_edges["weight"]):
    ax.text(val + max(top_edges["weight"]) * 0.015, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=13, color="#333333")

ax.set_xlabel("Tracks co-credited together", fontsize=15)
ax.set_title(f"Top {top_n} Artist Collaborator Pairs — UK Top 50\n(by number of tracks co-credited together)",
             fontsize=17, color=ATLANTIC_NAVY, fontweight="bold", pad=16)
ax.tick_params(axis="y", labelsize=13.5)
ax.tick_params(axis="x", labelsize=12.5)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.set_xlim(0, max(top_edges["weight"]) * 1.12)
ax.margins(y=0.01)

fig.tight_layout()
fig.savefig("outputs/figures/05_collab_network.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"saved outputs/figures/05_collab_network.png, figure size (in): {fig.get_size_inches()}")
