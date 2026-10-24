# tape-trials — export bundle

Assembled 2026-10-12 in answer to the operator's step 1. **No GPU was used to
produce any part of this**: every byte below was already on disk, in shared
storage, or in a finished job's artifact store. Re-downloading records is not a
reason to hold a card.

284 files, 49 MB before zipping. Layout:

```
job-list.json              every job, both experiments: id, name, status, card,
                           vendor, start/end, wall GPU-min, rung, model, prompt,
                           split, score, error
job-list-summary.json      the same, rolled up by vendor and by card
storage/tape-trials/       the 122 objects in shared storage, verbatim
jobs/
  77d28852-rank-stability/     H5 rank-stability verdict (s6.5)
  7dae5ade-c8-compare/         cross-rung calibration comparison (s6.3)
  a7773982-analysis/           s6.2/s6.4 subgroup + error-labelling outputs,
                               including per_row_labelled.jsonl (14,128 rows)
  c4c2c79e-controls/           the C4/C6 control scoring runs with transcripts
  dc983887-controls/           the s5.5 reasoning-rung control scoring runs
                               with transcripts (control_c4, control_c6)
  c2-paraphrase/               5 wordings x 5 rungs, transcripts + per-row
                               files + result files
  c5-repeat/                   the five greedy repeats at 14B-R and 14B, with
                               per-row files and disagreement logs
  c8-calibration/              verbalized + self-consistency readings at
                               14B-R, 14B and 3B, with transcripts
analysis/
  task/                        the s6.2/s6.4 analysis task source
  rank-stability/              the H5 job's source and README
  c8-compare/                  the cross-rung comparison job's source and README
  _shared/                     the serving, calibration, gate, card-fit and
                               supervise modules every s6 job imported
  ref/                         the calibration overlap reference the gate reads
  assemble-public.sh           the bundle assembler
  WAVES.md                     the cell ledger for the whole s6 campaign
s6-runs/                   the four s6 result write-ups
evidence/                  the paper's evidence ledger and the budget ledger
```

## Job totals

110 jobs across both experiments, **4,874.1 wall-clock GPU-min** in total.

| Vendor | GPU-min | Jobs |
|---|---|---|
| aws | 3,353.4 | 88 |
| nebius | 1,461.7 | 12 |
| Runpod | 58.5 | 3 |
| gcp | 0.5 | 1 |
| **no accelerator (CPU-only)** | 0 | 6 |

| Card | GPU-min |
|---|---|
| L40S | 4,436.9 |
| A10G | 240.3 |
| T4 | 110.1 |
| L4 | 86.3 |
| A100-40GB | 0.5 |

The 4,874.1 is computed as `(end_time - start_time) x GPU count` over every job
in both job lists, including the 57 jobs whose `job_data.status` is null. Those
are the launch failures and the cells stopped by hand: they charged wall clock
for the time their card was held, which is the number the project's own ledger
uses and the one the stop-and-ask gate reads. It agrees with the hand-kept
ledger (4,942.96) to within 69 GPU-min over 110 entries; the difference is the
ledger's launch-failure provisioning entries, which the job records do not carry
as separate intervals.

## Two things a reader should know before using this

- **The private split is inside this bundle.** `storage/tape-trials/private.jsonl`,
  the eight `per_item_*_private.jsonl` files and the eight
  `transcripts_*_private.jsonl` files are the sealed holdout. It is bundled here
  because the operator asked for the complete run records, not because it is
  shareable. Anything derived from this bundle that goes to another person must
  leave those files out.
- **The transcripts are the raw model output**, including any text a model wrote
  before or after its answer. They are not filtered, and the scorer's behaviour
  on them is what the per-item files record.
