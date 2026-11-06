# Data license: CC BY 4.0

The corpus splits (`benchmark-corpus/splits/`), prompt battery (`benchmark-corpus/prompts/`),
derived control stimuli and recorded results (`results/`), raw model transcripts
(`results/transcripts/`), and the audit documents (`audit/`) are licensed under the
**Creative Commons Attribution 4.0 International License (CC BY 4.0)**.

You are free to share and adapt this material for any purpose, including commercially,
provided you give appropriate credit, link to the license, and indicate if changes were made.

Full legal code: https://creativecommons.org/licenses/by/4.0/legalcode
Human-readable summary: https://creativecommons.org/licenses/by/4.0/

Attribution: "tape-trials benchmark and audit, Mohammad A. Mahmoud (2026),
https://github.com/moassem89/tape-trials — corpus generated with Primus (Transformer Lab);
Varphi by Hassan El-Sheikha; Ampliphi by Hassan El-Sheikha, Kevin Thevara and Youssef Abouzied."

Code (everything under `benchmark-corpus/build/`, `eval-harness/`, `verification/`, and
`core/paper/figures/make_figures.py`) is licensed separately under the MIT License (`LICENSE`).

Model outputs are additionally subject to the licenses of the models that produced
them, which this grant cannot enlarge. Qwen2.5-0.5B/1.5B/7B/14B-Instruct are Apache 2.0
and the DeepSeek-R1 distills are MIT, but **Qwen2.5-3B-Instruct is released under the
Qwen Research License** (research or evaluation use; outputs used to create, train or
improve a model must display "Built with Qwen"), so the 3B transcripts and per-item
records in `results/` carry those terms alongside CC BY 4.0.

The private holdout split is **not** released under any license; see
`sealed-holdout/README.md` and `sealed-holdout/STATUS.md`.
