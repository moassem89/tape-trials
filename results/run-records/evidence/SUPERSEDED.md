# Notice: `evidence.md` is the agent's ledger for its draft

`evidence.md` is the evidence ledger the research agent built for its own draft
(`core/paper/paper.tex`). It is kept byte for byte as the agent wrote it. Several of its
values are superseded in the revised paper (`paper/main.tex`): the parser correction
(audit finding F21) changed every number for the two distilled models, and several
analyses were redone (the paper's Appendix A lists the corrections). Check the revised
paper's numbers against `verification/rescore_transcripts.py`, not against this ledger.

The entries a reader is most likely to compare, with their revised values:

| id | ledger | revised |
|---|---|---|
| E21 | 7B-R holdout 0.8123 | 0.8259 (484/586) |
| E28 | public 14B-R 0.9644, 7B-R 0.8229 | 0.9686 (1,143/1,180), 0.8373 (988/1,180); other rungs unchanged |
| E40 | quintile medians 86 / 203 / 524 / 1,296 / 6,573 | third median is 524.5 |
| E41 | 14B-R by quintile 0.992, 0.992, 0.941, 0.949, 0.914 | 0.991, 0.991, 0.941, 0.949, 0.915 |
| E42 | 7B-R by quintile 0.872, 0.812, 0.822, 0.778, 0.778; max drop 6.0 | 0.872, 0.829, 0.839, 0.795, 0.795; max drop 4.4 |
| E70 | 8,756 failing rows | 8,726 |
| E85 | slopes +357.5, +289.0, +275.2 tokens per decade (five quintile means) | per-row holdout fits in words: 338.8, 268.6, 251.2 (14B-R, 14B-CoT, 7B-R), with program-bootstrap intervals |
| E95, E97 | 7B-R pseudocode 0.8083 against a 0.8229 headline; gap 1.5 | same items in Ampliphi: 0.775; effect +3.3 [−3.8, 11.6] |
| E99 | 7B-R suffix probe 0.7870 against a 0.8229 headline | 0.787 against 0.809 on the same items' full versions |
| E114 | 14B-R wording spread 0.0462 | 0.042 [0.017, 0.085] |
| E115 | 7B-R wording spread 0.1345, P3 0.7773 to P5 0.9118 | 0.105 [0.060, 0.165], P4 0.8109 to P5 0.9160 |
| E121 | P5 beats the frozen prompt by 3.03 [1.60, 4.34] | best paraphrase +2.7 [1.3, 4.0] |
| E146, E147 | cost of asking for a confidence 0.55 / 18.45 / 1.62 | withdrawn: the confidence battery prompted without chat templates (paper §8, correction 15) |
| E181 | 7B-R max adjacent drop 6.0; Q1–Q5 falls 7.8 (14B-R) and 9.4 (7B-R) | 4.4; 7.7 and 7.7 |
| E183 | 14B-R P1 0.9454, P5 0.9916; 7B-R P3 0.7773, P5 0.9118 | 0.9538, 0.9958; 0.8361, 0.9160 |

This table is not exhaustive. Pointed out by Zehao Fan's review of the paper (2 November 2026).
