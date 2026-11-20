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
- Output: `LIB_COMFY/games/Vibecode3D_Play_<Name><seed>.livecodescript`, kept apart from the hand-made
  games in LIB_GAMES (owner, 18 Nov: one ComfyPong demo stays in LIB_GAMES as the teaser; the rest
  would clutter the one-off prototypes). Build Game's `save_to` can still pick LIB_GAMES (old
  workflows keep working) or ComfyUI's output folder. The owner's tested games are kept in git there.
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
- Lander and Rock Blaster followed the same night. Rotation: `Entity.SetRotation id, 0, 0, a` turns a
  shape drawn pointing up (-y) so its nose is at (sin a, -cos a): positive a leans right on screen
  (the engine's Mat3.RotZYX is the standard one), the same way the kits' thrust pushes.
- **Dice on a ratio.** `roll()` wanders by a share of the value, so a speed-up of 1.02 could roll 1.3.
  The Ball node now rolls only the part above 1 for every kit but Pong (Pong keeps its first dice, so a
  saved Pong seed makes the same game).
- **Autopilots must play like a person would, or a test stalls:** the brick autopilot aims at the lowest
  brick (without aiming the ball went up the same gap for ever); the wave autopilot leads its target and
  steps aside from bombs. `tests/kit_play_test.py --seed N` was run for seeds 1 to 10.
- Ideas next: event nodes across kits ("when a brick breaks -> sparks / sound / speed up"), a Title Card node, sound
  once `Sound.Play` has sounds in the Game Player.

## Remix: Squad Buggy and Vector Toss (18 Nov 2026, Fable, job 4) -- STEPS 1, 2 AND 3 DONE, waits for the owner's Queue

Branch `comfy-remix`. Brief: `Next_Steps_With_Claude/FABLE_JOB_4_COMFY_REMIX.md`. Both games are Engine 1
(pure xTalk) game scripts; the originals in LIB_GAMES are read and never changed.

- **The chain:** Remix Source -> the game's nodes (any, in any order) -> Mutate -> Build Game. Build Game
  was reused as it is (`kits.build` sends kit `remix` to `remix.build`; `preview.draw` to
  `remix.preview_image`). Everything is in `kits/remix.py`; category Vibecode3D/Remix, 11 nodes:
  Remix Source; Buggy, Terrain, Enemies, Palette (Squad Buggy); Arena, Ball, Heroes, Rules, Palette
  (Vector Toss); Mutate. A node of the other game is left out with a note, it never breaks the Queue.
- **Three kinds of knob** (tables at the top of remix.py):
  - *constant*: a `constant kX = value` line; only the value is replaced, the comment stays. Defaults
    are read from the game's file at every build, so dice 0 follows the owner's own retuning.
  - *patch*: Squad Buggy's enemy pacing is numbers written into three lines, not constants
    (`sNextEnemy`, `sESpeed`, `sNextFly`). `SQUAD_PATCHES` holds each exact line and its replacement:
    the same sum times a factor. This is the answer to the owner's "we are unbeatable": walker_gap
    0.3 = three times the walkers. If the original line changes, the build stops and says which.
  - *colour*: Vector Toss has colour constants. Squad Buggy's are literals in the code:
    `SQUAD_COLORS` maps literal -> role (buggy, flag, gunner, squad, ground, enemy, bomber, bomb,
    tower) and the literal is replaced everywhere it stands, sparks too.
- **Sliders start at the original's numbers**, read from the game files when ComfyUI starts (a typed
  table, `FALLBACK`, only if the files can't be reached then). A saved workflow keeps the numbers it
  was saved with.
- **Rolls stay inside the safe range** (`roll_in`): dice 1 can reach either end and never passes it.
  `assemble.roll` was not used: it wanders by a share of the value, which throws ratios like kRollDrag
  0.95 straight to their limits (the "dice on a ratio" trap above). A knob no node has set is rolled
  around the original with dice 0.5 times the master dice.
- **Mutate** (chance, most 1-3): by the seed, pushes numbers to the edge of their safe range and writes
  them into the title: "SQUAD BUGGY: AIR RAID, LONG HOLDS, TOWER CITY", "VECTOR TOSS: SUDDEN DEATH,
  DEAD BALL, FLOATY BALL". The words are in the knob tables (`low`, `high`); a knob without a word
  is never mutated. It runs before the fix-ups, so a mutation can't make a dead game.
- **Fix-ups** (notes say what changed): Squad Buggy: the jump 85..300 high (craters stack to 70 deep),
  craters no wider than a jump can cross, sniper rounds no faster than 0.4 of your shots, sniper range
  shorter than the gap between towers. Vector Toss: the floor is whole tiles, a jump clears the level
  walls (32), reach under the ceiling, run speed enough to get under a roof throw in a big arena, catch
  radius wider than a big ball, the camera follows the arena's size.
- **Ranges that are narrow on purpose:** kSeg only 20..30 (Squad.Ground has a literal 24 slices behind
  the buggy); kHalfW not under 240 (the level walls stand up to 120 from the centre).
- **Data:** Vector Toss finds its clips and banter by fixed paths (`Game.FindFile("LIB_GAMES/...")`),
  not by its own name, so a renamed copy finds them. Nothing had to be pinned.
- **Header:** line 2 gets the new card name, the title and "(remixed in ComfyUI from <game>, seed N)";
  a `## REMIX` block lists every change (was -> now) and the notes. The original's CONTROLS / RULES
  words are kept, so "20 seconds" can be out of date; the block says so.
- **Stills:** Squad Buggy: the buggy, its jump as dots, a crater, a walker, a bomber, a tower, and
  under it the course of one level (flags, towers, sniper range). Vector Toss: the arena from above
  and from the side (a roof throw stepped as the game steps it), and the list of changes.
  **Nobody has looked at them** (the images rule): the owner sees them first on the node.
- **Workflows:** `workflows/squad_remix.json`, `toss_remix.json` (+ `_api.json`), written by
  `tools/make_kit_workflows.py` from `kit_chains.remix_chain` (every node at its defaults, dice 0.7,
  Mutate 0.6). `tools/queue.sh 1 5 squad_remix` queues five seeds.
- **Tests:** `python3 -I tests/remix_play_test.py --real`: seeds compile and play 600 steps on the
  stand-ins (stubs + LIB_ig3d's alias file: without it `Camera.Reset` is not found); even seeds use
  the whole chain with Mutate always, odd seeds Remix Source alone. Run for seeds 1-50: 0 failed.
  Squad Buggy drives, jumps and fires; Vector Toss plays itself and makes 3-5 catches. Seed 1 of each
  runs and draws in the Game Player on the generated engine. Installed (`tools/install.sh`, both
  installs), and both API workflows were run node by node from the installed pack with the install's
  `.venv` python: 42 nodes, every widget default in range, `[1,600,900,3]` previews.
- **Not tested:** ComfyUI was not running, so nothing was queued through it and the nodes were not
  seen in its window. No person has played a variant: the autopilot proves a game runs, not that the
  mutations are fun or fair (AIR RAID plus SWARM may be too much; that is what his notes are for).
  The headless drive never gets stuck in a crater, so the crater fix-ups are sums, not play.
- **Not built:** Squad Buggy's crew size (three soldiers is written through the code, not one number).

### Step 3: the When nodes (events), same night

- **Two nodes:** When (Squad Buggy remix), When (Vector Toss remix): event, action, amount, text,
  color, chance (each time it happens), appear (is the rule in this seed's game). Chain several, at
  most 8 (`MAX_RULES`). `random` for event or action lets the seed pick: that is where the odd ones
  come from ("when a flag is held: crater ahead").
- **Squad Buggy events:** bomber down, sniper down, walker shot, walker squashed, man overboard,
  soldier lost, flag reached, flag held, crater dug, jump. **Actions:** sparks, score, say, extra life,
  bomber comes, walkers faster, walker rush, crater ahead, bounce.
- **Vector Toss events:** catch, big catch, rally, drop, floor broke, pit took the ball, hero falls,
  new level. **Actions:** sparks, score, say, extra hang, mend the floor, crack a tile.
- **How an event is found:** by one exact line of the original (`SQUAD_EVENTS`, `TOSS_EVENTS`: the
  line, before or after, the two values handed over). Build puts `Remix.On "<event>", a, b` there,
  only for events a rule uses, and `Remix.Flush` as the first line of `Game.OnUpdate`. The spots are
  looked up BEFORE the colours are replaced (two anchors hold a colour literal). A line that is gone
  or there twice stops the build and names it.
- **Why a queue:** `Remix.On` only writes the event down; `Remix.Flush` runs the actions at the top of
  the next step. Most events sit inside the game's own `repeat for each key` loops over walkers,
  bombs and shots; an action that kills walkers there (a crater) would pull the list out from under
  the loop. One step late can't be seen. Events raised while Flush runs are dropped (`sRemixBusy`),
  so "when a crater is dug: crater ahead" makes one crater, not one every step for ever.
- **Vector Toss trap:** `VT.Advance` (roof, wall and floor bounces) is also run for the ghost ball
  and the companion's planning, so a hook there would fire on throws nobody made. No roof / wall
  events for that reason; they need a flag saying "this is the real ball" in the original first.
- **Adding an event or an action:** one line in the table. An action's lines may use tA, tB (the
  event's values; Vector Toss: tA = the hero, or "*") and %(n)s, %(text)s, %(rgb)s.
- **Tests added to `remix_play_test.py`:** a rule really goes off (Squad Buggy: 500 points a jump took
  the score from 545 to 4065; Vector Toss: 20 a catch, 6 to 87); every event with every action (90
  pairs, 48 pairs) is built, compiled and set off by hand without an error; seeds 1-50 with two set
  rules and two random ones on even seeds: 0 failed. Installed; both API workflows run from the
  installed pack (44 nodes).
- **Not tested:** the actions on the real engine with a person playing (the stand-ins' FX.Sparks draws
  nothing); whether a rule is fun. ComfyUI was still not running.

## The Comfy Games app (19-20 Nov 2026, Opus, branch `comfy-games-app`)

- `Player/` is the app (README there); `genres.tsv` lists the genres; `tools/make_game.py GENRE` makes one
  game without ComfyUI (the starter chains run through the node classes; no torch/numpy/PIL).
- Every build now has `-- comfy: genre=<g> seed=<n> built=<iso>` right under the header block
  (`assemble.comfy_line`; a kit's `GENRE`, a remix game's `"genre"`). A new kit: give it `GENRE` and a line
  in genres.tsv, and its chain in kit_chains.py.
- Trap met: on Windows, `shell()` runs `cmd /C <line>`; a line holding more than two quotes loses its first
  and last quote, so the app wraps such lines in one more pair (CG.MakeCommand, CG.ComfyCommand).
