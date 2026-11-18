# LIB_COMFY

ComfyUI as a Blueprint-style editor for Vibecode3D games. Game parts are **nodes**; you chain
them, set their sliders, press **Queue**, and the **Build Game** node picks up the xTalk script
parts the chain needs and writes a playable `Vibecode3D_Play_<Name>.livecodescript` into
`LIB_COMFY/games`, kept apart from the hand-made games in LIB_GAMES (one ComfyPong demo stays there).

## Layout

| Path | What |
|---|---|
| `ComfyUI-Vibecode3D/` | the node pack (category **Vibecode3D/Vectors**). `assemble.py` builds games and needs no ComfyUI; `preview.py` draws a still frame |
| `parts/cpong/` | the script parts: `core` (always), one `court_*`, one `ball_*`, `control_keys` and/or `control_cpu` |
| `parts/common/vec.part.livecodescript` | shared by every kit but Pong: wire shapes (`Vec.Shape`), floors (`Vec.Decor`), keys, mouse |
| `parts/cbrick` `cwave` `ccoil` `cdodge` `cland` `crock` | the genre kits' game parts (one `core` each) |
| `ComfyUI-Vibecode3D/kits/` | one module a genre kit: what its nodes set, fix-ups, the config handler, header, preview |
| `workflows/<kit>_variants.json` | a starter chain per kit (brick, wave, coil, dodge, lander, rocks), made by `tools/make_kit_workflows.py` from `tools/kit_chains.py` |
| `tests/kit_test.py KIT SEED [dir] [small]` | builds a kit's chain through the node classes (any python3; previews need PIL) |
| `tests/kit_play_test.py` | builds every kit and plays it headless in OXT-Beyond: stand-ins with the autopilot, then the real engine |
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

## The genre kits (Vibecode3D/... categories)

Start every chain with **Game Start** (and **Palette** if you like); the first node of a kit decides
what Build Game makes. **Arena** (Vibecode3D/Shared) sizes the play area and its floor for every
kit but Pong and the worm. Nodes marked *chain several* add one more each time.

| Kit | Nodes | The game |
|---|---|---|
| Brick Breaker (`cbrick`) | Brick Wall, Bat, Power-Up *(chain several)*, Breaker Rules; Ball from Pong | break every brick; patterns change level by level; tough bricks; wide bat, more balls, slow ball, extra life |
| Wave Shooter (`cwave`) | Shooter Ship, Enemy Wave *(chain several: one a level)*, Shields, Wave Rules | a formation marches and steps down; bombs, divers; shields wear away; waves come round faster |
| Grid Worm (`ccoil`) | Worm Board, Worm, Food *(chain several kinds)*, Worm Rules | grow by eating; walls or wrapping edges; blocks grow each level; gold, shrink and slow food |
| Lane Dodger (`cdodge`) | Runner, Hazard *(chain several)*, Pickup *(chain several)*, Dodge Rules | last the distance; lanes or free running; coins, shields, slow time, extra lives; the floor scrolls |
| Lander (`cland`) | Lander Craft, Ground, Lander Rules | gravity and fuel; turn-and-burn or slide; set down slowly and upright on a pad (narrow pads score more); new ground and a stronger pull each level, wind if you like |
| Rock Blaster (`crock`) | Blaster Ship, Rock Field, Saucer, Rock Rules | turn, thrust and drift through wrapping space; big rocks split in two, then two again; a saucer now and then; one more rock each level |

Each game has an autopilot for tests and demos (`Brick.TestAuto true` ...) and a `State()` line.

## Adding a kind of part

1. Write `parts/<kit>/<part>.part.livecodescript` (handlers use the kit's prefix).
2. Add a node class in `ComfyUI-Vibecode3D/__init__.py` that writes its settings into the game dict
   (for the genre kits: one `_node(...)` line set, calling a function in `kits/<kit>.py`).
3. Teach the kit's `parts_needed` / `config` about it (Pong: `assemble.parts_needed` / `config_handler`).
   Add it to the kit's chain in `tools/kit_chains.py`, run `tools/make_kit_workflows.py` and
   `tests/kit_play_test.py`. Run `tools/install.sh`, restart ComfyUI.

## Adding a genre kit

`kits/__init__.py` says what a kit module holds (KIT, PREFIX, TITLE, fixups, parts_needed, config,
rules_lines, preview). Copy the smallest one (`dodge.py`), write `parts/<kit>/core.part.livecodescript`
on `parts/common/vec` with `Game.OnStart`, `Game.OnUpdate`, `PREFIX.State()` and `PREFIX.TestAuto`,
add the kit to `KITS` in `kits/__init__.py` and `tools/kit_chains.py`.
