#!/bin/sh
# Bundle the C8 calibration battery for `lab task add`.
#
# Usage: assemble-c8.sh <destination> [plain|reason]
#
# Refuses to build a bundle containing the sealed holdout. C8 reads every row
# six times, and the one guarantee C7 rests on is that the holdout was read
# once.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
S4="$HERE/../../../s4-data-preparation"
DEST=${1:?usage: assemble-c8.sh <destination> [plain|reason]}
VARIANT=${2:-plain}

mkdir -p "$DEST/harness" "$DEST/prompts" "$DEST/data"
cp "$HERE/main.py" "$DEST/"
cp "$HERE/task.$VARIANT.yaml" "$DEST/task.yaml"
cp "$HERE/../_shared/serving.py" "$DEST/serving.py"
for f in parse.py score.py mocks.py; do cp "$S4/harness/$f" "$DEST/harness/$f"; done
for f in P1_frozen.txt P6_confidence.txt; do cp "$S4/prompts/$f" "$DEST/prompts/$f"; done
cp "$S4/splits/public.jsonl" "$DEST/data/public.jsonl"

if find "$DEST" -name 'private.jsonl' -o -name 'holdout*.jsonl' | grep -q .; then
  echo "refusing: the bundle contains a copy of the sealed holdout" >&2
  exit 1
fi

python3 "$HERE/../_shared/verify_shared.py"
echo "bundled into $DEST (task.$VARIANT.yaml):"
find "$DEST" -type f | sed "s|$DEST/|  |" | sort
