# Comfy Games + AUDIO: hand-off (24 Nov 2026)

To do **together with the Comfy Games rebuild** (Priority Tube n-c58324eb, `PLAN_STANDALONE.md` What's next).
The owner's words (24 Nov): "ComfyGames can remain without sounds for now. When sounds are specifically set
for certain games then those choices should move with the ComfyGames."

## Where sound stands (24 Nov)
- LIB_AUDIO (hidden AUDIO stack) steps 1-5 on main: the Game Player opens AUDIO (`GL.Audio` in
  LIB_DEV/livecode/game_launch), the engine's `Sound.Play "<Name>"` goes to `Audio.Play`, the AUDIO window
  (`...` > Sounds...) chooses files per name and saves `Data/Sounds/Games/<Game>.txt`.
- 55 LIB_GAMES games call kit names (`LIB_AUDIO/GAME_SOUNDS.md`), MERGED to LIB_GAMES main 24 Nov (aa8b531).
  Owner tried lots: "Very nicely done ... filler material ... some need special attention to make them pop."
- Kit names (= folders in `Data/Sounds/`): Blip Bounce Bullet Enemy Explode Hit Hurt Jump Lose Pickup
  PlayerCrash PlayerLaser Powerup Select Shoot Throw Thud Warp Win Zap. AUDIO finds a game's names by reading
  its script for the literal `Sound.Play "<Name>"`.

## What Comfy games lack (checked 24 Nov, nothing changed in LIB_COMFY)
1. **The Comfy player never opens AUDIO.** `CG.Play` (Player/comfy_games.livecodescript ~line 1161) makes
   its own window and does not call `GL.Audio`, so `Audio.Hosted()` is false: the engine's old sound-kit way.
2. **Remix kits** (Photon, Toss, Squad: `ComfyUI-Vibecode3D/kits/remix.py`) copy the LIB_GAMES script when
   built, so **new** remixes now carry the sounds. The 37 games already in `games/` are older copies: silent.
3. **Node kits** (Brick, Coil, Dodge, Lander, Pong, Rocks, Waves, Worm: `parts/<kit>/*.part.livecodescript`)
   have only `Sound.Play "boom"` / `"shot"` (not kit names; cland, ccoil, cdodge, crock, cwave); cpong,
   cbrick and the worm have none.
4. **Choices don't follow:** each Comfy game has a seeded name (`ComfyPhoton937801948`), so it never finds
   `Games/PhotonBall.txt`.

## The plan (one small job, ~60 min)
1. **AUDIO lookup rule** in `Audio.Words` (LIB_AUDIO/livecode/lib_audio.livecodescript): use
   `Games/<Game>.txt`; else the family `Games/<Game without trailing digits>.txt` (ComfyPhoton.txt);
   else the remix source named in the header (`remixed in ComfyUI from Photon Ball` -> PhotonBall.txt).
   Save from the AUDIO window: ask "this game / the whole family".
2. **CG.Play calls GL.Audio** (or `Audio.Select`) before the window, as GL.Open does; the AUDIO cards need
   the Comfy games folder too (`Audio.Refresh` takes one folder now: let it take a list).
3. **Parts use kit names:** boom -> Explode, shot -> PlayerLaser/Shoot; add events to cpong (Hit, Bounce,
   Pickup, Hurt, Win, Lose), cbrick, worm. Test with a copy of `LIB_AUDIO/tests/t82_game_sounds.txt`
   pointed at `LIB_COMFY/games`.
4. Old games in `games/`: rebuild them with the nodes (seed = same game), or leave silent: ask the owner.
5. The public download (PLAN_STANDALONE.md) needs the kit: `Data/Sounds/<Category>` + `Sounds/Music`
   (LIB_SFX/kit), about the size of 42 short .wav files + 5 songs.

Note: LIB_COMFY had the owner's own uncommitted changes on 24 Nov (Player/ComfyGames.livecode,
games/Vibecode3D_Play_ComfyPhoton1.livecodescript): left as they are.
