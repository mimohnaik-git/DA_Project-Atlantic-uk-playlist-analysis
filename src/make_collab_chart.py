"""Generate the top collaborator-pair chart from canonical chart entries.

The horizontal bar chart ranks artist pairs by repeated co-credited chart-entry
appearances. It intentionally avoids implying network topology: the analytical
question is pair frequency, and unique collaborative recording-proxy counts are
reported separately in structured outputs.
"""
import sys
sys.path.insert(0, "src")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import analytics as an
from data_prep import run

ATLANTIC_NAVY = "#0B1F3A"
ATLANTIC_RED = "#E4572E"
ATLANTIC_TEAL = "#2C7873"
ATLANTIC_GREY = "#8A94A6"

df, _, _ = run()
edges = an.collaboration_edges(df)
if edges.empty:
    raise RuntimeError("No collaboration pairs were produced from the canonical chart-entry dataset.")
top_n = 25
top_edges = edges.head(top_n).copy()
top_edges["pair_label"] = top_edges["artist_a"] + "  ×  " + top_edges["artist_b"]
top_edges = top_edges.sort_values("weight")  # ascending for horizontal barh (largest on top)

fig_h = max(8, top_n * 0.42)
fig, ax = plt.subplots(figsize=(9.5, fig_h))

bars = ax.barh(top_edges["pair_label"], top_edges["weight"], color=ATLANTIC_NAVY, height=0.62)

# Highlight the single highest-weight bar for visual anchoring
if len(bars) > 0:
    bars[-1].set_color(ATLANTIC_RED)
for bar, val in zip(bars, top_edges["weight"]):
    ax.text(val + max(top_edges["weight"]) * 0.015, bar.get_y() + bar.get_height() / 2,
            str(val), va="center", ha="left", fontsize=13, color="#333333")

ax.set_xlabel("Co-credited chart-entry appearances", fontsize=15)
ax.set_title(f"Top {top_n} Artist Collaborator Pairs — UK Top 50\n(by repeated chart-entry appearances)",
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
