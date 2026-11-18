# Plan: a stand-alone Comfy Games app (on the to-do list, 18 Nov 2026)

**Waits until the other projects are cleared** (owner, 18 Nov: "lets clear other projects before moving forward").

The owner tested the genre kit nodes' output on 18 Nov; the 20 games they made are kept in
LIB_GAMES/Vibecode3D_Games (`Vibecode3D_Play_Comfy*`, LIB_GAMES main 7097b38).

## What it is
A stand-alone built on the Vibecode3D Library stack whose only focus is the ComfyUI-made games.

## Menus
- **Game menu:** lists the node kits / genres (Pong, Brick Breaker, Wave Shooter, Grid Worm, Lane
  Dodger, Lander, Rock Blaster, and any kit added later).
- **Games menu:** lists the games built from the chosen genre (default and seeded builds).

## Rating and sorting
- A **star rating** per game (the player sets it).
- **Sort** the games list by stars, and by date built.

## Open questions for when it starts
- Where ratings are kept (beside the game file, or one ratings file).
- How a game's genre is known (file name today: ComfyBricks, ComfyWaves...; or a header line the
  Build Game node writes).
