# The known-good baseline, and what the re-run is being diffed against

Written 2026-08-22 for the s6.5 re-look, at the operator's instruction to treat
the first re-run as a test of the image hypothesis rather than as a re-run.

## What happened

Two GPU cells queued on 2026-08-21 evening held their cards for close to 23
hours and produced nothing: `a7b6cd37` (C8 calibration, 7B-R, nebius, started
17:51:48) and `f837e005` (C2 paraphrase, plain 14B, aws us-east-1a, started
18:20:18). Both were stopped on 2026-08-22 for 2,718.3 GPU-min between them.
Neither wrote a scoring line. Both logged `flashinfer.comm already imports
cleanly; no repair needed` where every healthy cell in this project logs a
27-file annotation repair.

## What makes the aws pair a clean A/B

`8068a860` (C2 paraphrase, 7B-R) completed on aws us-east-1a/1b the **same
calendar day**, 02:23:09 to 04:33:56, roughly sixteen hours before `f837e005`
wedged. Their job specs are identical field for field:

| field | `8068a860` (good) | `f837e005` (wedged) |
|---|---|---|
| accelerators | `L40S:1` | `L40S:1` |
| cpus / memory / disk | 16 / 64 / 200 | 16 / 64 / 200 |
| setup | `pip install -q vllm transformers` | `pip install -q vllm transformers` |
| run | `python main.py` | `python main.py` |
| provider / zone | aws, us-east-1a | aws, us-east-1a |

Nothing this project controls differs between them. Whatever changed came from
underneath the task spec.

## What could not be recovered, and why

The good jobs' actual version strings are gone. Task logs carry only harness
lines; `lab job machine-logs 8068a860` returns a 737-line tail with the setup
phase already rolled off; `request-logs` returns 46 bytes; saved artifacts carry
no environment metadata. So the baseline below is **inferred**, from two
independent kinds of evidence, and the re-run's fingerprint is what will confirm
or kill it.

### Evidence 1: the libraries did not move

`vllm`'s last release before the incident was 0.27.1 on 2026-08-11, and
`flashinfer-python`'s was 0.6.17, also 2026-08-11. Neither published anything
between 2026-08-11 and 2026-08-22. An unpinned `pip install -q vllm
transformers` therefore resolved to the same wheels on the good day and the bad
one, which rules the serving libraries out as the thing that changed.

### Evidence 2: the repair fires, so the interpreter was old

Every healthy job in this project logs a 27-file flashinfer annotation repair.
The repair exists because flashinfer's sources subscript `array.array[...]` at
class-definition time, which is legal from Python 3.12 onward and a `TypeError`
below it. A job that needs the repair is running an interpreter **older than
3.12**, and the project's records put the good image at **Python 3.10**. Both
wedged jobs logged that the import was already clean, which is what an
interpreter of 3.12 or newer produces.

## The prediction being tested

If the base image changed on 2026-08-21, the most likely single change is an
**interpreter bump to 3.12 or newer**, which would make the repair a no-op and
could leave the import path in a state the harness never sees past. A secondary
candidate is a driver or CUDA bump under the same interpreter.

**If the re-run reports Python 3.10 and the repair fires as before, the
image-change theory is wrong** and the wedge has to be explained some other way
(the operator asked to be told this before the other nine cells start).

## How to read the answer

`env_fingerprint()` in `serving.py` now emits one line, first thing, after the
stall watchdog is armed and before any weights load:

```
serving stack: python <ver>, torch <ver>, vllm <ver>, flashinfer-python <ver>, transformers <ver> | image: <os pretty name>, kernel <rel>, driver <ver> on <card>, cuda <ver>, venv <path>, executable <path>
```

The fields to read against this file, in order of how much they would tell us:
`python`, then `<os pretty name>` and `kernel`, then `driver` and `cuda`. The
library versions are expected to be vllm 0.27.1 and flashinfer-python 0.6.17 on
both sides; a surprise there would itself be informative, since PyPI says it
should not happen.

## Re-run pairing

| re-look | job | provider / card | diffs against | why that pairing |
|---|---|---|---|---|
| 3R (C8, 7B-R) | `6587ac1e` | nebius L40S | `cbc1215f` (aws) and `a7b6cd37` (nebius, wedged) | reproduces the wedged nebius configuration exactly |
| 4R (C2, plain 14B) | `2301e6b7` | aws L40S | `8068a860` (aws, good, same day) and `f837e005` (aws, wedged) | the clean same-provider A/B described above |

Both re-runs deliberately reproduce the configuration that hung, which is what
makes them a test. The standing project preference for A10-class cards is set
aside for these two cells only, and applies again from cell 5 onward; the
14B rung could not use it in any case, since it needs 29.5 GB against A10G's
21.6 GB budget.

---

## Result, 2026-08-22T18:05Z — the image did change, and the prediction was right

`6587ac1e` (row 3R, nebius L40S) reported:

```
serving stack: python 3.12.3, torch 2.13.0, vllm 0.27.1,
  flashinfer-python 0.6.16.post3, transformers 5.15.1
| image: Ubuntu 24.04.4 LTS, kernel 6.11.0-1016-nvidia,
  driver 580.173.02 on NVIDIA L40S, cuda 13.0.3,
  venv none, executable /opt/transformerlab-venv/bin/python
```

followed by `flashinfer.comm already imports cleanly; no repair needed` and a
clean vLLM import probe.

**The interpreter is 3.12.3 where the good image was 3.10.** The predicted bump
is exactly what the runner received, and it explains the behavioural marker
without residue: on 3.12 the `array.array[...]` subscript is legal, so the
27-file repair has nothing to do, which is why both wedged jobs and this one log
that the import is already clean. The image-change theory survives its first
test.

**Two things this does not yet establish.** First, `6587ac1e` is running: it
passed the import probe, the same point both wedged jobs reached before going
silent, so a 3.12 image is not fatal on its own and the wedge is downstream of
the import. Second, one vendor is not the A/B; `2301e6b7` on aws is the run that
compares against a same-spec success from the same zone. Read both before
concluding.

### A correction to Evidence 1

The libraries do **not** float with PyPI. The runner uses a prebuilt venv at
`/opt/transformerlab-venv`, and it holds `flashinfer-python 0.6.16.post3`, which
is a release *older* than the 0.6.17 that an unpinned install would have
resolved to. So library versions travel with the image, and the argument that
"the wheels could not have changed because PyPI published nothing" does not
hold: the image can move a pin in either direction without any release
happening. The conclusion is unaffected, since the interpreter moved too, but
the reasoning behind it was weaker than it looked and the next such argument
should read the image rather than the index.

### Candidate mechanisms, now that the interpreter is known

Ranked by how well they fit a hang that begins after a clean import and during
weight load, with no further output for 20 hours:

1. **CUDA 13.0.3 with driver 580.173.02** under `torch 2.13.0` and `vllm
   0.27.1`, a stack combination this project has never run before 2026-08-21.
   A hang in graph capture or in a kernel-autotune path would look exactly like
   the observed silence.
2. **`flashinfer-python 0.6.16.post3` against `vllm 0.27.1`**, where the earlier
   image paired a repaired 0.6.17 with the same vllm. A backward pin is an
   untested pairing, not a safer one.
3. **`transformers 5.15.1`**, a major version, in the weight-loading path.

The hardening that follows from any of the three is the same and was already
named: pin the serving stack in `task.*.yaml` instead of installing whatever the
image offers. That change is deferred until both re-runs report, because pinning
now would destroy the comparison the operator asked for.

### Both vendors reported, 2026-08-22T18:12Z

`2301e6b7` (row 4R, aws L40S us-east-1a) reported:

```
serving stack: python 3.12.3, torch 2.13.0, vllm 0.27.1,
  flashinfer-python 0.6.16.post3, transformers 5.15.1
| image: Ubuntu 24.04.4 LTS, kernel 6.17.0-1020-aws,
  driver 595.91.07 on NVIDIA L40S, cuda 13.2.20260303,
  venv none, executable /opt/transformerlab-venv/bin/python
```

Laid against the nebius run:

| field | nebius `6587ac1e` | aws `2301e6b7` |
|---|---|---|
| python | 3.12.3 | 3.12.3 |
| torch / vllm | 2.13.0 / 0.27.1 | 2.13.0 / 0.27.1 |
| flashinfer-python | 0.6.16.post3 | 0.6.16.post3 |
| transformers | 5.15.1 | 5.15.1 |
| OS | Ubuntu 24.04.4 LTS | Ubuntu 24.04.4 LTS |
| kernel | 6.11.0-1016-nvidia | 6.17.0-1020-aws |
| driver | 580.173.02 | 595.91.07 |
| cuda | 13.0.3 | 13.2.20260303 |
| venv | `/opt/transformerlab-venv` | `/opt/transformerlab-venv` |

**The Python stack is identical across the two vendors and the kernel, driver and
CUDA are not.** So the platform ships one common venv on top of a vendor-specific
base, which is why the same hang could appear on nebius and aws on the same
evening: the shared layer is the one that moved. The vendor-specific layer varies
by two CUDA minor versions and fifteen driver releases, and both wedged.

### Where the two re-runs stand

Both cleared the import probe, which is where `a7b6cd37` and `f837e005` were last
seen alive, and both have gone further than their predecessors ever did.
`2301e6b7` subsampled 238 rows over 61 programs, hashed all five wordings,
passed its pre-flight on 5 units and is loading 14B weights. `6587ac1e` is
running. Each carries a 45-minute stall watchdog, so a repeat of the hang costs
one window rather than a day.

**Read this as the image having changed, not yet as the image having caused the
hang.** A 3.12 image with CUDA 13 clearly does not wedge every job, since two
are progressing on it right now. What the fingerprints buy is a named, recorded
environment for every cell from here, so if a wedge recurs the comparison is
between two known stacks.


## 2026-08-22T22:45Z — the freeze point, and one hypothesis removed

Two findings change what this dossier is for.

**All four cells freeze at the same instruction.** Every wedged log ends on the
import probe, and the next line of every runner is the vLLM `LLM(...)`
constructor. No rows read, no prompts rendered, nothing generated. The apparent
difference in how far the two 2026-08-22 jobs got is runner ordering and nothing
else: the calibration runner builds its engine before subsampling, the paraphrase
runner after, so one had already logged its row counts and the other had not.
Both stopped in the same call.

That is the most useful thing known about this failure, because it makes the
trigger cheap to reach. Testing a fix needs an engine build, not a cell.

**Graph capture is ruled out.** The leading mechanism recorded above was a CUDA 13
graph-capture or autotune hang. Half of it is now dead: job `2301e6b7` is a C2
paraphrase cell, and `paraphrase/main.py:608` has passed `enforce_eager=True`
since the battery was written, so it froze with capture already disabled. Any
account of this hang has to explain a cell that never captured a graph.

What is left inside the constructor, in the order the probe tests it:

| Candidate | Standing |
|---|---|
| flashinfer JIT / autotune | Strongest. The installed version moved **backward** across the image change, 0.6.17 to 0.6.16.post3, and the annotation repair that every successful cell logged is exactly what the wedged cells reported as unnecessary. Tested by two attention-backend arms and a version pin. |
| Process-group / NCCL init under CUDA 13 | Open. Single-GPU jobs still initialise a group. Not directly tested; would survive all four arms. |
| Weight loading under transformers 5.15.1 | Open. Both vendors ship it. Would survive all four arms. |
| KV-cache memory profiling | Open. Runs inside the constructor and touches the allocator. Would survive all four arms. |
| CUDA graph capture | **Ruled out.** See above. |

The bottom three are why the stack dumps matter more than the arm verdicts. If
every arm hangs, the frames are the only evidence left, and the operator's
instruction was that a third hang should produce a diagnosis rather than another
data point.

**The card question stays open, and is being answered elsewhere.** All four hangs
were on L40S. So was every other GPU cell in this project, which is why that fact
carries no evidence in either direction. WAVES row 7 (`b16db17a`) is the first
A10G cell here, and it is queued regardless of what the probe finds.


## 2026-08-26T00:05Z — the dump, and what it settles

The stall handoff added on 2026-08-22T23:50Z worked on its first outing. Job
`a483488c` (WAVES row 4R, C2 paraphrase at plain 14B) froze in the same place as
the five before it, the in-process guard wrote its sentinel instead of calling
`os._exit`, and `supervise.sh` ran `py-spy dump --native` over the whole process
tree before reaping it. Six hangs in, this project finally has frames.

**What the dump shows.**

- The launcher is blocked inside `LLM.__init__`, `vllm/entrypoints/llm.py:339`.
  The frame above it carries `enable_multiprocessing: True` and a resolved
  `vllm_config`, so the constructor had got as far as building its engine client.
- A **second process, PID 2437, named `VLLM::EngineCore`**, is holding
  **40,973 MiB of the L40S's 46,068**. At `gpu_memory_utilization=0.90` that is
  the entire budget: 29.5 GB of bf16 weights plus a fully allocated KV cache. The
  child had finished building. It was ready.
- **GPU-Util is 0%.** Nothing anywhere is computing.
- Every thread in both processes is `state=S`, parked on `futex_do_wait` or
  `ep_poll`. The kernel stack is `futex_do_wait`.
- There are roughly **eight repeated sets** of `pt_nccl_watchdg`,
  `pt_nccl_heartbt`, `gloo_tcp_loop` and `pt_gloo_runloop`, plus a
  `pt_tcpstore_uv`, in a job running at `tensor_parallel_size=1`.

**What that kills.** Two candidates in the table above required the constructor to
still be doing work. Weight loading under transformers 5.15.1 had completed, and
so had KV-cache memory profiling: both are upstream of the allocation the dump
measures. Neither survives.

**What it promotes.** The failure is a lost handshake between the launcher and its
engine-core child, not a CUDA fault, not a kernel, not a card. The child finished
and went idle; the parent never learned it had. That is the row this dossier has
carried as "Process-group / NCCL init, open, not directly tested" since
2026-08-22, and it is now the only mechanism the frames support.

| Candidate | Standing as of 2026-08-26 |
|---|---|
| Engine-core handshake under `enable_multiprocessing` | **Leading, and the only one the frames support.** Child fully built and idle, parent blocked forever, nothing computing. |
| flashinfer JIT / autotune | **Weak.** Was the strongest reading before the dump. A JIT compile or autotune would burn GPU or CPU; the dump shows 0% utilisation and every thread asleep on a futex. |
| Process-group / NCCL init under CUDA 13 | Folded into the row above. Eight duplicated NCCL and gloo thread sets at TP=1 is the anomaly that names the mechanism. |
| Weight loading under transformers 5.15.1 | **Ruled out.** Weights are resident in the dump. |
| KV-cache memory profiling | **Ruled out.** The cache is allocated in the dump. |
| CUDA graph capture | **Ruled out.** See 2026-08-22. |

**Why the probe passed and the cells did not.** `4bdf6575` built the same engine on
the same configuration three times out of three and never froze. A lost handshake
explains that where a broken image does not: whether the ready signal arrives
depends on the node the job lands on, so a mechanism of this shape is expected to
be intermittent, and the probe's three arms are three draws that happened to come
up healthy.

**One loose end the frames do not close.** vLLM 0.27.1 sets
`VLLM_ENGINE_READY_TIMEOUT_S` to 600 by default, so a wait on engine startup
should have raised after ten minutes rather than run past forty-five. The block
is therefore somewhere in the client construction that is *not* covered by that
deadline; the message-queue handshake is the obvious candidate, and it has no
timeout. Recorded as a gap in the account, not smoothed over.

**The mitigation adopted, and the two not taken.** `VLLM_ENABLE_V1_MULTIPROCESSING=0`
removes the whole mechanism at once: no child process, no ZMQ ready handshake, no
fork of an interpreter that already owns CUDA and gloo threads, and no dependence
on how the node's own hostname resolves. The knob is real in the installed vllm
0.27.1 — `envs.py` reads `int(os.getenv("VLLM_ENABLE_V1_MULTIPROCESSING", "1"))`,
checked against the source rather than assumed, because a flag vLLM does not
recognise is indistinguishable from no flag until the deadline fires.

Two narrower candidates fit the same dump and were deliberately not used, so that
one change is under test and the overlap control means something:

- `VLLM_WORKER_MULTIPROC_METHOD=spawn`, which removes the fork-after-threads
  hazard while keeping the two-process architecture. Weaker on this evidence: the
  child clearly ran, so a fork-time deadlock in the child is not what happened.
- `VLLM_LOOPBACK_IP=127.0.0.1`, which pins the handshake to loopback if the node's
  own name is what resolves wrong.

Both stay on the shelf for the next attempt if the adopted one fails.

**How a silent no-op is now caught.** `env_fingerprint()` prints an `engine env:`
segment naming every transport knob and whether it was set, with `-` for unset,
on every cell from here. The knobs are read from `os.environ` and not from
`vllm.envs`, deliberately: `from vllm import envs` executes `vllm/__init__.py`,
and the fingerprint runs *before* `make_flashinfer_importable()` precisely so
that a cell which cannot import flashinfer still records which image it got.

**A repair found while wiring this in.** `verify_shared.py` was already failing
before any of today's edits: `start_stall_watchdog` in `_shared/serving.py` had
picked up the handoff documentation and a disable guard that never reached the
copies in `temperature/main.py` and `paraphrase/main.py`. Since `assemble-c8.sh`
runs that check and stops on it, **both outstanding C8 cells (WAVES rows 5 and 9)
would have refused to assemble.** All three copies are now byte-identical and the
check passes on 8 functions.

## 2026-08-26T15:05Z — the image moved a second time, mid-control

The overlap control `2072549d` logged its fingerprint five minutes after taking a
card, and it does not match the stack every cell since 2026-08-21 has run:

```
serving stack: python 3.12.3, torch 2.13.0, vllm 0.28.0, flashinfer-python
0.6.16.post3, transformers 5.16.0 | image: Ubuntu 24.04.4 LTS, kernel
6.17.0-1020-aws, driver 595.91.07 on NVIDIA L40S, cuda 13.2.20260303, venv none,
executable /opt/transformerlab-venv/bin/python | engine env:
ENABLE_V1_MULTIPROCESSING=0, WORKER_MULTIPROC_METHOD=-, ATTENTION_BACKEND=-,
HOST_IP=-, LOOPBACK_IP=-
flashinfer.comm already imports cleanly; no repair needed
```

Against the 2026-08-23 baseline, two libraries moved: **vllm 0.27.1 → 0.28.0** and
**transformers 5.15.1 → 5.16.0**. Everything else is byte-identical, including the
kernel, the driver, the CUDA build, the interpreter and flashinfer itself. The
platform's common Python layer therefore moved twice in five days, and nothing
announced either move; the fingerprint line is the only reason we know.

**The mitigation is still valid on the new version.** `vllm-0.28.0`'s `envs.py` was
pulled and read directly rather than assumed: `VLLM_ENABLE_V1_MULTIPROCESSING`
is still declared `bool = True` and still resolves as
`bool(int(os.getenv("VLLM_ENABLE_V1_MULTIPROCESSING", "1")))`, so `0` disables
engine-core multiprocessing exactly as it did in 0.27.1. `VLLM_WORKER_MULTIPROC_METHOD`
(`"fork"`) and `VLLM_ENGINE_READY_TIMEOUT_S` (600) are also unchanged, so the open
loose end about the ten-minute ready deadline that never fired survives the bump
intact and is not explained by it.

**The no-op detector earned its keep on first use.** `engine env:
ENABLE_V1_MULTIPROCESSING=0` on the run's own log is the proof that the knob reached
the process, which is the one thing a silent mitigation cannot be assumed to have
done. Had the flag been mistyped or dropped by the queue script, the line would read
`-` and a forty-five-minute freeze would have looked identical to a mitigation that
failed on its merits.

**What the version bump costs the control.** Row OC now carries two differences from
`cbc1215f`, not one: the single-process engine, and a serving stack two library
versions newer. The reference cell is older than we had been treating it as, too:
its log opens with `repaired flashinfer: deferred annotations in 27 file(s)`, the
signature of the **pre-2026-08-21 image**, so it never ran the 0.27.1 stack at all.
The honest reading of the control is therefore the one the operator's standing note
actually asks for, a check that *the compute path as it now stands* reproduces a
known answer, and not an isolation of the mitigation's own effect. Two consequences,
both to be carried into the write-up rather than smoothed away:

1. If the numbers reproduce inside the 2.8-point noise floor, the remaining rows are
   safe to run, which is the decision the control exists to unblock. The causal claim
   that the handshake was the fault stays supported by the stack dump, which is direct
   evidence, and not by this cell, which cannot separate the two changes.
2. If the numbers move, the cause is ambiguous between the engine mode and the
   library bump, and the correct response is still to stop, because either way the
   ladder's measurements are no longer being produced by a stable path.

No attempt will be made to pin 0.27.1 back. Pinning was checked on 2026-08-22 and is
not reachable through this platform, and installing a specific vllm into the job's
setup step would change the compute path a third way to chase a version that only
ever ran wedged cells.
