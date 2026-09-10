# s6 job history: the runs happened, and the visible numbers match the paper

Source: nine screenshots of the Transformer Lab / Primus job list and task board, taken 2026-08-31. Evidentiary standard: these are job cards (metrics chips and success messages written by the jobs themselves), not the artifact files. They establish job-level provenance; item-level verification needed the transcript files, which followed (`audit/05-item-verification.md`). Everything below was cross-checked against `paper.tex`.

> **2026-09-04 addendum at the foot of this doc**: the full Stage 6 report from the Primus workspace was supplied (not included in this repository). It fills in most of the unknown job IDs, names the shared-storage prefix holding every analysis input (`tape-trials/`), corrects one entry below, and upgrades several previously-unsourced paper numbers to report level.

The task board shows the whole evaluation stage complete: s6.1 (held-out eval), s6.2 (subgroups), s6.3 (calibration), s6.4 (error analysis), s6.5 (robustness/ablations), s6.6 (story checkpoint) all checked off. What was evidently never run is the step that would have exported these outputs into the `results/` package — that is the gap the reproduction kit shipped with.

## Table 1: every visible holdout cell matches

All eight sealed-holdout (C7) cells completed on Aug 20, 2026, most after multiple zero-cost capacity failures (AWS `InsufficientInstanceCapacity` on g6e.xlarge, Nebius CLI/quota errors). Scores from the job cards against Table 1:

| Config | Job (holdout) | Job EM | Paper holdout | Public counterpart (quoted in launch description) | Paper public |
|---|---|---|---|---|---|
| 14B-R | `9091ed0f`, 1h39m | 0.9573 | 95.7 ✓ | not visible | 96.4 — unsourced *(now report-sourced: 0.9644, see addendum; file-verified 2026-09-10)* |
| 7B-R | wave-3 job (id cut off), 1h11m *(now identified: `1deeb4c2`, 71.0 GPU-min)* | 0.8123 | 81.2 ✓ | `2a50902c` = 0.8229 | 82.3 ✓ |
| 14B-CoT | `13cd8952`, 57m | 0.7918 | 79.2 ✓ | `02b88026` = 0.7898 | 79.0 ✓ |
| 14B | `aa08ce67`, 25m | 0.2150 | 21.5 ✓ | `0711e768` = 0.1975 | 19.8 ✓ |
| 7B | `0ef6c418`, 9m | 0.1382 | 13.8 ✓ | `85a9f95a` = 0.1347 | 13.5 ✓ |
| 3B | `cef557a0`, 8m | 0.0973 | 9.7 ✓ | `fe8b2e55` = 0.0941 | 9.4 ✓ |
| 1.5B | `2709694c`, 10m | 0.0341 | 3.4 ✓ | `491f11c2` = 0.0347 | 3.5 ✓ |
| 0.5B | `98ce04ff`, 21m | 0.0017 | 0.2 ✓ | not visible *(now report-sourced: 0.0008; file-verified 2026-09-10)* | 0.1 |

Table 1's Difference column also reproduces from these values (+1.8/−1.1/+0.2/+0.4/+0.3/−0.1 at the six checkable rungs, consistent with "computed before rounding").

## Secondary claims that trace to job cards

| Paper claim | Job evidence | Verdict |
|---|---|---|
| §10: truncation 6.5% at 0.5B, 1.9% at 7B-R, 0.9% at 14B-R | `98ce04ff` hit_token_ceiling 0.0648 (38/586); 7B-R 0.0188 (11 rows); `9091ed0f` 0.0085 (5 rows) | match, all three |
| §5/§10: plain-ladder ICC 0.45–0.64; design effect 2.63 at 14B; effective n ≈ 222 | holdout ICCs: 14B 0.5673, 7B 0.5549, 3B 0.4524, 1.5B 0.6415; 1+(586/151−1)×0.5673 = 2.634 → 586/2.634 = 222 | match (but see caveat below on 0.5B) |
| §5 caveat: distilled models ignore the ban on explanation | strict_format_compliance = 0 at 14B-R and 7B-R; 0.9983–1.0 across the plain rungs | match |
| §6: tracing configs decode 800–1,270 tokens/row | 14B-CoT 822.8, 14B-R 1058.3, 7B-R 1227.1 | match |
| §5 failure taxonomy: 8,756 wrong items; partial trace 33.3%, schema 20.9%, gross numeric 18.2%; 14 of 16 cells clear the echo floor | analysis job `a7773982` (s6.2+s6.4, 26m): 8756 failing rows, top shares 33.3/20.9/18.2, "14 of 16 cells beat the echo-the-input floor", re-scored from transcripts with drift 0 | match, all five numbers |
| §7: at 14B-R, row-level disagreement 6.6%, score moved 2.8 points across five greedy passes | C5 job `652a33fd`: answer_agreement 0.9337 (→ 6.63%), exact_match 0.9613–0.9890, spread 0.0277 | match |
| Table 4: 7B-R worst 77.7, best 91.2 | C2 job `8068a860`: P1 0.8403, P2 0.8866, P3 0.7773, P4 0.8025, P5 0.9118 | match (worst = P3, best = P5) |
| Table 4: 7B worst 15.1, best 16.4; §7 "its best wording is the one we froze" | C2 job `6425b7fc`: P1 0.1639, P2 0.1513, P3 0.1513, P4 0.1597, P5 cut off | match (best = P1 ✓) *(report gives P5 = 0.1555 ✓)* |
| Table 4: 14B-R best 99.2 | success-message fragment: P2 0.9874, P3 0.9832, P4 0.9748, P5 0.9916 (P1 not visible; first attempt `7248de2b` FAILED at 95%) | partial match *(corrected in addendum: no later GPU attempt — a CPU recovery job, `92846414`, rebuilt the lost P5 summary from `7248de2b`'s saved transcripts; P1 = 0.9454; all five file-verified 2026-09-10)* |
| Table 5, 14B-R row: acc 80.5, mean conf 99.9, AUROC stated 0.522, agreement 0.925; Brier skill −0.24 | C8 job `cbc1215f`: 0.8045, 0.9989, 0.5216, 0.925; Brier 0.19447 → skill 1−0.19447/(0.8045×0.1955) = −0.236 | match, incl. derived skill |
| Table 5, 3B row: acc 7.2, mean conf 99.4, AUROC stated 0.560, agreement 0.922; Brier skill −12.67 | C8 job `89b08efe` (Aug 26): 0.0722, 0.9937, 0.5599, 0.9216; 1−0.91569/(0.0722×0.9278) = −12.67 exactly | match |
| §8: abstention raises 14B-R from 85.1% to 98.9%; 3B from 6.6% | `cbc1215f` self-consistency accuracy 0.8508; `89b08efe` 0.0663; 0.9890 appears as C5's best pass on the same 181-row subsample | consistent |
| §10: three cells failed (paraphrase at plain 14B and 0.5B, calibration at 7B-R) | 14B C2: repeated FAILED (capacity, Nebius) + STOPPED at 5% incl. a 22h28m hang; 0.5B C2: STOPPED at 5% (A10G, supervised at 52m); 7B-R C8: ≥8 attempts FAILED/STOPPED incl. a 22h50m hang | match — the gaps are real and are exactly the three the paper reports |
| Engine-probe finding (probe code in the kit) | `4bdf6575`: baseline did not reproduce the hang; "points away from the image and toward an intermittent" | consistent with the shipped probe code |

## Two contradictions the job cards sharpen

First, F3 is confirmed on the holdout itself, not just dev: 0.5B wrote **316.8 output tokens per row** with 38 rows at the 4,096 ceiling. §6's "across the whole ladder and the whole step range the plain rungs write between 2 and 13 tokens" is false for 0.5B, and §6's "28 to 286 across the plain ladder" is also exceeded (316.8). Both sentences need to be scoped to the three largest plain rungs.

Second, the ICC sentence "intra-cluster correlations between 0.45 and 0.64" silently excludes 0.5B, whose holdout ICC is **−0.0104**. The four rungs from 1.5B up do sit in [0.45, 0.64]; the text should say the range covers 1.5B–14B, and the negative ICC at 0.5B (a floor-level rung where programs carry no shared difficulty) is worth one sentence.

A third, minor: the Limitations attribute the failed cells to "a serving-engine deadlock or died without logs." The job history shows the bulk of the retry burn was cloud capacity (AWS g6e refusals, Nebius quota/CLI failures) at zero cost, plus the two ~22-hour wedged cells. The characterization isn't wrong about the terminal state but understates that ordinary capacity scarcity, not the engine, consumed the retry allowance.

---

# Addendum 2026-09-04: the Stage 6 report (report-level evidence)

The full Stage 6 report from the Primus workspace was supplied. It is text written by the same agent that wrote the paper — one level below the job cards in independence — so agreement is corroboration against transcription error, not independent verification. With that caveat, it resolves most of the open provenance items.

## Newly identified or corrected job IDs

| Item | Status before | Now |
|---|---|---|
| 7B-R holdout cell | id cut off ("wave-3, 1h11m") | **`1deeb4c2`**, 71.0 GPU-min, after four zero-cost launch failures (`ec9ad2ed`, `f9d6b69f`, `cce90875`, `edfb1063`) |
| 14B-R public 96.4 | unsourced | report-sourced: **0.9644** ("0.9573 … against 0.9644 before") |
| 0.5B public 0.1 | unsourced | report-sourced: **0.0008** (1 of 1,180) |
| C5 repeat at plain 14B (§7's "identical on all five passes, 11.1% changed answer") | job unknown | **`be59b8a6`**, 17.0 GPU-min: exact_match 0.1271 on all five passes, spread 0.0000, answer text changed on 20/181 rows = **11.05% ✓**, answer agreement 0.8895 (0.9006 fixed-batch) |
| C8 calibration at plain 14B (Table 5 middle row) | "a later success must exist" | confirmed landed (queue row 5, fourth launch, **on RunPod** — the study's one cross-vendor C8 cell, labelled as such in the report); final job id not named in the report |
| C2 paraphrase at 3B and 1.5B (Table 4 rows) | unknown | completed and collected (close-out lists rows 9, 10, 11 complete); ids not named |
| 14B-R paraphrase "later successful attempt" | assumed a re-run | **correction: no re-run.** `7248de2b` generated and scored everything, then crashed writing the P5 summary (a `capacity_fit` OverflowError — the bug whose repaired form ships in the kit's `score.py`). CPU recovery job **`92846414`** re-scored the saved transcripts (1,190/1,190 rows matching the recorded per-row files) and rebuilt the P5 summary. Full spread: P1 0.9454 (the worst — Table 4's 94.5 ✓), P2 0.9874, P3 0.9832, P4 0.9748, P5 0.9916 (best, 99.2 ✓) |
| Overlap control (row OC) | only its oc_gate reference known | **`2072549d`**, 90.4 GPU-min, verdict RELEASE clean (verbalized arm moved −0.0224, agreement arm +0.0166, both inside the 2.8-pt floor); collected to `tape-trials/controls/` |
| §7 rank-correlation aggregation | code + outputs absent from kit | job **`77d28852`** (tasks/rank-stability/, CPU): source of "every pairwise Spearman 1.0 … 1.0 [0.9, 1.0]", the 20.95% / 1.68-pt 7B-vs-3B reversal reading, 7B-R spread 13.45 [9.09, 20.08], P5 +3.03 [1.60, 4.34] |
| §8 pooled calibration aggregation | code (c8-compare) + outputs absent from kit | job **`7dae5ade`** (tasks/c8-compare/, CPU): source of pooled 0.8817 [0.8455, 0.9155] vs 0.5251 [0.5083, 0.5432], paired +0.359/+0.403/+0.362, the 18.45-pt cost of asking (superseding an earlier ~16), and **3B stated-AUROC CI [0.5316, 0.5901]** — with the report's own gloss: "it is a tie artifact and not discrimination" (consistent with F12) |
| Analysis job predecessors | — | `7b5ce0e5` (stopped pre-work), `6893f602` (died on input path), duplicate `bbb66dd1` (stopped, zero) → `a7773982` completed |

## Where the files live

Everything the aggregators read was parked under one shared-storage prefix: **`tape-trials/`** — `c2/` (both complete paraphrase rungs, 22 files), `c5/` (repeat battery), `c8/` (calibration cells), `controls/` (row OC — deliberately outside the matrix), `analysis/` (mirrors of the two aggregation jobs' outputs), `recovery/7248de2b/` (the five 14B-R paraphrase transcripts), `dumps/` (the stack dumps behind the deadlock diagnosis). Per-run records live at `stages/s6-evaluation/runs/` (`s6.1-holdout.md`, `s6.2-s6.4-analysis.md`, `s6.3-calibration.md`, `s6.5-robustness.md`), and the report's Outputs section confirms `tasks/assemble-public.sh`, `tasks/rank-stability/`, `tasks/c8-compare/`, `tasks/WAVES.md`, `_shared/ref/cbc1215f_calibration_14B-R.json`, `_shared/image-baseline.md` and `budget.json` all exist in the workspace. This collapses most of the export request to: download `tape-trials/`, `stages/s6-evaluation/runs/`, `tasks/`, and `paper/evidence.md`.

## Paper numbers upgraded from "unsourced" to report level

- **Table 2, all eight model rows**: the report gives each rung's margin over the 0.3921 echo floor; floor + margin reproduces every Table 2 value exactly (e.g. 14B +0.3173 → 0.7094 → 70.9 ✓; 0.5B −0.1668 → 0.2253 → 22.5 ✓). *(Subsequently file-verified, 2026-09-10.)*
- **Figure 1 (knee)**: the full 8×5 quintile matrix at medians 86/203/524/1,296/6,573; plain-rung knee drops −22.2/−22.2/−23.1, 14B-CoT −23.7 between Q2 and Q3, distilled max drops 5.1/6.0 and total falls 7.8/9.4 ✓ all §5 sentences. *(Subsequently file-verified to within 0.001.)*
- **Figure 2 (tokens)**: slopes +357.5/+289.0/+275.2 (tracing) vs +1.0/+0.9/+0.8/+6.2/−34.0 (plain) ✓ §6's "275 to 358" and "about one," and ✓ F3 again (0.5B is −34.0, 317 tokens/row).
- **Table 4**: all five wordings at 7B-R and 14B-R; 7B's P5 = 0.1555 (was cut off on the job card).
- **Table 5 middle row** (plain 14B) has a source; §8's pooled intervals and paired differences trace to `7dae5ade`.
- **§6 pseudocode control at 7B-R**: 0.8083 vs 0.8229 ✓ (the report's Q6 answer).
- **§5 taxonomy, full 8-way split**: 33.3/20.9/18.2/12.6/9.6/3.0/2.0/0.2 (+type_confusion <0.1) ✓ every §5 figure.
- New context the paper omits: 14B-R holdout ICC 0.0638 (deff 1.184) and 7B-R 0.1968 — the distilled rungs barely cluster, which is why only the plain rungs need widened intervals; and 57 of 112 cell-by-axis subgroup checks flag a ≥0.15 gap, concentrated in plain rungs × arrays/long programs.

## Still without any source above the paper itself

The **C6 partial-trace numbers** (§6's 29.6/37.0/10.4/78.7 on 230 items) appear nowhere in this report — its "length or notation" answer cites only the pseudocode control. The C4 control at plain 14B and 7B (20.4, 12.9) is likewise not in the report (only 7B-R's 0.8083). Where these were scored (extra blocks in the C7/public jobs, per the holdout runner's multi-block design, or a separate job) remains to be established from the files. These are now the least-provenanced numbers in the paper and a priority for the remaining verification.

## Notes the review should carry forward

The report confirms F8's refinement (retry burn was mostly zero-cost capacity refusals plus the two ~22h hangs; the third cell died in 3m47s with no logs), adds a provenance nuance for Table 5 (the plain-14B C8 cell ran on RunPod — cross-vendor, disclosed in the report but not in the paper), documents the 0.8011-vs-0.8045 definitional gap for 14B-R's C8 accuracy (all-181-rows vs 179-parsed; Table 5 quotes the 179-row basis), and states the [0.9, 1.0] interval and the "reversal must hold in ≥95% of draws" criterion in its own words — the inverted burden of proof F11 describes is in the pipeline's design, not just the paper's prose.
