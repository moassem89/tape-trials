#!/bin/sh
# Bundle the s6.2/s6.4 analysis task for `lab task add`.
#
# The bundle carries the scoring harness and the inputs. Shipping the inputs is
# a change of mind: the first build fetched them from shared storage on the
# compute node, and the SDK handed back an object-store URI instead of a local
# file, so the job died on its first read. The whole input set -- sixteen
# transcript files, sixteen per-item files and the two splits -- is 23 MB, which
# is small enough that shipping it removes an entire class of failure for no
# meaningful cost.
#
# The download happens here, in the sandbox, where the CLI is authenticated and
# a failure is visible immediately rather than eleven minutes into a job.
#
# Usage: assemble-analysis.sh <destination> [storage-cache]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
HARNESS="$HERE/../../../s4-data-preparation/harness"
DEST=${1:?usage: assemble-analysis.sh <destination> [storage-cache]}
CACHE=${2:-/tmp/s6store}

# Start clean. A destination reused from a local pre-flight would carry that
# run's output artifacts and bytecode into the bundle, and a stale
# per_row_labelled.jsonl sitting next to the real one is a trap worth avoiding.
rm -rf "$DEST"
mkdir -p "$DEST/harness" "$DEST/inputs"
cp "$HERE/main.py" "$HERE/task.yaml" "$DEST/"
for f in parse.py score.py mocks.py; do
  cp "$HARNESS/$f" "$DEST/harness/$f"
done

# Refresh the cache only if it is missing. `storage download` skips files that
# are already there at the right size, so a re-run is cheap, but a cold sandbox
# needs the fetch and must not silently bundle nothing.
if [ ! -d "$CACHE/tape-trials" ]; then
  mkdir -p "$CACHE"
  lab storage download tape-trials "$CACHE"
fi
cp "$CACHE"/tape-trials/*.jsonl "$CACHE"/tape-trials/*.json "$DEST/inputs/"

# An empty inputs directory would let the job start and fail on its first read,
# which is exactly the failure this script exists to prevent.
n=$(find "$DEST/inputs" -type f | wc -l)
if [ "$n" -lt 34 ]; then
  echo "refusing: only $n input files bundled, expected at least 34" >&2
  exit 1
fi

echo "bundled into $DEST ($n inputs):"
find "$DEST" -type f | sed "s|$DEST/|  |" | sort | head -20
echo "  ... $(find "$DEST" -type f | wc -l) files, $(du -sh "$DEST" | cut -f1)"
