#!/bin/sh
# Bundle the H5 rank-stability task for `lab task add`.
#
# The bundle is main.py, task.yaml and the inputs. It does not need the scoring
# harness: this job reads scores that were already produced and audited, never a
# model reply, so there is nothing left to score.
#
# The inputs ride in the bundle rather than being fetched on the node, for the
# reason the analysis job found out the hard way: the SDK's storage fetch hands
# back an object-store address there, not a readable file. The C2 per-item files
# are a couple of hundred kilobytes each and the C5 result files are smaller
# still, so the whole set is a few megabytes.
#
# Usage: assemble-rank.sh <destination> [storage-cache]
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
DEST=${1:?usage: assemble-rank.sh <destination> [storage-cache]}
CACHE=${2:-/tmp/s6store}

rm -rf "$DEST"
mkdir -p "$DEST/inputs/c2" "$DEST/inputs/c5"
cp "$HERE/main.py" "$HERE/task.yaml" "$DEST/"

for sub in c2 c5; do
  if [ ! -d "$CACHE/tape-trials/$sub" ]; then
    mkdir -p "$CACHE"
    lab storage download "tape-trials/$sub" "$CACHE/tape-trials"
  fi
  cp "$CACHE/tape-trials/$sub"/* "$DEST/inputs/$sub/"
done

# Seven rungs x five wordings is 35 per-item files. Fewer means the ladder has a
# hole in it, and the job would refuse anyway -- better to find that out here.
n2=$(find "$DEST/inputs/c2" -type f | wc -l)
n5=$(find "$DEST/inputs/c5" -type f | wc -l)
echo "bundled into $DEST: $n2 C2 cell files, $n5 C5 result files"
if [ "$n2" -lt 35 ]; then
  echo "warning: $n2 C2 files, expected 35 (7 rungs x 5 wordings)" >&2
fi
if [ "$n5" -lt 1 ]; then
  echo "warning: no C5 result bundled; spreads will be reported without a noise floor" >&2
fi
