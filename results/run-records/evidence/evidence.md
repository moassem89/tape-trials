# Evidence ledger — s7.1 (p2)

Internal QA artifact. Every number in `paper.tex` must trace to a row here, and no
row may be written from memory: each one is copied out of a recorded project
artifact named in `source`. The paper ships standalone, so no ledger ids appear in
the LaTeX.

Built 2026-08-26. Sources walked in pipeline order: s6 report and its four run
files, s5 report and its run files, `budget.json`, s4 report and data card,
`overview.md`.

## A. Benchmark and corpus (s4)

| id | value | source | context |
|----|-------|--------|---------|
| E1 | 500 | stages/s4-data-preparation/report.md | distinct Ampliphi programs generated and admitted |
| E2 | 1,960 | stages/s4-data-preparation/report.md | released test items (program x input rows) |
| E3 | 22 to 18,941 | stages/s4-data-preparation/report.md | range of executed Varphi transitions per item |
| E4 | 60.2% / 9.9% / 29.9% | stages/s4-data-preparation/report.md | public / dev / private split shares, grouped on program_id so no program crosses a boundary |
| E5 | 1,180 | stages/s5-experimentation/report.md | rows in the public split, the iteration set |
| E6 | 586 rows, 151 programs | stages/s6-evaluation/runs/s6.1-holdout.md | sealed private holdout, evaluated once |
| E7 | 0.0% | stages/s4-data-preparation/report.md | echo-the-input strategy exact_match on the corpus (never correct) |
| E8 | 0.46% | stages/s4-data-preparation/report.md | all-zeros strategy exact_match on the corpus |
| E9 | 6 | overview.md | program categories: straightline, branching, bounded_loops, arrays, procedures, decision |
| E10 | 5 | overview.md | difficulty tiers by executed step count: T1 <=50, T2 51-200, T3 201-1,000, T4 1,001-5,000, T5 5,001-20,000 |
| E11 | 6 | overview.md | admission gates: halting, determinism (>=3 separate processes), optimizer agreement, >=1 changed variable, no same-variable binary operands, program-level discrimination |
| E12 | ampliphi==1.0.0, varphi-python==2.0.6 | overview.md | pinned, hash-verified toolchain producing the answer key |
| E13 | 240 of 240 | stages/s4-data-preparation/report.md | C4 matched-pseudocode control rows verified |
| E14 | 230 of 452 | stages/s4-data-preparation/report.md | C6 partial-trace probe rows verified (attempted 452) |
| E15 | 4 | stages/s4-data-preparation/report.md | duplicate (source, input) pairs found in EDA and deduped |
| E16 | dc99dfc1 | stages/s4-data-preparation/report.md | corpus build job id |
| E17 | 1,467,138 bytes / 1,964 rows | stages/s4-data-preparation/report.md | dataset.jsonl as built, before dedupe to 1,960 |

## B. Headline ladder, sealed holdout (s6.1 / C7 / C1)

All exact_match on E6 unless stated. "Public" is the paired s5 reading on E5.

| id | value | source | context |
|----|-------|--------|---------|
| E20 | 0.9573 | stages/s6-evaluation/runs/s6.1-holdout.md | 14B-R (DeepSeek-R1-Distill-Qwen-14B), frozen prompt, job 9091ed0f |
| E21 | 0.8123 | stages/s6-evaluation/runs/s6.1-holdout.md | 7B-R (DeepSeek-R1-Distill-Qwen-7B), frozen prompt, job 1deeb4c2 |
| E22 | 0.7918 | stages/s6-evaluation/runs/s6.1-holdout.md | 14B-CoT (Qwen2.5-14B-Instruct, C3_cot tracing prompt), job 13cd8952 |
| E23 | 0.2150 | stages/s6-evaluation/runs/s6.1-holdout.md | 14B (Qwen2.5-14B-Instruct), frozen prompt, job aa08ce67 |
| E24 | 0.1382 | stages/s6-evaluation/runs/s6.1-holdout.md | 7B (Qwen2.5-7B-Instruct), frozen prompt, job 0ef6c418 |
| E25 | 0.0973 | stages/s6-evaluation/runs/s6.1-holdout.md | 3B (Qwen2.5-3B-Instruct), frozen prompt, job cef557a0 |
| E26 | 0.0341 | stages/s6-evaluation/runs/s6.1-holdout.md | 1.5B (Qwen2.5-1.5B-Instruct), frozen prompt, job 2709694c |
| E27 | 0.0017 | stages/s6-evaluation/report.md | 0.5B (Qwen2.5-0.5B-Instruct), frozen prompt, holdout |
| E28 | 0.9644 / 0.8229 / 0.7898 / 0.1975 / 0.1347 / 0.0941 / 0.0347 / 0.0008 | stages/s6-evaluation/runs/s6.1-holdout.md; stages/s5-experimentation/runs/s5.5-detail.md | public-split counterparts of E20-E27 in the same order |
| E29 | -0.0071, -0.0106, +0.0020, +0.0175, +0.0035, +0.0032, -0.0006 | stages/s6-evaluation/runs/s6.1-holdout.md | holdout minus public for the seven collected pairs; five within half a point |
| E30 | 8 of 8 | stages/s6-evaluation/report.md | sealed comparisons reproducing their public reading |
| E31 | 1.75 points | stages/s6-evaluation/report.md | largest public-to-holdout discrepancy on the plain ladder |
| E32 | 57.7 points | stages/s6-evaluation/report.md | prompt effect at fixed 14B weights; derived: E22 - E23 |
| E33 | 21.3 points | stages/s6-evaluation/report.md | scale effect across the 28-fold plain ladder; derived: E23 - E27 |
| E34 | 28-fold | overview.md, stages/s6-evaluation/report.md | parameter ratio 0.5B to 14B |
| E35 | 0.0638, design effect 1.184 | stages/s6-evaluation/runs/s6.1-holdout.md | intra-cluster correlation across 151 programs, 14B-R holdout cell |
| E36 | icc 0.45 to 0.64, design effect 2.63 at 14B, effective n ~222 of 586 | stages/s6-evaluation/report.md | clustering on the plain ladder, which is why adjacent gaps are not separately significant |
| E37 | 3.2 to 7.7 points | stages/s6-evaluation/report.md | adjacent gaps inside the plain ladder |
| E38 | 1,058.3 tokens/row at 132.3 tok/s | stages/s6-evaluation/runs/s6.1-holdout.md | 14B-R holdout output length |
| E39 | 0.0068 parse failures (4 rows), 0.0085 hit the 16,384-token ceiling (5 rows) | stages/s6-evaluation/runs/s6.1-holdout.md | 14B-R holdout, both marginally above the public cell |

## C. Knee, tier and category structure (s6.2)

| id | value | source | context |
|----|-------|--------|---------|
| E40 | 86 / 203 / 524 / 1,296 / 6,573 | stages/s6-evaluation/report.md | median executed steps of the five exec-step quintiles |
| E41 | 0.992, 0.992, 0.941, 0.949, 0.914 | stages/s6-evaluation/report.md | 14B-R accuracy by quintile; no knee in range, max drop 5.1 pts |
| E42 | 0.872, 0.812, 0.822, 0.778, 0.778 | stages/s6-evaluation/report.md | 7B-R by quintile; no knee in range, max drop 6.0 pts |
| E43 | 0.983, 0.940, 0.703, 0.718, 0.615 | stages/s6-evaluation/report.md | 14B-CoT by quintile; knee at 203 -> 524 steps, -23.7 pts |
| E44 | 0.530, 0.308, 0.102, 0.051, 0.086 | stages/s6-evaluation/report.md | 14B by quintile; knee at 86 -> 203 steps, -22.2 pts |
| E45 | 0.359, 0.137, 0.034, 0.086, 0.077 | stages/s6-evaluation/report.md | 7B by quintile; knee at 86 -> 203 steps, -22.2 pts |
| E46 | 0.342, 0.111, 0.017, 0.017, 0.000 | stages/s6-evaluation/report.md | 3B by quintile; knee at 86 -> 203 steps, -23.1 pts |
| E47 | 0.137, 0.034, 0.000, 0.000, 0.000 | stages/s6-evaluation/report.md | 1.5B by quintile; knee at 86 -> 203, -10.3 pts |
| E48 | 0.009, 0.000, 0.000, 0.000, 0.000 | stages/s6-evaluation/report.md | 0.5B by quintile; never above floor |
| E49 | ~6,600 | stages/s6-evaluation/report.md | top of the tested executed-step range, above which neither reasoning model was measured |
| E50 | 0.989 -> 0.657 | stages/s6-evaluation/report.md | 14B-CoT tier accuracy T1-T2 -> T4-T5; labelled length-limited |
| E51 | 0.617 -> 0.073 | stages/s6-evaluation/report.md | 14B tier accuracy T1-T2 -> T4-T5; labelled length-limited |
| E52 | 0.014 -> 0.000 | stages/s6-evaluation/report.md | 0.5B tier accuracy T1-T2 -> T4-T5; the only rung labelled rule-limited |
| E53 | mixed at 7B and 3B; flat at 14B-R, 7B-R, 1.5B | stages/s6-evaluation/report.md | length-vs-rules labels for the remaining rungs |
| E54 | 1.000, 0.976, 0.983, 1.000, 0.840, 0.948 | stages/s6-evaluation/report.md | 14B-R by category (straightline, branching, bounded_loops, decision, arrays, procedures) |
| E55 | 0.975, 0.795, 0.767, 0.843, 0.630, 0.906 | stages/s6-evaluation/report.md | 7B-R by category, same order |
| E56 | 1.000, 0.988, 0.825, 0.898, 0.820, 0.260 | stages/s6-evaluation/report.md | 14B-CoT by category, same order |
| E57 | 0.544, 0.205, 0.467, 0.028, 0.070, 0.000 | stages/s6-evaluation/report.md | 14B by category, same order |
| E58 | 0.367, 0.060, 0.333, 0.056, 0.010, 0.000 | stages/s6-evaluation/report.md | 7B by category, same order |
| E59 | 0.342, 0.096, 0.167, 0.018, 0.000, 0.000 | stages/s6-evaluation/report.md | 3B by category, same order |
| E60 | 57 of 112 | stages/s6-evaluation/report.md | cell-by-axis checks flagging a subgroup gap >= 0.15, job a7773982 |
| E61 | 16 | stages/s6-evaluation/report.md | model-by-block cells re-scored with zero drift against recorded per-item files |

## D. Trivial-strategy floors (s6.2)

| id | value | source | context |
|----|-------|--------|---------|
| E65 | 0.3921 | stages/s6-evaluation/report.md | echo-the-input per-variable accuracy floor |
| E66 | 0.2825 | stages/s6-evaluation/report.md | all-zeros per-variable accuracy floor |
| E67 | +0.5906, +0.5248, +0.5233, +0.3173, +0.2538, +0.1847, +0.0705, -0.1668 | stages/s6-evaluation/report.md | per-variable margin over echo for 14B-R, 14B-CoT, 7B-R, 14B, 7B, 3B, 1.5B, 0.5B |
| E68 | 14 of 16 | stages/s6-evaluation/report.md | model-by-block cells clearing the echo floor; both 0.5B cells (0.2253 private, 0.2412 public) do not |
| E69 | 0.0147 to 0.9778 | stages/s6-evaluation/report.md | changed-variable accuracy, 0.5B to 14B-R; every rung above the zero floor by construction |

## E. Failure taxonomy (s6.4)

| id | value | source | context |
|----|-------|--------|---------|
| E70 | 8,756 | stages/s6-evaluation/report.md | failing rows pooled across all 16 cells |
| E71 | 33.3% | stages/s6-evaluation/report.md | partial_trace share of E70 |
| E72 | 20.9% | stages/s6-evaluation/report.md | schema_mismatch share |
| E73 | 18.2% | stages/s6-evaluation/report.md | gross_numeric share |
| E74 | 12.6% | stages/s6-evaluation/report.md | other_wrong_value share |
| E75 | 9.6% | stages/s6-evaluation/report.md | off_by_one_only share |
| E76 | 3.0% | stages/s6-evaluation/report.md | echoed_input share |
| E77 | 2.0% | stages/s6-evaluation/report.md | truncated share |
| E78 | 0.2% | stages/s6-evaluation/report.md | unparseable share |
| E79 | under 0.1% | stages/s6-evaluation/report.md | type_confusion share |
| E80 | under 3% | stages/s6-evaluation/report.md | refusal plus unparseable combined; derived from E76-E79 framing in the s6 headline |

## F. Tracing versus guessing (s6.4)

| id | value | source | context |
|----|-------|--------|---------|
| E85 | +357.5, +289.0, +275.2 | stages/s6-evaluation/report.md | reply-length slope in tokens per decade of log executed steps: 14B-R, 14B-CoT, 7B-R |
| E86 | +1.0, +0.9, +0.8, +6.2, -34.0 | stages/s6-evaluation/report.md | same slope for 14B, 7B, 3B, 1.5B, 0.5B |
| E87 | 2 tokens at 86 steps, 4 tokens at 6,573 steps | stages/s6-evaluation/report.md | plain 14B mean reply length at the extreme quintiles |
| E88 | 2 to 13 tokens | stages/s6-evaluation/report.md | reply-length range for the plain rungs under the frozen prompt across the whole step range |
| E89 | 174 tokens at Q1, 699 at Q5 | stages/s6-evaluation/report.md | the same 14B weights under the tracing prompt |
| E90 | 1,270 vs 28-286 | stages/s5-experimentation/report.md | output tokens per row, reasoning rung vs the plain ladder, public split |

## G. Notation control C4 and continuation probe C6 (s5.5)

| id | value | source | context |
|----|-------|--------|---------|
| E95 | 0.8083 (n=240, 61 programs) | stages/s5-experimentation/runs/s5.5-detail.md | 7B-R matched-pseudocode control, job dc983887, against a 0.8229 headline |
| E96 | 0.0000, 0.0208, 0.0417, 0.1292, 0.2042 | stages/s5-experimentation/runs/s5.5-detail.md | C4 control for 0.5B, 1.5B, 3B, 7B, 14B |
| E97 | 1.5 points | stages/s5-experimentation/runs/s5.5-detail.md | 7B-R C4 gap against its headline, inside noise on 240 rows |
| E98 | 0.0000, 0.0087, 0.1043, 0.2957, 0.3696 | stages/s5-experimentation/runs/s5.5-detail.md | C6 partial-trace probe for 0.5B, 1.5B, 3B, 7B, 14B (T4-T5 rows only) |
| E99 | 0.7870 (n=230) | stages/s5-experimentation/runs/s5.5-detail.md | 7B-R C6 probe, below its 0.8229 headline: being handed the early state buys it nothing |
| E100 | 0.0208 parse failures, 5 rows at the token ceiling, icc 0.0308, design effect 1.09, 1,251.0 tokens/row at 178.6 tok/s | stages/s5-experimentation/runs/s5.5-detail.md | 7B-R C4 block diagnostics |
| E101 | T4-T5 only | stages/s5-experimentation/runs/s5.5-detail.md | the C6 rows, which is why the plain-rung comparison against a full-split average understates the effect |

## H. Prompt-wording robustness C2 and the noise floor C5 (s6.5)

| id | value | source | context |
|----|-------|--------|---------|
| E105 | refuted (ordering identical under every wording) | stages/s6-evaluation/runs/s6.5-robustness.md | H5 verdict, job 77d28852, CPU-only 2m08s |
| E106 | 5 rungs x 5 wordings, 238 rows / 61 programs per cell | stages/s6-evaluation/runs/s6.5-robustness.md | the paraphrase matrix actually measured: 14B-R, 7B-R, 7B, 3B, 1.5B |
| E107 | 2,000 draws, seed 20260821 | stages/s6-evaluation/runs/s6.5-robustness.md | coupled program bootstrap resampling whole programs once and rebuilding the whole matrix |
| E108 | 1.0 | stages/s6-evaluation/runs/s6.5-robustness.md | every pairwise Spearman between wordings, and every Kendall tau-b |
| E109 | 1.0 [0.9, 1.0] | stages/s6-evaluation/runs/s6.5-robustness.md | each wording's Spearman against the frozen prompt, with bootstrap interval |
| E110 | 0 and 0 | stages/s6-evaluation/runs/s6.5-robustness.md | adjacent pairs reversed; reversals sustained under resampling |
| E111 | 10.5, 67.7, 5.04, 5.5 | stages/s6-evaluation/runs/s6.5-robustness.md | adjacent gaps under the frozen prompt: 14B-R/7B-R, 7B-R/7B, 7B/3B, 3B/1.5B, in points |
| E112 | 1.68 points, reverses in 20.95% of draws | stages/s6-evaluation/runs/s6.5-robustness.md | the 7B/3B gap under P3_tutorial |
| E113 | 2.10 points, reverses in 17.45% of draws | stages/s6-evaluation/runs/s6.5-robustness.md | the 7B/3B gap under P5_inverted |
| E114 | 0.0462 [0.0209, 0.0913] | stages/s6-evaluation/runs/s6.5-robustness.md | 14B-R wording spread, P1_frozen 0.9454 to P5_inverted 0.9916; does not clear the floor |
| E115 | 0.1345 [0.0909, 0.2008] | stages/s6-evaluation/runs/s6.5-robustness.md | 7B-R wording spread, P3_tutorial 0.7773 to P5_inverted 0.9118; the only rung clearing the floor |
| E116 | 0.0126 [0.0083, 0.0464] | stages/s6-evaluation/runs/s6.5-robustness.md | 7B wording spread, P2_reference_card 0.1513 to P1_frozen 0.1639 |
| E117 | 0.0210 [0.0166, 0.0581] | stages/s6-evaluation/runs/s6.5-robustness.md | 3B wording spread, P1_frozen 0.1134 to P3_tutorial 0.1345 |
| E118 | 0.0252 [0.0041, 0.0628] | stages/s6-evaluation/runs/s6.5-robustness.md | 1.5B wording spread, P1_frozen 0.0588 to P3_tutorial 0.0840 |
| E119 | 0.0663 | stages/s6-evaluation/runs/s6.5-robustness.md | serving-noise floor: row-level answer disagreement from the 14B-R C5 cell (agreement 0.9337) |
| E120 | 0.1105 | stages/s6-evaluation/runs/s6.5-robustness.md | plain-14B answer disagreement from the row-6 C5 cell; the floor is not uniform across the ladder |
| E121 | +3.03 points [1.60, 4.34] | stages/s6-evaluation/runs/s6.5-robustness.md | P5_inverted averaged over rungs under the coupled resample; the only wording whose interval excludes zero |
| E122 | +1.60 [-0.17, 3.25], +0.17, +0.08 | stages/s6-evaluation/runs/s6.5-robustness.md | P2_reference_card, P3_tutorial, P4_formal_rules against frozen; all straddle zero |
| E123 | 0.9337 agreement, 0.989 canonical-order only | stages/s6-evaluation/report.md | C5 five-pass repeat at 14B-R, job 652a33fd, 181 rows / 46 programs |
| E124 | 0.9613 to 0.9890, spread 0.0277, 12 rows changed | stages/s6-evaluation/report.md | C5 exact_match across the five identical passes at 14B-R |
| E125 | 0.1271 on all five, 20 of 181 rows changed answer | stages/s6-evaluation/report.md | the row-6 C5 repeat cell at plain 14B: identical score, moving text |
| E126 | 2 | stages/s6-evaluation/runs/s6.5-robustness.md | paraphrase cells missing from the matrix (plain 14B and 0.5B), named in missing_cells |

## I. Calibration C8 (s6.3)

All three cells are 181 rows over 46 programs behind one weight load.

| id | value | source | context |
|----|-------|--------|---------|
| E130 | 3 of 4 | stages/s6-evaluation/runs/s6.3-calibration.md | calibration cells measured: 14B-R, 14B, 3B; 7B-R died and stays a hole |
| E131 | 0.0722 / 0.1326 / 0.8045 | stages/s6-evaluation/runs/s6.3-calibration.md | accuracy within the confidence-eliciting condition at 3B / 14B / 14B-R |
| E132 | 0.9937 / 1.0000 / 0.9989 | stages/s6-evaluation/runs/s6.3-calibration.md | mean stated confidence at 3B / 14B / 14B-R |
| E133 | 4 / 1 / 2 | stages/s6-evaluation/runs/s6.3-calibration.md | distinct confidence values emitted across 181 rows at 3B / 14B / 14B-R |
| E134 | 0.0 | stages/s6-evaluation/runs/s6.3-calibration.md | Murphy resolution at all three rungs, to five decimal places |
| E135 | -12.665 / -6.542 / -0.236 | stages/s6-evaluation/runs/s6.3-calibration.md | Brier skill against the base rate at 3B / 14B / 14B-R; negative everywhere |
| E136 | 0.5599 [0.5316, 0.5901] / 0.5000 [0.5000, 0.5000] / 0.5216 [0.4880, 0.5633] | stages/s6-evaluation/runs/s6.3-calibration.md | verbalized-confidence AUROC at 3B / 14B / 14B-R |
| E137 | 1.11% vs 7.22% | stages/s6-evaluation/runs/s6.3-calibration.md | 3B accuracy on its most-confident half vs overall; why its AUROC interval is a tie artifact |
| E138 | 13.33% vs 13.26%, 81.11% vs 80.45% | stages/s6-evaluation/runs/s6.3-calibration.md | the same most-confident-half test at 14B and 14B-R; no gain anywhere |
| E139 | 0.8588 [0.7148, 0.9430] / 0.9250 [0.8352, 0.9813] / 0.9216 [0.8100, 0.9940] | stages/s6-evaluation/runs/s6.3-calibration.md | self-consistency AUROC at 14B / 14B-R / 3B, majority-of-5 at temperature 0.8 |
| E140 | +0.3588 [0.2148, 0.4430] / +0.4033 [0.3117, 0.4717] / +0.3617 [0.2526, 0.4405] | stages/s6-evaluation/runs/s6.3-calibration.md | paired self-consistency minus verbalized AUROC at 14B / 14B-R / 3B; all exclude zero |
| E141 | 0.5251 [0.5083, 0.5432] over 540 rows | stages/s6-evaluation/runs/s6.3-calibration.md | pooled verbalized AUROC, clustered on (rung, program) |
| E142 | 0.8817 [0.8455, 0.9155] over 543 rows | stages/s6-evaluation/runs/s6.3-calibration.md | pooled self-consistency AUROC, same clustering |
| E143 | 12.15% -> 21.11%, 6.63% -> 13.33%, 85.08% -> 98.89% | stages/s6-evaluation/runs/s6.3-calibration.md | accuracy after abstaining on the half of rows where five samples disagree most, at 14B / 3B / 14B-R |
| E144 | 0.7894 [0.5186, 0.9903] / 0.8065 [0.6552, 0.9144] / 0.6307 [0.5067, 0.7448] | stages/s6-evaluation/runs/s6.3-calibration.md | AUROC of exec_steps, a difficulty reference the model never sees, at 3B / 14B / 14B-R |
| E145 | 3 separable, 2 with signal available and unreported | stages/s6-evaluation/runs/s6.3-calibration.md | the job's rolled-up reading; kills the "unrankable pool" explanation |
| E146 | 0.1381 [0.0769, 0.2079] / 0.9890 [0.9722, 1.0000] / 0.0884 [0.0385, 0.1534] | stages/s6-evaluation/runs/s6.3-calibration.md | accuracy on the same 181 rows without the confidence request, at 14B / 14B-R / 3B |
| E147 | 0.55 / 18.45 / 1.62 points | stages/s6-evaluation/runs/s6.3-calibration.md | cost of asking for a confidence statement at 14B / 14B-R / 3B; derived: E146 - E131 |
| E148 | 0.0146 | stages/s6-evaluation/report.md | correlation between stated confidence and sampling agreement at 14B-R |
| E149 | 0.09392 vs 0.12692 base rate, AUROC 0.925, gap -0.1293 | stages/s6-evaluation/report.md | 14B-R self-consistency Brier and its under-confident direction, job cbc1215f |
| E150 | 8-fold | stages/s6-evaluation/runs/s6.3-calibration.md | accuracy range spanned by the three calibration rungs, 7% to 80% |

## J. Compute and provenance

| id | value | source | context |
|----|-------|--------|---------|
| E155 | 4,942.96 of 5,400 GPU-min | budget.json | final project spend against the approved plan, 457.04 unused |
| E156 | 106 | budget.json | ledger entries (jobs and launch attempts) recorded |
| E157 | 839.3 GPU-min | stages/s5-experimentation/report.md | s5 closing spend, of which 736.9 in s5 and 102.4 in the s4 build jobs |
| E158 | 3 | stages/s6-evaluation/report.md | cells never measured: C2 at 0.5B, C2 at plain 14B, C8 at 7B-R |
| E159 | ~240 GPU-min | stages/s6-evaluation/tasks/WAVES.md | spend on the three dead cells, which returned no result |
| E160 | 4 models unreachable | stages/s5-experimentation/report.md | no key for ChatGPT, Gemini or DeepSeek; the stored Claude key is not an Anthropic key. The study runs open-weight only |
| E161 | L40S:1 and A10G | stages/s6-evaluation/report.md; stages/s5-experimentation/report.md | the two card types used; every paired public/holdout cell matched card, provider, prompt, decoding and token ceiling |
| E162 | 16,384 | stages/s6-evaluation/runs/s6.1-holdout.md | output token ceiling on every cell |
| E163 | VLLM_ENABLE_V1_MULTIPROCESSING=0 | stages/s6-evaluation/report.md | the mitigation adopted after the serving-engine deadlock was photographed |
| E164 | 56 | stages/s2-research-summary/notes/ | literature notes carried out of s2 |
| E165 | tape-trials-exp-20260820 | experiments.json | the Transformer Lab experiment holding every job in this study |

## K. Derived figures the paper states

| id | value | source | context |
|----|-------|--------|---------|
| E170 | 57.7 vs 21.3 points | derived: E32, E33 | prompting at fixed weights against 28-fold scale; the paper's central contrast |
| E171 | ~275x to ~358x | derived: E85 / E86 | reply-length slope ratio, tracing configurations against plain rungs |
| E172 | 6.1x | stages/s5-experimentation/runs/s5.5-detail.md | reasoning-vs-plain headline contrast at matched 7B parameter count, public split |
| E173 | 17.5 points | stages/s5-experimentation/report.md | reasoning-tuned 14B over tracing-prompted plain 14B at the same size and similar words written |
| E174 | 77% | stages/s5-experimentation/report.md | share of the plain-to-reasoning distance at 14B closed by the tracing prompt alone, public split |
| E175 | 5 rungs, not 7 | derived: E106, E126 | the paraphrase ladder actually tested |

## L. Gaps the ledger cannot fill

Recorded so the paper does not state them and p5 can check it did not.

| id | claim the paper may not make | why |
|----|------------------------------|-----|
| G1 | any wording result for plain 14B or 0.5B | their C2 cells died and were not retried (E126) |
| G2 | any calibration result for 7B-R | its C8 cell died (E130) |
| G3 | a per-rung serving-noise floor for 7B, 3B or 1.5B | only two C5 cells exist (E119, E120) |
| G4 | separate significance for each adjacent gap in the plain ladder | clustering leaves effective n near 222 (E36, E37) |
| G5 | any hosted frontier-model comparison | no usable credentials (E160) |
| G6 | a knee for either reasoning model | none inside the tested range, which stops near 6,600 steps (E41, E42, E49) |
| G7 | that P5_inverted is optimal | only five wordings were tested and only one clears zero (E121, E122) |

## M. Rows added during p3 drafting (verified against source records)

| id | claim | value | source |
|---|---|---|---|
| E176 | median Ampliphi source length by tier T1-T5 | 12, 13, 17, 17, 16 lines, while median executed steps over the same tiers spans three orders of magnitude | s4 report.md ("The difficulty axis is not a proxy for program length") |
| E177 | 0.5B holdout minus public difference (derived from E27, E28) | 0.17% - 0.08% = +0.1 pts | derived |
| E178 | per-variable accuracy = echo floor (E65) + margin (E67) | 14B-R 98.3, 14B-CoT 91.7, 7B-R 91.5, 14B 70.9, 7B 64.6, 3B 57.7, 1.5B 46.3, 0.5B 22.5 | derived; 0.5B value 22.5 confirmed against E68's 0.2253 |
| E179 | C5 14B-R cell (`652a33fd`) | exact_match 0.9613-0.9890 across five greedy passes, spread 0.0277; answer agreement 0.9337 (row-level disagreement 6.63%); 12 of 181 rows changed verdict | s6.5-robustness.md C5 table |
| E180 | C5 plain-14B cell (wave F row 6) | exact_match 0.1271 on all five passes, spread 0.0000, 0 of 181 rows changed verdict; answer agreement 0.8895 (disagreement 11.05%), 20 of 181 rows changed answer; fixed-batch replay 0.9006 | s6.5-robustness.md row-6 block |
| E181 | knee table max ADJACENT-quintile drop (not Q1-to-Q5) | 14B-R 5.1 pts, 7B-R 6.0 pts; Q1-to-Q5 falls are 7.8 and 9.4 pts; quintile median workload 86 to 6,573 steps is a factor of 76 | s6 report.md Q2 table |
| E182 | regime separation width | 58 to 96 points | s6 report.md Q1 |
| E183 | C2 per-wording extremes, all five rungs | 14B-R P1_frozen 0.9454 / P5_inverted 0.9916; 7B-R P3_tutorial 0.7773 / P5_inverted 0.9118; 7B P2_reference_card 0.1513 / P1_frozen 0.1639; 3B P1_frozen 0.1134 / P3_tutorial 0.1345; 1.5B P1_frozen 0.0588 / P3_tutorial 0.0840 | s6.5-robustness.md spread table |
| E184 | P5_inverted helps four of five rungs; 7B's best wording is the frozen one | see E183 | s6.5-robustness.md |
| E185 | prompt-compliance caveat: both distilled models ignore the frozen prompt's ban on explanation, so the frozen-prompt column mixes two variables; the controlled contrast is plain 14B under the CoT prompt against the two distilled rungs | qualitative | s5 report.md, "Next steps" |
| E186 | the three tracing configurations (14B-CoT, 7B-R, 14B-R) all decode 800-1,270 output tokens per row | 800-1,270 | s5 report.md, "Next steps"; upper end corroborated by E90 |
| E187 | plain ladder output tokens per row, public split | 28 to 286 | s5 report.md L710 (same sentence as E90) |
| E188 | output-token ceiling by configuration | plain ladder 4,096 tokens / 8,192 context; 14B-R, 7B-R and 14B-CoT 16,384 / 20,480; matched within each paired public-holdout reading, not across configurations | s5 tasks/detail/task.c1.yaml, task.c1r.yaml, task.c1rc.yaml; s6 tasks/holdout/task.{plain,reason,cot}.yaml; s6.1-holdout.md |
| E189 | holdout truncation rates (rows hitting the ceiling, scored as failures) | 0.5B 38 rows (6.48%), 7B-R (1.88%), 14B-R 5 rows (0.85%), one plain cell 2 rows (0.34%), zero elsewhere | s6.1-holdout.md |
| E190 | 0.5B is the most verbose plain rung | 316.8 output tokens/row against 34.4 at 3B | s6.1-holdout.md |
