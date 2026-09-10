"""Job entrypoint: build the interpreter here, in the open, then run the work under it.

Ampliphi 1.0.0 requires Python 3.13 and the provider image ships 3.12 with the Transformer
Lab SDK installed against it, so one interpreter cannot be both. The job is therefore split:
this wrapper runs under the system interpreter and does everything that talks to the
platform (config, logging, progress, artifacts, terminal status), while `main.py` runs under
a 3.13 interpreter and does the science. They meet at two files, a config handed down and an
output directory handed back.

The bootstrap that builds that 3.13 interpreter used to live in the task's `setup:` block,
where five builds died without leaving a line of evidence. It now lives in `bootstrap.py`
and runs from here, where its output reaches the task log. A heartbeat artifact is saved
before any of it, so a machine that vanishes mid-run still leaves proof the run step was
reached, and the bootstrap's own record is saved whether it succeeded or failed.

Artifacts are uploaded before the exit status is judged, so a run that fails a correctness
check still hands back the evidence of what it rejected.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import bootstrap

try:
    from lab import lab
except ImportError:
    lab = None

HERE = Path(__file__).resolve().parent
CHILD = "main.py"
OUT_DIR = "out"
ARTIFACTS = ("dataset.jsonl", "rejections.jsonl", "pilot_cross_check.json", "summary.json")


def emit(line: str) -> None:
    print(line, flush=True)
    if lab is not None:
        try:
            lab.log(line[:2000])
        except Exception:
            pass


def progress(percent: int) -> None:
    if lab is not None:
        try:
            lab.update_progress(percent)
        except Exception:
            pass


def save(path: Path) -> None:
    if not path.exists():
        return
    emit(f"saving {path.name} ({path.stat().st_size} bytes)")
    if lab is not None:
        try:
            lab.save_artifact(str(path))
        except Exception as exc:
            emit(f"could not save artifact {path.name}: {exc}")


def fail(message: str) -> None:
    emit(message)
    if lab is not None:
        try:
            lab.error(message)
        except Exception:
            pass
    raise SystemExit(1)


def manifest(out_dir: Path) -> None:
    """Print proof of what was produced, to the channel that is known to survive.

    Probe C showed that everything a job prints comes back in the machine log while
    nothing it hands the SDK necessarily does. So the run states, in the log itself, the
    size and checksum of every file it built and the first row of the corpus. A build
    whose artifacts fail to arrive is then still a build whose output can be described,
    counted and matched against a re-run, instead of a second hour of pure silence.
    """
    emit("--- manifest of everything this run produced ---")
    for path in sorted(out_dir.iterdir()):
        if not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = ""
        if path.suffix == ".jsonl":
            with path.open() as handle:
                rows = f", {sum(1 for _ in handle)} rows"
        emit(f"  {path.name}: {path.stat().st_size} bytes{rows}, sha256 {digest}")
    head = out_dir / "dataset.jsonl"
    if head.exists():
        with head.open() as handle:
            first = handle.readline().strip()
        emit(f"  first corpus row: {first[:1500]}")
    emit("--- end of manifest ---")


def upload(out_dir: Path) -> list[str]:
    """Save every artifact that exists. Returns the names that are missing."""
    missing = []
    for name in ARTIFACTS:
        path = out_dir / name
        if path.exists():
            save(path)
        else:
            missing.append(name)
    return missing


def main() -> None:
    cfg: dict = {}
    if lab is not None:
        lab.init()
        try:
            cfg = dict(lab.get_config() or {})
        except Exception:
            cfg = {}

    out_dir = HERE / OUT_DIR if OUT_DIR else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    heartbeat = out_dir / "heartbeat.json"
    heartbeat.write_text(json.dumps({
        "reached_run_step": True,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": sys.version,
        "executable": sys.executable,
        "cwd": os.getcwd(),
        "parameters": cfg,
    }, indent=2))
    save(heartbeat)
    emit(f"run step reached under {sys.version.split()[0]} at {sys.executable}")
    progress(2)

    bootstrap.configure(emit)
    python = bootstrap.interpreter()
    record = out_dir / "bootstrap.json"
    record.write_text(json.dumps(
        {"interpreter": str(python) if python else None, "steps": bootstrap.steps()}, indent=2))
    save(record)
    if python is None:
        fail("could not build a Python 3.13 interpreter with the Ampliphi toolchain on this "
             "machine; every bootstrap route failed, with its reason on the lines above")
    emit(f"work interpreter ready: {python}")
    progress(5)

    cfg_path = HERE / "job_config.json"
    cfg_path.write_text(json.dumps(cfg, indent=2))
    env = dict(os.environ, JOB_CONFIG=str(cfg_path), BUILD_OUT=str(out_dir),
               PYTHONUNBUFFERED="1")
    child = subprocess.Popen([str(python), CHILD], cwd=HERE, env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             bufsize=1)
    assert child.stdout is not None
    for line in child.stdout:
        line = line.rstrip("\n")
        print(line, flush=True)
        if line.startswith("##PROGRESS "):
            try:
                progress(int(line.split()[1]))
            except Exception:
                pass
        elif lab is not None and line and not line.startswith("##"):
            try:
                lab.log(line[:2000])
            except Exception:
                pass
    code = child.wait()

    manifest(out_dir)
    missing = upload(out_dir)
    if code != 0:
        fail(f"the job exited {code}; see the log above for the stage it stopped in")
    if missing:
        fail(f"the job exited 0 but did not write {', '.join(missing)}")

    progress(100)
    if lab is not None:
        try:
            lab.finish()
        except Exception:
            pass


if __name__ == "__main__":
    main()
