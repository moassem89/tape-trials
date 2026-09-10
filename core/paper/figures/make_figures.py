"""Figures for the tape-trials paper.

Every value below is copied from paper/evidence.md, which is itself sourced from the
recorded s6 job outputs. Nothing here computes a result; this script only draws.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 300,
})

# --- Figure 1: accuracy by executed-step quintile (E40-E48) -------------------
QUINTILE_MEDIAN_STEPS = [86, 203, 524, 1296, 6573]
KNEE = [
    # label, per-quintile exact_match, line style, marker
    ("14B-R",   [0.992, 0.992, 0.941, 0.949, 0.914], "-",  "o"),
    ("7B-R",    [0.872, 0.812, 0.822, 0.778, 0.778], "-",  "s"),
    ("14B-CoT", [0.983, 0.940, 0.703, 0.718, 0.615], "-",  "^"),
    ("14B",     [0.530, 0.308, 0.102, 0.051, 0.086], "--", "v"),
    ("7B",      [0.359, 0.137, 0.034, 0.086, 0.077], "--", "D"),
    ("3B",      [0.342, 0.111, 0.017, 0.017, 0.000], "--", "P"),
    ("1.5B",    [0.137, 0.034, 0.000, 0.000, 0.000], ":",  "X"),
    ("0.5B",    [0.009, 0.000, 0.000, 0.000, 0.000], ":",  "*"),
]

fig, ax = plt.subplots(figsize=(6.2, 3.3))
greys = ["#000000", "#303030", "#565656", "#6e6e6e", "#868686", "#9c9c9c",
         "#b0b0b0", "#c4c4c4"]
for (label, ys, ls, mk), c in zip(KNEE, greys):
    ax.plot(QUINTILE_MEDIAN_STEPS, [100 * y for y in ys], ls, marker=mk,
            color=c, markersize=4, linewidth=1.3, label=label)
ax.set_xscale("log")
ax.set_xticks(QUINTILE_MEDIAN_STEPS)
ax.set_xticklabels([str(v) for v in QUINTILE_MEDIAN_STEPS])
ax.minorticks_off()
ax.set_xlabel("Executed steps (quintile median, log scale)")
ax.set_ylabel("Exact-match accuracy (%)")
ax.set_ylim(-3, 103)
ax.legend(frameon=False, fontsize=8, loc="upper left",
          bbox_to_anchor=(1.01, 1.02), handlelength=2.8, labelspacing=0.55)
fig.tight_layout()
fig.savefig("knee.png", bbox_inches="tight")
plt.close(fig)

# --- Figure 2: reply-length slope, tokens per decade (E85, E86) ---------------
SLOPES = [
    ("14B-R",   357.5, True),
    ("14B-CoT", 289.0, True),
    ("7B-R",    275.2, True),
    ("1.5B",      6.2, False),
    ("14B",       1.0, False),
    ("7B",        0.9, False),
    ("3B",        0.8, False),
    ("0.5B",    -34.0, False),
]

fig, ax = plt.subplots(figsize=(5.4, 3.0))
labels = [s[0] for s in SLOPES][::-1]
values = [s[1] for s in SLOPES][::-1]
traces = [s[2] for s in SLOPES][::-1]
colors = ["#333333" if t else "#b4b4b4" for t in traces]
bars = ax.barh(range(len(labels)), values, color=colors, height=0.62)
ax.axvline(0, color="black", linewidth=0.7)
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels)
ax.set_xlabel("Reply length slope (output tokens per decade of executed steps)")
ax.set_xlim(-80, 420)
for i, v in enumerate(values):
    off = 6 if v >= 0 else -6
    ax.text(v + off, i, f"{v:+.1f}", va="center",
            ha="left" if v >= 0 else "right", fontsize=7.5)
handles = [plt.Rectangle((0, 0), 1, 1, color="#333333"),
           plt.Rectangle((0, 0), 1, 1, color="#b4b4b4")]
ax.legend(handles, ["writes out a trace", "answers directly"],
          frameon=False, fontsize=7.5, loc="lower right")
fig.tight_layout()
fig.savefig("tokens.png", bbox_inches="tight")
plt.close(fig)
print("wrote knee.png and tokens.png")
