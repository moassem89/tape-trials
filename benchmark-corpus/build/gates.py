"""The gate predicates that are pure functions of already-collected evidence.

Separated from `main.py` so the self-test can call them with fabricated evidence. A gate
that is only ever exercised through a real build can only be shown to fire by finding a
program that trips it, and for the determinism gate that means depending on a runtime
quirk continuing to exist. Here the same logic can simply be handed disagreeing runs.
"""

from __future__ import annotations

WANT_RUNS = 6


def determinism_gate(runs: list[dict], want_runs: int = WANT_RUNS) -> str | None:
    """Which determinism condition a row's repeated executions fail, or None if all hold.

    Repeats must differ in their executor seed, because that is the only thing the
    nondeterminism actually depends on. Varphi resolves equally-specific transition rules
    with `random.choice`, so two runs in one process with one RNG state agree by
    construction, and an earlier version of this gate leaned on separate processes to
    supply the variation by accident. Seeds make the variation deliberate and countable.

    How many repeats is not a free choice. On the reference case `a == a`, sixteen seeds
    produce three distinct outcomes with the most common one taking ten of them, so three
    repeats would let a genuinely ambiguous program through around a quarter of the time.
    A row that slips through carries an answer key that is a coin flip, and every model is
    then scored against it.

    Steps are compared as well as outputs: the same answer can be reached by a different
    route, and step count is the study's difficulty axis, so a row whose difficulty is
    unstable is unusable even when its answer is not.
    """
    if len(runs) < want_runs or any(r["canonical"] is None for r in runs):
        return "determinism:missing-runs"
    if len({r.get("seed") for r in runs}) < want_runs:
        return "determinism:repeated-seed"
    if len({r["canonical"] for r in runs}) != 1:
        return "determinism:disagreement"
    if len({r["steps"] for r in runs}) != 1:
        return "determinism:step-disagreement"
    return None
