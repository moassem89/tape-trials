#!/bin/sh
# Pull one finished battery cell's artifacts down and park them in shared
# storage where the aggregation jobs expect to find them.
#
# The two aggregators (rank-stability for H5, and whatever reads C8) take the
# whole matrix at once, so every cell has to land under the same prefix with the
# same naming. Doing that by hand once per cell is how a rung ends up missing a
# wording and the ladder quietly ranks on a hole. This script is the one path.
#
#   collect-cell.sh <job-id> c2     -> tape-trials/c2/
#   collect-cell.sh <job-id> c5     -> tape-trials/c5/
#   collect-cell.sh <job-id> c8     -> tape-trials/c8/
#
# DEST=<prefix> parks the files somewhere else. A CONTROL cell must use it. Row
# OC repeats the 14B-R C8 cell, so its files are named `calibration_14B-R.json`
# and `per_row_confidence_14B-R.jsonl` — exactly the names cbc1215f already
# occupies. Sent to `tape-trials/c8/` they would overwrite the reference the
# control is being compared against, and c8-compare globs that prefix, so a
# renamed copy would instead enter the matrix as an invented extra rung. Neither
# is recoverable from the numbers afterwards. Controls go to
# `tape-trials/controls/`, which no aggregator reads:
#
#   DEST=tape-trials/controls collect-cell.sh <job-id> c8
#
# Uploading over a file that already exists needs OVERWRITE=1 and a reason. The
# default refuses, because every name in these prefixes is derived from the rung
# rather than the job, so a second cell on the same rung silently replaces the
# first.
#
# Only the files an aggregator reads are uploaded. Transcripts stay on the job:
# they are large, and nothing downstream re-scores a battery cell the way the
# holdout analysis re-scores the sweep.
set -e
JOB=${1:?usage: collect-cell.sh <job-id> <c2|c5|c8> [experiment]}
KIND=${2:?usage: collect-cell.sh <job-id> <c2|c5|c8> [experiment]}
EXP=${3:-tape-trials-exp-20260820}
WORK=$(mktemp -d)
DEST=${DEST:-tape-trials/$KIND}
OVERWRITE=${OVERWRITE:-0}

case "$KIND" in
  c2) PATTERN='per_item_*.jsonl result_*.json' ;;
  c5) PATTERN='result_*.json disagreements_*.jsonl' ;;
  c8) PATTERN='calibration_*.json per_row_confidence_*.jsonl' ;;
  *)  echo "unknown battery kind: $KIND" >&2; exit 1 ;;
esac

status=$(lab --format json job status "$JOB" -e "$EXP" | python3 -c \
  'import sys,json; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d.get("status"))')
if [ "$status" != "COMPLETE" ]; then
  echo "refusing: job $JOB is $status, not COMPLETE" >&2
  exit 1
fi

# --file takes a glob and can be repeated; without it the whole job comes down
# as a zip, which would mean unpacking a few hundred megabytes of transcripts to
# reach a handful of score files.
args=""
for pat in $PATTERN; do
  args="$args --file $pat"
done
# shellcheck disable=SC2086
lab job download "$JOB" -e "$EXP" -o "$WORK" $args

# What is already parked under the destination, so an upload cannot silently
# replace a cell that is already collected.
existing=$(lab --format json storage ls | python3 -c \
  'import sys,json;
d=json.load(sys.stdin)
print("\n".join(x["relpath"] for x in d if isinstance(x, dict) and "relpath" in x))')

found=0
for f in "$WORK"/*; do
  [ -f "$f" ] || continue
  base=$(basename "$f")
  if [ "$OVERWRITE" != "1" ] && echo "$existing" | grep -qxF "$DEST/$base"; then
    echo "refusing: $DEST/$base already exists." >&2
    echo "  A C8 or C2 filename carries the rung, not the job id, so this is a" >&2
    echo "  second cell on a rung that is already collected. If it is a control," >&2
    echo "  re-run with DEST=tape-trials/controls. If it really should replace" >&2
    echo "  what is there, re-run with OVERWRITE=1 and say why in the report." >&2
    exit 1
  fi
  lab storage upload "$f" --dest "$DEST" --force
  found=$((found + 1))
done

if [ "$found" -eq 0 ]; then
  echo "refusing: job $JOB produced no files matching '$PATTERN'" >&2
  exit 1
fi
echo "collected $found file(s) from $JOB into $DEST"
