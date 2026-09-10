"""Deliberately defective programs, one per admission gate.

A build that reports no rejections is not obviously a clean corpus; it is equally
consistent with gates that never fire. Each case here is a program the toolchain is known
to mishandle, or one that a non-executing strategy answers correctly, and the build
refuses to start unless every gate catches its own case.

There are two kinds of check here and the difference matters.

`run` is fatal. Everything in it is deterministic and every failure means the screening
code itself is broken, which is the only condition that should stop a build.

`observe` is not. It records what the toolchain currently does with same-variable
operands, and the honest reason it cannot be fatal is that the behaviour is random. On
the public toolchain `a == a` returns a stable answer inside one interpreter and
disagrees between interpreters, and even across fresh processes the disagreement shows up
in roughly half of small samples. An earlier version of this file asserted it, ten times
in a single process, and stopped a build over a coin flip that had landed the other way.

The determinism gate is proven live by handing its logic three disagreeing runs instead,
in `run`. That holds whatever the runtime happens to do on the day.

Same-variable operands do not all fail the same way: `a == a` and `b && b` are
nondeterministic, while `a + a` with a = 3 quietly returns 3. One family, two failure
modes, which is why the lint gate bans the whole family rather than the cases that would
be caught downstream anyway.
"""

from __future__ import annotations

import multiprocessing as mp
from typing import Any

import lint
from gates import WANT_RUNS, determinism_gate
from runner import canonical, compile_program, execute

SAME_VAR = """int a;
int b;
procedure main {
    b = a + a;
}
"""

NO_HALT = """int n;
bool g;
procedure main {
    g = n > 0;
    while (g) {
        n = n + 1;
        g = n > 0;
    }
}
"""

NO_CHANGE = """int a;
int b;
procedure main {
    a = a + 0;
    b = b + 0;
}
"""

NONDET_EQ = """int a;
bool r;
procedure main {
    r = a == a;
}
"""

NONDET_AND = """bool b;
bool r;
procedure main {
    r = b && b;
}
"""


def _once(job: tuple[str, dict, int, float]) -> str | None:
    """Compile and run in this worker's own process, so the answer is that process's."""
    source, inputs, max_steps, wall_limit_s = job
    result = execute(compile_program(source, optimize=False), inputs, max_steps, wall_limit_s)
    return canonical(result.outputs) if result.ok else None


def run(max_steps: int = 20_000, wall_limit_s: float = 120.0) -> list[str]:
    """Return a list of failures. Empty means every gate caught its own case."""
    failures: list[str] = []

    if not lint.check(SAME_VAR):
        failures.append("lint gate did not catch same-variable binary operands")
    if not lint.check("int a;\nprocedure notmain {\n    a = a + 1;\n}\n"):
        failures.append("lint gate did not catch a missing main procedure")

    result = execute(compile_program(NO_HALT, optimize=False), {"n": 1, "g": False},
                     max_steps, wall_limit_s)
    if result.ok:
        failures.append("halting gate: a non-terminating loop reported as halted")

    result = execute(compile_program(NO_CHANGE, optimize=False), {"a": 3, "b": 4},
                     max_steps, wall_limit_s)
    if not result.ok:
        failures.append("changed-variable probe did not halt")
    elif result.outputs != {"a": 3, "b": 4}:
        failures.append(f"changed-variable probe changed something: {result.outputs}")

    # The determinism gate is tested on fabricated evidence, not by trying to catch the
    # runtime being nondeterministic. An earlier version executed a known-ambiguous
    # program and asserted the repeats disagreed; whether they do is itself a coin flip,
    # and a flaky assertion in a gate self-test costs a job launch every time it lands
    # wrong. What has to be true is that the predicate fires, and that is decidable here.
    def runs_of(n: int, **over) -> list[dict]:
        out = [{"canonical": "x", "steps": 10, "seed": 1000 + i} for i in range(n)]
        for key, values in over.items():
            for run, value in zip(out, values):
                run[key] = value
        return out

    verdict = determinism_gate(runs_of(WANT_RUNS))
    if verdict is not None:
        failures.append(f"determinism gate rejected {WANT_RUNS} agreeing runs: {verdict}")
    for name, runs, want in (
        ("disagreeing outputs",
         runs_of(WANT_RUNS, canonical=["x", "y"] + ["x"] * (WANT_RUNS - 2)),
         "determinism:disagreement"),
        ("disagreeing steps",
         runs_of(WANT_RUNS, steps=[10, 11] + [10] * (WANT_RUNS - 2)),
         "determinism:step-disagreement"),
        ("a repeated seed",
         runs_of(WANT_RUNS, seed=[7] * WANT_RUNS),
         "determinism:repeated-seed"),
        ("too few runs",
         runs_of(WANT_RUNS - 1),
         "determinism:missing-runs"),
        ("a run that did not finish",
         runs_of(WANT_RUNS, canonical=[None] + ["x"] * (WANT_RUNS - 1)),
         "determinism:missing-runs"),
    ):
        got = determinism_gate(runs)
        if got != want:
            failures.append(f"determinism gate returned {got!r} for {name}, expected {want!r}")

    return failures


def observe(max_steps: int = 20_000, wall_limit_s: float = 120.0,
            samples: int = 24, workers: int = 6) -> dict[str, Any]:
    """Record what this toolchain build does with same-variable operands.

    Recorded rather than asserted, and reported next to the corpus so a reader can see
    which defects the lint gate was actually protecting against on the day the corpus was
    built. A run that finds one answer everywhere is not a failure; it is a sample in
    which the coin came up the same way every time.
    """
    out: dict[str, Any] = {}
    for label, source, inputs in (("a == a", NONDET_EQ, {"a": 3, "r": False}),
                                  ("b && b", NONDET_AND, {"b": True, "r": False})):
        jobs = [(source, inputs, max_steps, wall_limit_s)] * samples
        with mp.Pool(workers) as pool:
            answers = [a for a in pool.map(_once, jobs, chunksize=1) if a is not None]
        out[label] = {"samples": len(answers), "distinct_answers": len(set(answers)),
                      "answers": sorted(set(answers))}

    result = execute(compile_program(SAME_VAR, optimize=False), {"a": 3, "b": 9},
                     max_steps, wall_limit_s)
    out["a + a"] = {"input_a": 3, "expected": 6,
                    "got": result.outputs.get("b") if result.ok else None,
                    "status": result.status}
    return out
