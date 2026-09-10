"""Build one vLLM engine under one named configuration, then stop.

This is the child half of the s6.3 hang probe. It is deliberately a separate
process from the runner that supervises it, for two reasons. The failure being
chased freezes an interpreter, so anything sharing that interpreter with it dies
too: the in-process watchdog that was supposed to bound the 2026-08-22 hangs
never fired for exactly that reason. And each configuration under test mutates
process-global state -- environment variables the vLLM platform layer reads once
at import, CUDA contexts, sometimes the installed flashinfer wheel -- so arms run
back to back in one interpreter would contaminate each other in ways no result
could be trusted through.

What it does is the smallest thing that reproduces the failure. Both wedged jobs
stopped at the same instruction, the `LLM(...)` constructor, immediately after
the import probe and before a single row was read or generated. Neither had
touched its data. So the trigger needs no dataset, no prompts, no scoring and no
harness: an engine build and one four-token completion exercise the whole
suspect path in a few minutes, where the full cells they stand in for cost
roughly 87 GPU-minutes apiece.

The completion at the end is not ceremony. A constructor that returns has proved
only that setup finished; the first generate call is where CUDA graph replay,
attention-backend dispatch and KV-cache addressing are first exercised together,
and the earlier pair of hangs on 2026-08-21 stopped there rather than in the
constructor. An arm that builds but cannot serve is a failed arm.

Output is one JSON object on stdout between two sentinels, so the parent can
recover a verdict from a log even when the process is killed mid-write and the
result file never lands.
"""

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

BEGIN = "===PROBE-RESULT-BEGIN==="
END = "===PROBE-RESULT-END==="


def emit(result, out_path):
    """Report the verdict twice, on stdout and to a file, because either can be lost.

    A killed process leaves no result file. A truncated job log leaves no
    stdout. Writing both means one arm's verdict survives the loss of either.
    """
    blob = json.dumps(result, indent=2, default=str)
    print(BEGIN, flush=True)
    print(blob, flush=True)
    print(END, flush=True)
    if out_path:
        try:
            Path(out_path).write_text(blob)
        except Exception as exc:  # a lost file is not worth failing the arm over
            print(f"[probe] could not write {out_path}: {exc}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, help="name of the configuration under test")
    ap.add_argument("--model", required=True)
    ap.add_argument("--max-model-len", type=int, default=20480)
    ap.add_argument("--gpu-util", type=float, default=0.90)
    ap.add_argument("--enforce-eager", action="store_true",
                    help="disable CUDA graph capture, as the C2/C5/C7 runners already do")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    t0 = time.time()
    result = {
        "arm": args.arm,
        "model": args.model,
        "enforce_eager": bool(args.enforce_eager),
        "attention_backend": os.environ.get("VLLM_ATTENTION_BACKEND", "(default)"),
        "stage": "starting",
        "ok": False,
    }

    try:
        from serving import (make_flashinfer_importable, probe_vllm_import_paths,
                             env_fingerprint)
        result["fingerprint"] = env_fingerprint()
        print("[probe] " + result["fingerprint"], flush=True)

        result["stage"] = "flashinfer_repair"
        result["flashinfer_repair"] = make_flashinfer_importable()
        print("[probe] " + str(result["flashinfer_repair"]), flush=True)
        result["import_paths"] = probe_vllm_import_paths()
        print("[probe] " + str(result["import_paths"]), flush=True)

        # The constructor. This is the instruction both wedged jobs stopped at,
        # and the reason this file exists.
        result["stage"] = "engine_build"
        print(f"[probe] building engine: arm={args.arm} "
              f"eager={args.enforce_eager} "
              f"backend={result['attention_backend']}", flush=True)
        from vllm import LLM, SamplingParams
        t_build = time.time()
        llm = LLM(model=args.model, dtype="bfloat16",
                  max_model_len=args.max_model_len,
                  gpu_memory_utilization=args.gpu_util,
                  trust_remote_code=True,
                  enforce_eager=bool(args.enforce_eager))
        result["build_seconds"] = round(time.time() - t_build, 1)
        print(f"[probe] engine built in {result['build_seconds']}s", flush=True)

        # First generate: graph replay, backend dispatch and KV addressing, which
        # the constructor alone does not exercise.
        result["stage"] = "first_generate"
        t_gen = time.time()
        outs = llm.generate(["Reply with the single word: ready."],
                            SamplingParams(temperature=0.0, max_tokens=4))
        result["generate_seconds"] = round(time.time() - t_gen, 1)
        result["sample_output"] = outs[0].outputs[0].text.strip()[:120]
        print(f"[probe] served in {result['generate_seconds']}s: "
              f"{result['sample_output']!r}", flush=True)

        result["stage"] = "done"
        result["ok"] = True

    except BaseException as exc:  # a clean failure is a result, not a crash
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()[-4000:]
        print(f"[probe] FAILED at {result['stage']}: {result['error']}", flush=True)

    result["total_seconds"] = round(time.time() - t0, 1)
    emit(result, args.out)
    # Exit 0 whichever way it went: the verdict is in the payload, and the
    # supervisor's own exit code is reserved for "this arm never came back".
    return 0


if __name__ == "__main__":
    sys.exit(main())
