# Inventory and provenance check of the reproduction kit

Source: the reproduction kit Primus produced (`repro.tar.gz`), received 2026-08-28, five packages with directory structure intact, 113 files. (An earlier flattened upload of the same files had six documents named `main.py`, five `README.md` and three `MANIFEST.md` with only one of each reachable; the archive superseded it.)

## Integrity

Every file listed in the five package manifests verifies. Recomputing sha256 for all 107 manifest entries: 107 match, 0 mismatch, 0 missing. (`verification/verify_manifests.py` repeats this check; in this public repository the sealed holdout is the one entry reported as withheld rather than missing.)

| Package | Manifest entries | Verified | On disk but unlisted |
|---|---|---|---|
| benchmark-corpus | 31 | 31 | `splits/splits_manifest.json` |
| core | 12 | 12 | — |
| eval-harness | 39 | 39 | — |
| results | 23 | 23 | — |
| sealed-holdout | 2 | 2 | — |

**Publication note (2026-09-15).** The machine-generated draft (`core/paper/paper.tex`, `paper.pdf`, `arxiv.sty`) is published in this repository unmodified, watermark intact, with Transformer Lab's written permission. Shipping it byte-identical is what lets `verification/verify_manifests.py` confirm all 12 core entries; the only file withheld anywhere in the repository is the sealed holdout split.

`splits/splits_manifest.json` is present and used by the paper but is not covered by `benchmark-corpus/MANIFEST.md`. Nit (F6): add it, so the split definition is inside the provenance record rather than beside it.

## The results package does not contain the paper's results

> **Addendum 2026-08-31.** Screenshots of the Transformer Lab job history later established that the s6 runs DID happen and that every visible job-card number matches the paper — see `audit/06-s6-job-history.md`. **Addendum 2026-09-10.** Raw transcripts for the sixteen holdout/public cells were subsequently obtained and independently re-scored — see `audit/05-item-verification.md`; the public-split transcripts are in this repository under `results/transcripts/`. The gap described below is therefore a packaging defect of the kit as originally shipped, not evidence the measurements are unsourced. The description of what the kit contained remains accurate.

`core/REPRODUCE.md` describes `results/` as "the recorded per-item predictions, result JSONs and control derivations, verbatim." What it actually holds is the **dev split**, at an earlier stage of the study (`s5.3`), for six of eight configurations.

| Rung | Split in file | Rows | Programs | Recorded exact match |
|---|---|---|---|---|
| 0.5B | dev | 194 | 50 | 0.0000 |
| 1.5B | dev | 194 | 50 | 0.0412 |
| 3B | dev | 194 | 50 | 0.0928 |
| 7B | dev | 194 | 50 | 0.1546 |
| 14B | dev | 194 | 50 | 0.2113 |
| 7B-R | dev | 194 | 50 | 0.8144 |

The paper reports no dev numbers anywhere. Every table in the paper is on the 586-item holdout or the 1,180-item public split, and neither appeared in `results/`. Missing from the kit as shipped:

- All 16 cells of Table 1 (8 configurations × holdout and public).
- 14B-R and 14B-CoT files entirely — the two configurations that carry the headline claim, since 57.7 points is 14B-CoT (79.2) minus 14B (21.5) on the holdout.
- Table 2 (per-variable accuracy on the holdout). The dev `per_item` records carry no per-variable fields, so per-variable accuracy cannot be recomputed even for the dev cells; it exists only as a pre-aggregated number.
- Table 3 (category breakdown on the holdout), the §5 failure taxonomy over 8,756 wrong items, the §6 reply-length regressions, Table 4 (paraphrase), Table 5 (calibration), and the temperature-repeat battery.
- Model results on the two controls. `controls/control_c4.jsonl` (240 pseudocode items) and `controls/control_c6.jsonl` (230 partial-trace items) are the **derived stimuli**, not scored model output. The §6 numbers computed on them — 80.8 against 82.3 at 7B-R, 20.4 against 19.8 at 14B, 12.9 against 13.5 at 7B — have no recorded source in the kit.

## The figure provenance chain is broken at both links (in the kit)

`core/paper/figures/make_figures.py` opens: "Every value below is copied from `paper/evidence.md`, which is itself sourced from the recorded s6 job outputs. Nothing here computes a result; this script only draws." Neither referent is in the kit: `evidence.md` was not shipped, and no s6 output file was shipped — the kit carries the s6 job *code* (`tasks/holdout` = s6.1/C7, `tasks/paraphrase` = C2, `tasks/calibration` = s6.3/C8, `tasks/temperature` = s6.5/C5) with none of its output. Both figures and all tables in `paper.tex` are typed literals.

**Verdict (updated 2026-09-10).** The measurements happened and the headline numbers trace to job records (`audit/06-s6-job-history.md`) and, for Tables 1–3, Figure 1 and Table 4's 14B-R row, to independent re-scoring of raw transcripts (`audit/05-item-verification.md`). Before any submission the `results/` package must still be completed from the remaining job artifacts (aggregation outputs, control scoring, battery files, `evidence.md`), manifest included, so that Tables 4–5, Figure 2 and §8 become file-verifiable too.

## What the dev cells do establish

Internal consistency of the scoring pipeline is good. Recomputing each rung's exact match and mean reply length directly from its `per_item_*.jsonl` reproduces its `result_*.json` aggregate to four decimals in all six cells. So the harness's own arithmetic is sound.
