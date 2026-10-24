#!/bin/sh
# Assemble and queue exactly one s6 battery cell.
#
#   queue-cell.sh <battery> <variant> <model> <rung> [extra -p args…]
#
#     battery   paraphrase | temperature | calibration
#     variant   plain | reason
#     model     the Hugging Face id, passed through as -p model=
#     rung      the label the artifacts are named after, as -p rung=
#
#   PLANNED=<min>       the cell's estimate from WAVES.md, used to size the deadline
#   LIMIT_MIN=<n>       override the deadline outright
#   ATTN=<backend>      force VLLM_ATTENTION_BACKEND (a mitigation; see below)
#   FLASHINFER_PIN=<v>  pin flashinfer-python (a mitigation; see below)
#   MP=0                single-process engine, no engine-core handshake (see below)
#   DRYRUN=1            assemble, fit-check and rewrite task.yaml, then stop
#                       without registering or queueing anything. Costs no
#                       GPU slot and produces no result; it exists so a
#                       whole wave can be checked before the card is free.
#
# Three mistakes this exists to prevent. Typing a model id by hand into a queue
# command is how a cell ends up labelled 7B while serving 14B weights, and the
# label is what the paper reads. A retry loop around `lab task queue` that does
# not stop on its first success queues the same work twice, which is how this
# project acquired one stopped duplicate; here the queue runs once, and a timeout
# is reported for a human to resolve rather than retried blind.
#
# And a cell with no deadline outside its own process can hold a card for a day.
# Four have. Every bundle now ships `supervise.sh` and runs under it, because the
# in-process stall watchdog in `serving.py` is a thread inside the interpreter it
# guards: when the 2026-08-22 pair froze, it froze with them and never fired. The
# in-process guard is left armed as well, since it still catches the slow-but-
# alive case the supervisor's blunt wall clock cannot distinguish.
set -e
HERE=$(cd "$(dirname "$0")" && pwd)
BATTERY=${1:?battery}; VARIANT=${2:?variant}; MODEL=${3:?model}; RUNG=${4:?rung}
shift 4
EXPERIMENT=${EXPERIMENT:-tape-trials-exp-20260820}
# L40S is sold by AWS (g6e) and Nebius. When us-east-1 has no g6e capacity the
# same cell can go to Nebius on the same card; set PROVIDER=nebius to do that.
PROVIDER=${PROVIDER:-aws}
# CARD overrides the accelerator the bundle's task.yaml asks for. Every cell in
# this study ran on L40S until 2026-08-21, so that stays the default and any
# other value is a deliberate, recorded choice — see "Which card a cell runs on"
# in WAVES.md. Only the accelerator line changes; cpus, memory, max_model_len
# and gpu_memory_utilization are held fixed, because those alter the serving
# configuration and condition C5 exists to measure exactly that.
CARD=${CARD:-L40S}

case "$BATTERY" in
  paraphrase|temperature) ASSEMBLE="$HERE/assemble-public.sh $BATTERY" ;;
  calibration)            ASSEMBLE="$HERE/calibration/assemble-c8.sh" ;;
  *) echo "unknown battery: $BATTERY" >&2; exit 1 ;;
esac

DEST=$(mktemp -d "/tmp/${BATTERY}-${RUNG}-XXXXXX")
# shellcheck disable=SC2086
$ASSEMBLE "$DEST" "$VARIANT" >/dev/null

# Refuse a rung that cannot hold its weights on the requested card, rather than
# spending a GPU slot to be told so by vLLM at load time.
python3 "$HERE/_shared/card_fit.py" --check "$RUNG" "$CARD" || exit 1

if [ "$CARD" != "L40S" ]; then
  sed -i.bak "s|^  accelerators: \"L40S:1\"|  accelerators: \"${CARD}:1\"|" "$DEST/task.yaml"
  rm -f "$DEST/task.yaml.bak"
  grep -q "accelerators: \"${CARD}:1\"" "$DEST/task.yaml" || {
    echo "refusing: accelerator rewrite to $CARD did not take" >&2; exit 1; }
  echo "card overridden to ${CARD}:1"
fi

# --- out-of-process deadline -------------------------------------------------
# supervise.sh holds the clock in the job's shell and, on the deadline, dumps
# every process in the tree with py-spy before reaping it. Sized at 1.5x the
# longest known-good comparable cell in the ledger, per the operator's rule; see
# _shared/watchdog_limit.py for how the number is derived.
cp "$HERE/_shared/supervise.sh" "$DEST/supervise.sh"
chmod +x "$DEST/supervise.sh"

PLANNED=${PLANNED:-0}
LIMIT_MIN=${LIMIT_MIN:-$(python3 "$HERE/_shared/watchdog_limit.py" "$PLANNED" "$VARIANT")}
[ -n "$LIMIT_MIN" ] || { echo "could not size the watchdog deadline" >&2; exit 1; }

# py-spy is what makes a repeat hang produce a diagnosis rather than another data
# point: it reads a frozen process from outside, so a held GIL cannot block it.
if grep -q '^setup:' "$DEST/task.yaml"; then
  sed -i.bak 's|^  pip install -q vllm transformers$|  pip install -q vllm transformers\n  pip install -q py-spy|' "$DEST/task.yaml"
  rm -f "$DEST/task.yaml.bak"
  grep -q 'py-spy' "$DEST/task.yaml" || {
    echo "refusing: py-spy was not added to setup, so a hang could not be dumped" >&2
    exit 1; }
fi

# --- optional serving mitigations --------------------------------------------
# Set by whatever the s6.3 engine probe (`4bdf6575`) endorses, and by nothing
# else. Both default to empty, so a cell queued without them runs the same
# serving configuration as every rung already measured.
#
# Any value here changes the compute path, which is a confound in exactly the
# comparison the ladder is for. The operator's condition on using one, given
# 2026-08-22, is that an already-measured neighbouring cell is re-run under the
# same setting, so there is an overlapping point showing the numbers did not
# move. That control is row OC in WAVES.md and is not optional.
ATTN=${ATTN:-}
FLASHINFER_PIN=${FLASHINFER_PIN:-}
# MP=0 forces the single-process engine. Added 2026-08-26, on the first stack
# dump this project ever captured (`a483488c`, the row 4R hang). What the dump
# shows: the launcher blocked inside LLM.__init__ with enable_multiprocessing
# True; a separate `VLLM::EngineCore` process holding 40,973 MiB of 46,068,
# which is weights plus a fully allocated KV cache, so the child had finished
# building; GPU utilisation 0%; and every thread in both processes parked on a
# futex or an epoll, including eight repeated sets of NCCL and gloo helper
# threads for a job at tensor_parallel_size 1. Nothing was computing. The child
# was ready and the parent never learned it.
#
# VLLM_ENABLE_V1_MULTIPROCESSING=0 removes that entire mechanism: no child
# process, no ZMQ ready handshake, no fork of an interpreter that already owns
# CUDA and gloo threads, no dependence on how the node's hostname resolves. It
# is a real knob in the installed vllm 0.27.1 (`envs.py` reads
# `int(os.getenv("VLLM_ENABLE_V1_MULTIPROCESSING", "1"))`), checked against the
# source rather than assumed, because a mitigation vLLM does not recognise is
# indistinguishable from no mitigation at all until the deadline fires.
#
# Two narrower candidates fit the same dump and are recorded untested, so the
# next attempt does not have to re-derive them: VLLM_WORKER_MULTIPROC_METHOD=
# spawn, which stops the fork-after-threads hazard while keeping the two-process
# architecture, and VLLM_LOOPBACK_IP=127.0.0.1, which pins the handshake to
# loopback if the node's own name is what resolves wrong. One mitigation at a
# time, so an overlap control means something.
MP=${MP:-}
PREFIX=""

if [ -n "$FLASHINFER_PIN" ]; then
  sed -i.bak "s|^  pip install -q py-spy\$|  pip install -q py-spy\n  pip install -q flashinfer-python==${FLASHINFER_PIN}|" "$DEST/task.yaml"
  rm -f "$DEST/task.yaml.bak"
  grep -q "flashinfer-python==${FLASHINFER_PIN}" "$DEST/task.yaml" || {
    echo "refusing: the flashinfer pin did not take" >&2; exit 1; }
  echo "flashinfer pinned to ${FLASHINFER_PIN}"
fi

if [ -n "$ATTN" ]; then
  PREFIX="${PREFIX}VLLM_ATTENTION_BACKEND=${ATTN} "
  echo "attention backend forced to ${ATTN}"
fi

if [ -n "$MP" ]; then
  PREFIX="${PREFIX}VLLM_ENABLE_V1_MULTIPROCESSING=${MP} "
  echo "engine multiprocessing set to ${MP} (0 = single process, no engine-core handshake)"
fi

sed -i.bak "s|^run: python main.py\$|run: ${PREFIX}sh supervise.sh ${LIMIT_MIN} dumps ${RUNG} python main.py|" "$DEST/task.yaml"
rm -f "$DEST/task.yaml.bak"
grep -q "sh supervise.sh ${LIMIT_MIN} " "$DEST/task.yaml" || {
  echo "refusing: the run command was not wrapped in the supervisor" >&2; exit 1; }
echo "supervised: wall-clock deadline ${LIMIT_MIN} min, outside the job process"

if [ -n "$DRYRUN" ]; then
  echo "dry run: assembled at $DEST; nothing registered, nothing queued"
  grep -E '^  accelerators:|^run:' "$DEST/task.yaml" | sed 's/^/  /'
  echo "  would queue: model=$MODEL rung=$RUNG provider=$PROVIDER card=$CARD"
  exit 0
fi

TASK_ID=$(cd "$DEST" && lab task add . -e "$EXPERIMENT" --no-interactive \
  | sed -n 's/.*Task created with ID: //p')
[ -n "$TASK_ID" ] || { echo "task add produced no id" >&2; exit 1; }
echo "task $TASK_ID  ($BATTERY/$VARIANT, $RUNG, $MODEL)"

# The in-process stall limit stays armed, but it no longer kills. supervise.sh
# exports SUPERVISE_DUMP_DIR, and the watchdog writes a sentinel there instead
# of calling os._exit, so a stall reaches the supervisor's dump-and-kill path.
# Before this handoff the two guards raced, the inner one won every time at 45
# minutes against 52, and three hangs were killed by the side that captures
# nothing. 45 clears the slowest legitimate silence in this study by a wide
# margin: the longest weight load was about seven minutes and the harness writes
# a line every 32 rows.
#
# 45 is not passed as a task parameter: the batteries' task.yaml schemas do not
# declare stall_minutes, and `lab task queue` rejects a key they do not list. It
# is the default in the code (`cfg.get("stall_minutes", 45)`), which is where it
# is set. Anything other than 45 needs a `stall_minutes` entry in the battery's
# task.yaml parameters block first.
lab task queue "$TASK_ID" -e "$EXPERIMENT" --no-interactive --provider "$PROVIDER" \
  -p model="$MODEL" -p rung="$RUNG" "$@" \
  -m "s6 $BATTERY battery, $RUNG rung ($MODEL), provider $PROVIDER, card $CARD, supervised at ${LIMIT_MIN} min${ATTN:+, attention $ATTN}${FLASHINFER_PIN:+, flashinfer $FLASHINFER_PIN}${MP:+, v1 multiprocessing $MP}"
