"""s6.3 hang probe: find out what freezes the vLLM engine build, cheaply.

Four cells in this study have frozen on an L40S and held the card until a human
stopped them: two on 2026-08-21 for about twenty hours each, two on 2026-08-22
for eighty-five minutes. Reading the four logs side by side puts all of them at
the same place. The last line every one of them wrote is the import probe, and
the next instruction in every runner is the `LLM(...)` constructor. No rows were
read, no prompts rendered, nothing generated. Whatever this is, it happens
before the study's data is involved at all.

That is the opening this file uses. A frozen cell costs roughly 87 GPU-minutes
before anyone can say anything about it, and the operator has authorised exactly
one further attempt at the two outstanding rungs. Spending that attempt on a
full cell would buy one bit at full price. An engine build plus one four-token
completion exercises the identical path for a few minutes, so the same GPU hour
buys a reproduction, a diagnosis and a test of every candidate fix.

The design follows from what is and is not known.

  Reproduce first. Every arm after the first is worthless if the baseline does
  not hang, because a mitigation that "works" against a failure that did not
  occur has shown nothing. So arm one is the failing configuration exactly as it
  ran, and what happens to it decides what runs next: hang, and the mitigations
  are worth testing; survive, and the useful measurement is repetition, since an
  intermittent fault and an image fault call for completely different responses
  and repetition is what separates them.

  One arm per process. Each configuration is a fresh interpreter under an
  external supervisor. The environment variables vLLM reads at import are read
  once, CUDA contexts do not unwind cleanly after a freeze, and one arm replaces
  an installed wheel. Arms sharing an interpreter would contaminate each other.

  The clock lives outside. The 2026-08-22 pair ran with an in-process stall
  watchdog and it never fired, because a hang that stops the interpreter stops
  the watchdog thread with it. `supervise.sh` holds the deadline in the job's
  shell, and captures native stacks before it kills anything. That capture is
  the point of the exercise as much as the verdict is: the operator's standing
  instruction is that a repeat hang should produce a diagnosis rather than
  another data point.

One thing this probe cannot settle. Every GPU cell in this project has run on an
L40S, so the fact that all four hangs were on L40S carries no information; there
is no other card in the record for them to not have happened on. The smaller
cells now queued on A10G are what will answer that, and they are queued
regardless of how this comes out.
"""

import json
import os
import re
import shlex
import subprocess
import sys
import time
import traceback
from pathlib import Path

from lab import lab

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

SUPERVISOR = HERE / "supervise.sh"
CHILD = HERE / "engine_probe.py"
DUMPS = HERE / "dumps"

TIMEOUT_RC = 75  # supervise.sh reserves this for "killed on the deadline"
BEGIN = "===PROBE-RESULT-BEGIN==="
END = "===PROBE-RESULT-END==="


def save(obj, name):
    path = HERE / name
    path.write_text(json.dumps(obj, indent=2, default=str))
    lab.save_artifact(str(path), name)
    print(f"[artifact] {name} ({path.stat().st_size} bytes)", flush=True)


def save_text(text, name):
    path = HERE / name
    path.write_text(text)
    lab.save_artifact(str(path), name)
    print(f"[artifact] {name} ({path.stat().st_size} bytes)", flush=True)


def parse_embedded(stdout):
    """Recover the child's verdict from its log if the result file never landed.

    A killed arm writes no file, and a killed arm is the case that matters most.
    """
    try:
        chunk = stdout.split(BEGIN)[-1].split(END)[0]
        return json.loads(chunk)
    except Exception:
        return None


def run_arm(arm, model, max_model_len, gpu_util, limit_minutes):
    """Run one configuration to completion, to failure, or to the deadline."""
    label = arm["name"]
    print(f"\n{'=' * 68}\n[arm] {label}: {arm['why']}\n{'=' * 68}", flush=True)

    env = dict(os.environ)
    env.update(arm.get("env", {}))
    # Armed here as well as in the supervisor, because the fallback dump path
    # needs the handler installed before the process starts.
    env["PYTHONFAULTHANDLER"] = "1"

    record = {
        "arm": label,
        "why": arm["why"],
        "env_overrides": arm.get("env", {}),
        "enforce_eager": bool(arm.get("enforce_eager")),
        "limit_minutes": limit_minutes,
        "pre": arm.get("pre", ""),
    }

    if arm.get("pre"):
        print(f"[arm] {label}: preparing: {arm['pre']}", flush=True)
        pre = subprocess.run(arm["pre"], shell=True, capture_output=True, text=True,
                             timeout=1800)
        record["pre_rc"] = pre.returncode
        record["pre_tail"] = (pre.stdout + pre.stderr)[-1500:]
        print(f"[arm] {label}: preparation rc={pre.returncode}", flush=True)

    out_json = HERE / f"probe-{label}.json"
    if out_json.exists():
        out_json.unlink()

    cmd = [
        "sh", str(SUPERVISOR), str(limit_minutes), str(DUMPS), label,
        sys.executable, str(CHILD),
        "--arm", label, "--model", model,
        "--max-model-len", str(max_model_len),
        "--gpu-util", str(gpu_util),
        "--out", str(out_json),
    ]
    if arm.get("enforce_eager"):
        cmd.append("--enforce-eager")

    t0 = time.time()
    # No `timeout=` here on purpose. supervise.sh owns the clock; a second timer
    # in this process would race it and could kill the supervisor mid-dump,
    # losing the stack trace that is the whole reason for the deadline.
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    record["wall_seconds"] = round(time.time() - t0, 1)
    record["rc"] = proc.returncode
    record["hung"] = proc.returncode == TIMEOUT_RC
    stdout = proc.stdout or ""
    record["log_tail"] = (stdout + "\n--- stderr ---\n" + (proc.stderr or ""))[-6000:]

    verdict = None
    if out_json.exists():
        try:
            verdict = json.loads(out_json.read_text())
        except Exception:
            verdict = None
    if verdict is None:
        verdict = parse_embedded(stdout)
    record["child"] = verdict
    record["ok"] = bool(verdict and verdict.get("ok"))
    record["stage_reached"] = (verdict or {}).get("stage", "no verdict recovered")

    dump = DUMPS / f"{label}.stack.txt"
    if dump.exists():
        # The faulthandler tracebacks go to the guarded processes' stderr, which
        # arrives here rather than in the supervisor's file. Fold them in before
        # the artifact is saved, so one file holds the whole diagnosis and
        # reading it later does not also require finding the right job log.
        if proc.stderr:
            with dump.open("a") as fh:
                fh.write("\n\n--- guarded stderr (faulthandler tracebacks) ---\n")
                fh.write(proc.stderr[-40000:])
        record["stack_dump"] = dump.name
        record["stack_bytes"] = dump.stat().st_size
        lab.save_artifact(str(dump), f"dump-{label}.stack.txt")
        # The frames are the deliverable, so put a slice of them in the job log
        # too: artifacts can be read later, a log line is read now.
        head = dump.read_text(errors="replace")[:4000]
        print(f"[arm] {label}: STACK DUMP (first 4000 chars)\n{head}", flush=True)

    outcome = "HUNG" if record["hung"] else ("ok" if record["ok"] else "failed")
    print(f"[arm] {label}: {outcome} after {record['wall_seconds']}s "
          f"(rc={record['rc']}, reached {record['stage_reached']})", flush=True)
    lab.log(f"arm {label}: {outcome} in {record['wall_seconds']}s, "
            f"reached {record['stage_reached']}")
    return record


def build_arms(cfg, reproduced):
    """Choose what to test next from what the baseline did.

    Reproduced hang, and the mitigations are the question: does taking flashinfer
    out of the compute path help, does restoring the version pairing that every
    successful cell in this study ran under help, does disabling graph capture
    help. Graph capture is included for completeness and is not expected to: one
    of the two 2026-08-22 cells was a C2 paraphrase cell, and that runner already
    passes `enforce_eager=True`, so it froze with capture disabled.

    No hang, and mitigations would be untestable. Repetition is the measurement
    instead, because a fault that appears in some builds and not others is an
    intermittent, and an intermittent is a hardware or scheduling story rather
    than an image one.
    """
    pin = str(cfg.get("flashinfer_pin", "0.6.17"))
    if not reproduced:
        return [
            {"name": f"repeat-{i}",
             "why": "the baseline configuration again: an intermittent fault and a "
                    "deterministic one need different responses, and only repetition "
                    "tells them apart"}
            for i in (2, 3)
        ]
    return [
        {"name": "attn-flash",
         "why": "flashinfer out of the attention path, FlashAttention in its place: "
                "the cheapest way to ask whether flashinfer is where this lives",
         "env": {"VLLM_ATTENTION_BACKEND": "FLASH_ATTN"}},
        {"name": "attn-sdpa",
         "why": "the most conservative backend vLLM ships, no custom kernels at all: "
                "if this hangs too, attention is not the story",
         "env": {"VLLM_ATTENTION_BACKEND": "TORCH_SDPA"}},
        {"name": "eager",
         "why": "no CUDA graph capture. Expected not to help, and recorded anyway: "
                "the C2 cell that hung already ran this way, so a hang here confirms "
                "graph capture is ruled out on the C8 path as well",
         "enforce_eager": True},
        {"name": "flashinfer-pin",
         "why": f"flashinfer-python=={pin}, the version every successful cell in this "
                f"study ran against, restoring the pairing the image change moved off. "
                f"Runs last: it replaces the installed wheel for anything after it",
         "pre": f"pip install -q flashinfer-python=={pin}"},
    ]


def main():
    lab.init()
    try:
        cfg = lab.get_config() or {}
        from serving import env_fingerprint
        lab.log(env_fingerprint())
        print("[probe] " + env_fingerprint(), flush=True)

        model = cfg["model"]
        rung = cfg.get("rung", "unknown")
        max_model_len = int(cfg.get("max_model_len", 20480))
        gpu_util = float(cfg.get("gpu_memory_utilization", 0.90))
        arm_minutes = float(cfg.get("arm_minutes", 18))
        total_minutes = float(cfg.get("total_minutes", 75))

        DUMPS.mkdir(exist_ok=True)
        if not SUPERVISOR.exists():
            raise RuntimeError(
                f"{SUPERVISOR} is missing. The deadline has to be held outside this "
                f"process; the in-process watchdog is what failed on 2026-08-22, so "
                f"running without the supervisor would repeat the mistake.")
        os.chmod(SUPERVISOR, 0o755)

        started = time.time()
        records = []

        # Arm one is the configuration that hung, unchanged. The first weight
        # load also warms the HuggingFace cache, so every arm after it pays for
        # the engine build alone.
        baseline = {
            "name": "baseline",
            "why": f"the {rung} configuration exactly as it ran when it froze, to "
                   f"establish that the failure reproduces before anything is changed",
        }
        records.append(run_arm(baseline, model, max_model_len, gpu_util, arm_minutes))
        reproduced = records[0]["hung"] or not records[0]["ok"]

        lab.log("baseline " + ("reproduced the failure" if reproduced
                               else "completed normally") +
                "; testing " + ("mitigations" if reproduced else "for intermittency"))

        for arm in build_arms(cfg, reproduced):
            spent = (time.time() - started) / 60.0
            if spent + arm_minutes > total_minutes:
                print(f"[probe] stopping before arm {arm['name']}: {spent:.1f} of "
                      f"{total_minutes} budgeted minutes used, and one more arm could "
                      f"overrun it", flush=True)
                lab.log(f"skipped arms from {arm['name']} onward: probe budget "
                        f"{total_minutes} min would be exceeded")
                records.append({"arm": arm["name"], "skipped": "probe budget exhausted",
                                "why": arm["why"]})
                continue
            records.append(run_arm(arm, model, max_model_len, gpu_util, arm_minutes))

        ran = [r for r in records if "skipped" not in r]
        hung = [r["arm"] for r in ran if r.get("hung")]
        passed = [r["arm"] for r in ran if r.get("ok")]
        broke = [r["arm"] for r in ran if not r.get("ok") and not r.get("hung")]

        summary = {
            "model": model,
            "rung": rung,
            "reproduced_baseline_failure": reproduced,
            "arms_run": len(ran),
            "hung": hung,
            "passed": passed,
            "failed_with_error": broke,
            "wall_minutes": round((time.time() - started) / 60.0, 1),
            "dumps": sorted(p.name for p in DUMPS.glob("*.stack.txt")),
            "records": records,
        }

        # The recommendation is stated here rather than left to be inferred,
        # because the next decision after this job is which configuration the two
        # outstanding rungs run under, and that decision should not require
        # re-reading four arm logs.
        if not reproduced:
            summary["reading"] = (
                "The baseline did not fail. Whatever stopped the four wedged cells is "
                "not a property of this configuration on this node, which points away "
                "from the image and toward an intermittent: scheduling, a particular "
                "host, or a card. The repeat arms give a first rate estimate.")
        elif passed:
            summary["recommendation"] = passed[0]
            summary["reading"] = (
                f"The baseline failed and {passed[0]} did not. Run the outstanding "
                f"rungs under {passed[0]}, and re-run one already-measured "
                f"neighbouring cell under it as well, so there is an overlapping "
                f"point showing the change did not move the numbers.")
        else:
            summary["reading"] = (
                "Every arm failed, including the ones that remove flashinfer from the "
                "attention path entirely. The cause is underneath the serving "
                "configuration, so the stack dumps are the only remaining evidence and "
                "no further full-cell attempt should be spent before they are read.")

        save(summary, "probe-summary.json")
        for r in ran:
            if r.get("child"):
                save(r["child"], f"probe-{r['arm']}.json")
        if summary["dumps"]:
            joined = "\n\n\n".join(
                (DUMPS / d).read_text(errors="replace") for d in summary["dumps"])
            save_text(joined, "stack-dumps.txt")

        print("\n" + json.dumps(
            {k: v for k, v in summary.items() if k != "records"}, indent=2), flush=True)
        lab.finish(
            message=(
                f"Engine-build probe on {rung} ({model}), {len(ran)} arms in "
                f"{summary['wall_minutes']} min. Baseline "
                + ("reproduced the failure. " if reproduced
                   else "completed normally, so the failure did not reproduce. ")
                + f"Passed: {', '.join(passed) or 'none'}. "
                f"Hung: {', '.join(hung) or 'none'}. "
                f"Errored: {', '.join(broke) or 'none'}. "
                f"{len(summary['dumps'])} stack dumps captured. "
                + summary["reading"]),
            score={
                "arms_run": len(ran),
                "reproduced": 1 if reproduced else 0,
                "n_passed": len(passed),
                "n_hung": len(hung),
                "n_errored": len(broke),
                "wall_minutes": summary["wall_minutes"],
            },
        )

    except Exception as e:
        lab.error(f"Probe failed: {e}")
        print(traceback.format_exc(), flush=True)
        raise


if __name__ == "__main__":
    main()
