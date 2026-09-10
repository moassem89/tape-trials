#!/usr/bin/env python3
"""Recompute the corpus description in section 3 of the paper from the split files.

Runs on the public and development splits alone (1,374 items, 349 programs); with
`--private path/to/private.jsonl` it covers the full 1,960-item corpus and compares
every section-3 figure to the published value.

Also prints the category x tier item table (the corrected form of audit finding F2:
category is *partially aliased* with tier — nine of thirty cells are structurally
empty — not nested, as the first audit session wrongly recorded).
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = dict(programs=500, items=1960, min_steps=22, max_steps=18941,
             split_pct=(60.2, 9.9, 29.9), holdout=(586, 151), public_items=1180,
             median_lines_by_tier=[12, 13, 17, 17, 16])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--private")
    args = ap.parse_args()
    files = [ROOT / "benchmark-corpus/splits/public.jsonl", ROOT / "benchmark-corpus/splits/dev.jsonl"]
    if args.private:
        files.append(Path(args.private))
    rows = [json.loads(l) for f in files for l in open(f)]
    full = args.private is not None

    by_split = Counter(r["split"] for r in rows)
    progs = lambda rs: len({r["program_id"] for r in rs})
    print(f"items: {len(rows)}  programs: {progs(rows)}" + (f"   (paper: {PAPER['items']} / {PAPER['programs']})" if full else "  (public+dev only)"))
    for s in ("public", "dev", "private"):
        rs = [r for r in rows if r["split"] == s]
        if rs:
            print(f"  {s:8} items={len(rs):5} programs={progs(rs):4}" + (f"  {100*len(rs)/len(rows):5.1f}%" if full else ""))
    if full:
        print(f"  paper: 60.2 / 9.9 / 29.9 %; holdout 586 items over 151 programs; public 1,180 items")
    steps = [r["exec_steps"] for r in rows]
    print(f"executed steps: {min(steps)} to {max(steps)}" + (f"   (paper: {PAPER['min_steps']} to {PAPER['max_steps']:,})" if full else ""))
    print("categories:", dict(sorted(Counter(r["category"] for r in rows).items())))
    print("tiers:     ", dict(sorted(Counter(r["difficulty_tier"] for r in rows).items())))

    lines = defaultdict(list)
    for r in rows:
        lines[r["difficulty_tier"]].append(len([l for l in r["program"].splitlines() if l.strip()]))
    med = [statistics.median(lines[t]) for t in sorted(lines)]
    print("median source lines by tier (item-weighted):", med, ("  (paper: 12, 13, 17, 17, 16)" if full else ""))

    # program grouping: no program may straddle splits
    split_of = defaultdict(set)
    for r in rows:
        split_of[r["program_id"]].add(r["split"])
    straddle = [p for p, s in split_of.items() if len(s) > 1]
    print("programs appearing in more than one split:", len(straddle), "(must be 0)")

    print("\ncategory x tier, items:")
    cats = sorted({r["category"] for r in rows}); tiers = sorted({r["difficulty_tier"] for r in rows})
    table = defaultdict(Counter)
    for r in rows:
        table[r["category"]][r["difficulty_tier"]] += 1
    print(f"{'':14}" + "".join(f"{t:>6}" for t in tiers))
    for c in cats:
        print(f"{c:14}" + "".join(f"{table[c][t]:>6}" for t in tiers))
    empty = sum(1 for c in cats for t in tiers if table[c][t] == 0)
    print(f"structurally empty cells: {empty} of {len(cats)*len(tiers)}")


if __name__ == "__main__":
    main()
