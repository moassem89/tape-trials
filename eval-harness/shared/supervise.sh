#!/bin/sh
# Wall-clock supervision for one GPU sub-run, from OUTSIDE the process it guards.
#
#   supervise.sh <limit_minutes> <dump_dir> <label> <command...>
#
# Why this exists, and why the guard it replaces was not enough.
#
# Four cells in this study froze inside vLLM's engine constructor and held their
# cards until a human noticed: two for about twenty hours, two for eighty-five
# minutes. The second pair ran under an in-process stall watchdog
# (`start_stall_watchdog` in serving.py) which never fired. That is not a bug in
# the watchdog. It is a watchdog thread inside the interpreter that froze, so
# whatever holds the GIL during the hang starves the guard along with everything
# else. An in-process timer cannot bound a hang deep enough to stop the
# interpreter.
#
# So the clock lives here, in the job's shell, in a process that shares nothing
# with the guarded one but a pid. The operator's instruction on 2026-08-22 was to
# move the timeout outside the job process, to a scheduler or supervisor level
# kill. There is no scheduler level available: `minutes_requested` in task.yaml
# is documented as guidance, not enforcement, which is how a job that asked for
# 420 minutes held a card for 1,370. Supervisor level is what is left, and it is
# enough, because the failure is confined to the guarded tree.
#
# The tree, not the process. vLLM v1 runs its engine core and its workers as
# separate processes, and those are the ones holding GPU memory. Killing the
# launcher alone leaves them orphaned on the card, so the next arm finds no
# memory and fails for a reason that has nothing to do with what it was testing.
# Descendants are enumerated from /proc before anything is signalled, and any pid
# nvidia-smi still reports against the GPU afterwards is swept as a backstop.
#
# For the same reason, the dump covers every process in the tree. A launcher
# blocked reading a pipe from a frozen engine core tells you nothing; the frames
# that matter are in the child. Three methods are tried per process, in order of
# how much they show, and each reads from outside so a held GIL cannot block it:
#
#   1. py-spy dump --native   Python frames plus the C and CUDA frames beneath,
#                             which is the half that names the actual hang.
#   2. py-spy dump            Python frames only, if libunwind is unavailable.
#   3. SIGABRT + faulthandler Every thread's traceback, written by a handler that
#                             does not take the GIL. Needs PYTHONFAULTHANDLER=1
#                             in the guarded process; it is exported below.
#
# Kernel wait channels and nvidia-smi are captured alongside, because a spin
# inside a CUDA call and a wait on a lock look identical in a Python stack and
# completely different in those two.
#
# Exit codes: the guarded command's own status when it finishes in time, or 75
# when it is killed on the deadline. 75 is reserved so a caller can tell a
# timeout from any code the command itself might return. A stall signalled from
# inside (see $STALL_FLAG below) takes the same path and the same code: from the
# caller's side it is the same event, a cell that stopped making progress and
# was killed after being photographed.
set -e

LIMIT_MIN=${1:?usage: supervise.sh <limit_minutes> <dump_dir> <label> <command...>}
DUMP_DIR=${2:?dump_dir}
LABEL=${3:?label}
shift 3
[ "$#" -gt 0 ] || { echo "supervise: no command given" >&2; exit 2; }

mkdir -p "$DUMP_DIR"
LIMIT_S=$(awk "BEGIN{printf \"%d\", $LIMIT_MIN * 60}")
POLL_S=5
STACK="$DUMP_DIR/$LABEL.stack.txt"

# faulthandler is the last-resort dump path and must be armed before start.
PYTHONFAULTHANDLER=1
export PYTHONFAULTHANDLER

# The guarded process's in-process stall watchdog writes $DUMP_DIR/STALL rather
# than exiting when it sees this, so a stall reaches the dump path here instead
# of releasing the card with nothing captured. See start_stall_watchdog in
# serving.py; three hangs were lost to the two guards racing before this existed.
SUPERVISE_DUMP_DIR=$DUMP_DIR
export SUPERVISE_DUMP_DIR
STALL_FLAG="$DUMP_DIR/STALL"
rm -f "$STALL_FLAG"

# Every pid under $1, deepest last, so a tree can be signalled parents-first and
# reaped children-first. Reads /proc directly: pgrep and pstree are not
# guaranteed to be in a training image, and /proc always is.
descendants() {
  _d_parent=$1
  _d_frontier=$1
  _d_all=""
  _d_depth=0
  while [ -n "$_d_frontier" ] && [ "$_d_depth" -lt 12 ]; do
    _d_next=""
    for _d_p in $_d_frontier; do
      for _d_stat in /proc/[0-9]*/stat; do
        [ -r "$_d_stat" ] || continue
        # comm can contain spaces and parentheses, so ppid is read after the
        # last ')' rather than by field number from the start of the line.
        _d_line=$(cat "$_d_stat" 2>/dev/null) || continue
        _d_pid=${_d_line%% *}
        _d_rest=${_d_line#*') '}
        _d_ppid=$(echo "$_d_rest" | awk '{print $2}')
        [ "$_d_ppid" = "$_d_p" ] && _d_next="$_d_next $_d_pid"
      done
    done
    _d_all="$_d_all $_d_next"
    _d_frontier=$_d_next
    _d_depth=$((_d_depth + 1))
  done
  echo "$_d_parent $_d_all"
}

# Everything nvidia-smi still attributes to the GPU. The backstop for a worker
# that reparented away from our tree before we enumerated it.
gpu_pids() {
  command -v nvidia-smi >/dev/null 2>&1 || return 0
  timeout 60 nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null \
    | tr -d ' ' | grep -E '^[0-9]+$' || true
}

dump_one() {
  _p=$1
  echo >> "$STACK"
  echo "======== pid $_p  ($(cat /proc/$_p/comm 2>/dev/null)) ========" >> "$STACK"
  if command -v py-spy >/dev/null 2>&1; then
    if ! timeout 120 py-spy dump --pid "$_p" --native --locals >> "$STACK" 2>&1; then
      echo "(py-spy --native failed here; retrying without native frames)" >> "$STACK"
      timeout 120 py-spy dump --pid "$_p" >> "$STACK" 2>&1 \
        || echo "(py-spy plain dump also failed for pid $_p)" >> "$STACK"
    fi
  else
    echo "(py-spy not installed; relying on faulthandler)" >> "$STACK"
  fi
  echo "-- per-thread state / wchan --" >> "$STACK"
  for _t in /proc/"$_p"/task/*; do
    [ -d "$_t" ] || continue
    printf '   %s  comm=%-16s state=%s  wchan=%s\n' \
      "$(basename "$_t")" \
      "$(cat "$_t/comm" 2>/dev/null)" \
      "$(awk '{sub(/^[^)]*\) /,""); print $1}' "$_t/stat" 2>/dev/null)" \
      "$(cat "$_t/wchan" 2>/dev/null)" >> "$STACK" 2>&1
  done
  echo "-- kernel stack --" >> "$STACK"
  cat "/proc/$_p/stack" >> "$STACK" 2>&1 || echo "   (needs privileges)" >> "$STACK"
}

echo "supervise[$LABEL]: starting, wall-clock limit ${LIMIT_MIN} min" >&2
START=$(date +%s)
"$@" &
PID=$!

while : ; do
  if ! kill -0 "$PID" 2>/dev/null; then
    set +e; wait "$PID"; RC=$?; set -e
    ELAPSED=$(( $(date +%s) - START ))
    echo "supervise[$LABEL]: exited rc=$RC after ${ELAPSED}s" >&2
    exit "$RC"
  fi
  ELAPSED=$(( $(date +%s) - START ))
  if [ -f "$STALL_FLAG" ]; then
    REASON="STALL SIGNALLED at ${ELAPSED}s ($(cat "$STALL_FLAG" 2>/dev/null))"
    break
  fi
  [ "$ELAPSED" -ge "$LIMIT_S" ] && { REASON="DEADLINE at ${ELAPSED}s"; break; }
  sleep "$POLL_S"
done

TREE=$(descendants "$PID")
echo "supervise[$LABEL]: ${REASON}; tree =$TREE" >&2
echo "supervise[$LABEL]: capturing stacks before kill" >&2
{
  echo "=== supervise dump: $LABEL ==="
  echo "captured_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "elapsed_seconds: $ELAPSED"
  echo "limit_minutes: $LIMIT_MIN"
  echo "trigger: $REASON"
  echo "launcher_pid: $PID"
  echo "tree:$TREE"
} > "$STACK"

for p in $TREE; do
  [ -d "/proc/$p" ] || continue
  dump_one "$p"
done

echo >> "$STACK"; echo "--- nvidia-smi ---" >> "$STACK"
timeout 60 nvidia-smi >> "$STACK" 2>&1 || echo "(nvidia-smi failed or itself hung)" >> "$STACK"
echo >> "$STACK"; echo "--- nvidia-smi compute-apps ---" >> "$STACK"
timeout 60 nvidia-smi --query-compute-apps=pid,used_memory --format=csv >> "$STACK" 2>&1 \
  || echo "(unavailable)" >> "$STACK"

# faulthandler last: it ends the processes it reports on. Its output goes to each
# process's stderr, which is the job log rather than this file.
#
# One process at a time, with a pause between. Every process in the tree shares
# one stderr, and signalling them together interleaves their tracebacks
# character by character into something unreadable. The pause is what keeps each
# one intact, and legibility is the whole point of capturing them.
echo >> "$STACK"
echo "--- SIGABRT sent per process; faulthandler tracebacks follow in the job log ---" >> "$STACK"
for p in $TREE; do
  kill -0 "$p" 2>/dev/null || continue
  echo "supervise[$LABEL]: SIGABRT -> pid $p ($(cat /proc/$p/comm 2>/dev/null))" >&2
  kill -ABRT "$p" 2>/dev/null || true
  sleep 3
done
sleep 5

# Reap the tree, then sweep anything still on the card.
for p in $TREE; do kill -9 "$p" 2>/dev/null || true; done
sleep 3
for p in $(gpu_pids); do
  [ "$p" = "$$" ] && continue
  if kill -0 "$p" 2>/dev/null; then
    echo "supervise[$LABEL]: pid $p still holds the GPU after the tree was reaped; killing" >&2
    echo "note: pid $p still held GPU memory after the tree was reaped" >> "$STACK"
    kill -9 "$p" 2>/dev/null || true
  fi
done
sleep 2

# Get the dump off this machine. It is written to local disk, and a killed job's
# machine is torn down shortly after, so the file alone does not survive.
#
# Three exits are tried because the reliable one depends on who died. A runner
# that is still alive saves the dump as a job artifact itself (see
# probe/main.py). A runner that the supervisor just killed cannot, so the dump
# goes to shared storage from here, and is echoed into the job log as well. The
# echo is the last resort and is not always enough on its own: machine logs are
# not retained for every job on this platform, which is exactly why the upload
# was added.
if command -v lab >/dev/null 2>&1; then
  # </dev/null and a timeout on purpose: this runs on a deadline path with a
  # held GPU, and an upload that stops to ask something would hang the cleanup
  # it is part of.
  if timeout 180 lab storage upload "$STACK" --dest "tape-trials/dumps" \
       </dev/null >/dev/null 2>&1; then
    echo "supervise[$LABEL]: dump uploaded to tape-trials/dumps/$(basename "$STACK")" >&2
  else
    echo "supervise[$LABEL]: storage upload failed; the dump is in the log below only" >&2
  fi
fi

echo "supervise[$LABEL]: dump follows, $(wc -c < "$STACK") bytes" >&2
echo "===SUPERVISE-DUMP-BEGIN $LABEL===" >&2
head -c 400000 "$STACK" >&2
echo "" >&2
echo "===SUPERVISE-DUMP-END $LABEL===" >&2

echo "supervise[$LABEL]: killed after deadline; dump at $STACK" >&2
exit 75
