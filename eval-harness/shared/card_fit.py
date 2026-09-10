#!/usr/bin/env python3
"""Does a rung fit on a given card at this study's fixed serving settings?

Planning arithmetic only — it produces no metric and nothing here reaches a
report as a result. It exists because the operator asked whether the remaining
s6 cells can move from L40S to an A10-class card, and "try it and see" costs a
GPU slot per wrong answer.

Config numbers are read from each model's published config.json (layers,
kv_heads, head_dim); parameter counts are the published totals. Serving settings
are the ones every cell in this study already uses and which must NOT change
between cells: gpu_memory_utilization 0.90, and the max_model_len the battery
sets.
"""
import sys

CARDS = {"L40S": 48.0, "A10G": 24.0, "A10": 24.0, "L4": 24.0, "A100-40GB": 40.0}

# name: (params_B, layers, kv_heads, head_dim)
RUNGS = {
    "0.5B":  (0.494, 24, 2,  64),
    "1.5B":  (1.544, 28, 2, 128),
    "3B":    (3.086, 36, 2, 128),
    "7B":    (7.616, 28, 4, 128),
    "14B":  (14.770, 48, 8, 128),
    "7B-R":  (7.616, 28, 4, 128),   # DeepSeek-R1-Distill-Qwen-7B, Qwen2.5-7B arch
    "14B-R":(14.770, 48, 8, 128),   # DeepSeek-R1-Distill-Qwen-14B
}

UTIL = 0.90
# vLLM overhead outside weights and KV cache: CUDA graphs, activations, the
# allocator's own slack. 2.0 GB is deliberately pessimistic for a 1-GPU server.
OVERHEAD_GB = 2.0


def fit(rung, card, max_model_len):
    params_b, layers, kv_heads, head_dim = RUNGS[rung]
    total = CARDS[card]
    budget = total * UTIL
    weights = params_b * 2.0                      # bf16
    kv_per_tok = 2 * layers * kv_heads * head_dim * 2   # bytes
    free = budget - weights - OVERHEAD_GB
    tokens = free * 1e9 / kv_per_tok if free > 0 else 0.0
    seqs = tokens / max_model_len
    return {
        "rung": rung, "card": card, "budget_gb": budget, "weights_gb": weights,
        "kv_kib_per_tok": kv_per_tok / 1024, "kv_free_gb": free,
        "kv_tokens": tokens, "concurrent_seqs": seqs,
        # vLLM refuses to start if the cache cannot hold one full-length sequence.
        "starts": free > 0 and tokens >= max_model_len,
        # Under ~8 concurrent sequences the batch collapses and the cell takes
        # multiples of its L40S wall-clock; treat that as "fits but not worth it".
        "comfortable": seqs >= 8.0,
    }


def check(rung, card, max_model_len=8192):
    """Exit-code gate for queue-cell.sh. 0 = queue it, 1 = do not."""
    if rung not in RUNGS:
        print(f"card_fit: unknown rung {rung!r}", file=sys.stderr); return 1
    if card not in CARDS:
        print(f"card_fit: unknown card {card!r}", file=sys.stderr); return 1
    r = fit(rung, card, max_model_len)
    if not r["starts"]:
        print(f"card_fit: REFUSING {rung} on {card} — {r['weights_gb']:.1f} GB of "
              f"weights against a {r['budget_gb']:.1f} GB budget leaves "
              f"{r['kv_free_gb']:.1f} GB for the KV cache. vLLM will not start.",
              file=sys.stderr)
        return 1
    note = "" if r["comfortable"] else (
        f"  (note: {r['concurrent_seqs']:.1f} concurrent sequences — small batch, "
        f"expect a longer wall-clock than the L40S estimate)")
    print(f"card_fit: {rung} on {card} ok, {r['kv_free_gb']:.1f} GB KV cache, "
          f"{r['concurrent_seqs']:.1f} concurrent sequences{note}")
    return 0


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        raise SystemExit(check(sys.argv[2], sys.argv[3],
                               int(sys.argv[4]) if len(sys.argv) > 4 else 8192))
    plan = [
        ("14B",  8192,  "row 5  C8 calibration"),
        ("14B",  8192,  "row 6  C5 repeat"),
        ("0.5B", 8192,  "row 7  C2 paraphrase"),
        ("7B",   8192,  "row 8  C2 paraphrase"),
        ("3B",   8192,  "row 9  C8 calibration"),
        ("3B",   8192,  "row 10 C2 paraphrase"),
        ("1.5B", 8192,  "row 11 C2 paraphrase"),
    ]
    hdr = f"{'cell':24} {'rung':6} {'card':6} {'wts GB':>7} {'kv GB':>7} {'seqs':>6}  verdict"
    print(hdr); print("-" * len(hdr))
    for rung, mml, label in plan:
        for card in ("L40S", "A10G"):
            r = fit(rung, card, mml)
            v = ("does not start" if not r["starts"]
                 else "fits, batch too small" if not r["comfortable"]
                 else "fits")
            print(f"{label:24} {rung:6} {card:6} {r['weights_gb']:7.1f} "
                  f"{r['kv_free_gb']:7.1f} {r['concurrent_seqs']:6.1f}  {v}")
        print()
