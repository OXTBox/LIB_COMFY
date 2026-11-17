# LIB_COMFY

ComfyUI as a Blueprint-style editor for Vibecode3D games. Game parts are **nodes**; you chain
them, set their sliders, press **Queue**, and the **Build Game** node picks up the xTalk script
parts the chain needs and writes a playable `Vibecode3D_Play_<Name>.livecodescript` into
`LIB_GAMES/Vibecode3D_Games` (the game launcher opens it like any other game).

## Layout

| Path | What |
|---|---|
| `ComfyUI-Vibecode3D/` | the node pack (category **Vibecode3D/Vectors**). `assemble.py` builds games and needs no ComfyUI; `preview.py` draws a still frame |
| `parts/cpong/` | the script parts: `core` (always), one `court_*`, one `ball_*`, `control_keys` and/or `control_cpu` |
| `workflows/vector_pong_variants.json` | drag this into ComfyUI: Game Start, Palette, Court, 4 Paddles, Ball, Match Rules, Build Game, Preview |
| `workflows/vector_pong_variants_api.json` | the same for `tools/queue.sh` |
| `tools/install.sh` | copies the pack into Comfy Desktop's `custom_nodes` (restart ComfyUI after) |
| `tools/queue.sh [seed] [count]` | queues variants from WSL (ComfyUI on Windows 127.0.0.1:8188, reached through Windows curl) |
| `tools/make_workflow.py` | writes both workflow files |
| `tests/chain_test.py SEED [dir]` | runs a chain without ComfyUI (use Comfy's python.exe: it has PIL) |

## Nodes

- **Game Start**: title, file name, **seed** (set *control after generate* to randomize), master dice.
- **Palette**: five colours from one hue and a scheme; colour fields left at `auto` use them.
- **Pong Court**: size, floor style (classic / grid / rings / bare / random). Sides with a paddle are goal mouths, the rest walls.
- **Paddle**: side, control (arrows / wasd / cpu), team, length, speed, inset (foosball rows), skill, colour, **appear** (chance it is in the game for a seed).
- **Ball**: size, speed, speed-up per hit, top speed, count 1-3, shape.
- **Match Rules**: points to win, levels, speed-up per level.
- **Build Game**: writes the game; outputs the script path, a preview image and the script text.

Every node has **dice** (0 = exactly as set, 1 = up to 60% either way). Same seed, same game.
Build Game also makes the game playable whatever the chain says (adds a home paddle or an
away goal if missing) and prints what it changed on the preview.

## Adding a kind of part

1. Write `parts/<kit>/<part>.part.livecodescript` (handlers use the kit's prefix).
2. Add a node class in `ComfyUI-Vibecode3D/__init__.py` that writes its settings into the game dict.
3. Teach `assemble.parts_needed` / `config_handler` about it. Run `tools/install.sh`, restart ComfyUI.
