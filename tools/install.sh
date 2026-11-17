#!/usr/bin/env bash
# Copies the node pack into Comfy Desktop's custom_nodes. Restart ComfyUI afterwards.
set -e
SRC="$(cd "$(dirname "$0")/.." && pwd)/ComfyUI-Vibecode3D"
DST="/mnt/c/Users/Private/AppData/Local/Comfy-Desktop/ComfyUI-Installs/Comfy_instace_001/ComfyUI/custom_nodes/ComfyUI-Vibecode3D"
mkdir -p "$DST"
cp "$SRC"/*.py "$DST"/
rm -rf "$DST/__pycache__"
echo "installed to $DST"
