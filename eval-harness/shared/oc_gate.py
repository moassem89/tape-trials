#!/usr/bin/env python3
"""Does the overlap control reproduce the answer already on record?

Row OC repeats cell `cbc1215f` (C8 calibration, 14B-R, 181 rows) with
`VLLM_ENABLE_V1_MULTIPROCESSING=0`. Its whole job is to show that the changed
compute path did not move the numbers, which is the operator's standing
condition on a mid-study serving change (note of 2026-08-22). Six held cells
run under that flag if it clears and none of them run if it does not, so the
call is worth making mechanically rather than by eye at the end of a long wait.

Reads no model and computes no metric: both sides are score files that already
exist. Comparison only, so it belongs on this machine.

The reference is cbc1215f's own `calibration_14B-R.json`, not the figures in
the stage report. The two differ on purpose: the report states the verbalized
arm's accuracy over all 181 rows (0.8011) while the JSON states it over the 179
whose confidence parsed (0.8045). Comparing a candidate JSON against a report
figure would read that 0.34-point definitional gap as drift.

Three verdicts:

  VOID    the two cells did not measure the same thing (different rows,
          programs, k, sampling seeds, block or model). Nothing to compare;
          fix the candidate, do not interpret it.
  HOLD    an accuracy moved by more than the noise floor. The mitigation
          changed the answer, so it is not adopted and the held rows stay held.
  RELEASE the accuracies held. Any softer statistic that moved is printed and
          flagged, and a flagged RELEASE is reported as such rather than
          quietly passed.

Tolerances, and why each is what it is:

  accuracy      0.028   the C5 repeat noise floor measured on this study's own
                        greedy passes. It is an accuracy floor, so it gates
                        accuracy; the coverage of the verbalized arm rides on
                        the same number because it is also a per-row rate.
  brier / ece   0.028   same units as accuracy (squared and absolute error on
                        the probability scale), so the same floor is the
                        honest default. Soft, because they are not what the
                        floor was measured on.
  auroc         0.05    a rank statistic over a confidence distribution with
                        resolution 0.0. It is unstable by construction here and
                        a tighter bound would fire on nothing but its own noise.
  correlation     --    informational. Reference is 0.0146, i.e. no signal;
                        a bound on the size of a null is not meaningful.

The qualitative reading is checked too, because it is what the paper says: the
verbalized arm has to stay near-chance and badly overconfident and the
self-consistency arm has to stay a good signal. A candidate can pass every
numeric bound and still be reported honestly as having broken the finding.

  usage: oc_gate.py --candidate <calibration_*.json> [--reference <json>]
                    [--key 14B-R/public]
  exit:  0 RELEASE (clean or flagged) · 1 HOLD · 2 VOID · 3 bad invocation
"""
import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DEFAULT_REF = HERE / "ref" / "cbc1215f_calibration_14B-R.json"

ACC_FLOOR = 0.028      # C5 repeat noise floor
SCORE_FLOOR = 0.028    # brier / ece / gap, same probability scale
AUROC_FLOOR = 0.05     # rank statistic on a resolution-0 distribution

# Fields that have to match exactly for the comparison to mean anything.
STRUCTURAL = ["rung", "model", "block", "n_rows", "n_programs", "k_samples"]
NESTED_STRUCTURAL = [
    ("sampling", "sc_temperature"), ("sampling", "sc_top_p"), ("sampling", "sc_seed"),
    ("subsample", "frac"), ("subsample", "seed"),
]

# (arm, field, tolerance, hard?)
CHECKS = [
    ("verbalized",       "accuracy",          ACC_FLOOR,   True),
    ("verbalized",       "coverage",          ACC_FLOOR,   True),
    ("self_consistency", "accuracy",          ACC_FLOOR,   True),
    ("verbalized",       "mean_confidence",   SCORE_FLOOR, False),
    ("verbalized",       "overconfidence_gap", SCORE_FLOOR, False),
    ("verbalized",       "brier",             SCORE_FLOOR, False),
    ("verbalized",       "ece",               SCORE_FLOOR, False),
    ("verbalized",       "auroc",             AUROC_FLOOR, False),
    ("self_consistency", "brier",             SCORE_FLOOR, False),
    ("self_consistency", "ece",               SCORE_FLOOR, False),
    ("self_consistency", "auroc",             AUROC_FLOOR, False),
]


def pick(doc, key):
    """The one block a C8 cell scores, by key or as the sole entry."""
    if key:
        if key not in doc:
            raise KeyError(f"key {key!r} not in {sorted(doc)}")
        return key, doc[key]
    if len(doc) != 1:
        raise KeyError(f"expected one block, found {sorted(doc)}; pass --key")
    k = next(iter(doc))
    return k, doc[k]


def structural_diffs(ref, cand):
    out = []
    for f in STRUCTURAL:
        if ref.get(f) != cand.get(f):
            out.append((f, ref.get(f), cand.get(f)))
    for outer, inner in NESTED_STRUCTURAL:
        a = (ref.get(outer) or {}).get(inner)
        b = (cand.get(outer) or {}).get(inner)
        if a != b:
            out.append((f"{outer}.{inner}", a, b))
    return out


def qualitative(cand):
    """Does the C8 finding still read the way the stage report states it?"""
    v, c = cand.get("verbalized", {}), cand.get("self_consistency", {})
    claims = [
        ("stated confidence near-chance",
         v.get("auroc") is not None and v["auroc"] < 0.60),
        ("stated confidence badly overconfident",
         v.get("overconfidence_gap") is not None and v["overconfidence_gap"] > 0.10),
        ("stated confidence beaten by the base rate",
         v.get("brier") is not None and v.get("brier_of_always_base_rate") is not None
         and v["brier"] > v["brier_of_always_base_rate"]),
        ("self-consistency a good signal",
         c.get("auroc") is not None and c["auroc"] > 0.85),
    ]
    return [(name, bool(ok)) for name, ok in claims]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--reference", default=str(DEFAULT_REF))
    ap.add_argument("--key", default=None)
    a = ap.parse_args()

    try:
        ref_doc = json.loads(pathlib.Path(a.reference).read_text())
        cand_doc = json.loads(pathlib.Path(a.candidate).read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"cannot read a side of the comparison: {e}", file=sys.stderr)
        return 3
    try:
        ref_key, ref = pick(ref_doc, a.key)
        cand_key, cand = pick(cand_doc, a.key)
    except KeyError as e:
        print(f"cannot locate the scored block: {e}", file=sys.stderr)
        return 3

    print(f"reference  {a.reference}  [{ref_key}]")
    print(f"candidate  {a.candidate}  [{cand_key}]")
    print()

    sd = structural_diffs(ref, cand)
    if sd:
        print("VOID - the two cells did not measure the same thing:")
        for f, x, y in sd:
            print(f"  {f}: reference {x!r}, candidate {y!r}")
        print("\nDo not read the numbers. Fix the candidate cell and re-run it.")
        return 2
    print(f"same measurement: {ref['n_rows']} rows / {ref['n_programs']} programs, "
          f"k={ref['k_samples']}, block {ref['block']}, {ref['model']}")
    print()

    hard_fail, soft_fail, missing = [], [], []
    rows = []
    for arm, field, tol, hard in CHECKS:
        x = (ref.get(arm) or {}).get(field)
        y = (cand.get(arm) or {}).get(field)
        if x is None or y is None:
            missing.append(f"{arm}.{field}")
            rows.append((f"{arm}.{field}", x, y, None, tol, hard, "MISSING"))
            (hard_fail if hard else soft_fail).append(f"{arm}.{field} missing")
            continue
        d = y - x
        # 1e-9 of slack: these are 4- and 5-decimal figures and a delta that is
        # exactly the bound in decimal can land a hair over it in binary.
        ok = abs(d) <= tol + 1e-9
        if not ok:
            (hard_fail if hard else soft_fail).append(
                f"{arm}.{field} moved {d:+.4f} against a {tol} bound")
        rows.append((f"{arm}.{field}", x, y, d, tol, hard,
                     "ok" if ok else ("FAIL" if hard else "flag")))

    w = max(len(r[0]) for r in rows)
    print(f"{'metric'.ljust(w)}  {'reference':>10}  {'candidate':>10}  "
          f"{'delta':>9}  {'bound':>6}  gate")
    for name, x, y, d, tol, hard, verdict in rows:
        xs = "--" if x is None else f"{x:.5g}"
        ys = "--" if y is None else f"{y:.5g}"
        ds = "--" if d is None else f"{d:+.4f}"
        print(f"{name.ljust(w)}  {xs:>10}  {ys:>10}  {ds:>9}  {tol:>6}  "
              f"{'hard' if hard else 'soft'} {verdict}")

    rc = ref.get("confidence_correlation")
    cc = cand.get("confidence_correlation")
    print(f"\nconfidence_correlation: reference {rc}, candidate {cc} "
          f"(informational, no bound)")

    print("\nthe finding as the stage report states it:")
    broken = []
    for name, ok in qualitative(cand):
        print(f"  [{'x' if ok else ' '}] {name}")
        if not ok:
            broken.append(name)

    print()
    if hard_fail:
        print("HOLD - " + "; ".join(hard_fail))
        print("\nThe mitigation moved the answer, so it is not adopted. The six held\n"
              "rows stay held and s6.3 and s6.5 close with the gaps recorded.")
        return 1
    if soft_fail or broken:
        print("RELEASE (flagged) - the accuracies held, but:")
        for f in soft_fail:
            print(f"  - {f}")
        for b in broken:
            print(f"  - the finding no longer reads as stated: {b}")
        print("\nRelease the held rows and report every flag above in the stage\n"
              "report. A flagged pass is not a clean one.")
        return 0
    print("RELEASE - every accuracy held inside the noise floor and no softer\n"
          "statistic moved past its bound. The changed compute path reproduces\n"
          "the recorded answer; the six held rows may run under the mitigation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
