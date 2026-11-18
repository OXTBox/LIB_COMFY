# Plan: a stand-alone Comfy Games app (on the to-do list, 18 Nov 2026)

**Waits until the other projects are cleared** (owner, 18 Nov: "lets clear other projects before moving forward").

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
