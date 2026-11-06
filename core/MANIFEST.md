# MANIFEST: Core reproduction kit

12 files. Every line is `sha256  path  bytes`. A file marked
`(cleaned)` had internal storage identifiers redacted for distribution; no
result value in it was changed, and the hash is of the copy shipped here.
`paper/paper.tex` is cleaned of one thing only: the personal e-mail address in the
draft's author block is replaced by `[e-mail withheld]` (2 November 2026; the
agent's text is otherwise byte-identical); `paper/paper.pdf` had the same address
redacted from its title block and nothing else.

```
b0a731c93e2d79f3af87b2a9f1f1061a86d95697e29c387a07fb9c69e1b610e2  REPRODUCE.md  4775
0985472fa0d7bca2dba6c779e2cc6ad282035ea658fbb3078c63409ac495dc9d  environment.md  2215
2b620cb51e33803716850801aa29ebea5cd80ef66eb24baa9e07dfefb63f9fd0  eval-command.sh  2253
2d63f008c9c04917293adf610030a84ae2fffc30957aeb28dbd022e183d71eac  model-card.md  16557
d8a2d32ffc165b4f388f574eee104ad86581bb675eb4495fbda3eff629929102  paper/arxiv.sty  3237
30b1d18c51232ba1bf8ad4bcde71b0b293aff6adf28e6f2e9b471224c5b3067c  paper/figures/knee.png  137158
01784854484a596189a6505f356aefefaa78974e6f651e9d563c573b46634f81  paper/figures/make_figures.py  3327
2f318160a636607782bfd6dc0f06c2a4798fa35fd5840917eff3d426dae9cd42  paper/figures/tokens.png  72661
f90f75593d68b8074c5bc11e0d70ebe99e719ff0e76baa7b43b3ff33ffcb3dec  paper/paper.pdf  326090  (cleaned)
d4193f3e759ce5b2d3d4bee3b51ef365f49848b58b0894bfc7ccb5c5cc239435  paper/paper.tex  41760  (cleaned)
7eba0446490501e24d5e00e57b5fa772de112c05aa8002fcc11f8a55398ee34f  paper/references.bib  21731
2d89a8409b87ea01431bbf4a3d42dda83976ebcd3994c7fa8f55e55d52376b5d  seeds-and-hashes.md  2277
```
