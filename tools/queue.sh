#!/usr/bin/env bash
# Queue the API workflow N times with seeds S, S+1, ...:  tools/queue.sh [first_seed] [count]
# ComfyUI listens on Windows' 127.0.0.1:8188, which WSL reaches through Windows curl.
S="${1:-1}"; N="${2:-1}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
C=/mnt/c/Windows/System32/curl.exe
TMP="$HERE/tests/.last_prompt.json"
for ((i=0; i<N; i++)); do
  python3 -I - "$HERE/workflows/vector_pong_variants_api.json" $((S+i)) > "$TMP" <<'PY'
import json, sys
wf = json.load(open(sys.argv[1]))
for n in wf.values():
    if n["class_type"] == "VC3D_GameStart":
        n["inputs"]["seed"] = int(sys.argv[2])
print(json.dumps({"prompt": wf, "client_id": "vc3d-queue"}))
PY
  $C -s -X POST -H "Content-Type: application/json" --data-binary "@$(wslpath -w "$TMP")" http://127.0.0.1:8188/prompt; echo
done
