#!/usr/bin/env python3
"""Fixtures for oc_gate.py, so the release call is trusted before it is needed.

Row OC lands once. If the gate that reads it is wrong, the error is either six
cells that should not have run or six cells wrongly abandoned, and neither is
visible until much later. Every case below is the real reference file with one
field perturbed, which is also the only way to be sure the gate is reading the
fields it prints.

Runs in about a second on CPU and touches no job.
"""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE / "oc_gate.py"
REF = HERE / "ref" / "cbc1215f_calibration_14B-R.json"
KEY = "14B-R/public"


def run(doc, tmp, name):
    p = pathlib.Path(tmp) / f"{name}.json"
    p.write_text(json.dumps(doc))
    r = subprocess.run([sys.executable, str(GATE), "--candidate", str(p)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def perturb(base, path, value):
    d = copy.deepcopy(base)
    node = d[KEY]
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = value
    return d


def main():
    base = json.loads(REF.read_text())
    failures = []
    checks = 0

    def check(name, cond, detail=""):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(f"{name}: {detail}")

    with tempfile.TemporaryDirectory() as tmp:
        # 1. The control reproducing itself exactly must be a clean release.
        rc, out = run(base, tmp, "identical")
        check("identical -> RELEASE", rc == 0, f"exit {rc}")
        check("identical is clean, not flagged", "RELEASE (flagged)" not in out
              and "RELEASE -" in out, out[-400:])

        # 2. An accuracy move larger than the C5 floor must hold the rows.
        v = base[KEY]["verbalized"]["accuracy"]
        rc, out = run(perturb(base, ["verbalized", "accuracy"], round(v + 0.05, 4)),
                      tmp, "acc-drift")
        check("accuracy +0.05 -> HOLD", rc == 1, f"exit {rc}")
        check("HOLD names the metric", "verbalized.accuracy moved" in out, out[-400:])

        # 3. A move inside the floor is the case the control exists to allow.
        rc, out = run(perturb(base, ["verbalized", "accuracy"], round(v + 0.02, 4)),
                      tmp, "acc-inside")
        check("accuracy +0.02 -> RELEASE", rc == 0, f"exit {rc}")

        # 4. The floor is a boundary, and 0.028 is inside it.
        rc, _ = run(perturb(base, ["verbalized", "accuracy"], round(v + 0.028, 4)),
                    tmp, "acc-edge")
        check("accuracy +0.028 (on the bound) -> RELEASE", rc == 0, f"exit {rc}")
        rc, _ = run(perturb(base, ["verbalized", "accuracy"], round(v + 0.0281, 4)),
                    tmp, "acc-over")
        check("accuracy +0.0281 (past the bound) -> HOLD", rc == 1, f"exit {rc}")

        # 5. The self-consistency arm gates just as hard as the verbalized one.
        sc = base[KEY]["self_consistency"]["accuracy"]
        rc, _ = run(perturb(base, ["self_consistency", "accuracy"], round(sc - 0.06, 4)),
                    tmp, "sc-drift")
        check("self-consistency accuracy -0.06 -> HOLD", rc == 1, f"exit {rc}")

        # 6. A softer statistic moving alone releases, but must say so.
        au = base[KEY]["verbalized"]["auroc"]
        rc, out = run(perturb(base, ["verbalized", "auroc"], round(au + 0.08, 4)),
                      tmp, "auroc-drift")
        check("auroc +0.08 -> RELEASE flagged", rc == 0 and "RELEASE (flagged)" in out,
              f"exit {rc}\n{out[-400:]}")

        # 7. A different measurement is void, not a result to interpret.
        rc, out = run(perturb(base, ["n_rows"], 150), tmp, "rows")
        check("n_rows changed -> VOID", rc == 2, f"exit {rc}")
        check("VOID refuses to interpret", "Do not read the numbers" in out, out[-300:])
        rc, _ = run(perturb(base, ["sampling", "sc_seed"], 99), tmp, "seed")
        check("sampling seed changed -> VOID", rc == 2, f"exit {rc}")
        rc, _ = run(perturb(base, ["model"], "Qwen/Qwen2.5-14B-Instruct"), tmp, "model")
        check("model changed -> VOID", rc == 2, f"exit {rc}")

        # 8. The paper's reading is checked, not just the deltas. A verbalized
        #    arm that suddenly discriminates well is a different finding.
        rc, out = run(perturb(base, ["verbalized", "auroc"], 0.95), tmp, "finding")
        check("broken finding is reported", "no longer reads as stated" in out,
              out[-500:])

        # 9. A hard field the candidate never wrote must not pass silently.
        d = copy.deepcopy(base)
        del d[KEY]["self_consistency"]["accuracy"]
        rc, out = run(d, tmp, "missing")
        check("missing hard field -> HOLD", rc == 1, f"exit {rc}")
        check("missing field is named", "missing" in out.lower(), out[-300:])

    print(f"oc_gate selftest: {checks - len(failures)}/{checks} checks passed")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
