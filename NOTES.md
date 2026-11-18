# LIB_COMFY: notes on making it work

Everything learned getting the first node-built game (Comfy Pong, 17 Nov 2026) from ComfyUI to
the Game Browser. Read this before making more nodes or workflows.

## The setup on this PC

- **Comfy Desktop** (ComfyUI 0.45.5, frontend 1.58.5, Python 3.13, torch cu130), RTX 3060 laptop
  6 GB, 16 GB RAM. It can have **several installs** in
  `C:\Users\Private\AppData\Local\Comfy-Desktop\ComfyUI-Installs\`. The owner runs
  **VectorPong3D_Game_Node** for this work; `Comfy_instace_001` is the older one.
- **First failure:** every node had a red border and "Missing Node Packs / Unknown pack". The nodes
  had been copied into the other install. Check which install is running: its `logs/comfyui.log`
  is the newest, and its "Import times for custom nodes" lists what it loaded.
  `tools/install.sh` now copies into every install (or `tools/install.sh <InstallName>`).
- **ComfyUI must be restarted** (close Comfy Desktop, open it) after any change to the Python files.
  Changes to `parts/` need no restart: Build Game reads them from disk at every Queue.
- Server: `http://127.0.0.1:8188` on Windows. **WSL's curl can't reach it**;
  `/mnt/c/Windows/System32/curl.exe` can. Useful calls:
  - `/system_stats`: version, GPU, which install's arguments
  - `/object_info`: every loaded node with its inputs. `grep -o 'VC3D_[A-Za-z]*'` checks ours loaded
  - `POST /prompt` with `{"prompt": <api workflow>}`: queues a run (`tools/queue.sh seed count`)
  - `/history`: results of finished runs
- Comfy's own Python (`<install>\standalone-env\python.exe`) has torch, numpy and PIL; WSL's
  python3 has no PIL. Run `tests/chain_test.py` with it (give it Windows paths via `wslpath -w`).
  Windows Python reads and writes `\\wsl$\Ubuntu\home\igame3d\projects` fine.

## How the pack is built

- Old-style node classes (`INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `CATEGORY`, `OUTPUT_NODE`)
  still work in 0.45. Category `Vibecode3D/Vectors`; class names `VC3D_*`.
- **One custom wire type** `VC3D_GAME` (a plain dict) passed node to node like a Blueprint
  exec wire. Each node **deep-copies** the game before changing it: ComfyUI caches node outputs
  and reuses them, so changing the incoming dict in place makes results drift between Queues.
- **Seed**: an INT input named `seed` with `"control_after_generate": True` gets the
  fixed / increment / randomize widget. Only Game Start has it; every other node rolls with the
  game's seed plus its own salt (`assemble.roll`, `roll_choice`, `roll_chance`), so one seed =
  one whole game, and nothing else needs wiring.
- **dice** on each node times the master dice on Game Start. Rolling the whole slider range was
  far too wild (paddles 20 long or 200); now dice 1 = up to 60% of the set value either way.
- **Build Game** returns `{"ui": {"images": [...], "text": [...]}, "result": (...)}`: the image is
  saved to `folder_paths.get_temp_directory()` with type `temp` so it shows on the node; the IMAGE
  output (tensor `[1,H,W,3]` float 0..1) also feeds a normal Preview Image node.
- Build Game **repairs** chains that can't make a game (no home paddle, no away goal) and prints
  what it did on the preview. Keep doing this for every kit: a Queue should never give a dead game.
- `assemble.py` has no ComfyUI imports, so builds can be tested without ComfyUI.

## How a game is put together

- `parts/<kit>/*.part.livecodescript`: plain xTalk handlers. `core` always; then one of each
  "slot" (`court_*` defines `Cpong.Decor`, `ball_*` defines `Cpong.BallMesh`) and the optional
  ones (`control_keys`, `control_cpu`) only when a paddle needs them. LiveCode compiles calls
  to handlers that aren't there, so the core can call `Cpong.CpuMove` even when that part is left
  out, as long as it is never reached.
- The node settings become one generated handler, `Cpong.Config`, at the end of the script
  (`sCfg[...]`, `sPad[i][...]`, `sGoal[side]`).
- The header follows the game-launcher format (`## CARD SCRIPT:`, `## CONTROLS`, `## RULES`), so
  `GL.Info` reads title, controls and levels (`Cpong.StartLevel n`).
- Output: `LIB_GAMES/Vibecode3D_Games/Vibecode3D_Play_<Name><seed>.livecodescript`. The Game Browser
  lists every `Vibecode3D_Play_*` file in that folder (reopen it to see new ones); Game_Player.exe
  plays it. These generated games are **not** kept in git.
- Top-down view: `Camera.Reset`, everything at z = 300 (1 unit = 1 pixel), y grows
  downward, the court's middle at screen y 40. Court half sizes up to 380 x 220 fit the window.
- Meshes: `Mesh.New()` returns an array; `Mesh.AddVertex`/`Mesh.AddLine` take it by reference
  (`@`), and `the result` after AddVertex is the new vertex's number. Pass meshes into helpers
  with `@pM`. One mesh is one colour: floor decoration got its own dim mesh (`decoColor` = walls x 0.4).

## Testing a new kit or node (the loop that worked)

1. `"$PY" "$(wslpath -w tests/chain_test.py)" <seed> [out folder]` with Comfy's python.exe: builds
   a variant and a preview PNG.
2. `~/projects/LIB_MCP/tools/lcmcp compile <script>`: real LiveCode compile check.
   (Caught: `add x into y` must be `add x to y`.)
3. `LIB_GAMES/tools/engine_play.sh <Name> Cpong "0:10 32:2 65362:40 0:80" C:/LIB_MCP/x.png`:
   plays on the real engine with held keys, prints `Cpong.State()` (level|home|away|ball|serving|over)
   and saves a frame. Compare the frame to the preview.
4. `tools/install.sh`, owner restarts ComfyUI, `object_info` shows the nodes, then queue.

## Making more workflows

- `tools/make_workflow.py` writes a chain in **both formats**: the editor format (drag into
  ComfyUI: `nodes` with `widgets_values` in input order, `links` as
  `[id, from_node, from_slot, to_node, to_slot, type]`) and the API format
  (`{"<id>": {"class_type", "inputs"}}`, wires as `["<node id>", slot]`), which `/prompt` takes.
- In the editor format, a widget with `control_after_generate` takes an **extra value** right after
  it in `widgets_values` (`1, "randomize"`). Leaving it out shifts every later widget.
- Copy the CHAIN list in `make_workflow.py` for a new workflow (different paddles, styles,
  dice); one script, many workflow files.
- Ideas queued for later: event nodes ("when ball hits paddle" -> "sparks / add block / speed
  up"), a second kit (breakout or a shooter) to prove the parts idea beyond Pong, image nodes for
  textures (6 GB VRAM: SD1.5-class models), a "Play now" switch on Build Game that starts Game_Player.

## The genre kits (18 Nov 2026, Opus, overnight: written and tested without ComfyUI running)

- **How it was tested without ComfyUI.** WSL can run Windows Pythons: Comfy's `standalone-env\python.exe`
  has PIL; the install's `ComfyUI\.venv\Scripts\python.exe` has torch too (ComfyUI's own interpreter).
  With the latter the pack loaded (24 nodes, every widget default in range) and each API workflow was
  run node by node as `/prompt` would, giving a game and a `[1,600,900,3]` preview. Build Game reads parts
  from `projects_root()`; a `config.json` beside `__init__.py` (`{"projects": "..."}`) points it elsewhere.
- **Not tested:** the nodes inside the ComfyUI window (how they look, wiring by hand), and playing the
  games with a person at the keys. The autopilots prove the rules run; they do not prove the games are fun.
- **The xTalk trap that cost the most:** a one-line `if ... then statement` directly above an `else`
  line takes that `else` as its own, and the handler stops compiling ("190/166/165" at its `end`).
  Write the inner `if` as a block, or move it into a function. Every part was checked for the pattern.
- **One colour per entity, for life.** `Entity.Spawn` sets the colour and nothing in the contract
  changes it, so a reused entity (the worm's tail becoming its head) keeps its first colour. An
  `Entity.SetColor` would let kits flash, fade and stripe; for now the worm is one colour.
- **Headless frames are not real frames.** On the stand-ins one `Game.OnUpdate` is one step; in the
  Game Player `Vibe.Step` paces steps by the clock, so a tight loop of `Vibe.Step` runs fewer of them.
- Ideas next: a Lander kit (gravity, fuel, pads), a Rock Blaster kit (inertia, rocks that split), event
  nodes across kits ("when a brick breaks -> sparks / sound / speed up"), a Title Card node, sound
  once `Sound.Play` has sounds in the Game Player.
