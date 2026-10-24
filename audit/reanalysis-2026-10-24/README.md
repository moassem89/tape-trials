# Re-analysis scripts, 2026-10-24

The scripts behind the revised paper's changed and new numbers, kept as a record. They
ran against the agent's full run-record export, which includes the sealed holdout, so
their paths point at that export and they will not run from this repository alone; the
public-split parts are reproduced by `verification/rescore_transcripts.py` and the files
in `results/corrected-per-item/`.

| Script | What it produced |
|---|---|
| `fixed_parse.py` | The corrected extractor as first written (now integrated into `eval-harness/harness/parse.py`; the two agree on all 22,358 rows) |
| `rescore_all.py` | Original vs corrected verdict for every exported transcript; the 61 changed rows |
| `build_fixed.py` | Corrected per-item records with failure labels from the released classifier |
| `numbers.py` | Table 1, headline contrasts with paired intervals, quintiles, loops-excluded knee, within-tier and marginal category tables, failure shares by regime |
| `within_tier.py`, `knee7br.py` | The first within-tier and 7B-R knee analyses (original parser) |

The paraphrase intervals were recomputed by re-running the released
`results/run-records/analysis/rank-stability/main.py` unchanged on corrected verdicts
(seed 20260821); the confidence comparison by re-running `.../c8-compare/main.py`.
