# Statistics review: clustering, the three §7–§8 claims, baselines, and the tier×category design

Session 2, 2026-08-31. Numbers labelled "recomputed" were produced from the shipped data and the shipped code, run unmodified. This document also corrects one finding of session 1 (F2): the "complete nesting" table in `audit/02-reproduction-log.md` is an artifact of how programs were collapsed to one tier, and the true design is materially less broken than that session recorded.

## 1. Clustering machinery: verified

The `icc_anova` implementation (byte-identical in all four shipped copies) is the standard one-way random-effects ANOVA estimator on binary outcomes with the standard unequal-cluster-size adjustment: `m0 = (n − Σs²/n)/(k−1)`, `ICC = (MSB − MSW)/(MSB + (m0−1)·MSW)`, `deff = 1 + (m0−1)·max(0, ICC)`. On the holdout's actual cluster sizes (140 programs of 4 rows, 6 of 3, 3 of 2, 2 of 1) `m0 = 3.8804` against `n/k = 3.8808` — the corpus is near-balanced, so the adjustment is nearly inert, but it is implemented correctly. With the job-card ICC 0.5673 at 14B: deff = 1 + 2.8804 × 0.5673 = **2.634**, effective n = 586/2.634 = **222.5** — the paper's 2.63 and "closer to 222" both reproduce from the code's own formula. The same formula on the other job-card ICCs gives deff 2.60 (7B), 2.30 (3B), 2.85 (1.5B), and — because negative ICCs are clamped only where they feed the design effect, which the code discloses — 1.00 at 0.5B, which is the quiet exclusion F8 already flags. `cluster_bootstrap` (resample whole programs, percentile interval, fixed seed) reproduces the recorded dev intervals bit-for-bit. Nothing in this machinery is wrong.

Two honest limitations worth one sentence each in the paper: the ANOVA ICC on binary outcomes is an approximation (fine at these accuracies, degenerate at 0.5B, which is exactly where the estimate goes negative), and percentile intervals from 2,000 draws carry ±one-order-statistic wobble that matters only when an endpoint is quoted to a decimal.

## 2. Claim (i): rank correlations of 1.0 with a bootstrap interval of [0.9, 1.0]

§7: "every pairwise Spearman correlation between wordings is 1.0, every Kendall's tau-b is 1.0, and each wording's correlation against the frozen specification is 1.0 with a bootstrap interval of [0.9, 1.0] over 2,000 draws that resample whole programs and rebuild the entire matrix."

What produces that interval is not mysterious, and it is worth stating because it shows what the interval does and does not mean. With five configurations, Spearman's ρ between two orderings has discrete support: 1.0 for identity, and **0.9 for exactly one adjacent transposition** — nothing in between. (Kendall's τ for one adjacent swap is 0.8, so the quoted interval is only arithmetically possible for Spearman; if τ-b intervals were computed they cannot have been [0.9, 1.0].) A percentile interval of [0.9, 1.0] therefore says exactly one thing: in between 2.5% and 97.5% of the 2,000 coupled resamples, at least one adjacent pair swapped. That is consistent with the paper's own reversal numbers — the 7B/3B pair alone reverses in 17–21% of draws under two paraphrases — so the interval is *internally coherent*, but it is not a confidence interval in any useful sense: the statistic sits at the boundary of its support, the upper endpoint is 1.0 by construction, and the lower endpoint is forced to 0.9 by *any* near-tie anywhere in the ladder. It compresses the informative quantity (which pair swaps, how often) into a two-point summary that reads like strong evidence while encoding "some pair swaps in at least 1-in-40 draws."

The deeper problem is the direction of the inferential bar. §7 sets a "95% bar … for calling a reversal sustained" and concludes "the verdict stands" when 7B-over-3B reverses in only 21% of draws. That inverts the burden of proof: a reversal rate of 21% means the *ordering* of that pair is supported at roughly 79%, not that the ordering survived a test at 95%. Had the pair reversed in 50% of draws — total uncertainty — it would still have failed the paper's bar for a "sustained reversal" and the ordering would still have been declared to stand.

(a) Wrong: the interval is technically correct arithmetic presented as if it measured the stability of a correlation; the "95% bar" framing is a genuine methodological error of direction. (b) Matters: moderately. The substantive conclusion mostly survives, because three of four adjacent gaps are huge and the observed orderings really were identical five times; the only pair at issue is 7B/3B. (c) Fix: delete the [0.9, 1.0] interval (or replace it with "the resampled ranking is identical to the observed one in X% of draws"), report per-pair order-support probabilities (≈79–83% for 7B/3B, >95% elsewhere), and state the 7B>3B step as unresolved rather than defended by an inverted test. Required revision; no headline threatened.

## 3. Claim (ii): "a perfect rank correlation would arise from a random one in a single case out of 120"

The arithmetic is right (5! = 120) and the inference is empty. The implied null — a paraphrase induces a uniformly random permutation of five model rankings — has no relationship to any process in the experiment. The five configurations differ by up to 90 accuracy points; any measurement with noise far smaller than the gaps would reproduce the ordering with probability near 1, not 1/120. The informative null is "rankings are stable up to sampling noise," and the paper's own coupled bootstrap already computes exactly that, giving ~0.79–0.83 same-order probability for the one close pair and ≫0.95 elsewhere. Under the strawman uniform null the sentence also understates its own case (five wordings all agreeing would be (1/120)⁵ if independent) — a sign the sentence is decoration, not analysis. (a) Wrong: as inference, yes. (b) Matters: little quantitatively; it pads §7 with a significance-flavoured number that a statistically literate reviewer will single out. (c) Fix: delete the sentence. The honest statement — "the gaps are large relative to resampling noise everywhere except 7B/3B" — is already in the section.

## 4. Claim (iii): the 3B stated-confidence AUROC of 0.560 "technically excludes chance"

Three code facts first. The shipped `auroc` handles ties correctly (midranks, ties count half — a textbook Mann–Whitney). The shipped `murphy` computes resolution on **ten equal-width bins**, and every stated-confidence value at 3B sits in [0.99, 1.0] (mean 0.9937, four near-identical values), so all mass lands in one bin and resolution is *identically* zero whatever ordering signal exists within the bin. "Resolution 0.0 to five decimals" and "AUROC above 0.5" are therefore not in tension — they are computed on different scales — and the paper's rhetorical pairing of them is a binning artifact, not a contradiction. Third: **no shipped code computes an AUROC interval at all.** `arm_metrics` attaches `cluster_ci` to Brier, ECE and the overconfidence gap but reports AUROC as a bare point estimate; the intervals in §8 (0.560 "excludes chance", the pooled 0.882 [0.846, 0.916] vs 0.525 [0.508, 0.543], the paired differences) came from an analysis job whose code the kit's own docstring names — `c8-compare/main.py` — and does not contain. The §8 intervals are thus doubly unverifiable: no per-item data (F1) and no interval code.

What can be tested is whether an interval built the way this codebase builds intervals can be trusted in this regime. Using the shipped `auroc` and `cluster_ci` verbatim, the C8 3B geometry was simulated — 181 rows over 46 programs, 13 correct rows, four near-identical confidence values, confidence independent of correctness by construction — asking how often the 95% interval excludes 0.5 under this null:

| Null regime | Interval excludes 0.5 (nominal 5%) | Null point-AUROC 2.5–97.5% range |
|---|---|---|
| correctness iid, confidence iid by row (500 draws) | 8.0% | [0.36, 0.61] |
| correctness clustered by program, confidence iid (500 draws) | 13.3% | [0.36, 0.63] |
| same, at the study's own 2,000 draws | **11.3%** | — |
| correctness and confidence both clustered by program (500 draws) | 16.0% | [0.28, 0.79] |

Under realistic clustering the interval excludes chance two to three times as often as advertised, and the *point estimate's* null distribution comfortably covers 0.560 in every regime. Two mechanisms: with near-total ties, the AUROC of a resample is decided by a handful of program-level coincidences, so the bootstrap distribution is lumpy and the percentile interval anticonservative; and `cluster_ci` silently drops resamples where `auroc` returns None (no correct row drawn — a live possibility at 7% accuracy over 46 programs), conditioning the interval on informative draws.

(a) Wrong: "the 3B interval on AUROC technically excludes chance" is unreliable — under the null it would "technically exclude chance" in roughly one simulation in eight. (b) Matters: for §8's headline, no — the paper already discounts the number, and the claim that matters (agreement AUROC ≈ 0.88 versus stated ≈ 0.52, paired difference 0.36–0.40) is an order of magnitude larger than the anticonservatism and is safe. For the sentence itself, yes: it asserts the one thing the interval cannot support. (c) Fix: delete "technically excludes chance" and say the stated-confidence AUROCs are statistically indistinguishable from 0.5 at 3B's tie structure; ship the `c8-compare` code with the re-exported results. Required revision, one sentence.

## 5. Trivial baselines: recomputed on every split

Echo-the-input and answer-all-zeros were scored through the real harness (`score_row`, typed zeros) on each split separately. Per-variable is the harness's pooled definition (Σ correct variables / Σ variables); the macro mean-of-rows differs and matches nothing in the paper, so the paper's numbers are pooled.

| Split | Echo per-var | Zeros per-var | Zeros exact-match items | Echo exact-match items |
|---|---|---|---|---|
| public (1,180) | 39.51% | 29.22% | **0.51%** (6 items) | 0.00% |
| dev (194) | 38.71% | 27.55% | 1.03% | 0.00% |
| holdout (586) | **39.21%** | **28.25%** | 0.17% (1 item) | 0.00% |
| all 1,960 | 39.34% | 28.77% | 0.46% | 0.00% |
| paper (§3, Table 2) | 39.2% | 28.3% | 0.5% | "never right on a whole item" |

The per-variable figures are the **holdout's**, exactly (39.21 → 39.2, 28.25 → 28.3), which agrees with Table 2's caption ("per-variable accuracy on the holdout"). But the 0.5% item figure in the same §3 sentence is **not** the holdout's — on the holdout all-zeros is exact on 1 item of 586 (0.17%). 0.5% matches the public split (0.51%) or the pooled corpus (0.46%). So one sentence quotes three numbers from two different splits while attributing them to "the same corpus." "Echo is never right on a whole item" holds on every split, by construction of the changed-variable gate. (a) Wrong: a split-attribution error, small but checkable by anyone with the data. (b) Matters: little — no model comparison moves. (c) Fix: state the split; if the holdout is the basis, 0.5% becomes 0.2%. Nit, but the kind a careful reviewer finds in an afternoon.

## 6. Tier × category: correcting session 1, naming the design, and what survives

**Correction of F2's supporting table.** Session 1's table ("all 80 procedure programs are T5; decision is 3 programs in T4 and 87 in T5; T4 rests on three programs") was produced by collapsing each program to the tier of its lexicographically first item id. That rule is an artifact twice over — the first-selected row's tier is set by global tier scarcity during selection, and string-sorting `_i1863` before `_i186` is arbitrary — and the resulting table describes nothing about the design. The actual structure, over items (which is what Table 3 aggregates) and over program tier-spans:

Items per category × tier, all 1,960 (holdout in parentheses):

| | T1 | T2 | T3 | T4 | T5 |
|---|---|---|---|---|---|
| arrays | 0 | 51 (10) | 124 (36) | 102 (31) | 83 (23) |
| bounded_loops | 80 (24) | 45 (14) | 76 (23) | 97 (29) | 102 (30) |
| branching | 0 | 153 (47) | 115 (36) | 0 | 0 |
| decision | 0 | 90 (27) | 91 (27) | 92 (28) | 87 (26) |
| procedures | 0 | 0 | 136 (42) | 103 (30) | 81 (24) |
| straightline | 38 (11) | 129 (40) | 85 (28) | 0 | 0 |

Program tier-spans agree: procedures programs span T3–T5 (78 of 80), decision T2–T5 (87 of 90), bounded_loops T1–T5 (80 of 100), arrays T2/T3–T5, while branching and straightline are capped at T3. T4 items come from **353 programs across four categories**, not 3. So: the design is **not** nested. Nine of thirty cells are structurally empty; two categories never reach the top two tiers; three never appear in T1; procedures never below T3. The name a reviewer would use: an **incomplete, systematically unbalanced two-way layout — category partially aliased with tier** (marginal category comparisons are workload-confounded because each category's tier mix differs by construction), with within-tier contrasts estimable wherever cells coexist: all six categories at T3, four at T4 and T5. The paper's own sentence — "tier and category are not crossed in the generator, so a tier effect and a category effect cannot be fully separated" — is a fair description; session 1's escalation to complete nesting was wrong and F2 is downgraded accordingly.

**Which §5 / Table 3 claims survive.** Because the confound is partial, some of Table 3 can be salvaged by arithmetic the paper never does — bounding within-tier accuracies from the marginal accuracy and the known tier mix:

- *"Procedures as the hardest construct for every plain rung, all three scoring zero"* — **does not survive as a construct claim.** Plain rungs are near zero on *every* category's T3+ items (dev, within T3–T5: 14B arrays 1/29, procedures 1/32, decision 2/27); procedures merely have no T1/T2 items to prop up their marginal. The marginal ranking restates each category's tier mix.
- *The tracing prompt's procedure failure (14B-CoT 26.0% on procedures vs 100/98.8 on straightline/branching)* — **survives, provably.** 26.0% of 96 procedure items = 25 correct; even if every success sat at T3, procedures-at-T3 ≤ 25/42 = **59.5%**. Branching 98.8% of 83 = 82 correct; even if every failure sat at T3, branching-at-T3 ≥ 35/36 = **97.2%** (straightline-at-T3 = 100%). The gap cannot be a tier effect. The paper is entitled to this claim and currently cannot prove it from its own table; one bounding sentence (or a within-tier table from the holdout per-item files) fixes that.
- *"The distilled models are weakest instead on arrays"* — **survives, against the tier gradient.** Procedures (no items below T3) score 90.6% at 7B-R while arrays (with a T2 cushion) score 63.0%; dev within-tier agrees (7B-R, T3–T5: procedures 27/32, arrays 16/29). A tier-only account predicts the opposite sign.
- *"Call-and-return state resists prompting"* — the phenomenon survives (above); the **mechanism naming is doubtful**: `gen.py` documents that `invoke` "is a paste, so three invokes apply thrice" — procedures are inlined, so there is no runtime call-and-return state to carry. What the model faces is source-level indirection it must mentally expand. Reword.
- **A finding the paper misses: bounded loops are anomalously easy for the plain rungs.** Table 3 has plain 14B at 46.7% on loops against ≤ 20.5% everywhere else and 0–2.8% on the three "deep" categories; the bound from the tier mix shows loops-at-T3–T5 ≥ 18/82 = 22% for plain 14B while procedures-at-T3–T5 = 0/96, and dev shows loops surviving where every other category dies (14B: loops 9/28 within T3–T5). Bounded loops of the generator's shape have closed forms (an accumulator stepped a computable number of times), so a model can answer without tracing. This is directly relevant to §6's claim that plain-rung scores are "the rate at which a guess happens to be right": on loops it is plausibly the rate at which *arithmetic shortcuts* are right, which is a different and more interesting failure of the difficulty axis — executed steps overstate the difficulty of shortcuttable categories.

**Does category add anything once executed steps are in the model?** Yes — decisively, on the shipped dev cells. GEE logistic regressions (exchangeable working correlation by program, robust covariance) of correctness on log₁₀ steps + (log₁₀ steps)², with and without category dummies:

| Config | p (category block, cluster-robust) | AUC steps-only | AUC + category |
|---|---|---|---|
| 1.5B | 1.0 (degenerate: 8 successes) | 0.834 | 0.913 |
| 3B | < 10⁻⁴ | 0.897 | 0.927 |
| 7B | < 10⁻⁴ | 0.744 | 0.864 |
| 14B | < 10⁻⁴ | 0.773 | 0.914 |
| 7B-R | < 10⁻⁴ | 0.659 | 0.747 |
| pooled (config × steps interactions) | 2 × 10⁻⁵ | — | — |

Pooled category coefficients (log-odds relative to arrays): bounded_loops +3.20, straightline +3.53, branching +1.44, decision +1.30, procedures +1.59. Two readings matter. First, the answer to the design question: step count does **not** absorb the category structure — the axes are partially separable and the data show both effects, so the paper's flat "we report the two axes side by side rather than one adjusted for the other" is leaving identifiable structure on the table. Second, the adjusted ordering contradicts Table 3's marginal narrative: adjusted for workload, **arrays are the hardest category and procedures are unremarkable** for these six configurations; the marginal "procedures hardest" is the tier mix talking. (Dev has no 14B-CoT cell, so the tracing-prompt procedure deficit — which the bound above proves on the holdout — is a separate, real effect.) Caveats: 194 items per cell over 50 programs, and Wald tests with ~46 informative clusters are approximate; the within-tier raw tables and the bounds carry the same message without the model.

(a) Wrong: session 1's F2 was overstated (collapse artifact); the paper's §5 mechanistic sentences remain unidentified *as presented*, but two of the three category claims are provable from existing data and one is refuted at the plain rungs. (b) Matters: this reverses F2's "rejection-level as stated" — the fix is analysis and rewording, not corpus regeneration. (c) Fix: add the within-tier breakdown (T3 alone contains all six categories; the holdout per-item files suffice), state the bounds where cells are empty, reword the mechanism sentence, and address the loops shortcut explicitly.

## 7. One further §7 note: the spread statistic

Table 4's "spread between worst and best wording" is a max−min over five noisy estimates: it is biased upward when true spreads are small (a range of noisy replicates is positive even under a zero true spread), and a percentile bootstrap of the same statistic inherits the bias — visible in Table 4's floors, where even the null-ish 7B row shows spread 1.3 [0.8, 4.6]. The paper's defence (comparing spreads to the repeat-noise floor) is the right instinct and should be stated as the formal criterion; the 7B-R conclusion (13.5 points, interval [9.1, 20.1], floor 6.6%) survives comfortably. Nit: say "range statistics are upward-biased under noise; only 7B-R's spread clears the measured floor" rather than presenting all five spreads as estimates of wording sensitivity.

## Summary of verdicts

| Finding | Wrong? | Threatens a headline? | Severity |
|---|---|---|---|
| deff/ICC machinery | no — verified, reproduces job cards and dev records | no | — |
| [0.9, 1.0] interval + "95% bar" inversion | interval uninformative; bar inverted | ordering claim survives except 7B/3B, which was already flagged | required revision |
| "1 in 120" null | yes (strawman null) | no | required revision (delete) |
| 3B AUROC "excludes chance" | yes (interval anticonservative 2–3× under ties; interval code unshipped) | no — §8's agreement-vs-stated contrast is safe | required revision (delete claim; ship c8-compare) |
| Baseline split attribution | yes (0.5% is not the holdout's number) | no | nit |
| F2 as recorded by session 1 | yes — collapse artifact; design is partially aliased, not nested | changes the *grading*: Table 3's construct claims are salvageable by within-tier analysis; one is provable now, one refuted | required revision (downgraded from rejection-level) |
| Loops shortcut anomaly | new observation | complicates "steps = difficulty" and the §6 guessing account at the plain rungs | required revision (discuss) |
| Spread statistic bias | mild | no | nit |
