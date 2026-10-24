# Citation verification (session 3, 2026-10-24)

All 33 references cited in paper.tex (the .bib holds 52; 19 are uncited and do not print) were checked by three parallel reviewers against arXiv listings, PDFs and HTML pages, with a fourth pass re-reading five entries whose first verdict rested on memory. arXiv abs pages were intermittently blocked in the sandbox, so existence for some entries rests on search listings; every 2026 ID was confirmed against fetched text. Citing sentences were checked in full (an extraction bug truncated them at the dot inside arXiv IDs in the first pass; corrected before final verdicts).

**Headline: nothing is fabricated. All 33 IDs exist with matching titles. Nine citations are misattributed or materially overstated and must be reworded or replaced; about ten carry metadata or version slips.** As defects, the misattributions are a required revision, not rejection-level — but two of them sit in the sentences that position the paper against its three named competitors, which a reviewer from that line of work would catch at once.

## Misattributions (must change)

| Key | Paper says | What the work actually shows | Fix |
|---|---|---|---|
| 2502.11167 SURGE | accuracy "rising at its hardest coding-complexity tier, because models answer such items end to end"; its axis "inverts at its hardest tier" | §5.2 notes a slight uptick at the top level for some models and *conjectures* end-to-end answering; not uniform (GPT-4o falls from 84.0 at level 4 to 61.5 at level 5) | "SURGE observes, for some models, a slight uptick at its highest difficulty level and conjectures that such items are answered end to end"; drop "inverts" |
| 2607.18642 Spaghetti Architect | "difficulty knob is program size … its length axis and its complexity axis move together" | Two axes crossed by construction (r = 0.00): intrinsic size, and incidental presentation "messiness" at fixed semantics. v2 (Aug 30, 2026) current | Describe both axes; position ours as the converse manipulation — workload varies with presentation held byte-identical, where theirs varies presentation with semantics held fixed |
| 2510.08730 micro-benchmarking | "small-benchmark reliability literature argues [sealed holdout + paired public counterparts] is the minimum" | Subsampled benchmarks cannot reliably rank models 3.5–4 points apart; ~250 items needed for close pairs. Says nothing about sealed holdouts | Cite for the small-sample ranking result only |
| 2409.18836 CI benchmark | same sentence as above | 13 CI methods for generalization error on 19 tabular datasets; nothing about LLM benchmarks | Remove |
| 2605.15607 Syntax Without Semantics | "models can be taught to write in a language they have never seen" | Main result is the opposite: fine-tuning teaches the syntax of an invented language but not its semantics | Reword to that finding — it actually *supports* this paper's premise. v2 current |
| 2502.20129 FSA inside CoT transformers | "theory on how chain-of-thought supports state tracking" | Empirical mechanistic study (late-layer MLP neurons), not theory | "mechanistic evidence that CoT transformers track state" |
| 2404.08819 Illusion of State | same sentence | A limits result: SSMs and transformers without CoT cannot track state in one pass | "theory on the limits of state tracking without intermediate steps" |
| 2503.12686 abstract interpreters | "a comparable split between applying a rule and tracking the state it acts on" | Invariant generation on 22 SV-COMP programs; models set up equations but fail the iterative update. Since retitled | Reword to the actual finding; update title |
| 2406.03636 SPEAC | "taught to write in a language they have never seen" | Very-low-resource (not unseen) languages, via an intermediate language the model knows | Reword |

## Overstatements and metadata (fix in passing)

2501.14275 (LiveAoPSBench) is mined, time-stamped items, not "generation", and one example does not make "standard practice" — soften to "increasingly common", pair with LiveBench (2406.19314, verified). 2502.20377 PhantomWiki: "designed to resist contamination" (its own wording; not tested). 2603.09678 EsoLang-Bench: 11.2% is a best-configuration body figure (abstract: 0–11%; the paper is internally inconsistent) — write "0–11%". 2509.18458 CogniLoad: "task length", not "trace length". 2511.20836: Michael (not Mike) Pfeffer; "changes measured performance and rankings". 2604.02709: add author Ge Li; it is formal-language recognition, not execution. 2506.09250: v2 is titled "Comment on The Illusion of Thinking". 2312.04474 Chain of Code: OK. Version suffixes v5 (SURGE), v3 (2508.16745), v2 (2510.02386, 2603.13285) unconfirmed — drop version suffixes from keys in the revision.

## One citation that cuts against the paper

2603.13285 Brittlebench reports meaning-preserving perturbations reshuffle model rankings in ~63% of comparisons. The paper's "ranking is stable across paraphrases" is not contradicted — its adjacent gaps are 5–68 points, far wider than Brittlebench's — but the revision should say so explicitly, because a reader of that literature will expect the opposite result.

OK as cited: 2112.00114, 2305.11169, 2310.11324, 2401.03065, 2403.07974, 2411.10541, 2502.07266, 2503.05703, 2503.16402, 2506.06941, 2508.16745, 2509.01790, 2510.02386, 2601.06341, 2605.21856.
