#!/usr/bin/env bash
# Queue an API workflow N times with seeds S, S+1, ...:  tools/queue.sh [first_seed] [count] [workflow]
# workflow: a name in workflows/ without _api.json (default vector_pong_variants; squad_remix, toss_remix, ...)
# ComfyUI listens on Windows' 127.0.0.1:8188, which WSL reaches through Windows curl.
S="${1:-1}"; N="${2:-1}"; WF="${3:-vector_pong_variants}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
C=/mnt/c/Windows/System32/curl.exe
TMP="$HERE/tests/.last_prompt.json"
for ((i=0; i<N; i++)); do
  python3 -I - "$HERE/workflows/${WF}_api.json" $((S+i)) > "$TMP" <<'PY'
import json, sys
wf = json.load(open(sys.argv[1]))
for n in wf.values():
    if n["class_type"] in ("VC3D_GameStart", "VC3D_RemixSource"):
        n["inputs"]["seed"] = int(sys.argv[2])
print(json.dumps({"prompt": wf, "client_id": "vc3d-queue"}))
PY
  $C -s -X POST -H "Content-Type: application/json" --data-binary "@$(wslpath -w "$TMP")" http://127.0.0.1:8188/prompt; echo
done
