# Session 2026-10-24 — export verification, citations, and the revised manuscript

Mohammad asked for a ready-to-submit paper and authorised use of his computer and browser. This session (1) retrieved the full Primus run-record export, (2) closed every "not yet examined" item in the findings index except the from-the-spec oracle, (3) verified all citations (`claude/review-citations.md`), and (4) produced a revised manuscript on the TMLR template (`claude/paper-revision/`).

## Primus state (checked in the browser pane, 13:30 local)

Project `tape-trials` is Running/idle. Stage s8 (operator-directed extension, 2026-10-12): s8.1 export **done**; s8.2 CPU corrections **done**; s8.3 GPU cells **blocked on two operator answers** — (i) does GPU time bill to credits, (ii) raise the 457 GPU-min headroom or cut (its costed cells total 553–636; its own priority list puts permission-only control → Qwen3-14B thinking on → R1-0528-8B → thinking off at 230 GPU-min). Not answered on Mohammad's behalf: it commits spend. Nothing in the revised paper depends on s8.3.

The export (`tape-trials-export.zip`, 284 files, 6.1 MB, contains the sealed holdout) was downloaded from the Primus project's Downloads page. Keep it private.

Primus's s8.2 report, checked: its "189, 259, 286 words per decade" are the **public** split per-row slopes; they do not correct the holdout figure. Its "knee got stronger excluding loops" is right for 7B-R (see F18).

## Number verification from the export (closes F1's remaining list)

Independent agent recomputed from per-row files and transcripts, re-running the released analysis code (`rank-stability`, `c8-compare`, the analysis job's `classify`) with a stub for the platform SDK; the main reviewer spot-checked the three load-bearing items (C4/C6 matched baselines, control job cards, C8 per-row files) and they hold.

| Item | Paper | Recomputed | Verdict |
|---|---|---|---|
| Table 4 7B-R spread | 13.5 | 13.45 (32/238) → 13.4 | twice-rounded; also abstract, intro, §7, Discussion |
| Table 4 3B best | 13.5 | 13.45 → 13.4 | twice-rounded |
| Table 4 7B, 1.5B, all CIs | — | exact (seed 20260821) | reproduces |
| §7 7B-R→7B gap | 67.7 | 67.65 → 67.6 | twice-rounded |
| §7 7B/3B reversal 21% / 17%; best paraphrase +3.0 [1.6, 4.3] | — | 20.95% / 17.45%; +3.03 [1.60, 4.34] | reproduces |
| Repeat battery 14B-R 6.6%, 2.8 pts | — | 12/181, 2.76 | reproduces |
| Repeat battery plain 14B 11.1% | 11.1 | 20/181 = 11.05 → 11.0 | twice-rounded; "stricter 6.6%" is the *smaller* rate |
| Table 5 3B, 14B rows | — | exact from transcripts | reproduces |
| Table 5 14B-R accuracy | 80.5 | 144/179 = 80.45 → 80.4 | twice-rounded; **run cbc1215f has no per-row file or transcripts** — only a summary; the only 14B-R per-row/transcripts are the overlap re-run 2072549d (newer image): 78.2 / AUROC 0.493 / 0.892 |
| Cost of asking 18.5 | 18.45 | different denominators (181 vs 179); matched rows 18.2–19.3 (two unparsed rows unknown); re-run 21.0; 14B 0.55, 3B 1.66 | **misstated; "item sets line up exactly" false** |
| 3B "most confident half 1.1%" | — | tie-order artifact; 8.2% expected (2.2–13.3) under random tie-break | reword |
| §8 pooled AUROCs, paired diffs, abstention, step AUROCs | — | exact | reproduces |
| **C4 pseudocode control** | "moves 0.6–1.5 pts" | same-row Ampliphi baselines 76.67 / 17.50 / 11.25 / 7.08 → effects +4.2 / +2.9 / +1.7 / −2.9 (3B C4 = 4.17 omitted by paper); 7B-R paired CI [−3.3, 12.1] | **wrong baseline (full-split average)** |
| **C6 "partial-trace" probe** | "roughly doubles", "first half of a trace" | plain rungs 0/230 on the full items; probe gives the machine state at a cut + only the remaining statements (suffix share 0.01–0.85, median 0.37; median 802 vs 3,149 steps); step-matched public baselines 11.8 / 8.5 / 5.1 | **misdescribed and wrong baseline; confounded with less work** |
| Plain-rung C4/C6 scores | 20.4/12.9; 37.0/29.6/10.4 | job-card aggregates only (job 0711e768 etc.) | not row-verifiable |
| §5 failure shares 33.3/20.9/18.2/12.6/9.6/3.0/2.0/0.2 | — | exact via released `classify` | reproduces, but "schema violation" is 80% 0.5B (wrong key set, not parse failure) and "partial trace" is 90% plain rungs that do not trace — label misleads |
| Figure 2 slopes 357.5/289.0/275.2/… | — | five-point OLS on quintile means (rounded) vs log10 quintile median — reproduces exactly | method unstated; per-row holdout OLS: 338.8 [196.7, 522.3] / 268.6 [216.6, 325.1] / 251.2 [119.5, 383.9]; plain 1.0/0.9/0.8; 1.5B 5.3; 0.5B −28.9 |
| "800 to 1,270 output tokens" | — | holdout sampler telemetry 822.8–1,227.1 | 1,270 unsourced |

## New findings

**F18. 7B-R has an early drop the paper hides — required revision.** (a) "Neither distilled model has a knee" is true for 14B-R only. 7B-R's Q1 is depressed by zero-iteration bounded loops (13/24 correct; all failures at 32 steps; transcripts show it executing the body once despite a false guard, plus one correct answer lost to malformed JSON). Excluding loops, 7B-R falls 16.3 points Q1→Q2 (cluster bootstrap [6.9, 26.0]); the drop coincides with a shift toward branching items, its weakest category, so step count vs category is not separable. (b) Touches the knee claim, not the headline. (c) Fixed in the revision (§5 "Knees").

**F19. The two mechanism controls used the wrong baseline — required revision, the most consequential finding of this session.** See the C4/C6 rows above. "Unfamiliar notation is not the cause" survives in weakened form (effects −2.9 to +4.2; no regime change). "Carrying state is the cause" does not survive as stated: the probe removes most of the work. Fixed in the revision (§6 rewritten: "not the main obstacle"; "the work, not the rules, defeats the plain rungs").

**F20. Within-tier categories (closes F2's analysis ask).** Holdout, T3 (all six categories) and T4–T5 (four): tracing-prompt procedure deficit survives (26.2% T3, 25.9% T4–T5 vs ≥69.5% elsewhere); distilled-models-weakest-on-arrays survives at T4–T5 (83.3, 63.0); plain-rung "procedures hardest" does not (near zero on arrays/decision/procedures alike); loops shortcut strong (plain 14B 27.1% on T4–T5 loops vs 0.0 on every other T4–T5 category). Now Table 2 of the revision.

## Venue decision

Target: **TMLR** — rolling, correctness-over-novelty, 12-page main body (revision's body ends p.10), preprints allowed. TMLR FAQ: LLM use must be disclosed in a first-page footnote, and "the ideas, claims and results found in submissions are human-sourced". The study concept and design are Mohammad's; the experiments and first draft are Primus's; every number is now human-verified. That is defensible but is exactly the boundary the clause is about — **recommend emailing the TMLR editors-in-chief before submitting**, describing the provenance, rather than letting an action editor discover it. ICLR's policy (human author accountable, full disclosure) is compatible; ICLR 2027's deadline has passed. NeurIPS D&B 2026 has passed.

## The revised manuscript

`claude/paper-revision/main.tex` + `references.bib` + `figures/make_figures.py` (recomputes both figures from per-item holdout records; nothing copied from evidence.md). Changes against the Primus draft are listed in its Appendix A ("Corrections relative to the agent's draft"). Credit: Varphi → Hassan El-Sheikha alone; AmpliPhi → El-Sheikha, Thevara, Abouzied (UofT compilers course), both as cited software. Disclosure footnote on p.1; provenance table in Appendix A; no watermark.

## Independent cold review (Fable-tier agent, no access to audit notes) — verdict: major revision, then likely accept

It recomputed >100 values (nearly all exact) and found five things that changed the paper. Each was re-verified here before acting:

**F21. Parser defect — required revision (would be rejection-level uncorrected). Verified and fixed.** `parse.py` finds "the last balanced top-level `{…}`" by brace depth; an unmatched `{` quoted in a `<think>` block (e.g. `while (h) {`) keeps depth ≥1 for the rest of the reply, so the final answer object is never found → scored `truncated`/`bad_json`. Re-scoring every exported transcript with a corrected extractor (text after the last `</think>` first; objects found by `json.JSONDecoder.raw_decode` from every `{`; otherwise the released logic) changes **61 verdicts, all upward, all `finish_reason=stop`, all answers taken from after the reasoning block, zero downgrades, zero changes for any plain rung or 14B-CoT**. Cells: 7B-R holdout 81.23→82.59, public 82.29→83.73; 14B-R public 96.44→96.86 (holdout unchanged 95.73); 7B-R paraphrase P1 84.03→85.71, P3 77.73→83.61; 14B-R P1 94.54→95.38; each 14B-R repeat pass +1 row. Consequences: 7B-R paraphrase spread 13.4→**10.5 [6.0, 16.5]**, now *equal to* (not larger than) the 9.7-point 14B-R gap — a headline-2 sentence falls; best paraphrase +3.0→+2.7 [1.3, 4.0]; 14B-CoT vs 7B-R gap 2.0→3.4 [−2.6, 9.8]; 7B-R excluded-loops drop 16.3→14.3 [5.1, 23.3]; 14B-R no-request accuracy on the C8 rows 98.9→99.4 (six-pass mean 98.4). Confidence battery: 3B and 14B unaffected; 9 of 905 agreement samples in the 14B-R re-run affected. Scripts: `claude/paper-revision/reanalysis/`. **The kit's `parse.py` and `verification/rescore_transcripts.py` targets must be updated before the artifact is mirrored.**

**F22. Title/headline asymmetry — required revision (framing). Accepted.** "Elicitation outweighs scale" compares a prompt effect at 14B with a scale effect measured only under the prompt that suppresses the capability; no small-model tracing cell exists. Retitled ("How a No-Explanation Prompt Hides Execution Ability…"); abstract, §6, Limitations rewritten; headline CIs added: 57.7 [51.4, 63.7], 21.3 [16.4, 26.7]. Cheapest strengthening: 0.5B/3B/7B under the tracing prompt on the public split (a 2×2) — a better use of Primus credits than any new model.

**F23. The step axis conflates magnitude, statement count and composition — required revision. Verified.** Q1 is 36% straightline / 48% single-changed-variable items vs Q2 19% / 4%; straightline plain-14B accuracy by step tercile 92.3 / 69.2 / 3.7 (fixed statements, magnitude only). Added the design's natural test — **within-program, smallest vs largest input (149 programs, median 19.2× steps)**: 14B-R −4.7 [0.0, 9.4], 7B-R −0.7 [−8.1, 8.7], 14B-CoT −12.1 [4.0, 19.5], 14B −10.1 [4.0, 16.8], 7B −2.7 (ns), 3B −8.7 [3.4, 14.1]. Plain rungs' small-input accuracy is already ~27%, so most of their quintile "knee" is composition. Now Table 2 of the revision.

**F24. Procedure failure is a trace-order error. Verified.** 94/96 14B-CoT holdout procedure transcripts start by executing helper bodies in file order (71 wrong); the 2 starting at `main` are right. Plausibly induced by the tracing prompt's "one statement at a time". Replaces the "source-level indirection" sentence.

**F25. Missing primary citation and an earlier contamination date. Verified.** "Varphi: A Description Language for Turing Machines", Hassan El-Sheikha and Mohammad A. Mahmoud (University of Toronto), WCCCE '25, Calgary; UTM news 2 May 2025. Varphi's public description dates to WCCCE, 28–29 April 2025, not 31 Aug 2025 — still after Qwen2.5 (Sep 2024) and R1-Distill (Jan 2025), so the argument holds. 

Also adopted: suffix-probe composition (115 arrays / 111 procedures / 4 decision → the 0/230 is near-guaranteed by selection) and the matching rule stated (±0.15 decade; +category-matched 4.9/0.3/0.3); the pseudocode control renders clamping explicitly (easier, strengthens the claim); T1 bounded loops are 80 items all at 32 steps with a false guard; plain-rung replies are bare JSON (585/586, 586, 586, 584/586), replacing the near-degenerate word-count framing; agreement and stated-confidence arms differ in prompt (verified from transcripts); 3B tie range 0–14.4%, expectation 8.1%; 14B-R total fall 7.7; truncation labels from `finish_reason`; Brittlebench "63% of cases"; Bogavelli takes no position in the flaw/artifact debate. Not adopted: the reviewer's claim that all 1,960 keys reproduce under its own from-spec interpreter — its code was not seen, so it is not cited.

## Deliverables (2026-10-24)

`claude/paper-revision/` — main.tex (`\anontrue` = TMLR double-blind; `\anonfalse` = preprint), references.bib, figures/make_figures.py (reads corrected per-item records), reanalysis/ (corrected parser and the scripts that produced every changed number). PDFs were sent in the conversation.

## Status after this session

The revised paper (in `paper/`) addresses every finding above. On 2026-10-24 the parser
fix, the corrected verification targets, the public run records and the corrected
per-item files were added to this repository. Remaining before submission: the venue's
double-blind supplementary package and a note to the editors on the study's AI
provenance. Optional strengthening of F22: run the tracing prompt at 0.5B, 3B and 7B on
the public split.
