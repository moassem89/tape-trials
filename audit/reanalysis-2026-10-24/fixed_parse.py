"""Corrected answer extraction. Same contract as the released parse_answer, two changes:
1. If the reply contains a reasoning block, extraction runs on the text after the last
   </think> first (the final answer), falling back to the whole reply.
2. Object detection decodes JSON directly (json.JSONDecoder.raw_decode from every '{'),
   so an unmatched brace quoted earlier in the reply cannot hide a later object.
Everything else (fence preference, last-object-wins, truncation/abstention statuses) is
kept from the released parser so that only the defect changes."""
import json, sys
sys.path.insert(0, '/home/claude/tape-trials/eval-harness/harness')
import parse as P

_dec = json.JSONDecoder()

def _objects(text):
    out = []; i = 0; n = len(text)
    while True:
        j = text.find('{', i)
        if j < 0: break
        try:
            val, end = _dec.raw_decode(text, j)
            if isinstance(val, dict):
                out.append((j, end, val)); i = end; continue
        except json.JSONDecodeError:
            pass
        i = j + 1
    return out

def _extract(text):
    fenced = P.FENCE.findall(text)
    if fenced:
        objs = _objects(fenced[-1])
        if objs: return objs[-1][2], True
    objs = _objects(text)
    if objs: return objs[-1][2], True
    return None, False

def parse_answer(text):
    if text is None or not text.strip():
        return P.Parsed("no_json", raw=text or "")
    regions = []
    if '</think>' in text:
        tail = text.rsplit('</think>', 1)[1]
        if tail.strip(): regions.append(tail)
    regions.append(text)
    for reg in regions:
        val, ok = _extract(reg)
        if ok: return P.Parsed("ok", answer=val, raw=text)
    orig = P.parse_answer(text)          # keep original non-ok statuses
    return orig
