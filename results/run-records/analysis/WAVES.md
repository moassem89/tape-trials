# The remaining s6 cells, in queue order

Two GPU cells at a time is the hard limit, so this is a queue, not a plan. Take
the top unstarted row whenever a slot frees. Every command below is complete:
copy it, do not retype the model id. A cell labelled `7B` that served 14B weights
would be invisible in the results and fatal to the paper.

`queue-cell.sh` assembles, uploads and queues **once**. If it times out, check
`lab --format json job list -e tape-trials-exp-20260820` before doing anything
else: the queue may have succeeded with the response lost, and a blind retry is
how this project acquired a duplicate job.

## Every GPU cell now runs under a supervisor

As of 2026-08-22T22:45Z, `queue-cell.sh` copies `_shared/supervise.sh` into every
bundle, adds `py-spy` to setup, and rewrites the run command to
`sh supervise.sh <limit> dumps <rung> python main.py`. Nothing needs to be passed
by hand except `PLANNED=<the estimate in the table below>`, which is what sizes
the deadline; the commands in the table already carry it.

The deadline is 1.5x the longest known-good comparable cell, the operator's rule,
computed from the ledger by `_shared/watchdog_limit.py` rather than chosen. It
splits reasoning cells from plain ones because the completed reasoning cells here
ran 71 to 131 GPU-minutes and the completed plain cells ran 8.5 to 25, and it
takes the cell's own estimate as a floor so a legitimately slow cell is not
killed for having no fast precedent.

The in-process `start_stall_watchdog` stays armed as well. It is not redundant:
the supervisor's wall clock cannot tell a slow cell from a stuck one, and the
stall watchdog can, as long as the interpreter is still alive to notice. What it
cannot do is survive a freeze, which is the case it was reached for, so it is now
the second line rather than the only one.

Three things the supervisor does that a bare `timeout` would not:

- Kills the **tree**. vLLM v1 runs its engine core as a separate process, and it
  is the one holding GPU memory. Reaping only the launcher leaves the card busy
  and the next cell fails to allocate for reasons unrelated to what it was doing.
- Dumps **every process** in the tree, one at a time, with `py-spy dump --native`
  before killing anything. A launcher blocked reading a pipe from a frozen engine
  core has a useless stack.
- Echoes the dump into the job log. The dump file lives on a machine that is torn
  down minutes after a killed job, so the file alone would not survive.

## Order

Longest first, so the tail is short and no long cell starts last.

| # | Condition | Rung | Est. GPU-min | Command |
|---|---|---|---|---|
| ~~1~~ | C8 calibration | 14B-R | 180 | **`cbc1215f` complete, collected** (84.6 actual) |
| ~~2~~ | C2 paraphrase | 7B-R | 140 | **`8068a860` complete, collected** (130.8 actual) |
| 3R | C8 calibration | 7B-R | 120 | **STOPPED 2026-08-23T00:02Z as `992e6b7b`, 68.4 GPU-min, no result; UNQUEUED and written down for a re-look.** Third attempt, third first-generate hang: the engine built (CUDA graph capture 23:09:17Z, KV cache 24.25 GiB, JIT monitor armed 23:10:38Z) and nothing came back. Stopped by hand rather than left to its 196-min supervisor deadline, because both GPU slots were held by hung cells and the operator's rule is to stop a wedged cell and move on to the rest of the queue. Its 45-min stall watchdog was armed before the handoff existed, so it captured nothing, exactly as predicted. It does not requeue on its own: three attempts have now produced three hangs and no diagnosis, so the next attempt waits until a hang has actually been photographed on a cheaper cell (row 7, `c6f1cff2`). Prior: **RUNNING as `992e6b7b` since 2026-08-22T23:07Z on aws L40S, supervised at 196 min, configuration UNCHANGED.** Third attempt. The probe `4bdf6575` built this exact configuration on the same image and served a completion in 285.3 s, so the failure is not reproducible, no mitigation is adopted and the operator's stand-down condition (a hang under the pin) was not met. Routed to L40S rather than an A10-class card deliberately: `card_fit` clears 7B-R on A10G at only 4.4 GB of KV cache, and this is six passes of up to 16k tokens over 181 rows. Prior: Second attempt `6587ac1e` wedged at the `LLM(...)` constructor and was stopped 19:07Z, 88.3 GPU-min, no result; that was the one permitted kill for this cell. It does not requeue until the probe names a configuration that survives, and then only with `PLANNED=120`. Prior note: **RE-RAN as `6587ac1e` from 2026-08-22T17:44Z on nebius L40S; see the 17:46Z section below.** First attempt STOPPED 2026-08-22T16:42Z, no result. `a7b6cd37` held a nebius L40S for 22h50m (1,370.3 GPU-min charged), loaded weights, then went silent. Bundle `ec3a09ee` is uploaded and now carries the watchdog: `PROVIDER=nebius sh queue-cell.sh calibration reason deepseek-ai/DeepSeek-R1-Distill-Qwen-7B 7B-R` |
| 4R | C2 paraphrase | 14B | 55 | **DEAD as `a483488c`, 88.3 GPU-min, no result; UNQUEUED and out of retries.** Fourth attempt, fourth hang at the same constructor. It is also the most valuable job this project has run. The stall handoff fired on its first outing: the in-process guard wrote its sentinel instead of calling `os._exit`, `supervise.sh` ran `py-spy dump --native` over the process tree, and the frames are what finally named the mechanism. The launcher was blocked in `LLM.__init__` with `enable_multiprocessing: True`; a `VLLM::EngineCore` child held 40,973 MiB of 46,068, meaning weights plus a fully allocated KV cache; GPU-Util was 0%; every thread in both processes was parked on a futex or an epoll. The child was ready and the launcher never learned it. Full reading in `_shared/image-baseline.md`, 2026-08-26. This row does not requeue: the operator's allowance is one watchdog kill per cell and this cell has had four. It requeues only if the mitigation now under test (row OC) clears, and then as a fresh decision, not automatically. Prior: **RUNNING as `a483488c` since 2026-08-23T00:10Z on aws L40S, supervised at 82 min; configuration UNCHANGED, and the first cell to carry the stall handoff.** Provider is aws, not the nebius this row previously named: the team's provider note (`updated_at` 2026-08-11T23:20:20) sources L40S from aws g6e first and nebius second, and the reason the row said nebius (a second vendor sample on the hardware hypothesis) died with the hypothesis when row 7 hung on A10G. The first queue attempt at 23:59Z was refused for a reason worth recording: `queue-cell.sh` was passing `-p stall_minutes=45` and no battery's `task.yaml` declares that key, so `lab task queue` rejected the whole call. 45 is the default inside the code (`cfg.get("stall_minutes", 45)`), so the flag was dropped rather than the schemas widened; changing the stall limit now needs a `stall_minutes` entry in the battery's parameters block first. The second attempt was refused for GPU limit, both slots being held by rows 7 and 3R in teardown, which is what forced the stop decision recorded against those rows. Prior: **NEXT, queues when a slot frees; configuration UNCHANGED, supervised.** Released by the clean probe `4bdf6575` on the same reasoning as 3R. L40S is forced here, not chosen: 14B is 29.5 GB of weights against A10G's 21.6 GB budget, so `card_fit` refuses it. Prior: Second attempt `2301e6b7` wedged at the same constructor and was stopped 19:12Z, 86.2 GPU-min, no result. Note that this cell already ran with `enforce_eager=True` (`paraphrase/main.py:608`), which is what rules CUDA graph capture out as the shared cause. Prior note: **RE-RAN as `2301e6b7` from 2026-08-22T17:46Z on aws L40S; see the 17:46Z section below.** First attempt STOPPED 2026-08-22T16:48Z, no result. `f837e005` held an aws L40S for 22h28m (1,348.0 GPU-min charged), same silent failure on the other vendor. Bundle `22b255ab` is uploaded and now carries the watchdog: `PROVIDER=nebius sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-14B-Instruct 14B` |
| OC | C8 calibration | 14B-R | 85 | **CLEARED. COMPLETE as `2072549d` at 2026-08-26T16:16:08Z, 90.4 GPU-min against a planned 85 (+6.4%), no freeze, collected to `tape-trials/controls/`. `oc_gate.py` returns RELEASE, clean, exit 0.** Verbalized accuracy 0.7821 against the reference 0.8045 (-0.0224) and self-consistency 0.8674 against 0.8508 (+0.0166), both inside the 0.028 C5 floor; the two hard coverage and accuracy checks and all nine soft ones passed, the largest soft move being verbalized brier +0.0234 and self-consistency auroc -0.0330 against a 0.05 rank bound; all four qualitative claims still read as the stage report states them. **The mitigation is ADOPTED and rows 5, 6, 8, 9, 10 and 11 are RELEASED.** The gate had to be pointed at `_shared/ref/cbc1215f_calibration_14B-R.json/calibration_14B-R.json`: an earlier `lab job download -o` created a DIRECTORY at the path the gate's `DEFAULT_REF` names, so the bare default raises IsADirectoryError and exits 3. Pass `--reference` explicitly, or flatten the path, before trusting the default. Note also that `lab job download` does not create its `-o` directory: `mkdir -p` first or every file fails with ENOENT while the command still reports success. Prior: **REQUIRED AGAIN and RUNNING as `2072549d` (task `95d5b58a`) on aws L40S in us-east-1b, supervised at 196 min.** Three submits, one machine: `71dd900c` at 14:36Z and `d45e6634` at 14:42Z were both refused for g6e capacity across all four us-east-1 zones at zero cost, and `2072549d` took a card at 14:46:20Z. `d45e6634` is the submit whose client call was cut off before it returned an id; the platform's job list, which answered at 14:55Z after failing all session, confirms it died at launch and that no duplicate is holding a slot. The trigger condition written into this row has fired: a mitigation is adopted. The 2026-08-23 stack dump from `a483488c` names the engine-core handshake as the mechanism, and `VLLM_ENABLE_V1_MULTIPROCESSING=0` removes it. So this cell repeats `cbc1215f` exactly — same model, same 181 rows, same prompt, same card, same vendor — with the mitigation as the only change. Read it against the known answer: verbalized 0.8011 / 0.9989 / 0.19447 / 0.19441 / 0.5216, self-consistency 0.8508 / 0.09392 / 0.16022 / 0.925, correlation 0.0146. **Second variable, disclosed 15:05Z:** the control's fingerprint reports **vllm 0.28.0** and **transformers 5.16.0** where every cell since 2026-08-21 ran 0.27.1 and 5.15.1, so the platform image moved again between the diagnosis and the control. The mitigation still applies (0.28.0's `envs.py` was read directly and `VLLM_ENABLE_V1_MULTIPROCESSING` is unchanged in name, default and semantics) and the run log confirms the knob arrived as `ENABLE_V1_MULTIPROCESSING=0`. `cbc1215f` turns out to be older still, logging the 27-file flashinfer repair of the pre-2026-08-21 image. So this row tests whether the compute path as it now stands reproduces a known answer, which is what the operator's standing note asks for; it cannot isolate the mitigation's own effect, and the causal claim rests on the stack dump. Detail in `_shared/image-baseline.md`. **Nothing else queues until this lands.** If the numbers hold and it does not hang, rows 5, 6, 8, 9, 10 and 11 run under the mitigation. If they move, or if it hangs, the mitigation is dead and s6.3 and s6.5 close with the gaps recorded. Actual command: `MP=0 PLANNED=85 PROVIDER=aws sh queue-cell.sh calibration reason deepseek-ai/DeepSeek-R1-Distill-Qwen-14B 14B-R`. Prior: **NOT REQUIRED as of 2026-08-22T23:10Z, and unqueued.** The probe endorsed no mitigation, so the compute path of 3R and 4R is identical to every rung already measured and there is nothing for an overlapping point to control for. Becomes required again, before any affected cell, the moment a mitigation is adopted. Original terms: A repeat of `cbc1215f` (complete, 84.6 actual, 181 rows) under whatever the probe endorses. Same rows, same rung, one variable, so the mitigation's effect on the numbers is readable against a known answer rather than assumed to be zero. The operator's condition on changing the compute path mid-study, given 2026-08-22. `ATTN=<backend> FLASHINFER_PIN=<version> PLANNED=85 sh queue-cell.sh calibration reason deepseek-ai/DeepSeek-R1-Distill-Qwen-14B 14B-R` |
| 5 | C8 calibration | 14B | 50 | **COMPLETE 2026-08-26T22:49:17Z as `611cee24` (task `0c60ace3`) on RUNPOD L40S, 41.5 GPU-min against a planned 50, inside the 75-min supervised deadline. Fourth launch attempt, and the first to get a machine. 3 artifacts confirmed; 2 score files collected to `tape-trials/c8/`. Result: verbalized confidence stays saturated at 14B (mean 1.0) with AUROC exactly 0.5 (chance), accuracy 0.1326; self-consistency AUROC 0.8588, ECE 0.41105 - the 3B finding (row 9) holds at the larger rung.** Wave E. Three launches were refused before it and none of them ran: `41574289` at 21:38Z and `3e1b8ab1` at 22:00Z both for g6e.xlarge InsufficientInstanceCapacity in us-east-1, and `4c311756` at 21:51Z on a nebius `compute instance create` 300s timeout. No instance existed in any of the three and nothing was charged, so none of them spends the operator's one-kill-then-ask allowance, which covers wedged *running* cells. **The read that three refusals meant the card was gone was wrong.** The provider steering note (updated 2026-08-23T15:23Z by tony@lab.cloud) lists L40S with three sources in try order - AWS (g6e), Nebius, RunPod - and states that a card's row IS its complete source list and that you work it left to right without stopping before the last entry. RunPod had never been asked. **This is the one cross-vendor cell in wave E** - label its absolute accuracy as such wherever accuracy rather than spread is compared. Same L40S card, so the C5 noise floor still applies. L40S is forced not chosen: `card_fit` refuses 14B on A10G, the exception the operator's A10-preference note allows, and warns that 7.2 concurrent sequences will run longer than the L40S estimate. Collect with `sh collect-cell.sh 611cee24 c8`. Original command: `MP=0 PLANNED=50 PROVIDER=aws sh queue-cell.sh calibration plain Qwen/Qwen2.5-14B-Instruct 14B`; requeue form: `lab task queue 0c60ace3-59ca-486a-9be0-0d8a39f7980a -e tape-trials-exp-20260820 --no-interactive --provider Runpod -p model=Qwen/Qwen2.5-14B-Instruct -p rung=14B -m "..."` - **the requeue needs the FULL task uuid**, the 8-char short id prints `Task: Unknown` and then fails with a misleading `Task has no parameters declared` error. |
| 6 | C5 repeat | 14B | 40 | **COMPLETE 2026-08-26T23:17:55Z as `be59b8a6` (task `9a295079`) on RUNPOD L40S, 17.0 GPU-min against a planned 40, inside the 62-min supervised deadline. First launch attempt, no refusals, no freeze under MP=0. 7 artifacts confirmed; 7 score files collected to `tape-trials/c5/` (no collision: c5 previously held only the `14B-R` rung). Result: exact_match 0.1271 on every one of the five repeats, spread 0.0000, exact_match_stability 1.0 with zero rows changing verdict; answer agreement 0.8895 across all repeats and 0.9006 at fixed batch composition, text agreement 0.8729, modal answer share 0.968, 20 of 181 rows changed answer. This is the plain-rung companion to the 14B-R C5 cell and it is what the paraphrase spreads are read against.** Sent straight to RunPod rather than aws g6e per the standing instruction not to stack a second 14B/L40S capacity gamble on aws while RunPod is the vendor that actually took row 5. `card_fit`: 14B on L40S ok, 11.7 GB KV cache, 7.2 concurrent sequences; the predicted longer wall-clock did not materialise (116.8 s of generation across 905 generations). Command used: `MP=0 PLANNED=40 PROVIDER=runpod CARD=L40S sh queue-cell.sh temperature plain Qwen/Qwen2.5-14B-Instruct 14B`. **This was the last unqueued row in the queue; rows 5, 6, 8, 9, 10 and 11 are all complete and collected, and rows 3R, 4R and 7 are dead and out of retries, so the queue is closed.** |
| 7 | C2 paraphrase | 0.5B | 35 | **DEAD as `c6f1cff2`, 3.8 GPU-min, no result, cause UNKNOWN; UNQUEUED and out of retries.** Reported COMPLETE with progress 0, no task logs and no artifacts, after 3m47s. That is shorter than its own `pip install -q vllm transformers` step, so the harness never started and this is **not** the engine freeze the other cells show. The cluster was torn down before the machine log could be read, so the cause is recorded as unknown rather than guessed at. The one permitted retry is spent. Prior: **REQUEUED as `c6f1cff2` at 2026-08-23T00:12Z on aws A10G, supervised at 52 min. This is the one permitted retry.** The 52 replaces the 127 written here at 23:50Z, for two reasons. 127 was 1.5x the 84.6-min 14B-R cell, a reason-variant run and the wrong comparable for a plain 0.5B one; `watchdog_limit.py` anchors on the longest known-good *plain* cell, 24.7 min over five completed, and against a 35-min plan that gives 52. And 127 was sized to buy a dump at the wall clock, which the stall handoff now delivers at 45 min regardless of the deadline, so the extra 75 minutes would only buy held card on a hang. 52 still clears the 45-min stall limit, which is what keeps the handoff ordered correctly. The first attempt closed at **81.0 GPU-min, not the 45.9 the log implies**: the in-process watchdog `os._exit`ed at 23:41Z but the cluster stayed up and the slot stayed held until the job was stopped through the CLI at 00:02Z, 28 minutes later. A self-killed cell has to be stopped explicitly before the next one can queue. Prior: **HUNG and self-killed as `b16db17a`; requeue at `PLANNED=127`, one attempt, when a slot frees.** The engine built cleanly on A10G (18.35 GiB KV cache, 195.8x concurrency, JIT monitor 22:56:32Z) and the first `llm.generate` call never returned. The harness writes a line every 32 rows (`CHUNK`, `paraphrase/main.py:50`), so 45 minutes of silence is one chunk of 32 rows on a 0.5B model failing to come back, against a sub-minute expectation. **The hardware hypothesis is dead:** the same first-generate hang now has A10G, aws L40S and nebius L40S. No dump was captured, because the in-process stall watchdog at 45 min beat the supervisor at 52 and `os._exit`s without one; that race is now a handoff for every later cell: `supervise.sh` exports `SUPERVISE_DUMP_DIR`, `start_stall_watchdog` writes a `STALL` sentinel there and stops instead of killing, and the supervisor polls for it and runs its full dump-and-kill path at the 45-minute stall limit rather than at the wall clock. Patched in all three copies of the function (`_shared/serving.py`, `paraphrase/main.py:387`, `temperature/main.py:496`) and all three call sites; the two batteries that hang most often carry inlined copies, so a `_shared`-only fix would have missed them. Tested end to end against a toy stall. Requeue limit 127 min = 1.5x the 84.6-min known-good 14B-R C2 cell, the shortest of the two known-good C2 runs; the operator's 1.5x rule read against the longest (130.8) would give 196, and the shorter anchor is taken because a 0.5B cell that is working emits its first chunk line within about a minute, so the extra 70 minutes buys no protection for a healthy run and costs 70 GPU-min on a hang. 45.9 GPU-min spent, no result. Prior: **RAN as `b16db17a` from 2026-08-22T22:47Z on aws A10G, supervised at 52 min.** First non-L40S GPU cell in the project and the discriminator on the hardware hypothesis. `CARD=A10G PLANNED=35 sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-0.5B-Instruct 0.5B` |
| 8 | C2 paraphrase | 7B | 35→90 | **QUEUED 2026-08-26T21:36Z as `6425b7fc` (task `c416fae4`) on aws A10G, supervised at 135 min, MP=0.** Wave E. RUNNING and past the freeze point at 21:42Z: progress 69, lab initialized, so the single-process engine started where six earlier cells did not. Collect with the PLAIN form when it lands (`sh collect-cell.sh 6425b7fc-d5e6-41cd-8bce-59b84415310e c2`) - this is a matrix cell, not a control. Original command: `MP=0 CARD=A10G PLANNED=90 sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-7B-Instruct 7B` |
| 9 | C8 calibration | 3B | 30 | **QUEUED 2026-08-26T21:58Z as `89b08efe` (task `f1dce912`) on aws A10G, supervised at 45 min, MP=0. COMPLETE 22:10:45Z, 12.6 GPU-min against a planned 30; 2 score files collected to `tape-trials/c8/`.** Wave F, pulled forward into wave E's free slot the moment row 8 finished, per the header rule that this is a queue and not a plan. A10G is the operator's preferred card and `card_fit` passes 3B on it. The `queue-cell.sh` call outran the 120s client timeout; per the header rule the next action was `lab job list`, which showed the job already created, so nothing was resubmitted and there is no duplicate. Collected. `collect-cell.sh` downloaded 2 of the 3 listed artifacts and that is correct, not a partial pull: the script's `--file` glob excludes `transcripts_*.jsonl` on purpose, because the whole-job download is a zip of a few hundred megabytes of transcripts wrapped around a handful of score files. Result: verbalized confidence is at chance on this rung (AUROC 0.5599, ECE 0.9214, mean confidence 0.9937 against accuracy 0.0722) while self-consistency separates correct from incorrect sharply (AUROC 0.9216, ECE 0.3315). Command: `MP=0 CARD=A10G PLANNED=30 sh queue-cell.sh calibration plain Qwen/Qwen2.5-3B-Instruct 3B` |
| 10 | C2 paraphrase | 3B | 25 | **QUEUED 2026-08-26T22:14Z as `578ace1f` (task `87cff17a`) on aws A10G, supervised at 38 min, MP=0. COMPLETE 22:25:44Z, 10.75 GPU-min against a planned 25.** Taken ahead of row 6 into the slot row 9 freed, deliberately and against the strict top-of-queue reading of the header rule: row 6 is the other 14B cell, it needs L40S, and AWS g6e had refused three times within the hour, so a card that had just worked was worth more than a fourth capacity gamble. Ordering among rows 6, 10 and 11 disturbs no comparison. `card_fit`: 3B on A10G ok, 13.4 GB KV cache, 44.5 concurrent sequences. **The first `queue-cell.sh` call was wrapped in `timeout 110` and was killed AFTER `lab task add` registered task `87cff17a` and BEFORE `lab task queue` landed** - a registered task with no job, which looks like a total failure and is not. Requeued from the full task uuid. Never wrap a queue call in `timeout`; background it and confirm against `lab job list`. Collected: 11/11 files (5 `result_*.json` + 5 `per_item_*.jsonl` + `result_3B.json`) to `tape-trials/c2/`. Result: five wordings over 1190 rows (238 each), exact_match 0.1134 / 0.1134 / 0.1345 / 0.1134 / 0.1345, parse failures 0.0000 on the P1_frozen headline block, intra-cluster correlation 0.3268 over 61 programs. Command: `MP=0 CARD=A10G PLANNED=25 sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-3B-Instruct 3B` |
| 11 | C2 paraphrase | 1.5B | 20 | **QUEUED 2026-08-26T22:29Z as `800f79b5` (task `c7049ee8`) on aws A10G, supervised at 37 min, MP=0. LAUNCHING.** Taken into the slot row 10 freed, same reasoning as row 10: safe, fast A10G cell ahead of the L40S/RunPod gamble in row 6, which stays queued for whenever that slot frees rather than stacking a second capacity risk against RunPod while row 5 is still on it. `card_fit`: 1.5B on A10G ok, 16.5 GB KV cache, 70.3 concurrent sequences. Collect with `sh collect-cell.sh 800f79b5 c2`. Command: `MP=0 CARD=A10G PLANNED=20 sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-1.5B-Instruct 1.5B` |

**HOW TO COLLECT ROW OC, added 2026-08-26T15:44Z — read this before running
`collect-cell.sh` on it.** OC is a control, not a matrix cell, and it repeats a
rung that is already collected. Its two output files are named for the rung and
not for the job (`calibration_14B-R.json`, `per_row_confidence_14B-R.jsonl`), so
the plain `collect-cell.sh <job> c8` would have uploaded them straight over
`cbc1215f`'s files in `tape-trials/c8/` — destroying the reference the control
is read against, and doing it silently, since `--force` was already passed.
Renaming them into the same prefix is no better: `c8-compare/main.py` globs
`per_row_confidence_*.jsonl` and takes the rung from the filename, so a suffixed
copy would enter the C8 matrix as an invented extra rung. Collect it like this:

```sh
DEST=tape-trials/controls sh collect-cell.sh 2072549d-12f1-47fc-ba56-84336c56d55c c8
```

`collect-cell.sh` now refuses any upload that would land on an existing file
unless `OVERWRITE=1` is passed, so the mistake is no longer available by
accident. `tape-trials/controls/` is read by no aggregator, which is the point:
the control's numbers must never join the matrix, or the 14B-R rung is counted
twice.

**HOW TO READ IT.** `_shared/oc_gate.py` makes the release call mechanically
against `cbc1215f`'s own score file, which is parked locally at
`_shared/ref/cbc1215f_calibration_14B-R.json`:

```sh
python3 _shared/oc_gate.py --candidate <the downloaded calibration_14B-R.json>
```

It voids the comparison if the two cells did not measure the same thing (rows,
programs, k, sampling seeds, block, model), holds on any accuracy moving more
than the 2.8-point C5 floor, and otherwise releases, printing every softer
statistic that moved past its own bound and whether the C8 finding still reads
as the stage report states it. Exit codes 0 release, 1 hold, 2 void. Sixteen
fixture checks in `_shared/oc_gate_selftest.py`, all passing at 15:42Z.

Note the reference the gate uses is the JSON's own figures, where the verbalized
arm's accuracy is **0.8045** over the 179 rows whose confidence parsed. The
stage report's 0.8011 is the same arm over all 181. Comparing a candidate JSON
against the report figure would read that definitional 0.34-point gap as drift.


Rows 5 and 6 keep the L40S card and go to **nebius**; rows 7 to 11 move to
**A10G on aws**. Both changes are deliberate and the reasoning is in the next
section — do not "simplify" them back to one card and one vendor.

A row is struck once its job id is written next to it, which means queued, not
finished. The cell is done when `collect-cell.sh` has parked its files, and the
row says so.

**Status as of 2026-08-26T00:10Z.** Rows 1 and 2 are **done**: both complete,
artifacts confirmed, files collected. Rows 3R, 4R and 7 are **dead and unqueued**,
each having spent the operator's one-kill-then-ask allowance; between them they cost
about 240 GPU-min and produced one thing of value, the stack dump from `a483488c`.
Row OC is **running** as the overlap control for the mitigation that dump points at,
and holds one of the two GPU slots. Rows 5, 6, 8, 9, 10 and 11 have never been
attempted, carry their own allowances, and total about 255 GPU-min; every one of them
will run with `MP=0` if row OC clears.

The ledger stands at 4,741.2 of 5,400 GPU-min, so there is 658.8 of headroom against
about 340 of planned work. Even a worst case where all six remaining cells hang at
roughly 60 GPU-min apiece stays inside the gate, which is why continuing is affordable
and why each cell can be allowed its own attempt.

Prior status (2026-08-21T18:28Z): rows 3 and 4 running, rows 5 to 11 unstarted at
about 235 GPU-min.

**AWS g6e capacity returned at 18:21:40Z** after eleven consecutive refusals.
Queue the next row on the default provider (`aws`, per the provider note: L40S
goes to AWS g6e first, Nebius second) and fall back to `PROVIDER=nebius` only on
a fresh refusal. Only row 3 is cross-vendor; label its absolute accuracy as such,
and nothing else.

## 2026-08-21T17:45Z — neither vendor will take an L40S cell

Seven consecutive launches failed between 16:38Z and 17:39Z. Every one died
before an instance existed, so no GPU time was charged and no cell is half-run.
Two distinct faults, neither of them in this project's code:

| Vendor | Attempts | Failure |
|---|---|---|
| aws | `8bba6141`, `f57033ec`, `cc5fe16c`, `59a39a7b`, `c04b2160` | `InsufficientInstanceCapacity` for `g6e.xlarge`, us-east-1, the only AWS region holding GPU quota |
| nebius | `41e520cf`, `91067149`, plus two queue calls that returned no id | `nebius compute instance create` times out after 300s |

The lab API degraded during the same window: `job list` timed out repeatedly and
recovered, and three `lab task queue` calls timed out with no job id. **All three
of those created nothing** — the job count held at 71 across every check — so
there is no orphaned work to reconcile. A queue call that times out still has to
be checked against the job list before it is retried; that check is what kept
this from double-queueing.

This is recorded as a platform blocker at `s6.5`. When it clears, requeue rows 3
and 4 from their existing task ids, one per GPU slot:

```sh
lab task queue ec3a09ee-b459-4fe2-beda-d7c2cb2caffa -e tape-trials-exp-20260820 \
  --no-interactive --provider aws -p model=deepseek-ai/DeepSeek-R1-Distill-Qwen-7B -p rung=7B-R
lab task queue 22b255ab-5eae-434a-a267-ba0e4b96485d -e tape-trials-exp-20260820 \
  --no-interactive --provider aws -p model=Qwen/Qwen2.5-14B-Instruct -p rung=14B
```

Do not swap the card to get around this. The L40S constraint is in the next
section and in the C5 noise floor; a cell on a different card is not comparable
to the ladder it is meant to sit beside. Swapping the **vendor** is fine and is
already covered below.

## 2026-08-26T22:07Z — "neither vendor will take it" was never the whole row

The section above, and the 2026-08-21 one before it, both frame L40S sourcing as
a two-vendor question: AWS g6e, and nebius when g6e is full. That framing is
incomplete and it cost this queue three launch attempts on row 5 before anyone
checked. The provider steering note (updated 2026-08-23T15:23Z by tony@lab.cloud,
read with `lab provider note`) gives L40S **three** sources in try order:

    L40S   48GB   AWS (g6e), Nebius, RunPod

and states the rule plainly: a card's row IS its complete source list, worked
left to right, and you do not stop before its last entry. There is no default
chain underneath it. RunPod sells L40S, this team has a RunPod provider
configured, and until row 5 attempt 4 nothing in this study had ever asked it.

So the standing rule for any refused GPU cell here is:

1. **Work the full row before concluding anything.** Three refusals across two
   vendors is not an exhausted card when the row names three.
2. **A launch refusal is not a wedge.** No instance is created and nothing is
   charged. It does not spend the operator's one-watchdog-kill-then-ask
   allowance, which is about a *running* cell that has stopped producing output.
3. **If the whole row really is empty, escalate up the memory ladder — do not
   park.** The note is explicit that parking costs a day of the researcher's
   project and reaches a human who cannot fix it. Go UP only. A100-40GB is a
   capacity *downgrade* from a 48GB card that reads like an upgrade, and T4 is
   the one allowed card without bf16.
4. **But this study is the note's narrow exception, so escalation is not free.**
   Every cell here is a rung compared against numbers already measured on L40S.
   The note says: where the number will be compared directly against one already
   measured on specific hardware, work the card's full row first, and if you
   still have to escalate, **re-measure the earlier number on the new card** so
   both sides of the comparison sit on identical hardware. Price a card
   escalation at roughly two cells, not one, and treat the re-measurement the
   same way row OC was treated — as a gate, not a nicety.

Record in the stage report which card was wanted, which was got, and why.

## When AWS has no g6e capacity, the cell goes to nebius

Three launches were refused on 2026-08-21 with `InsufficientInstanceCapacity`
for `g6e.xlarge` in us-east-1d. AWS GPU quota exists only in us-east-1 and
us-east-2, so there is nowhere else on that vendor to scan, and a straight retry
four minutes later was refused identically. No instance is created by a refused
launch, so nothing is charged and nothing is half-run: treat the job id as dead
and queue the cell again.

`queue-cell.sh` now honours a `PROVIDER` variable, defaulting to `aws`:

```sh
PROVIDER=nebius sh queue-cell.sh paraphrase plain Qwen/Qwen2.5-14B-Instruct 14B
```

nebius sells the same L40S card, which is why the swap is safe for this study:
the battery compares wordings inside one cell, and both cells run whole on one
vendor. Absolute accuracy against the AWS-run ladder could still carry a small
vendor effect, so a cross-vendor cell is noted as such wherever its accuracy is
compared rather than its spread. Do not swap the card itself; the C5 noise floor
was measured on L40S and a different card would confound it.

A queue command that times out with no job id needs the check the header
describes, and the task id it already printed can be requeued directly with
`lab task queue <task-id> -e <exp> --no-interactive --provider <p> -p ...`
rather than assembling and adding the task a second time.

## Collect the recovered summary too, not just the job's own files

The 14B-R paraphrase cell had a hole in shared storage until 2026-08-21T16:50Z:
the four summaries that survived `7248de2b` were uploaded by hand, but the
recovered fifth (`result_14B-R_public__P5_inverted.json`) stayed on the recovery
job and was never parked under `tape-trials/c2/`. The H5 aggregator reads that
prefix and refuses on a missing wording, so it would have failed on a cell the
records call complete. Both that file and the cell's rebuilt `result_14B-R.json`
are now uploaded. Any cell whose files come from somewhere other than
`collect-cell.sh` needs this check done by hand.

## The 14B-R paraphrase cell is not in this queue

It ran as `7248de2b`, generated and scored all five wordings, and then died
writing the last summary when `capacity_fit` overflowed on a near-perfect cell.
The harness is fixed and the cell is being restored from its own saved
transcripts by `recover-c2/` (job `92846414`, CPU-only). **Do not re-queue it.**
Its per-row files and four of its five summaries are already under
`tape-trials/c2/`; the fifth arrives from the recovery job, which is why that
cell's collection step is the manual upload recorded in the s6 report.
`collect-cell.sh` refuses a job that is not COMPLETE, correctly.

The 0.5B paraphrase cell sits above 1.5B and 3B on purpose. It is the most
verbose plain rung by a wide margin, 317 output tokens per row against 34 at 3B,
so it decodes more despite being the smallest weights in the study.

C2 is not run on the chain-of-thought rung. The battery varies the specification
prose and holds the output contract fixed; the CoT arm changes the contract, and
running it there would confound the two.

## After each cell completes

```sh
sh collect-cell.sh <job-id> c2      # or c5, or c8
```

That parks the cell's score files under the storage prefix the aggregators read.
Skipping it for one cell leaves a hole in the ladder, and the H5 job will refuse
rather than rank around it.

## Once every C2 cell has been collected

```sh
sh rank-stability/assemble-rank.sh /tmp/rank
cd /tmp/rank && lab task add . -e tape-trials-exp-20260820 --no-interactive
lab task queue <task-id> -e tape-trials-exp-20260820 --no-interactive --provider aws
```

CPU-only, so it does not wait for a GPU slot.

## Rungs and their weights

| Rung | Model |
|---|---|
| 14B-R | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` |
| 7B-R | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` |
| 14B | `Qwen/Qwen2.5-14B-Instruct` |
| 7B | `Qwen/Qwen2.5-7B-Instruct` |
| 3B | `Qwen/Qwen2.5-3B-Instruct` |
| 1.5B | `Qwen/Qwen2.5-1.5B-Instruct` |
| 0.5B | `Qwen/Qwen2.5-0.5B-Instruct` |

The `14B-CoT` rung is the plain 14B weights under the chain-of-thought contract,
not a separate model. It appears in the holdout sweep and the analysis job and in
neither battery.

## 2026-08-21T17:47Z — capacity rechecked, AWS still refusing, cell moved to nebius

The lab API had recovered by 17:42Z (`job list` returns, quota reads clean, 71
jobs, no GPUs held), so the outage above was two separate faults and only one of
them has cleared. Row 3 (C8 / 7B-R, task `ec3a09ee`) was requeued on AWS as
`565dd2e5` at 17:47Z. It scanned all four candidate zones — 1a, 1b, 1c, 1d — and
was refused in every one for `g6e.xlarge`, the eighth consecutive on-demand
refusal and again at zero GPU cost. AWS's own error text still names 1a/1b/1c as
having capacity, so the message is stale relative to what RunInstances actually
does.

Row 3 was then requeued on nebius as `a7b6cd37` at 17:51Z, the documented
same-card fallback.
It reached `cluster_started` at 18:00:04Z, so nebius `instance create` is
working again; its 300s timeouts earlier in the day belonged to the same window
in which the lab API was timing out, not to a standing fault.

Row 4 (C2 / plain 14B, task `22b255ab`) followed on nebius as `42f7f55e` at
18:04Z, filling the second GPU slot. Its first queue call timed out with no job
id; the job list was checked before retrying and held at 73, confirming that
call created nothing, so there is no duplicate. That check is the one the header
of this file demands and it earned its keep a second time.

Both cells are cross-vendor. The C2 spread is measured inside one cell on one
machine and is unaffected; the plain-14B absolute accuracy carries a possible
vendor effect and is labelled wherever it is compared to the AWS-run ladder. The
C8 cells are compared against each other and against the 14B-R cell from row 1,
which ran on AWS — so the 7B-R-to-14B-R calibration comparison is cross-vendor
too, and says so.


## 2026-08-21T18:28Z — row 4 is on AWS, and the job count is why

Row 4's fourth launch (`42f7f55e`, nebius) died the same way its second did:
`compute instance create` timed out after 300s with no instance, zero cost. It
was requeued on AWS at 18:19:24Z and **that call also timed out, with no job
id** — the third response lost to the lab API today.

The check this file demands found the difference. The job count read **75**
against the 74 recorded at 18:13Z, and the extra row was `f837e005`,
`tape-trials-s6.5-c2-plain`, RUNNING: the launch had worked and only the
response was lost. Retrying blind would have run the cell twice against a
two-GPU allowance.

So the rule now has evidence on both sides of it. Earlier today three timed-out
queue calls created **nothing** and the count held at 71; this one created a
job. A timed-out queue call tells you nothing either way, which is exactly why
the count, not the timeout, decides what to do next.

`f837e005` scanned all four us-east-1 zones and took 1d on `g6e`. AWS is selling
L40S again.


## Which card a cell runs on (2026-08-21T18:40Z)

The operator asked whether the remaining cells can take an A10-class card
instead of L40S, and said nebius should have freed up. Both are actionable, and
they split the queue cleanly in two. The card question is settled by arithmetic
first and by what each cell *measures* second.

### Arithmetic: two cells cannot move, five can

`_shared/card_fit.py` computes weights, KV-cache headroom and concurrent
sequences from each model's published config at this study's fixed serving
settings (`gpu_memory_utilization: 0.90`, `max_model_len: 8192`). Run it with no
arguments for the whole table; `--check <rung> <card>` is the exit-code gate that
`queue-cell.sh` now calls before it will queue anything.

| Rung | Weights (bf16) | On L40S (48 GB) | On A10G (24 GB) |
|---|---|---|---|
| 0.5B | 1.0 GB | 400 seqs | 185 seqs |
| 1.5B | 3.1 GB | 162 seqs | 70 seqs |
| 3B | 6.2 GB | 116 seqs | 44 seqs |
| 7B | 15.2 GB | 55 seqs | **9.3 seqs** |
| 14B | 29.5 GB | 7.2 seqs | **will not start** |

The 14B rung needs 29.5 GB of weights against A10G's 21.6 GB budget, so rows 5
and 6 stay on L40S. There is no version of this that works: 2-GPU tensor
parallel would eat the entire 2-card allowance for one cell and change the
numerics, and quantising the weights would change the model the paper is
reporting on.

7B on A10G is the tight one at 9.3 concurrent sequences. It is worth noting that
**the 14B cells already in this study run at 7.2**, so 9.3 is inside the batch
regime this project has been operating in all along, not below it. Expect the
wall-clock to roughly double against the L40S estimate; the row's estimate is
updated to match.

### What the swap can and cannot disturb

The standing rule in this file — do not swap the card — was written to protect
comparisons against the ladder, and it still holds for exactly those. What the
five moved cells measure is a **within-cell contrast**, and every arm of that
contrast runs behind one weight load on one machine:

- **C2** reports the *spread* across five wordings, and the *ranking* of those
  wordings. Both are differences inside one cell.
- **C8** reports stated confidence against realised accuracy, and agreement
  across resamples against the same. Both are differences inside one cell.

Neither quantity can be moved by the card, because the card is held fixed inside
the cell. What the card *could* move is a cell's absolute accuracy, and the
honest position is that we do not yet know by how much.

### The swap prices itself, at no extra cost

Every C2 cell reruns `P1_frozen` as one of its five wordings, and every plain
rung already has an L40S reading of `P1_frozen` on the full public split from
s5.5. So each A10G cell yields a **card-effect delta for free**: four of them,
at 0.5B, 1.5B, 3B and 7B, read against the 2.8-point serving-noise floor that
C5 measured. No dedicated probe cell is needed, and none is queued.

Record each delta in `runs/s6.5-robustness.md` as its cell lands. Be honest
about the power: the C2 subsample is 238 rows and the plain rungs cluster hard
by program (design effect 2.30 to 2.85), so a single delta carries roughly a
±6 point interval and can only rule out a *large* card effect. Four deltas
pointing the same way is the useful reading, not any one of them.

If a delta lands outside the noise floor, requeue **that** cell on L40S and
report both. Do not quietly keep the A10G number.

### Provider routing, and why it is split

The provider note (2026-08-11) routes L40S to AWS `g6e` then Nebius, and A10/A10G
to AWS then Lambda — A10G is not sold by GCP. AWS GPU quota is one shared
us-east-1 vCPU ceiling across `g4dn`/`g5`/`g6`/`g6e`, so the two L40S cells are
sent to nebius, which the operator reports has freed up. That keeps the AWS
ceiling for the five `g5` cells and stops the two families competing for it.

Each moved cell therefore carries **one** axis of difference from the ladder, not
two: rows 5 and 6 are same-card, different-vendor; rows 7 to 11 are same-vendor,
different-card. Label them that way and never collapse the two into one caveat.

## 2026-08-22T16:50Z: rows 3 and 4 stopped, and the queue is parked on budget

Both cells that held the GPU slots were stopped on the operator's instruction to
pause the robustness runs and proceed, keeping a note to re-look at them later.
The platform has no pause, so a stop was the only way to release the cards. They
are rows `3R` and `4R` above and they are the first two cells to re-run, in that
order, whenever the queue restarts.

Nothing was queued in their place. Charging the two holds at wall clock takes the
project ledger to 4,318.9 GPU-min against a 3,400 plan, which trips the overrun
gate: no further jobs until the operator answers the escalated request to raise,
stop, or continue over the plan. Rows 5 to 11 are unchanged and stay in this
order; their routing (rows 5 and 6 to nebius L40S, rows 7 to 11 to A10G on aws)
still holds.

**Before queueing anything again, know what changed underneath.** Every runner
now arms `start_stall_watchdog()` and logs `env_fingerprint()` as its first two
acts, so a job that repeats the 2026-08-21 hang exits 75 after 45 minutes of
silence, or 300 minutes total, and names its own torch/vllm/flashinfer versions
in the log. The first cell to run after this point is also a test of whether the
new machine image still hangs, so read its fingerprint line before queueing the
second.

The failure is not vendor-specific: one wedged cell was on nebius, the other on
aws, and both logged `flashinfer.comm already imports cleanly; no repair needed`
where every successful cell logged the 27-file annotation repair. Pinning the
serving stack in `task.*.yaml` (currently a bare `pip install -q vllm
transformers`) is the obvious next hardening step if a repeat happens.


## 2026-08-22T17:46Z: the overrun gate is answered and rows 3R and 4R are running

The operator raised the plan from 3,400 to 5,400 GPU-min and asked for the
re-look cells to go first. Both are queued and launching:

| row | job | task | provider / card | planned | started |
|---|---|---|---|---|---|
| 3R | `6587ac1e-4c92-47ec-b8c1-a54372f39cdb` | `44fbd5b3` (C8, 7B-R) | nebius L40S | 120 | 2026-08-22 17:44:22 |
| 4R | `2301e6b7-ba15-4713-9489-debd10fbb275` | `67a13eb0` (C2, plain 14B) | aws L40S, us-east-1a | 55 | 2026-08-22 17:46:27 |

Both bundles were re-assembled rather than requeued from `ec3a09ee` and
`22b255ab`, because the uploaded copies predate the extended `env_fingerprint()`
and would have reported library versions with no machine-image fields. The
diagnostic is the point of these two runs, so the bundles had to carry it.

**Card choice, and the standing preference set aside.** Both cells run L40S on
the vendor that wedged them: 3R on nebius, 4R on aws. Reproducing the exact
configuration that hung is what makes a re-run readable as a test, and the
operator's instruction for this run says so directly, which outranks the
standing project preference for A10-class cards. The preference applies again
from row 5 onward. Row 4R could not have honoured it in any case, since the 14B
rung needs 29.5 GB against A10G's 21.6 GB budget.

`card_fit.py` cleared both at queue time: 7B-R on L40S gives 26.0 GB of KV cache
and 55.3 concurrent sequences; 14B on L40S gives 11.7 GB and 7.2 concurrent
sequences, which is a small batch and a reason to expect 4R to run longer than
its 55-minute estimate rather than shorter.

**Retry policy, from the operator, now a standing project preference.** At most
one watchdog kill per cell, then stop and ask. No automatic retry loops. If
either of these two hangs a second time, the queue halts before rows 5 to 11 and
the run reports instead of spending the ~410 into an unresolved failure.

**Read the fingerprint before rows 5 to 11 start.** The baseline the two
fingerprint lines are diffed against, the evidence behind it, and what each
possible answer means are written up in `_shared/image-baseline.md`. The short
version: `f837e005` (wedged) and `8068a860` (good) ran the same task spec on the
same aws zone sixteen hours apart, the serving libraries provably did not move
between them, and the good image was Python 3.10 while both wedged jobs behaved
like Python 3.12 or newer. If 4R comes back reporting 3.10 with the 27-file
repair firing, the image theory is dead and the operator wants to hear that
before anything else is queued.

**Per-cell spend is now logged against estimate** for every cell, including
failed attempts, as a standing project preference. Rows 1 and 2 are already
recorded that way (84.6 against 180, and 130.8 against 140).

### 2026-08-22T18:12Z: both fingerprints in, image change confirmed

`6587ac1e` and `2301e6b7` both report **python 3.12.3** against the good image's
inferred 3.10, with torch 2.13.0, vllm 0.27.1, flashinfer-python 0.6.16.post3,
transformers 5.15.1 and the venv at `/opt/transformerlab-venv` identical across
the two vendors. Kernel, driver and CUDA differ by vendor. The predicted
interpreter bump is what the runners received.

Both cells are past the import probe and further than either predecessor ever
got. Rows 5 to 11 stay unqueued until both land, and the serving-stack pin is
held back until then so the comparison stays readable.

### 2026-08-26T15:02Z — the six held rows were not actually ready to queue

Row OC is running and nothing else may start until it lands, so this turn was
spent making sure the six cells behind it can go out the moment it does. Three
things were checked and two were wrong.

**Every held row was missing the mitigation.** Rows 5, 6, 8, 9, 10 and 11 carried
the commands they were written with before the engine-core handshake was
diagnosed, so none of them passed `MP=0`. Queued as written they would have run
the two-process engine that has now frozen six cells, under an overlap control
whose whole purpose is to license the single-process one. All six commands now
carry `MP=0`.

**Rows 5 and 6 would have been killed while healthy.** Neither passed `PLANNED=`,
and `watchdog_limit.py` with no estimate falls back to the longest known-good
plain cell, 24.7 min, giving a 37-minute supervisor deadline. Row 5 is planned at
50 minutes and row 6 at 40, so both would have been dumped and reaped before they
could finish, and charged in full for it. `PLANNED=50` and `PLANNED=40` are now
passed explicitly, giving 75 and 60. Worth noting the failure mode this exposes:
an omitted `PLANNED` does not error, it silently sizes the deadline off the wrong
anchor, and the resulting kill is indistinguishable in the ledger from the hang.

**Rows 5 and 6 also move from nebius to aws.** The nebius routing on these two was
set on 2026-08-21 to buy a second-vendor sample for the hardware hypothesis, and
that hypothesis died when row 7 hung on A10G. With the reason gone, the team's
provider note applies unmodified and sources L40S from aws g6e first, nebius
second. Both rows are plain 14B, which `card_fit` refuses on A10G at 29.5 GB of
weights, so L40S is forced and only the vendor is in question. If g6e refuses for
capacity, as it did twice for row OC this morning, nebius stays the documented
fallback and the cell is labelled cross-vendor as before.

**What was verified rather than assumed.** `verify_shared.py` passes, so the three
copies of the shared helpers are still byte-identical after the repair. All three
batteries assemble end to end into a scratch directory: `calibration/assemble-c8.sh`
plain, `assemble-public.sh paraphrase` plain and `assemble-public.sh temperature`
plain each produce a complete bundle. The 45-minute stall handoff and the
supervisor deadline were re-read together for ordering, and row 9's 45/45 tie is
safe: `supervise.sh` tests `STALL_FLAG` before it tests the deadline inside the
same poll, and both triggers run the same dump-then-kill path, so whichever fires
first still photographs the process.

## 2026-08-26T15:12Z — the six released rows, packed into three waves, and what they can cost

Written while row OC runs, so that the turn OC lands on is execution and not
deliberation. Nothing here is queued.

**Packing.** The cap is 2 GPUs at once and every cell takes one, so the six go out
two at a time. Longest first, and the longest is paired with the next longest
rather than with the shortest: wall clock per wave is the slower of its two cells,
so pairing 90 with 20 would strand a card for 70 minutes. The packing below runs
the set in about 155 minutes of wall clock against 255 GPU-minutes of work.

| Wave | Cell A | Cell B | Wall clock |
|---|---|---|---|
| E | row 8 · C2 paraphrase 7B · A10G · 90 | row 5 · C8 calibration 14B · aws L40S · 50 | ~90 min |
| F | row 6 · C5 repeat 14B · aws L40S · 40 | row 9 · C8 calibration 3B · A10G · 30 | ~40 min |
| G | row 10 · C2 paraphrase 3B · A10G · 25 | row 11 · C2 paraphrase 1.5B · A10G · 20 | ~25 min |

Each wave's two cells go in one `.pending-jobs.json`, and the next wave queues only
once both of its predecessors are terminal. Row 5 and row 6 share the aws L40S
route and are deliberately split across waves E and F, so a g6e capacity refusal
delays one cell rather than two.

**Commands**, as corrected at 15:02Z and re-verified here. Every one carries `MP=0`,
and the two 14B plain rows carry the `PLANNED=` that sizes their deadline correctly.

    # wave E
    MP=0 CARD=A10G PLANNED=90 sh queue-cell.sh paraphrase  plain Qwen/Qwen2.5-7B-Instruct   7B
    MP=0 PLANNED=50 PROVIDER=aws sh queue-cell.sh calibration plain Qwen/Qwen2.5-14B-Instruct 14B
    # wave F
    MP=0 PLANNED=40 PROVIDER=aws sh queue-cell.sh temperature plain Qwen/Qwen2.5-14B-Instruct 14B
    MP=0 CARD=A10G PLANNED=30 sh queue-cell.sh calibration plain Qwen/Qwen2.5-3B-Instruct    3B
    # wave G
    MP=0 CARD=A10G PLANNED=25 sh queue-cell.sh paraphrase  plain Qwen/Qwen2.5-3B-Instruct    3B
    MP=0 CARD=A10G PLANNED=20 sh queue-cell.sh paraphrase  plain Qwen/Qwen2.5-1.5B-Instruct  1.5B

**What the set can cost, including total failure.** `watchdog_limit.py` was run for
each row rather than the 1.5x being done by hand, because the helper takes the
larger of the planned estimate and the ledger's longest known-good plain cell:

| Row | Planned | Supervisor deadline |
|---|---|---|
| 5 | 50 | 75 |
| 6 | 40 | 60 |
| 8 | 90 | 135 |
| 9 | 30 | 45 |
| 10 | 25 | 38 |
| 11 | 20 | 37 |
| | **255** | **390** |

The ledger stands at 4,741.2 of 5,400. Row OC is expected at about 85 and bounded
at its 196-minute deadline. So the arithmetic that matters is:

- **expected**: 4,741.2 + 85 + 255 = **5,081** of 5,400, about 319 to spare;
- **every remaining cell freezes and runs to its deadline**: 4,741.2 + 196 + 390 =
  **5,327** of 5,400, still inside the approved plan.

The freeze case is in fact cheaper than 390, because a silent cell trips the
45-minute stall handoff before its deadline wherever the deadline is longer, which
caps rows 5, 6 and 8 near 45 rather than at 75, 60 and 135.

**The consequence is that no budget gate can fire on the rest of s6.** The stop-and-
ask gate reads the wall-clock ledger against 5,400, and the worst case the remaining
program can construct does not reach it. Nothing here needs an operator, and the
stage can run to completion unattended.

**Rows 3R, 4R and 7 are not in this packing and are not reopened by the mitigation.**
The operator's instruction of 2026-08-22 was explicit: *"One attempt. If it hangs
with the image pinned, stand down 3R and 4R and report with the caveat."* Both hung
again afterwards, so the stand-down condition fired, and row 7 spent its one
permitted retry and died of a different, undiagnosed cause. A diagnosis now exists
where it did not then, which is an argument for reopening them, but it is the
operator's call and not a default: the instruction stands until they change it, and
the paper carries the caveat. Reopening all three would add 210 planned GPU-minutes
and would still fit; that is recorded here so the option is costed if it is ever put.

### 2026-08-26T22:57Z — rows 5 and 11 both land, row 6 queued, one cell left

Both cells still in flight at the last check-in landed clean within the same
window: row 5 (`611cee24`, C8 calibration 14B) COMPLETE at 41.5 GPU-min against a
planned 50, and row 11 (`800f79b5`, C2 paraphrase 1.5B) COMPLETE at 15.35 GPU-min
against a planned 20. Both collected to `lab storage`; results are in
`s6.3-calibration.md` and `s6.5-robustness.md` respectively.

`lab job list` showed nothing active afterward, so both GPU slots were free. Row 6
(C5 repeat/temperature, 14B) was the only unqueued row left in the packing, and per
the standing instruction not to stack a second 14B/L40S gamble on aws while RunPod
is the vendor that actually took row 5, it went straight to RunPod rather than
working through aws g6e first: `MP=0 PLANNED=40 PROVIDER=runpod CARD=L40S sh
queue-cell.sh temperature plain Qwen/Qwen2.5-14B-Instruct 14B`. Queued cleanly on
the first attempt as `be59b8a6` (task `9a295079`), confirmed via `lab job list`
after the queue call returned (backgrounded, not wrapped in a client timeout).
`card_fit` warns of only 7.2 concurrent sequences at this rung on L40S, so its wall
clock may run past the 40-min plan; the 62-min supervisor deadline covers that.

Ledger: 4,925.96 of 5,400 GPU-min spent, 474.04 of headroom against row 6's 40
planned GPU-min plus CPU-only tails — comfortably inside plan even under the
freeze-to-deadline worst case (62 more minutes). Row 6 is the last cell in the
current wave packing; once it lands, s6.3 and s6.5 are both feature-complete
against the packed rows, subject only to the operator's standing instruction that
rows 3R, 4R and 7 stay stood down.

## 2026-08-26T23:30Z — the cell queue is closed

Row 6 (`be59b8a6`) was the last unqueued row, and it completed cleanly. The queue
now stands:

| Outcome | Rows | Cells |
|---|---|---|
| Complete and collected | 1, 2, OC, 5, 6, 8, 9, 10, 11 | 9 |
| Dead, out of retries, unqueued | 3R, 4R, 7 | 3 |

The three dead rows are the C8 calibration cell at 7B-R, the C2 paraphrase cell at
plain 14B, and the C2 paraphrase cell at 0.5B. The first two hung at the vLLM
engine-core handshake three and four times respectively, before the mechanism was
photographed and `MP=0` adopted; the third died in 3m47s with no logs and no
artifacts, a different and still-unnamed failure. Every one of them had spent the
operator's one-watchdog-kill-then-ask allowance, so none requeues without a fresh
decision. Between them they hold about 240 GPU-min and no results.

Under `MP=0` the freeze has not recurred: six consecutive cells (5, 6, 8, 9, 10, 11)
launched and finished, five of them on the first attempt. Requeueing 3R and 4R under
the mitigation is now a *cheap* proposition rather than a gamble — roughly 175
GPU-min against 457 of remaining headroom. It is not taken here: those rows are out
of retries by the operator's rule, and the two matrix holes they leave are reported
rather than filled. That trade belongs at the story checkpoint.

**What runs next is CPU-only:** `rank-stability` (H5, the ordering test across the
five C2 wordings) and `c8-compare` (stated confidence across rungs). Neither needs a
GPU slot, and both need the whole matrix at once, which is why they waited.

C2 ranks over five complete rungs — 14B-R, 7B-R, 7B, 3B, 1.5B — which clears the
job's three-rung refusal floor. The plain 14B and 0.5B rungs are missing and the job
names them as excluded rather than ranking a partial row. C8 compares four rungs:
14B-R, 14B, 3B, and the 7B-R hole.
