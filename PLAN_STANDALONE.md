# Plan: a stand-alone Comfy Games app (on the to-do list, 18 Nov 2026)

**Started 19-20 Nov 2026 (owner: "work can proceed on the StandAlone Comfy Games"). What was built and what is next: at the end.**

The owner tested the genre kit nodes' output on 18 Nov. The games they made live in
**LIB_COMFY/games** (and Build Game writes there now). LIB_GAMES keeps **one** demo, ComfyPong1, as
the teaser.

## The owner's direction (18 Nov)
- **Keep the Comfy games apart.** LIB_GAMES / the Vibecode3D Library is for games we spent more than
  one button and one gameplay on. Kit-made games in bulk clutter the one-off prototypes (iGame3D's
  ZGS and RTS wizards did the same).
- **The isolated ComfyUI genre / procedural content system is the favourite idea.**
- **Eventually** the Vibecode3D Library gets its own folder/subfolder and menu for Comfy games, but
  not while the Library is for hand-made games.
- **It goes public, and it must be absolutely effortless for the end user.** Install, open, pick a
  genre, play; no paths, no ComfyUI know-how, no engine setup.

## What it is
A stand-alone built on the Vibecode3D Library stack whose only focus is the ComfyUI-made games.

## Menus
- **Game menu:** lists the node kits / genres (Pong, Brick Breaker, Wave Shooter, Grid Worm, Lane
  Dodger, Lander, Rock Blaster, and any kit added later).
- **Games menu:** lists the games built from the chosen genre (default and seeded builds).

## Rating and sorting
- A **star rating** per game (the player sets it).
- **Sort** the games list by stars, and by date built.

## Effortless for the public (to design when it starts)
- One download / one installer: ComfyUI node pack, engine and player together, nothing to copy by hand
  (today: tools/install.sh, the V: refresh, restarting ComfyUI).
- Builds land where the app sees them at once; no reopening a browser to find new games.
- Starter workflows one click away per genre.

## Open questions for when it starts
- Where ratings are kept (beside the game file, or one ratings file).
- How a game's genre is known (file name today: ComfyBricks, ComfyWaves...; or a header line the
  Build Game node writes).

## Open questions: answered (20 Nov, defaults taken while the owner was away)
- **Ratings:** one file, `Data/Games/ComfyGames/ratings.tsv` in the player's Data folder (LIB_DATA rules: it
  follows a moved Data folder; it survives an uninstall and a wiped AppData). Beside each game would mean
  writing into games/, which is read-only once installed, and stars would be lost with a rebuilt game.
- **Genre:** a header line `-- comfy: genre=<g> seed=<n> built=<iso>` that Build Game (and make_game.py)
  writes right under the `####` header block; the file name is the fallback (the owner's 18 Nov builds have
  no header line). A plain `--` comment: GL.Info and the game player don't see it.

## What was built (19-20 Nov 2026, Opus; branch `comfy-games-app` in LIB_COMFY and LIB_PUBLIC)
- **The app** is the 18 Nov player grown up, in the same place (`LIB_COMFY/Player/comfy_games.livecodescript`,
  stack ComfyGames). Kept there, not LIB_COMFY/app or LIB_PUBLIC/comfy_games: the player already lived
  there with its build and test, and it finds `games/`, `tools/` and `genres.tsv` by walking up from its own
  folder, so the install is a copy of LIB_COMFY's shape and nothing needs a path setting.
- **Shared code with the Library:** not factored out. The app is one stack built into one .exe; a shared
  library would be a second stack in both builds, and the Library reads an install layout (vibeapps,
  appmanifests) this app has no use for. What is shared is copied with its origin noted (play a game as a
  second copy with `-game`, CG.Play = GL.Open). Worth doing once both are released and stable.
- **Window:** GENRE list (left, with counts) | GAMES list (middle, ✦ stars, Best rated / Newest / A-Z) | the
  game (right: stars, PLAY, Make a new one, Open in ComfyUI, its header words, seed, date). Lists and lit
  buttons instead of menus (the green-dropdown trap). Opens at 200,32. Title `FOR OWNER | Comfy Games`
  (`kTitleTag`: empty it for the public build). Re-reads games/ whenever the window comes to the front.
- **Make a new one** without ComfyUI: `tools/make_game.py <genre>` runs the genre's starter chain through
  the node classes themselves (the chains of the workflow files, `tools/kit_chains.py`; Pong's chain was
  added there), random seed that has no game yet. No torch / numpy / PIL: any Python 3. An xTalk port was
  not done: the kits are 1,700 lines of rolls, fix-ups and the remix rewriter; two copies would drift.
  Python is found as Player/python (to ship), Comfy Desktop's own standalone-env, or `py`.
- **Open in ComfyUI:** pings 127.0.0.1:8188 with Windows' curl.exe, posts the starter workflow into
  ComfyUI's user workflows (`/api/userdata/workflows%2FComfyGames_<genre>.json`), opens ComfyUI in the
  browser and says "Workflows panel (W) -> ComfyGames_<genre>". Not tried against a running ComfyUI.
- **genres.tsv** (LIB_COMFY): genre, maker, about, starter workflow. A new kit = one line (and its chain).
- **Installer:** `vibeinstall.py comfygames` (LIB_PUBLIC branch comfy-games-app) lays out
  `Program Files (x86)\Comfy Games\` = LIB_COMFY's shape (Player with the exe and Player/Engine, games in git
  only, parts, the node pack, tools, workflows, genres.tsv) + the two remix originals and Vector Toss's data
  (LIB_GAMES main, read with git show) + the five LIB_MOCAP clips + Desktop and Start Menu shortcuts, then
  `comfyverify` makes one game of every genre from the installed copy. Tried on a scratch drive: 21 games,
  89 files, all 9 genres made; the app found its engine in Player/Engine, made a Toss there and played it,
  and Vector Toss found its banter and clips in the install.
- **Tests:** OXT-BEYOND/tests/t64_comfy_games_app.txt, 45 checks, all pass on OXT-Beyond and on 9.6.3;
  t53 updated (21 pass); `tests/remix_play_test.py --seeds 1-2` and `tests/kit_play_test.py --seed 2`: 0 failed.

## What's next
1. **Owner:** open `Player/ComfyGames.livecode` in OXT-Beyond and try it (the stack has the new script);
   then build the .exe (Player/README.md, Build). The exe in Player/ is still the 18 Nov one.
2. `tools/install.sh` + restart ComfyUI, so Build Game writes the `-- comfy:` line too (the app reads
   older games by their names meanwhile).
3. **One download for the public** (not built): an installer (Inno Setup or NSIS) made from what
   `vibeinstall.py comfygames` lays out, plus
   - **Python:** ship the Windows embeddable Python (about 10 MB zip) as `Player/python/`; the app already
     looks there first. Then Make a new one works on a PC with no ComfyUI at all.
   - **The node pack for people who do have ComfyUI:** copy `ComfyUI-Vibecode3D` into their install's
     custom_nodes with a `config.json` whose `projects` is the Comfy Games folder, so Build Game writes into
     the app's games. Program Files is read-only for a normal user: put the games folder for ComfyUI builds
     in `Data/Games/ComfyGames/games` instead (the app lists it already) and give Build Game a "Comfy Games"
     choice in `save_to` that writes there.
   - **GameNotes** in a public copy writes notes to the player's Data folder (as the Library's), never the
     owner's inbox: check game_player's error-log patch covers the Comfy copy too (it does in install_engine_files).
4. Ideas: a thumbnail per game (Build Game's preview PNG beside the script; make_game.py could draw it when
   PIL is there); "Make 5" for a quick batch; delete / hide a game; ratings shown in ComfyUI.
