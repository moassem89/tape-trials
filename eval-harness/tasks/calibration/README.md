# s6.3 / C8 — the calibration battery

## Why there is a new condition here at all

The research plan has seven conditions and none of them elicits a confidence.
The frozen template asks for an answer and forbids anything else, and the
inference jobs did not retain logprobs, so no probability is attached to any of
the 12,000-odd recorded replies. Calibration cannot be recovered from those
files by reanalysis. Reporting a Brier score computed from them would mean
inventing the probability it scores, so C8 generates the missing signal instead.

Adding a condition after the plan was approved is recorded here and in the s6
report rather than folded in quietly. What it costs is four cells; what it buys
is the difference between a calibration section that measures something and one
that does not exist.

## The two arms

Both run over the same rows, behind one weight load, in one job.

**Verbalized.** One greedy pass with `P6_confidence.txt`. That template is
`P1_frozen.txt` with the output contract replaced: the reply is a single object
with exactly two keys, `answer` and `confidence`, the latter an integer from 0
to 100 giving the probability that *every* value in `answer` is right.
Everything above the contract, the specification and the worked example, is
byte-identical to the frozen template, so a difference in accuracy between this
arm and C1 is attributable to the contract and to nothing else.

**Self-consistency.** Five sampled passes at temperature 0.8 with the ordinary
frozen template. The prediction is the modal parsed answer and the confidence is
that mode's share of the five. Nothing is elicited: the model is asked the same
question five times and its own disagreement rate is read as uncertainty.

The comparison is the point. Stated confidence is free and needs the model to
introspect; sampled agreement costs five times as much and needs nothing of the
kind. A model that cannot state a useful probability may still reveal one by
disagreeing with itself, and on the low rungs of this ladder that is the more
likely outcome.

The self-consistency prediction is the mode rather than the greedy answer, so
its accuracy is a different number from the C1 headline. That is deliberate: a
confidence has to attach to the prediction it describes.

## Rows and rungs

The fixed-seed stratified 15% subsample of the public split — 181 rows over 46
programs, drawn by the C5 selector, byte-identical to the rows the repeat
battery used. Reusing them buys a noise floor: C5 has already measured how much
those rows move under rerun, so a calibration curve on them can be read against
that.

Four cells, chosen to span the accuracy range the study produced rather than to
cover the whole ladder: `14B-R` (0.96), `7B-R` (0.82), plain `14B` (0.20), `3B`
(0.09). The two ends of the ladder are omitted on purpose. Calibration at an
accuracy of 0.0017 is a question about a degenerate distribution, and the 0.5B
rung would spend a card to establish that a model which is never right is also
never usefully uncertain.

## What is reported

Per arm: accuracy, mean confidence, overconfidence gap, Brier, ECE and MCE over
ten equal-width bins, the full reliability table with bin occupancies, the
Murphy decomposition into reliability and resolution, AUROC, and a
risk-coverage curve. Brier, ECE and the gap each carry a whole-program cluster
bootstrap interval, matching every other interval in this study.

Equal-width bins rather than equal-mass, because a verbalized confidence piles
up on round numbers and equal-mass bins would collapse most of the mass into
one. Bin occupancies are reported so the reader can see where it actually sat.

The Murphy split is worth the space. Reliability is the part a temperature
rescaling could fix. Resolution is whether the confidence carries any
information at all, and no rescaling creates it: a model that says 90 on every
row has resolution exactly zero, however accurate 90 turns out to be.

Cross-arm: the correlation between the two confidence signals, and the mean
number of distinct answers a row drew across the five samples.

## Coverage, not repair

A confidence that is out of range, non-numeric, or absent is recorded as
missing, never clamped. Clamping would manufacture a probability the model did
not state. A reply that ignored the wrapper entirely is still scored on its
answer, and the `wrap_compliance` rate says how often that happened — itself an
instruction-following measurement, which is what this benchmark is about.

## Selftest

`python3 selftest.py`, from this directory. It checks the metrics against cases
whose answers are known by hand (a perfect forecaster, an inverted one, a flat
forecaster with zero resolution and the Murphy identity closing on it), checks
that five malformed confidences all read as absent, then runs the whole job
against a stubbed model whose modal shares are planted, and confirms the holdout
guard refuses. Passing output ends `selftest ok`.

## Queueing

```sh
sh assemble-c8.sh /tmp/c8 reason        # or: plain
cd /tmp/c8 && lab task add . -e <experiment> --no-interactive
lab task queue <task-id> -e <experiment> --no-interactive --provider aws \
  -p model=Qwen/Qwen2.5-3B-Instruct -p rung=3B
```

## Status

Authored and passing its selftest. Queued behind the s6.5 batteries.
