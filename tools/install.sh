#!/usr/bin/env bash
# Copies the node pack into the custom_nodes of every Comfy Desktop install
# (or only the one named: tools/install.sh VectorPong3D_Game_Node). Restart ComfyUI afterwards.
set -e
SRC="$(cd "$(dirname "$0")/.." && pwd)/ComfyUI-Vibecode3D"
BASE="/mnt/c/Users/Private/AppData/Local/Comfy-Desktop/ComfyUI-Installs"
for INST in "$BASE"/${1:-*}/; do
  [[ -d "$INST/ComfyUI/custom_nodes" ]] || continue
  DST="$INST/ComfyUI/custom_nodes/ComfyUI-Vibecode3D"
  mkdir -p "$DST"
  cp "$SRC"/*.py "$DST"/
  rm -rf "$DST/__pycache__"
  echo "installed to $(basename "$INST")"
done
