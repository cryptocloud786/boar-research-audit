#!/usr/bin/env bash
# Downloads exactly the public files this audit reads, pinned to the commits/revision audited (no clone needed).
#   boar-research 0590f3cf2fb1c1d4abba72983fc1c95f3c3734b1 (v1.1.2)
#   boar-bench    74a8984c09002a07e910837e1afc5e0dafb0dc68 (v1.1.2)
#   boar-traces   HF dataset revision f96e277cf8584b38c35c01106c1fe77457dfaa81
#   labrat-boar-fork 0ecd282d03a0c2e5a1130cd0016618b751506291 (Citations.kt, AnswerPipeline.kt, DeviceEvalRunner.kt, ChatViewModel.kt)
# usage: bash scripts/fetch_inputs.sh            -> ./inputs/{boar-research,boar-bench,labrat-boar-fork}
set -euo pipefail
cd "$(dirname "$0")/.."
BR=0590f3cf2fb1c1d4abba72983fc1c95f3c3734b1; BB=74a8984c09002a07e910837e1afc5e0dafb0dc68; HF=f96e277cf8584b38c35c01106c1fe77457dfaa81; LR=0ecd282d03a0c2e5a1130cd0016618b751506291
get() { mkdir -p "$(dirname "$2")"; curl -fsSL --retry 3 "$1" -o "$2"; echo "ok $2"; }
C=rnd/research/coordinator/arms
for f in $C/device-final/aggregates/m1.json $C/device-final/tools/m1_agg.py $C/device-final/tools/m1_traces.py \
         rnd/research/coordinator/repro/cut7.vs-0cfd4a77.patch; do
  get "https://raw.githubusercontent.com/r4topunk/boar-research/$BR/$f" "inputs/boar-research/$f"; done
for f in device-final/judge/dev-s42.opus.judgments.jsonl device-final/judge/dev-s42.codex.judgments.jsonl \
         device-final/judge/dev-s43.opus.judgments.jsonl device-final/judge/dev-s43.codex.judgments.jsonl \
         device-final/traces/dev-s42.traces.jsonl device-final/traces/dev-s43.traces.jsonl \
         device-final/out/df-m1-v04-s42.jsonl device-final/out/df-m1-v04-s42b.jsonl device-final/out/df-m1-v04-s43.jsonl \
         device-final/out/df-m2-probes-s42.jsonl device-final/out/df-m3-packproof-s42.jsonl device-final/out/df-m4-uxmatrix-s42.jsonl \
         native-rc/judge/rf/lite-s42.opus.judgments.jsonl native-rc/judge/rf/lite-s42.codex.judgments.jsonl \
         native-rc/work/v04/bench/questions.jsonl native-rc/work/v04/traces/lite-s42.traces.jsonl; do
  get "https://huggingface.co/datasets/r4topunk/boar-traces/resolve/$HF/$C/$f" "inputs/boar-research/$C/$f"; done
for f in bench/v0.4/items.jsonl bench/v0.4/refs/v2/claude.jsonl bench/v0.4/refs/v2/codex.jsonl bench/v0.4/refs/v2/MANIFEST.json \
         scorers/vendor/eval-lib/judge-core.mjs; do
  get "https://raw.githubusercontent.com/r4topunk/boar-bench/$BB/$f" "inputs/boar-bench/$f"; done
A=android-native
for f in $A/engine/src/main/java/team/sopa/boar/engine/answer/Citations.kt $A/engine/src/main/java/team/sopa/boar/engine/answer/AnswerPipeline.kt \
         $A/engine/src/main/java/team/sopa/boar/engine/rag/Compress.kt $A/app/src/main/java/team/sopa/boar/eval/DeviceEvalRunner.kt \
         $A/app/src/main/java/team/sopa/boar/chat/ChatViewModel.kt; do
  get "https://raw.githubusercontent.com/r4topunk/labrat-boar-fork/$LR/$f" "inputs/labrat-boar-fork/$f"; done
echo "done. Now: python3 scripts/ceiling.py && python3 scripts/citation_split.py"
