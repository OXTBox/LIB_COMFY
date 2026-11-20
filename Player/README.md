# Comfy Games (the app)

Plays the games the ComfyUI nodes build, kept apart from the Vibecode3D Library (owner, 18 Nov 2026).
Engine 1 (pure xTalk Vibecode3D) host. Its play code is the Library's (`LIB_PUBLIC/launcher`); it reads
no install: it finds its games beside itself.

**Pick a genre, pick a game, PLAY.** Double-click `ComfyGames.exe` (or open `ComfyGames.livecode` in
OXT-Beyond). It walks up from its own folder to the first folder holding `games/`:
`LIB_COMFY/Player/ComfyGames.exe` finds `LIB_COMFY/games/`.

| In the window | Does |
|---|---|
| GENRE (left) | All games, then the genres of `LIB_COMFY/genres.tsv` (Pong, Bricks, Waves, Worm, Dodge, Lander, Rocks, Squad, Toss), then any other genre a game says it is, with counts |
| GAMES (middle) | the games of that genre, with their stars. **Best rated** (most stars, newest first among equals), **Newest** (date built), **A-Z** |
| ✦✦✦✧✧ (right) | the game's stars: click one to set, the same one again to take them away; keys 1-5 (0 clears) |
| PLAY (Enter, double-click) | starts a second copy of the program with `-game <file>`: one game per program |
| Make a new one | builds one new game of the genre in about a second (`tools/make_game.py`, no ComfyUI); under All games, any genre. It is picked in the list at once |
| Open in ComfyUI | when ComfyUI runs on 127.0.0.1:8188: puts the genre's starter workflow in its Workflows panel as `ComfyGames_<genre>` and opens ComfyUI in the browser. Not running: says so, and where the workflow file is |
| Show Folder / Verify Games / Refresh | open games/; check every game, the engine and the Python Make uses; read games/ again (it also re-reads by itself whenever the window comes to the front) |

**A game's genre** is the `-- comfy: genre=<g> seed=<n> built=<iso>` line under its header (Build Game and
make_game.py write it since 20 Nov), else its file name (`ComfyBricks1` -> Bricks). **Date built** is that
line's `built=`, else the file's date.

**Stars** are kept in the player's Data folder, `Data/Games/ComfyGames/ratings.tsv` (game, stars, date),
through LIB_DATA (`Player/Engine/lib_data.livecodescript`, else `projects/LIB_DATA`), else `Documents/Data`.

**New games** go into `games/` when the program can write there (this PC), else into
`Data/Games/ComfyGames/games/` (an installed, read-only copy); both are listed.

**Python for Make a new one** (`CG.Python`): `Player/python/python.exe` if shipped, else Comfy Desktop's own
`%LOCALAPPDATA%\Comfy-Desktop\ComfyUI-Installs\*\standalone-env\python.exe`, else the `py` launcher.
make_game.py needs nothing but Python 3.

**The engine:** `Player/Engine/` if it is there (vibe_engine_xt3d, game_player, GameNotes, lib_data: a copy
that travels with the program, git-ignored), else from the projects folder above LIB_COMFY, so on this PC it
always plays with the newest engine. Logs and game errors: `%LOCALAPPDATA%\ComfyGames\logs\`.

## Files
- `comfy_games.livecodescript`: the whole app (stack "ComfyGames"); the window is made when it opens.
- `ComfyGames.livecode`: the stack saved with that script (re-saved headless 20 Nov with the new script;
  its standalone settings kept), which is what gets built.
- `ComfyGames.exe`: the build, copied up from `build/ComfyGames/Windows x86-64/` (both git-ignored).

## Build the .exe (OXT-Beyond IDE; not done yet for the 20 Nov app)
1. Delete `build/` first (a second build into an existing folder reports success but keeps the old exe, 18 Nov).
2. Open `ComfyGames.livecode` in OXT-Beyond. In the message box:
   `revSaveAsStandalone "ComfyGames", "<this folder>/build", false, true`
3. Copy `build/ComfyGames/Windows x86-64/ComfyGames.exe` up here (beside this README).
4. Optional, the one-folder install on V:: `python3 -I ~/projects/LIB_PUBLIC/install/vibeinstall.py comfygames`
   (Program Files (x86)\Comfy Games\LIB_COMFY\Player\ComfyGames.exe, Desktop shortcut "Comfy Games").

Tests: `OXT-BEYOND/tests/t64_comfy_games_app.txt` (45 checks: genres, games per genre, stars saved and read
back, the three sorts, Make a new Worm/Squad that plays on the engine, the play and ComfyUI command lines,
the Data folder through LIB_DATA), `t53_comfy_games.txt` (the 18 Nov checks, updated).
