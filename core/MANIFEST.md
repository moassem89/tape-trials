# MANIFEST: Core reproduction kit

14 files. Every line is `sha256  path  bytes`. A file marked
`(cleaned)` had internal storage identifiers redacted for distribution; no
result value in it was changed, and the hash is of the copy shipped here. A file
marked `(corrected)` was edited after generation to fix audit findings (F27/F28
holdout wording, F31 prompt-hash label, the 11.0% repeat rate, and the toolchain
section of `REPRODUCE.md`); `(added)` files were not part of the generated kit
(the vendored toolchain wheels). The generated originals of every `(corrected)`
file are recoverable from this repository's git history.
`paper/paper.tex` is cleaned of one thing only: the personal e-mail address in the
draft's author block is replaced by `[e-mail withheld]` (2 November 2026; the
agent's text is otherwise byte-identical); `paper/paper.pdf` had the same address
redacted from its title block and nothing else.

```
4b9637597310765cf62132e01e242160ad5c28d43ea600a9aac21c2c270202e6  REPRODUCE.md  7762  (corrected)
a4458d377a35db99319246b946e93b5b159e8abee3a2b8c30d60588ee845c467  environment.md  2215  (corrected)
2b620cb51e33803716850801aa29ebea5cd80ef66eb24baa9e07dfefb63f9fd0  eval-command.sh  2253
15d031e92cb7f0eb27b4dddd8ab8ef96602906cfd331e88360d295fed82a2ffe  model-card.md  17222  (corrected)
d8a2d32ffc165b4f388f574eee104ad86581bb675eb4495fbda3eff629929102  paper/arxiv.sty  3237
30b1d18c51232ba1bf8ad4bcde71b0b293aff6adf28e6f2e9b471224c5b3067c  paper/figures/knee.png  137158
01784854484a596189a6505f356aefefaa78974e6f651e9d563c573b46634f81  paper/figures/make_figures.py  3327
2f318160a636607782bfd6dc0f06c2a4798fa35fd5840917eff3d426dae9cd42  paper/figures/tokens.png  72661
f90f75593d68b8074c5bc11e0d70ebe99e719ff0e76baa7b43b3ff33ffcb3dec  paper/paper.pdf  326090  (cleaned)
d4193f3e759ce5b2d3d4bee3b51ef365f49848b58b0894bfc7ccb5c5cc239435  paper/paper.tex  41760  (cleaned)
7eba0446490501e24d5e00e57b5fa772de112c05aa8002fcc11f8a55398ee34f  paper/references.bib  21731
dc46d24b4ea387475925085cb6bba5241bf8a99d1ab85937c1add53dc3dccf73  seeds-and-hashes.md  3465  (corrected)
560a3c3124621bddb7c8f1e75e2fe84529784ff1df0944adff90ad6db30a8b56  wheels/ampliphi-1.0.0-py3-none-any.whl  63584  (added)
6b42b662da2367da6be8bb9d54714d8b2a56f6cf18c23cc514148affe32e3efd  wheels/varphi_python-2.0.6-py3-none-any.whl  8576  (added)
```
