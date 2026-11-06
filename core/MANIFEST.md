# MANIFEST: Core reproduction kit

14 files. Every line is `sha256  path  bytes`. A file marked
`(cleaned)` had internal storage identifiers redacted for distribution; no
result value in it was changed, and the hash is of the copy shipped here. A file
marked `(corrected)` was edited after generation to fix audit findings (F27/F28
holdout wording, F31 prompt-hash label, the 11.0% repeat rate, and the toolchain
section of `REPRODUCE.md`); `(added)` files were not part of the generated kit
(the toolchain fetch instructions in `wheels/`, which replaced two briefly vendored
wheels on 6 November 2026). The generated originals of every `(corrected)`
file are recoverable from this repository's git history.
`paper/paper.tex` is cleaned of one thing only: the personal e-mail address in the
draft's author block is replaced by `[e-mail withheld]` (2 November 2026; the
agent's text is otherwise byte-identical); `paper/paper.pdf` had the same address
redacted from its title block and nothing else.

```
13586b6efe56df9a48576befbfb990b699dd3d2fc32dd74933b8071e269705c8  REPRODUCE.md  7998  (corrected)
a4458d377a35db99319246b946e93b5b159e8abee3a2b8c30d60588ee845c467  environment.md  2215  (corrected)
2b620cb51e33803716850801aa29ebea5cd80ef66eb24baa9e07dfefb63f9fd0  eval-command.sh  2253
5dbeb943955b77856bc417e52639c260d2314f362522dcccc29d49ad0d30e05c  model-card.md  17351  (corrected)
d8a2d32ffc165b4f388f574eee104ad86581bb675eb4495fbda3eff629929102  paper/arxiv.sty  3237
30b1d18c51232ba1bf8ad4bcde71b0b293aff6adf28e6f2e9b471224c5b3067c  paper/figures/knee.png  137158
01784854484a596189a6505f356aefefaa78974e6f651e9d563c573b46634f81  paper/figures/make_figures.py  3327
2f318160a636607782bfd6dc0f06c2a4798fa35fd5840917eff3d426dae9cd42  paper/figures/tokens.png  72661
f90f75593d68b8074c5bc11e0d70ebe99e719ff0e76baa7b43b3ff33ffcb3dec  paper/paper.pdf  326090  (cleaned)
d4193f3e759ce5b2d3d4bee3b51ef365f49848b58b0894bfc7ccb5c5cc239435  paper/paper.tex  41760  (cleaned)
7eba0446490501e24d5e00e57b5fa772de112c05aa8002fcc11f8a55398ee34f  paper/references.bib  21731
43f875e7bc336a8d1474d0e4f67c0ca4defe79240213f21b96ce3200bdd9e387  seeds-and-hashes.md  3632  (corrected)
c63fa399c993a574b7c8acf5152e18d00a3c442a4d613812f9614602d883543f  wheels/README.md  841  (added)
68cdf28eef012f56c6ec86b39cdbb5cc01e59c6d1980fa20d8b4806bba92fddc  wheels/SHA256SUMS  201  (added)
```
