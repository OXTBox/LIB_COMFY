# Comfy Games (the player)

Plays the games the ComfyUI nodes build, kept apart from the Vibecode3D Library (owner, 18 Nov 2026).
A copy of the Library (`LIB_PUBLIC/launcher`) that reads no install: it finds its games beside itself.

**Double-click `ComfyGames.exe`.** It walks up from its own folder to the first folder holding
`games/` (or `Games/`): `LIB_COMFY/Player/ComfyGames.exe` finds `LIB_COMFY/games/`. New builds
show up with **Refresh**.

| In the window | Does |
|---|---|
| genre menu | All games, or one genre, made from the file names (`ComfyBricks1` -> Bricks); a new kit appears by itself |
| sort menu | By name, or Newest first (the file's date) |
| PLAY (Enter, double-click) | starts a second copy of the program with `-game <file>`: one game per program, closing the list leaves games running |
| Show Folder / Verify Games / Refresh | open games/; check every game and the engine; read games/ again |

**The engine:** `Player/Engine/` if it is there (vibe_engine_xt3d, game_player, GameNotes: a copy
that can travel with the program, git-ignored), else from the projects folder above LIB_COMFY
(`xt3D_Raylib_Livecode_Bridge/testbench`, `LIB_DEV/livecode`, `LIB_GAMES/tools`), so it always
plays with the newest engine on this PC. Game notes (` or F2) still reach the owner's GAME_NOTES.txt.
Logs and game errors: `%LOCALAPPDATA%\ComfyGames\logs\`.

## Files
- `comfy_games.livecodescript`: the whole app (stack "ComfyGames"); the window is made the first time it opens.
- `ComfyGames.livecode`: the stack saved with that script, which is what gets built.
- `ComfyGames.exe`: the build, copied up from `build/ComfyGames/Windows x86-64/` (both git-ignored).

## Build (OXT-Beyond)
Open `ComfyGames.livecode` (settings copied from the Library's, name ComfyGames), then
`revSaveAsStandalone "ComfyGames", <this folder>/build, false, true` and copy the exe up here.
**Delete `build/` first:** a second build into an existing build folder reports success but
leaves the old exe (seen 18 Nov).

Test: `OXT-BEYOND/tests/t53_comfy_games.txt` (23 checks: finds games/ from Player/, genres, sorting,
Verify, opens ComfyBricks1 and a Squad remix on the real engine).
