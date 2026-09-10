"""Build a Python 3.13 with the Ampliphi toolchain on the job machine, out loud.

This used to be the task's `setup:` block. Five builds died in it and none of them left a
single line of evidence: the platform discards a setup step's output and powers the machine
down when it fails, so the job lands in COMPLETE with no logs, no artifacts and progress 0,
which is indistinguishable from a fast success. Running the same commands from the run step
puts every one of them in the task log, bounded by its own timeout, announced before it runs
and reported after it.

Routes are tried cheapest first and the first that yields an interpreter able to import the
toolchain wins: a venv left by an earlier step, a 3.13 already on the image, uv already
installed, uv from PyPI, then the astral.sh installer script. `steps()` returns the record of
what was tried, for saving alongside the job's artifacts.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

HOME = Path.home()
VENV = HOME / "aphi-venv"
PROBE = ("import sys; from ampliphi.utils import get_ast; "
         "from varphi_python import VarphiToPythonCompiler; print(sys.version.split()[0])")
TOOLCHAIN = ("ampliphi==1.0.0", "varphi-python==2.0.6")

_LOG: list[dict] = []
_emit = print


def configure(emit) -> None:
    """Point this module's output at the caller's logger."""
    global _emit
    _emit = emit


def steps() -> list[dict]:
    return list(_LOG)


def _say(line: str) -> None:
    try:
        _emit(line)
    except Exception:
        print(line, flush=True)


def _run(name: str, argv: list, timeout: int) -> dict:
    _say(f"--- {name}: {' '.join(str(a) for a in argv)} (timeout {timeout}s)")
    started = time.time()
    record: dict = {"name": name, "argv": [str(a) for a in argv]}
    try:
        proc = subprocess.run([str(a) for a in argv], capture_output=True, text=True,
                              timeout=timeout)
        record["returncode"] = proc.returncode
        record["stdout_tail"] = proc.stdout[-800:]
        record["stderr_tail"] = proc.stderr[-800:]
    except subprocess.TimeoutExpired:
        record["returncode"] = None
        record["stdout_tail"] = ""
        record["stderr_tail"] = f"timed out after {timeout}s"
    except Exception as exc:
        record["returncode"] = None
        record["stdout_tail"] = ""
        record["stderr_tail"] = f"{type(exc).__name__}: {exc}"
    record["seconds"] = round(time.time() - started, 1)
    _LOG.append(record)
    _say(f"    -> rc={record['returncode']} in {record['seconds']}s")
    for stream in ("stdout_tail", "stderr_tail"):
        text = (record.get(stream) or "").strip()
        if text:
            for line in text.splitlines()[-6:]:
                _say(f"    {stream[:6]}| {line[:300]}")
    return record


def _ok(record: dict) -> bool:
    return record.get("returncode") == 0


def _usable(python: Path) -> bool:
    """A 3.13 that imports the toolchain is the only thing that counts as ready."""
    return python.exists() and _ok(_run(f"probe {python}", [python, "-c", PROBE], 120))


def _find_uv() -> Path | None:
    found = shutil.which("uv")
    if found:
        return Path(found)
    for candidate in (HOME / ".local" / "bin" / "uv", HOME / ".cargo" / "bin" / "uv",
                      Path(sys.executable).parent / "uv"):
        if candidate.exists():
            return candidate
    return None


def _with_uv(uv: Path) -> Path | None:
    if not _ok(_run("uv version", [uv, "--version"], 60)):
        return None
    if not _ok(_run("uv venv 3.13", [uv, "venv", "--python", "3.13", VENV], 600)):
        return None
    python = VENV / "bin" / "python"
    if not _ok(_run("uv pip install toolchain",
                    [uv, "pip", "install", "--python", python, *TOOLCHAIN], 600)):
        return None
    return python if _usable(python) else None


def interpreter() -> Path | None:
    """Return a ready Python 3.13, or None with the reason for each route in `steps()`."""
    if _usable(VENV / "bin" / "python"):
        return VENV / "bin" / "python"

    system_313 = shutil.which("python3.13")
    if system_313:
        _say(f"image ships python3.13 at {system_313}")
        if _ok(_run("venv from image 3.13", [system_313, "-m", "venv", VENV], 180)):
            python = VENV / "bin" / "python"
            if _ok(_run("pip install toolchain",
                        [python, "-m", "pip", "install", "-q", *TOOLCHAIN], 600)):
                if _usable(python):
                    return python

    uv = _find_uv()
    if uv is None:
        _say("no uv on PATH; installing it from PyPI")
        if _ok(_run("pip install uv", [sys.executable, "-m", "pip", "install", "-q", "uv"], 300)):
            uv = _find_uv()
    if uv is not None:
        python = _with_uv(uv)
        if python is not None:
            return python

    _say("falling back to the astral.sh installer")
    if _ok(_run("astral installer", ["bash", "-lc",
                'set -o pipefail; curl -LsSf --max-time 120 https://astral.sh/uv/install.sh | sh'],
                300)):
        uv = _find_uv()
        if uv is not None:
            python = _with_uv(uv)
            if python is not None:
                return python

    return None
