# Environment

## Hardware each cell ran on

| Configuration | Card | Why |
|---|---|---|
| 14B, 14B-R, 14B-CoT | L40S (48 GB), 1 GPU | a 14B model in bf16 does not start on an A10G at this study's context length; weights plus KV cache fall short |
| 0.5B, 1.5B, 3B, 7B, 7B-R | L40S (48 GB), 1 GPU for the headline and holdout passes | the holdout is a paired reading against the public split, so the card is held fixed even where a smaller one would fit |
| several later condition cells | A10G, 1 GPU | A10-class cards are preferred wherever the weights and KV cache fit; each cell records the card it used |

Machine shape for every cell: 16 vCPU, 64 GB RAM, 200 GB disk. Providers were AWS
and RunPod; a cell records the provider it actually landed on, which is not always
the one requested.

## Software

- Serving: `vllm`, installed at job setup time along with `transformers`.
- Answer key: `ampliphi 1.0.0` and `varphi-python 2.0.6`, both pinned. The key is
  produced by executing the program, never by a model.
- Corpus build, split, control derivation and scoring are pure Python with no
  accelerator; those jobs ran on 16-vCPU CPU-only machines.
- Figures: `matplotlib`. `make_figures.py` in `paper/figures/` computes nothing;
  every value in it is transcribed from a recorded result.
- Paper: `tectonic paper.tex` from inside `paper/`, which needs `arxiv.sty`
  (shipped here), `references.bib` and the two figure PNGs.

## Determinism

Decoding is greedy with one completion per row, so a cell is deterministic up to
the serving stack's own numerics. That last qualifier is measured rather than
assumed: five identical greedy passes over the same 181 rows moved the score by
2.8 points at 14B-R while 6.6% of rows disagreed at the row level, and at plain
14B the score was identical on all five passes while 11.1% of rows changed
answer. Treat any difference smaller than about three points as inside the noise
of the serving stack.

Corpus construction is seeded (master seed `20260819`) and each row's executor
seed is derived by hashing that seed with the row key, so a row replays exactly.
Each admitted row carries six distinct executor seeds that agreed on both the
output and the step count.
