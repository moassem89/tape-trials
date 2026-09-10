#!/bin/sh
# Bundle the s6.3 engine-build probe for `lab task add`.
#
# Usage: assemble-probe.sh <destination>
#
# Much smaller than a battery bundle, and the omissions are the point: no data,
# no prompts, no harness. The failure being chased happens in the vLLM
# constructor, before any runner touches a row, so a bundle carrying the study's
# splits would only create a way to leak them.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
DEST=${1:?usage: assemble-probe.sh <destination>}

mkdir -p "$DEST"
cp "$HERE/main.py" "$DEST/"
cp "$HERE/engine_probe.py" "$DEST/"
cp "$HERE/task.yaml" "$DEST/"
cp "$HERE/../_shared/serving.py" "$DEST/serving.py"
cp "$HERE/../_shared/supervise.sh" "$DEST/supervise.sh"
chmod +x "$DEST/supervise.sh"

if find "$DEST" -name '*.jsonl' | grep -q .; then
  echo "refusing: the probe bundle needs no data and has picked some up" >&2
  exit 1
fi

python3 "$HERE/../_shared/verify_shared.py"
echo "bundled into $DEST:"
find "$DEST" -type f | sed "s|$DEST/|  |" | sort
