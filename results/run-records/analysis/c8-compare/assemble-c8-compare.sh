#!/bin/sh
# Bundle the cross-rung C8 comparison for `lab task add`.
#
#   assemble-c8-compare.sh <destination> [min-cells] [storage-cache]
#
# Inputs ride in the bundle rather than being fetched on the node. That is the
# same choice the s6.2/s6.4 analysis made after its first build died on its
# first read: the SDK handed back an object-store URI where the code expected a
# local file. The whole C8 input set is under a megabyte per cell, so shipping
# it removes the failure mode for nothing.
#
# The download happens here, in the sandbox, where the CLI is authenticated and
# a missing file is visible immediately rather than eleven minutes into a job.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
DEST=${1:?usage: assemble-c8-compare.sh <destination> [min-cells] [cache]}
MIN=${2:-2}
CACHE=${3:-/tmp/s6store-c8}

rm -rf "$DEST"
mkdir -p "$DEST/inputs"
cp "$HERE/main.py" "$HERE/task.yaml" "$DEST/"
cp "$HERE/../_shared/calib_metrics.py" "$DEST/calib_metrics.py"

rm -rf "$CACHE"; mkdir -p "$CACHE"
lab storage download tape-trials/c8 "$CACHE" >/dev/null
find "$CACHE" -name 'calibration_*.json' -exec cp {} "$DEST/inputs/" \;
find "$CACHE" -name 'per_row_confidence_*.jsonl' -exec cp {} "$DEST/inputs/" \;

# The cost-of-asking reading needs each rung's recorded C1 public per-item file,
# restricted later to the C8 row ids. A rung whose file is missing is reported
# as unpriced rather than silently dropped, so a partial fetch is not fatal.
for f in "$DEST"/inputs/calibration_*.json; do
  [ -e "$f" ] || continue
  rung=$(basename "$f" .json); rung=${rung#calibration_}
  safe=$(echo "$rung" | tr '.' '_')
  lab storage download "tape-trials/per_item_${safe}_public.jsonl" "$DEST/inputs/" \
    >/dev/null 2>&1 || echo "note: no C1 per-item file for $rung; it will be unpriced"
done

n=$(find "$DEST/inputs" -name 'calibration_*.json' | wc -l)
if [ "$n" -lt "$MIN" ]; then
  echo "refusing: $n C8 cell(s) bundled, need at least $MIN." >&2
  echo "The comparison exists to separate a property of the task from a property" >&2
  echo "of one rung, and one cell cannot do that. Wait for the queue." >&2
  exit 1
fi

echo "bundled into $DEST ($n cells):"
find "$DEST" -type f | sed "s|$DEST/|  |" | sort
