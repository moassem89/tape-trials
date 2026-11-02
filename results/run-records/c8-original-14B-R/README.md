# The original 14B-R confidence cell (job cbc1215f)

Table 5's 14B-R row in the paper comes from this run. Its transcripts were not kept, but
its per-row scores were: these two files are the copies the cross-rung comparison job
(`run-records/analysis/c8-compare/`) read from the agent's storage prefix
`tape-trials/c8/`. The re-run of the same cell (job 2072549d, newer serving image) is the
one under `run-records/jobs/c8-calibration/`, with transcripts.

Both files are public-split only (181 items over 46 programs, two arms each). Recomputed
with the released metric code (`run-records/analysis/_shared/calib_metrics.py`), they
give exactly the published row: accuracy 80.4% over the 179 rows whose confidence parsed
(80.1% over all 181), mean stated confidence 99.9%, Brier skill −0.24, stated AUROC
0.522, agreement AUROC 0.925, and a majority-answer accuracy of 85.1% that rises to 98.9%
on the half of items with the highest agreement.

Two qualifications, both stated in the paper. These replies were scored with the
original parser, which the audit later found to mis-score some reasoning replies (F21),
and without transcripts they cannot be re-scored. And the confidence runner passed the
prompt to the model as raw text, without the chat template every other runner applies.
