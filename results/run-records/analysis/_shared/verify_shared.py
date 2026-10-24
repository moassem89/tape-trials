"""Fail if `serving.py` has drifted from the C5 runner it was extracted from.

The shared helpers exist so two batteries cannot disagree about what a
stratified subsample is. That guarantee is only worth something if it is
checked, so this re-extracts the same functions from `temperature/main.py` and
compares them byte for byte.
"""
import ast
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = ["make_flashinfer_importable", "probe_vllm_import_paths",
         "stratified_programs", "canonical_answer", "render_prompt", "icc_anova",
         "env_fingerprint", "start_stall_watchdog"]


def extract(path):
    src = Path(path).read_text()
    tree = ast.parse(src)
    return {n.name: ast.get_source_segment(src, n)
            for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in NAMES}


def main():
    origin = extract(HERE.parent / "temperature" / "main.py")
    shared = extract(HERE / "serving.py")
    bad = []
    for name in NAMES:
        if name not in origin:
            bad.append(f"{name}: gone from the C5 runner")
        elif name not in shared:
            bad.append(f"{name}: missing from serving.py")
        elif origin[name] != shared[name]:
            bad.append(f"{name}: drifted")
    if bad:
        print("\n".join(bad))
        sys.exit(1)
    print(f"shared helpers ok: {len(NAMES)} functions byte-identical to the C5 runner")


if __name__ == "__main__":
    main()
