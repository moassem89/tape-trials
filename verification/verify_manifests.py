#!/usr/bin/env python3
"""Check every file in the kit against the sha256 manifests it shipped with.

Each package directory carries a MANIFEST.md whose lines are `sha256  path  bytes`.
This script recomputes every hash and reports matches, mismatches, files the
manifest lists that are absent, and files present but unlisted.

Two absences are expected in the public repository and are reported as WITHHELD
rather than MISSING: the sealed holdout split (`sealed-holdout/private.jsonl`) and
the machine-generated paper build (`core/paper/paper.tex`, `paper.pdf`, `arxiv.sty`).
"""
from __future__ import annotations

import hashlib
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WITHHELD = {
    "sealed-holdout/private.jsonl": "sealed holdout — never published (see README)",
    "core/paper/paper.tex": "machine-generated draft under revision (see README)",
    "core/paper/paper.pdf": "machine-generated draft under revision (see README)",
    "core/paper/arxiv.sty": "carries the generator's watermark; withheld with the draft",
}
PACKAGES = ["benchmark-corpus", "core", "eval-harness", "results", "sealed-holdout"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    bad = 0
    for pkg in PACKAGES:
        man = ROOT / pkg / "MANIFEST.md"
        entries = re.findall(r"^([0-9a-f]{64})\s+(\S+)\s+(\d+)\s*$", man.read_text(), re.M)
        ok = mismatch = withheld = missing = 0
        listed = set()
        for digest, rel, size in entries:
            p = ROOT / pkg / rel
            listed.add(p.resolve())
            key = f"{pkg}/{rel}"
            if not p.exists():
                if key in WITHHELD:
                    withheld += 1
                else:
                    missing += 1
                    bad += 1
                    print(f"  MISSING   {key}")
                continue
            if sha256(p) == digest:
                ok += 1
            else:
                mismatch += 1
                bad += 1
                print(f"  MISMATCH  {key}  ({p.stat().st_size} bytes vs manifest {size})")
        unlisted = []
        for dirpath, _, files in os.walk(ROOT / pkg):
            for fn in files:
                p = Path(dirpath, fn).resolve()
                if p not in listed and fn != "MANIFEST.md" and "transcripts" not in str(p) \
                        and not fn.startswith("WITHHELD") and fn != "README.md":
                    unlisted.append(p.relative_to(ROOT))
        print(f"{pkg:18} listed={len(entries):3}  ok={ok:3}  mismatch={mismatch}  missing={missing}  withheld={withheld}")
        for u in unlisted:
            print(f"  unlisted (added by this repository or by the kit): {u}")
    print("\nRESULT:", "every present manifest entry verifies" if bad == 0 else f"{bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
