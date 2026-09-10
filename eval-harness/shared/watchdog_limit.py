"""Size the supervisor's wall-clock deadline for one cell, from the ledger.

The operator's rule, given on 2026-08-22, is "roughly 1.5x the longest known-good
runtime for a comparable cell". Both halves of that need care.

*Known-good* means the ledger, not the plan. `budget.json` records what every
completed job actually cost, so the bound is anchored to measured behaviour
rather than to an estimate that has already been wrong in both directions on this
study.

*Comparable* means the same variant, and the split that matters is reasoning
against plain. Completed reasoning cells here ran 71 to 131 GPU-minutes; completed
plain cells ran 8.5 to 25. Sizing a plain cell against the reasoning maximum would
give a bound so loose that a hang would burn two hours before anything noticed,
which is most of what this deadline exists to prevent.

The cell's own planned estimate is taken as a floor, because a cell can be
legitimately slower than anything comparable that came before it: row 8 is
estimated at 90 minutes against a plain maximum of 25, and clamping it to the
history would kill a healthy job.

Erring loose is the cheaper mistake. A deadline set too tight kills a good cell
and loses the whole run; one set too generous wastes some of a hang. So the
result is the larger of the two candidates, and the reasoning behind the number
is printed rather than left for someone to reconstruct.

    watchdog_limit.py <planned_minutes> [plain|reason]
"""
import json
import sys
from pathlib import Path

def _find_budget():
    """Walk up to the project root. Run from a queue script whose depth may move."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "budget.json"
        if candidate.exists():
            return candidate
    return Path("budget.json")


BUDGET = _find_budget()
FACTOR = 1.5
FLOOR = 30.0  # below this the deadline races cold start and weight download


def longest_known_good(variant):
    try:
        entries = json.loads(BUDGET.read_text())["entries"]
    except Exception as exc:
        print(f"# ledger unreadable ({exc}); falling back to the planned estimate",
              file=sys.stderr)
        return 0.0, 0
    want = "-reason" if variant == "reason" else "-plain"
    hits = [e["actual_gpu_min"] for e in entries
            if e.get("outcome") == "complete"
            and (e.get("actual_gpu_min") or 0) > 0
            and want in str(e.get("task", ""))]
    # Reasoning cells are named `-reason`; the plain ones are inconsistently
    # named across batteries, so a plain cell with no same-variant precedent
    # falls back to every completed cell rather than to nothing.
    if not hits and variant != "reason":
        hits = [e["actual_gpu_min"] for e in entries
                if e.get("outcome") == "complete" and (e.get("actual_gpu_min") or 0) > 0
                and "-reason" not in str(e.get("task", ""))]
    return (max(hits) if hits else 0.0), len(hits)


def main():
    planned = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    variant = sys.argv[2] if len(sys.argv) > 2 else "plain"
    known, n = longest_known_good(variant)
    limit = max(FACTOR * planned, FACTOR * known, FLOOR)
    print(f"# watchdog limit {limit:.0f} min = 1.5x max(planned {planned:.0f}, "
          f"longest known-good {variant} cell {known:.1f} over {n} completed), "
          f"floor {FLOOR:.0f}", file=sys.stderr)
    print(int(round(limit)))


if __name__ == "__main__":
    main()
