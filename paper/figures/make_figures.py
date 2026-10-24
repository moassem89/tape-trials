"""Figures for the revised paper. Every value is recomputed from per-item holdout
records (export: storage/tape-trials/per_item_<config>_private.jsonl); nothing is
copied from the agent's evidence ledger. Run: python3 make_figures.py <export_dir>
"""
import json, math, random, statistics, sys, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

EXP = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/export"
D = "/home/claude/reparse/fixed/"  # per-item records re-scored with the corrected parser
CFG = [("14B-R", "14B-R"), ("7B-R", "7B-R"), ("14B-CoT", "14B-CoT"), ("14B", "14B"),
       ("7B", "7B"), ("3B", "3B"), ("1.5B", "1_5B"), ("0.5B", "0_5B")]
BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
GREYS = {"14B": "#3a3a38", "7B": "#5e5d59", "3B": "#7f7e79", "1.5B": "#a09f99", "0.5B": "#bdbcb6"}
COLOR = {"14B-R": BLUE, "7B-R": BLUE, "14B-CoT": ORANGE, **GREYS}

plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.dpi": 300})

rows = {lab: [json.loads(l) for l in open(D + f"{slug}_private.jsonl")] for lab, slug in CFG}
edges = statistics.quantiles([r["exec_steps"] for r in rows["14B"]], n=5)
qi = lambda s: sum(s > e for e in edges)
med = [statistics.median([r["exec_steps"] for r in rows["14B"] if qi(r["exec_steps"]) == i]) for i in range(5)]

# ---- Figure 1: accuracy by executed-step quintile --------------------------------
fig, ax = plt.subplots(figsize=(6.0, 3.3))
ax.grid(axis="y", color=GRID, linewidth=0.6); ax.set_axisbelow(True)
for lab, _ in CFG:
    ys = []
    for i in range(5):
        s = [r["exact_match"] for r in rows[lab] if qi(r["exec_steps"]) == i]
        ys.append(100 * sum(s) / len(s))
    ls = "--" if lab == "7B-R" else "-"
    plain = lab in GREYS
    ax.plot(med, ys, ls, marker="o", markersize=4, linewidth=1.6, color=COLOR[lab],
            markeredgecolor="white", markeredgewidth=0.8, label=(lab if plain else None))
    print(lab, [round(y, 1) for y in ys])
    if not plain:
        ax.annotate(lab, (med[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=7.5, color=INK)
ax.legend(title="plain, frozen prompt", title_fontsize=7.5, fontsize=7.5, frameon=False,
          loc="center right", bbox_to_anchor=(1.0, 0.36))
ax.set_xscale("log"); ax.set_xticks(med); ax.set_xticklabels([f"{int(m):,}" for m in med]); ax.minorticks_off()
ax.set_xlim(med[0] / 1.25, med[-1] * 2.2)
ax.set_xlabel("Executed steps (quintile median, log scale)"); ax.set_ylabel("Exact-match accuracy (%)")
ax.set_ylim(-3, 103)
fig.tight_layout(); fig.savefig("knee.png", bbox_inches="tight"); plt.close(fig)

# ---- Figure 2: reply-length slope (words per decade), per-row OLS ----------------
def ols(pts):
    n = len(pts); mx = sum(x for x, _ in pts) / n; my = sum(y for _, y in pts) / n
    return sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)

order = ["14B-R", "14B-CoT", "7B-R", "1.5B", "14B", "7B", "3B", "0.5B"]
res = []
for lab in order:
    pg = collections.defaultdict(list)
    for r in rows[lab]:
        pg[r["program_id"]].append((math.log10(r["exec_steps"]), r["words"]))
    P = list(pg); allp = [p for v in pg.values() for p in v]
    b = ols(allp); rnd = random.Random(20261024); bs = []
    for _ in range(2000):
        bs.append(ols([p for _ in P for p in pg[rnd.choice(P)]]))
    bs.sort(); res.append((lab, b, bs[50], bs[1949]))
    print(f"{lab:8s} {b:7.1f} [{bs[50]:.1f}, {bs[1949]:.1f}]")

fig, ax = plt.subplots(figsize=(5.4, 3.0))
ax.grid(axis="x", color=GRID, linewidth=0.6); ax.set_axisbelow(True)
y = list(range(len(res)))[::-1]
for yi, (lab, b, lo, hi) in zip(y, res):
    ax.barh(yi, b, height=0.6, color=COLOR[lab])
    ax.errorbar(b, yi, xerr=[[b - lo], [hi - b]], fmt="none", ecolor=INK2, elinewidth=0.8, capsize=2)
    ax.text(max(hi, b, 0) + 8, yi, f"{b:+.1f}", va="center", ha="left", fontsize=7.5, color=INK)
ax.axvline(0, color=INK2, linewidth=0.7)
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in res])
ax.set_xlabel("Reply-length slope (words per decade of executed steps)")
ax.set_xlim(-80, 620)
h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (BLUE, ORANGE, GREYS["7B"])]
ax.legend(h, ["reasoning-distilled", "plain 14B, tracing prompt", "plain, frozen prompt"],
          frameon=False, fontsize=7.5, loc="lower right")
fig.tight_layout(); fig.savefig("tokens.png", bbox_inches="tight"); plt.close(fig)
json.dump(res, open("slopes.json", "w"), indent=1)
