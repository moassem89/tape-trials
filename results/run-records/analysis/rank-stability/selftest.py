"""Fixture test for the H5 rank-stability job. No model, no network, no GPU.

Three things are checked, in the order they would break something.

1. The rank statistics against cases whose answers are known by hand, including
   the tie case, which is the one a competition-ranking implementation gets
   silently wrong.
2. The reversal test against a planted ladder: two rungs are given a real,
   consistent swap under one wording and a coin-flip swap under another, and the
   job must sustain the first and reject the second.
3. Every guard: a repeated wording, a row-count mismatch between cells, and a
   ladder too short to have an ordering.
"""

from __future__ import annotations

import json
import random
import sys
import types
from pathlib import Path

HERE = Path(__file__).parent
FIX = Path("/tmp/rankstab_fix")


# ------------------------------------------------------------------ stub lab
class _Lab:
    def __init__(self):
        self.logs, self.score, self.msg = [], None, None

    def init(self):
        pass

    def get_config(self):
        return CONFIG

    def log(self, m):
        self.logs.append(m)
        print(f"[log] {m}", flush=True)

    def update_progress(self, p):
        pass

    def save_artifact(self, path, name):
        pass

    def storage_download(self, rel):
        p = FIX / rel.split("/", 1)[1]
        if not p.exists():
            raise FileNotFoundError(rel)
        return str(p)

    def finish(self, message=None, score=None):
        self.msg, self.score = message, score

    def error(self, m):
        print(f"[error] {m}", flush=True)


CONFIG = {"draws": 400, "seed": 7}
stub = types.ModuleType("lab")
stub.lab = _Lab()
sys.modules["lab"] = stub

sys.path.insert(0, str(HERE))
import main  # noqa: E402

main.HERE = Path("/tmp/rankstab_out")
main.HERE.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------- 1. statistics
assert main.spearman([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0
assert main.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
# One adjacent swap in a four-item ladder: rho = 1 - 6*2/(4*15) = 0.8.
assert abs(main.spearman([4, 3, 2, 1], [4, 3, 1, 2]) - 0.8) < 1e-9
# Ties must be midranked, not broken. Both orderings below are the same
# information, so the correlation has to come out the same either way.
tied = main.spearman([3, 1, 1], [3, 1, 1])
assert tied == 1.0, tied
assert main.spearman([1, 1, 1], [3, 2, 1]) is None  # no variance, no correlation
assert main.kendall_tau_b([4, 3, 2, 1], [4, 3, 2, 1]) == 1.0
assert main.kendall_tau_b([4, 3, 2, 1], [4, 3, 1, 2]) is not None
# Five pairs concordant, one discordant, out of six: tau = (5-1)/6.
assert abs(main.kendall_tau_b([4, 3, 2, 1], [4, 3, 1, 2]) - 4 / 6) < 1e-6
print("rank statistics ok")


# ------------------------------------------------------------- 2. fixture
# Five rungs, five wordings, 12 programs x 3 rows. Accuracy is planted per cell
# by choosing how many programs are fully correct, so the point estimates are
# exactly known and the bootstrap has real clusters to resample.
RUNGS = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")]
WORDS = ["P1_frozen", "P2_reference_card", "P3_tutorial", "P4_formal_rules",
         "P5_inverted"]
NPROG, PERPROG = 12, 3
main.RUNGS = RUNGS
main.WORDINGS = WORDS

#                P1    P2    P3    P4    P5      (programs correct out of 12)
PLANTED = {
    "A": [11, 11, 11, 10, 11],
    # B and C are the planted pair. Under P1 B leads C by 2 programs; under P3
    # C leads B by 6, which is a reversal that must be sustained. The planted
    # gap is deliberately wide: 12 programs is a thin bootstrap, and a 2-program
    # reversal sits at about 0.90 of draws, which the job is right to reject.
    "B": [9, 9, 4, 9, 9],
    "C": [7, 7, 10, 7, 7],
    "D": [3, 3, 3, 3, 4],
    "E": [0, 0, 0, 0, 0],
}


def write_fixture(rung_row_counts=None, skip=()):
    import shutil
    shutil.rmtree(FIX, ignore_errors=True)
    (FIX / "c2").mkdir(parents=True)
    (FIX / "c5").mkdir(parents=True)
    for rung, _ in RUNGS:
        for wi, w in enumerate(WORDS):
            if (rung, w) in skip:
                continue
            n_ok = PLANTED[rung][wi]
            rows = []
            n_prog = (rung_row_counts or {}).get(rung, NPROG)
            for p in range(n_prog):
                for k in range(PERPROG):
                    rows.append({
                        "row_id": f"{rung}-{w}-{p}-{k}",
                        "program_id": f"prog{p:02d}",
                        "tier": f"T{1 + p % 5}",
                        "exact_match": 1 if p < n_ok else 0,
                    })
            path = FIX / "c2" / f"per_item_{rung}_public__{w}.jsonl"
            with open(path, "w") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
    # One C5 result in the shape the temperature runner actually writes:
    # `stability` keyed by block at the top level. The fallback shapes are
    # exercised separately below, because a reader that only handles the shape
    # it was written against is a reader that breaks the first time a runner is
    # revised.
    (FIX / "c5" / "result_A.json").write_text(json.dumps({
        "rung": "A", "headline_block": "public",
        "stability": {"public": {
            "answer_agreement_rate": 0.97, "text_agreement_rate": 0.91,
            "fixed_batch_replay": {"answer_agreement": 0.99}}},
    }))


write_fixture()
res = main.main()
out = json.loads((main.HERE / "rank_stability.json").read_text())
score = stub.lab.score

assert out["rungs_ranked"] == ["A", "B", "C", "D", "E"], out["rungs_ranked"]
assert out["rows_per_cell"] == NPROG * PERPROG
assert out["programs_per_cell"] == NPROG
assert abs(out["accuracy_matrix"]["B"]["P1_frozen"] - 9 / 12) < 1e-9
assert abs(out["accuracy_matrix"]["B"]["P3_tutorial"] - 4 / 12) < 1e-4

# The planted swap must be found, and found as sustained.
pair = [r for r in out["adjacent_pair_tests"]
        if r["higher_under_frozen"] == "B" and r["lower_under_frozen"] == "C"]
assert len(pair) == len(WORDS) - 1, pair
swap = [r for r in pair if r["wording"] == "P3_tutorial"][0]
assert swap["reversed"] and swap["sustained"], swap
assert swap["gap_under_wording"] < 0 < swap["frozen_gap"], swap
# ...and the wordings that did not swap must not be reported as swaps.
for r in pair:
    if r["wording"] != "P3_tutorial":
        assert not r["reversed"], r
assert out["verdict"] == "supported", out["verdict"]

# The noise floor comes from C5 and is applied to every spread.
assert abs(out["serving_noise"]["floor_from_c5"] - 0.03) < 1e-9
bspread = [s for s in out["spread_by_rung"] if s["rung"] == "B"][0]
assert abs(bspread["spread"] - 5 / 12) < 1e-4, bspread
assert bspread["clears_serving_noise"] is True
assert bspread["worst_wording"] == "P3_tutorial"
espread = [s for s in out["spread_by_rung"] if s["rung"] == "E"][0]
assert espread["spread"] == 0.0 and espread["clears_serving_noise"] is False
assert espread["spread_ci95"] == [0.0, 0.0], espread

# P3 hurt exactly one rung and helped one; it must not read as a main effect.
p3 = [e for e in out["wording_effects"] if e["wording"] == "P3_tutorial"][0]
assert p3["rungs_hurt"] == 1 and p3["rungs_helped"] == 1, p3
assert score["sustained_reversals"] >= 1 and score["adjacent_reversals"] >= 1
print(f"reversal test ok: verdict {out['verdict']}, "
      f"{score['sustained_reversals']} sustained of "
      f"{score['adjacent_reversals']} seen, floor {score['serving_noise_floor']}")


# The two fallback shapes: a `by_block` nesting, and agreement rates promoted to
# the top level. Both must yield the same floor as the canonical shape.
for shape in [
    {"headline_block": "public", "by_block": {"public": {"stability": {
        "answer_agreement_rate": 0.97, "text_agreement_rate": 0.91}}}},
    {"answer_agreement_rate": 0.97, "text_agreement_rate": 0.91},
]:
    (FIX / "c5" / "result_A.json").write_text(json.dumps(shape))
    cells, floor, miss = main.read_c5([("A", "A")])
    assert abs(floor - 0.03) < 1e-9, (shape, floor)
    assert not miss, miss
# A C5 file with no agreement rate anywhere is named, not silently skipped.
(FIX / "c5" / "result_A.json").write_text(json.dumps({"rung": "A"}))
cells, floor, miss = main.read_c5([("A", "A")])
assert floor is None and miss and miss[0]["rung"] == "A", (floor, miss)
print("C5 floor parsing ok: canonical shape, 2 fallbacks, 1 refusal")


# --------------------------------------------- a ladder with no real reversal
# Same fixture with the swap removed. The verdict must flip, and must not be
# reported as a reversal that merely failed to reach significance.
PLANTED["B"][2] = 9
PLANTED["C"][2] = 7
write_fixture()
main.main()
flat = json.loads((main.HERE / "rank_stability.json").read_text())
assert flat["verdict"].startswith("refuted"), flat["verdict"]
assert not any(r["reversed"] for r in flat["adjacent_pair_tests"])
assert flat["rank_correlation_vs_frozen"][0]["spearman_vs_frozen"] == 1.0
print(f"no-reversal case ok: {flat['verdict']}")


# ------------------------------------------------------------- 3. the guards
def expect(fn, needle):
    try:
        fn()
    except RuntimeError as exc:
        assert needle in str(exc), f"wrong error: {exc}"
        return str(exc)
    raise AssertionError(f"guard did not fire: {needle}")


CONFIG["wordings"] = "P1_frozen,P1_frozen,P3_tutorial"
expect(main.main, "repeats a template")
CONFIG.pop("wordings")

# A cell with a different row count means the wordings did not see the same
# subsample, and every comparison in the job would be between different rows.
write_fixture(rung_row_counts={"D": 11})
expect(main.main, "disagree on row count")

# Too few complete rungs to have an ordering at all.
write_fixture(skip={(r, "P5_inverted") for r in ["B", "C", "D"]})
msg = expect(main.main, "needs at least")
assert "H5 is a claim about an ordering" in msg
print("guards ok: duplicate wording, row-count mismatch, short ladder")

print(f"selftest ok: {len(RUNGS)} rungs x {len(WORDS)} wordings, "
      f"{NPROG} programs, coupled bootstrap live, 3 guards live")
