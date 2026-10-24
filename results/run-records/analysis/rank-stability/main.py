"""s6.5 — does the ladder hold its order when the specification is reworded?

Hypothesis H5 says it does not: at least one adjacent pair of models reverses
across semantics-preserving paraphrases of the specification. The paraphrase
battery (C2) generates the evidence one model at a time, five wordings behind a
single weight load. Nothing in those per-model jobs can answer H5, because the
question is about the *ordering*, and an ordering only exists once every rung has
been run. That is what this job is for.

Two things make the naive version of this analysis wrong, and both are handled
here rather than mentioned in the report afterwards.

**A reversal has to survive resampling.** Two rungs half a point apart will swap
places under almost any perturbation, wording included, and calling that a
reversal would confirm H5 on noise alone. Every draw of the bootstrap resamples
whole programs once and recomputes the entire rung-by-wording matrix on that one
resample, so the accuracies being compared move together the way they actually
do. A pair counts as reversed only if the sign of the gap flips and the flipped
gap holds in at least 95% of draws.

**A reversal has to beat the serving noise.** Condition C5 measures how much the
same request moves when nothing about it changes: same wording, same weights,
same temperature, different batch. Any wording effect smaller than that is not a
wording effect. C5's disagreement rate is read in here and reported beside the
paraphrase spread, and every spread is labelled with whether it clears it.

No generation happens here and no GPU is held. The inputs are the per-item files
the C2 jobs wrote and the result files the C5 jobs wrote, both parked in shared
storage.
"""

from __future__ import annotations

import json
import math
import random
import sys
import traceback
from collections import defaultdict
from pathlib import Path

from lab import lab

HERE = Path(__file__).parent
STORE = "tape-trials"

# (rung label, artifact slug), strongest first. The slug is how the inference
# jobs named their files: dots are not legal there, so 1.5B became 1_5B.
RUNGS = [
    ("14B-R", "14B-R"),
    ("7B-R", "7B-R"),
    ("14B", "14B"),
    ("7B", "7B"),
    ("3B", "3B"),
    ("1.5B", "1_5B"),
    ("0.5B", "0_5B"),
]

# The frozen wording first: it is the reference every other wording is compared
# against, and the one the study's headline numbers were produced under.
WORDINGS = [
    "P1_frozen",
    "P2_reference_card",
    "P3_tutorial",
    "P4_formal_rules",
    "P5_inverted",
]

BLOCK = "public"


def save(obj, name):
    path = HERE / name
    path.write_text(json.dumps(obj, indent=2, default=str))
    lab.save_artifact(str(path), name)
    print(f"[artifact] {name} ({path.stat().st_size} bytes)", flush=True)


def read_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def fetch(relpath):
    """Locate one input, preferring the copy the bundle carries.

    The first build of this job called `lab.storage_download` and opened what it
    returned. On the compute node that came back as an object-store URI rather
    than a local file and the job died on its first read, eleven minutes in. The
    whole input set is 23 MB, which is nothing next to a task bundle, so the
    assembly script now fetches it once from the sandbox and ships it. Shared
    storage stays the fallback for anything the bundle happens to be missing,
    and the returned path is checked before it is opened rather than assumed.
    """
    local = HERE / "inputs" / relpath
    if local.exists():
        return local
    path = Path(lab.storage_download(f"{STORE}/{relpath}"))
    if not path.exists():
        raise RuntimeError(
            f"{relpath}: not in the bundle, and shared storage returned "
            f"{str(path)!r}, which is not a readable local path. Re-run the "
            f"assembly script so the bundle carries the inputs.")
    return path


# ------------------------------------------------------------------ ranking

def spearman(a, b):
    """Rank correlation with midranks for ties.

    Ties matter here more than they usually do. Two rungs that both score 0.0000
    are genuinely tied, and the competition-ranking version of Spearman would
    invent an order between them and then score that invented order as agreement
    or disagreement depending on which way it fell.
    """
    if len(a) != len(b) or len(a) < 2:
        return None

    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        out = [0.0] * len(xs)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and xs[order[j + 1]] == xs[order[i]]:
                j += 1
            mid = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                out[order[k]] = mid
            i = j + 1
        return out

    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    da = math.sqrt(sum((x - ma) ** 2 for x in ra))
    db = math.sqrt(sum((y - mb) ** 2 for y in rb))
    if da == 0 or db == 0:
        return None
    return round(num / (da * db), 6)


def kendall_tau_b(a, b):
    """Concordance over pairs, which is what H5 is actually about.

    Spearman answers "did the ordering shift"; tau answers "how many pairs
    changed places", and a single adjacent swap in a seven-rung ladder moves tau
    by a predictable amount while moving Spearman by an amount that depends on
    where in the ladder the swap happened. Both are reported.
    """
    n = len(a)
    if n != len(b) or n < 2:
        return None
    con = dis = ta = tb = 0
    for i in range(n):
        for j in range(i + 1, n):
            da, db = a[i] - a[j], b[i] - b[j]
            if da == 0 and db == 0:
                ta += 1
                tb += 1
            elif da == 0:
                ta += 1
            elif db == 0:
                tb += 1
            elif (da > 0) == (db > 0):
                con += 1
            else:
                dis += 1
    denom = math.sqrt((con + dis + ta) * (con + dis + tb))
    if denom == 0:
        return None
    return round((con - dis) / denom, 6)


# ---------------------------------------------------------------- resampling

def accuracy(rows):
    return sum(r["exact_match"] for r in rows) / max(1, len(rows))


def matrix_draws(cells, draws, seed):
    """Resample whole programs once per draw and rebuild the whole matrix on it.

    `cells` maps (rung, wording) to a program-keyed dict of rows. Every cell is
    the same 238 rows over the same 61 programs, so one program list drives every
    cell and the resampled accuracies stay coupled. Resampling each cell on its
    own seed would break exactly the correlation that makes a reversal test
    meaningful: two rungs would look independent when in fact they succeed and
    fail on the same programs.
    """
    programs = sorted({p for by_prog in cells.values() for p in by_prog})
    rng = random.Random(seed)
    out = []
    for _ in range(draws):
        picks = [programs[rng.randrange(len(programs))] for _ in programs]
        draw = {}
        for key, by_prog in cells.items():
            rows = []
            for p in picks:
                rows += by_prog.get(p, ())
            draw[key] = accuracy(rows)
        out.append(draw)
    return out, programs


def ci(values):
    vs = sorted(values)
    n = len(vs)
    return [round(vs[int(0.025 * n)], 4), round(vs[int(0.975 * n) - 1], 4)]


# ------------------------------------------------------------------ analysis

def reversal_tests(point, draws, rungs, wordings):
    """For every adjacent pair under the frozen wording, does any wording flip it?

    Adjacency is fixed by the frozen ordering and never recomputed per wording:
    the claim H5 makes is about *this* ladder, the one the headline reports, and
    letting the pair list move with the wording would make it untestable.
    """
    ref = wordings[0]
    order = sorted(rungs, key=lambda r: point[(r, ref)], reverse=True)
    results = []
    for i in range(len(order) - 1):
        hi, lo = order[i], order[i + 1]
        base_gap = point[(hi, ref)] - point[(lo, ref)]
        for w in wordings[1:]:
            gap = point[(hi, w)] - point[(lo, w)]
            flipped = gap < 0
            share = sum(1 for d in draws
                        if (d[(hi, w)] - d[(lo, w)]) < 0) / len(draws)
            results.append({
                "higher_under_frozen": hi,
                "lower_under_frozen": lo,
                "wording": w,
                "frozen_gap": round(base_gap, 4),
                "gap_under_wording": round(gap, 4),
                "reversed": bool(flipped),
                "share_of_draws_reversed": round(share, 4),
                # A reversal the resampling does not sustain is a coin flip
                # dressed as a finding, and H5 is refuted by the absence of
                # sustained ones, not by the absence of any at all.
                "sustained": bool(flipped and share >= 0.95),
            })
    return order, results


def spread_table(point, draws, rungs, wordings, c5_floor):
    """Per rung: how far apart the best and worst wording are, and does it matter."""
    out = []
    for r in rungs:
        vals = [point[(r, w)] for w in wordings]
        best = max(range(len(vals)), key=lambda i: vals[i])
        worst = min(range(len(vals)), key=lambda i: vals[i])
        spread_draws = [max(d[(r, w)] for w in wordings)
                        - min(d[(r, w)] for w in wordings) for d in draws]
        spread = vals[best] - vals[worst]
        row = {
            "rung": r,
            "by_wording": {w: round(point[(r, w)], 4) for w in wordings},
            "best_wording": wordings[best],
            "worst_wording": wordings[worst],
            "spread": round(spread, 4),
            "spread_ci95": ci(spread_draws),
            "frozen_minus_worst": round(point[(r, wordings[0])] - vals[worst], 4),
        }
        if c5_floor is not None:
            row["serving_noise_floor"] = round(c5_floor, 4)
            row["clears_serving_noise"] = bool(spread > c5_floor)
        out.append(row)
    return out


def wording_effects(point, draws, rungs, wordings):
    """Is any wording systematically easier, averaged over the ladder?

    Averaging accuracy across rungs would let the two rungs near the ceiling and
    the two near the floor dominate, since neither can move. The mean of each
    rung's deviation from its own frozen score is what is averaged instead, so a
    wording that costs every rung two points reads as two points.
    """
    out = []
    ref = wordings[0]
    for w in wordings:
        deltas = [point[(r, w)] - point[(r, ref)] for r in rungs]
        mean = sum(deltas) / len(deltas)
        draw_means = [sum(d[(r, w)] - d[(r, ref)] for r in rungs) / len(rungs)
                      for d in draws]
        lo, hi = ci(draw_means)
        out.append({
            "wording": w,
            "mean_delta_vs_frozen": round(mean, 4),
            "ci95": [lo, hi],
            "significant": bool(lo > 0 or hi < 0),
            "rungs_helped": sum(1 for d in deltas if d > 0),
            "rungs_hurt": sum(1 for d in deltas if d < 0),
        })
    return out


# ------------------------------------------------------------------ C5 floor

def read_c5(slugs):
    """The serving-noise floor, taken from whichever C5 cells actually ran.

    The floor used is the largest disagreement rate observed, not the mean: it is
    being used to discount wording effects, and discounting against the gentlest
    available estimate of noise would let a marginal effect through.
    """
    cells, missing = [], []
    for label, slug in slugs:
        try:
            data = json.loads(fetch(f"c5/result_{slug}.json").read_text())
        except Exception as exc:
            missing.append({"rung": label, "reason": str(exc)[:200]})
            continue
        head = data.get("headline_block") or ""
        stab = (data.get("stability") or {}).get(BLOCK) \
            or (data.get("by_block") or {}).get(head, {}).get("stability") \
            or {}
        answer = stab.get("answer_agreement_rate")
        text = stab.get("text_agreement_rate")
        if answer is None:
            answer = data.get("answer_agreement_rate")
            text = data.get("text_agreement_rate")
        if answer is None:
            missing.append({"rung": label, "reason": "no agreement rate in result file"})
            continue
        cells.append({
            "rung": label,
            "answer_agreement_rate": answer,
            "text_agreement_rate": text,
            "answer_disagreement_rate": round(1.0 - answer, 4),
        })
    floor = max((c["answer_disagreement_rate"] for c in cells), default=None)
    return cells, floor, missing


# ---------------------------------------------------------------------- main

def main():
    lab.init()
    cfg = lab.get_config()
    draws_n = int(cfg.get("draws", 2000))
    seed = int(cfg.get("seed", 20260821))
    want = [w.strip() for w in str(cfg.get("wordings", ",".join(WORDINGS))).split(",")
            if w.strip()]
    if len(set(want)) != len(want):
        raise RuntimeError(f"wordings={want!r} repeats a template; a wording "
                           f"compared against itself is not a paraphrase test.")

    lab.log(f"rank stability over {len(RUNGS)} rungs x {len(want)} wordings, "
            f"{draws_n} coupled bootstrap draws, seed {seed}")

    # ---------------------------------------------------------------- inputs
    cells, point, missing = {}, {}, []
    for label, slug in RUNGS:
        for w in want:
            name = f"c2/per_item_{slug}_{BLOCK}__{w}.jsonl"
            try:
                rows = read_jsonl(fetch(name))
            except Exception as exc:
                missing.append({"rung": label, "wording": w, "reason": str(exc)[:200]})
                continue
            by_prog = defaultdict(list)
            for r in rows:
                by_prog[r["program_id"]].append(r)
            cells[(label, w)] = dict(by_prog)
            point[(label, w)] = accuracy(rows)

    # A ladder with a hole in it cannot be ranked. Rather than rank what is there
    # and quietly drop the rest, the incomplete rungs are named and excluded, and
    # the count of them is part of the result.
    complete = [label for label, _ in RUNGS
                if all((label, w) in cells for w in want)]
    dropped = [label for label, _ in RUNGS if label not in complete]
    if len(complete) < 3:
        raise RuntimeError(
            f"only {len(complete)} rungs have all {len(want)} wordings "
            f"({complete}); H5 is a claim about an ordering and needs at least "
            f"three rungs to have one. Missing: {missing[:8]}")
    if dropped:
        lab.log(f"excluded from the ranking, incomplete: {dropped}")

    used = {k: v for k, v in cells.items() if k[0] in complete}
    row_counts = {f"{r}/{w}": sum(len(v) for v in used[(r, w)].values())
                  for r in complete for w in want}
    n_rows = set(row_counts.values())
    if len(n_rows) > 1:
        # Every wording is meant to be the same subsample. If they are not, the
        # comparison is between different row sets and the whole battery is void.
        raise RuntimeError(f"cells disagree on row count: {row_counts}")

    lab.log(f"{len(complete)} complete rungs, {sorted(n_rows)[0]} rows each")
    lab.update_progress(20)

    draws, programs = matrix_draws(used, draws_n, seed)
    lab.log(f"{len(programs)} programs resampled per draw")
    lab.update_progress(60)

    # ---------------------------------------------------------------- ranking
    per_wording_order = {}
    for w in want:
        per_wording_order[w] = sorted(
            complete, key=lambda r: point[(r, w)], reverse=True)

    ref = want[0]
    ref_vals = [point[(r, ref)] for r in complete]
    correlations = []
    for w in want[1:]:
        vals = [point[(r, w)] for r in complete]
        rho_draws = [spearman([d[(r, ref)] for r in complete],
                              [d[(r, w)] for r in complete]) for d in draws[:500]]
        rho_draws = [x for x in rho_draws if x is not None]
        correlations.append({
            "wording": w,
            "spearman_vs_frozen": spearman(ref_vals, vals),
            "spearman_ci95": ci(rho_draws) if len(rho_draws) > 20 else None,
            "kendall_tau_b_vs_frozen": kendall_tau_b(ref_vals, vals),
            "order": per_wording_order[w],
        })

    pairwise = {}
    for i, a in enumerate(want):
        for b in want[i + 1:]:
            pairwise[f"{a}|{b}"] = spearman(
                [point[(r, a)] for r in complete],
                [point[(r, b)] for r in complete])

    c5_cells, c5_floor, c5_missing = read_c5(
        [(l, s) for l, s in RUNGS if l in complete])
    if c5_floor is None:
        lab.log("no C5 result readable; spreads reported without a noise floor")
    else:
        lab.log(f"serving-noise floor {c5_floor:.4f} from "
                f"{len(c5_cells)} C5 cell(s)")
    lab.update_progress(80)

    order, reversals = reversal_tests(point, draws, complete, want)
    spreads = spread_table(point, draws, complete, want, c5_floor)
    effects = wording_effects(point, draws, complete, want)

    sustained = [r for r in reversals if r["sustained"]]
    any_reversal = [r for r in reversals if r["reversed"]]
    min_rho = min((c["spearman_vs_frozen"] for c in correlations
                   if c["spearman_vs_frozen"] is not None), default=None)

    # H5 predicts at least one sustained adjacent reversal. Anything short of
    # that is recorded as a refutation with the evidence behind it, not softened
    # into "no clear evidence either way".
    if sustained:
        verdict = "supported"
    elif any_reversal:
        verdict = "not supported (reversals seen, none survived resampling)"
    elif min_rho is not None and min_rho >= 0.999:
        verdict = "refuted (ordering identical under every wording)"
    else:
        verdict = "not supported"

    result = {
        "hypothesis": "H5",
        "verdict": verdict,
        "block": BLOCK,
        "wordings": want,
        "rungs_ranked": complete,
        "rungs_excluded": dropped,
        "rows_per_cell": sorted(n_rows)[0],
        "programs_per_cell": len(programs),
        "bootstrap": {"draws": draws_n, "seed": seed, "unit": "program",
                      "coupled": True},
        "frozen_order": order,
        "accuracy_matrix": {r: {w: round(point[(r, w)], 4) for w in want}
                            for r in complete},
        "rank_correlation_vs_frozen": correlations,
        "pairwise_spearman": pairwise,
        "adjacent_pair_tests": reversals,
        "spread_by_rung": spreads,
        "wording_effects": effects,
        "serving_noise": {"floor_from_c5": c5_floor, "cells": c5_cells,
                          "unreadable": c5_missing},
        "missing_cells": missing,
    }
    save(result, "rank_stability.json")
    lab.update_progress(100)

    worst = max(spreads, key=lambda s: s["spread"]) if spreads else None
    score = {
        "verdict": verdict,
        "rungs_ranked": len(complete),
        "wordings": len(want),
        "min_spearman_vs_frozen": min_rho,
        "adjacent_reversals": len(any_reversal),
        "sustained_reversals": len(sustained),
        "largest_spread": worst["spread"] if worst else None,
        "largest_spread_rung": worst["rung"] if worst else None,
        "serving_noise_floor": c5_floor,
        "cells_clearing_noise_floor": sum(
            1 for s in spreads if s.get("clears_serving_noise")),
    }
    lab.finish(
        message=(f"H5 {verdict}: {len(complete)} rungs x {len(want)} wordings, "
                 f"min Spearman {min_rho}, {len(any_reversal)} adjacent "
                 f"reversal(s) of which {len(sustained)} survived resampling; "
                 f"largest spread {score['largest_spread']} at "
                 f"{score['largest_spread_rung']}."),
        score=score)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        traceback.print_exc()
        lab.error(f"{type(exc).__name__}: {exc}")
        raise
