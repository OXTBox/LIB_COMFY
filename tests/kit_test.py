"""Build games from the genre kits without ComfyUI, through the node classes themselves.

    python tests/kit_test.py KIT SEED [out_dir]     KIT: brick wave coil dodge (or all)

Run it with Comfy's python.exe (it has PIL) to get the preview PNG beside each game; any
python3 builds the scripts. Each kit's chain below is what its workflow file holds."""
import os, sys, types, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "ComfyUI-Vibecode3D")
for mod in ("torch", "numpy"):
    try:
        __import__(mod)
    except ImportError:
        sys.modules[mod] = types.ModuleType(mod)
spec = importlib.util.spec_from_file_location("vc3d", os.path.join(PACK, "__init__.py"),
                                              submodule_search_locations=[PACK])
vc = importlib.util.module_from_spec(spec); sys.modules["vc3d"] = vc; spec.loader.exec_module(vc)
N = vc.NODE_CLASS_MAPPINGS


def run(key, game, **kw):
    return N[key]().run(game, **kw)[0]


def start(title, name, seed):
    g = N["VC3D_GameStart"]().run(title, name, seed, 1.0)[0]
    return run("VC3D_Palette", g, hue=(seed * 37) % 360, scheme="random", dice=0.5) if "VC3D_Palette" in N else g


def brick(seed, rows=6):
    g = start("Comfy Bricks", "ComfyBricks", seed)
    g = run("VC3D_Arena", g, width=720, height=440, floor="random", spacing=40, wall_color="auto", dice=0.5)
    g = run("VC3D_BrickWall", g, rows=rows, columns=10, pattern="random", next_patterns="pyramid, random",
            brick_height=16, gap=4, tough_rows=1, top_color="auto", bottom_color="auto", dice=0.5)
    g = run("VC3D_Bat", g, control="arrows", width=100, speed=10.0, color="auto", dice=0.5)
    g = N["VC3D_Ball"]().run(g, 12, 6.0, 1.02, 13.0, 1, "random", "auto", 0.5)[0]
    g = run("VC3D_PowerUp", g, kind="wide", chance=0.08, color="auto", appear=1.0, dice=0.3)
    g = run("VC3D_PowerUp", g, kind="multi", chance=0.06, color="auto", appear=0.7, dice=0.3)
    g = run("VC3D_PowerUp", g, kind="random", chance=0.05, color="auto", appear=0.6, dice=0.3)
    g = run("VC3D_BreakerRules", g, lives=3, levels=3, level_speed_up=0.12, points=10, dice=0.5)
    return g


def wave(seed, rows=4):
    g = start("Comfy Waves", "ComfyWaves", seed)
    g = run("VC3D_Arena", g, width=720, height=440, floor="stars", spacing=50, wall_color="auto", dice=0.5)
    g = run("VC3D_ShooterShip", g, control="arrows", shape="random", size=26, speed=6.0, fire_delay=12,
            shot_speed=11.0, max_shots=2, color="auto", dice=0.5)
    g = run("VC3D_EnemyWave", g, formation="block", foe="crab", rows=rows, columns=8, size=24, gap=12, speed=1.0,
            drop=14, fire=0.002, dive=0.0, points=10, top_color="auto", bottom_color="auto", appear=1.0, dice=0.4)
    g = run("VC3D_EnemyWave", g, formation="random", foe="random", rows=rows, columns=9, size=22, gap=12, speed=1.4,
            drop=12, fire=0.003, dive=0.002, points=20, top_color="auto", bottom_color="auto", appear=1.0, dice=0.6)
    g = run("VC3D_EnemyWave", g, formation="swarm", foe="random", rows=rows - 1, columns=7, size=26, gap=16, speed=1.8,
            drop=10, fire=0.004, dive=0.004, points=30, top_color="auto", bottom_color="auto", appear=0.8, dice=0.6)
    g = run("VC3D_Shields", g, count=4, columns=6, rows=3, cell=8, hits=2, color="auto", dice=0.5)
    g = run("VC3D_WaveRules", g, ships=3, waves_to_win=0, round_speed_up=0.25, rush=1.5, dice=0.5)
    return g


def wave_small(seed):
    g = wave(seed, rows=1)
    g["name"] = "ComfyWavesSmall"
    return g


def coil(seed, target=10):
    g = start("Comfy Worm", "ComfyWorm", seed)
    g = run("VC3D_WormBoard", g, columns=28, rows=16, cell=22, edges="random", blocks=6, block_style="random",
            floor="random", wall_color="auto", block_color="auto", dice=0.5)
    g = run("VC3D_Worm", g, control="arrows", length=4, step_frames=5, speed_up=0.1, fastest=2, head="tri",
            color="auto", dice=0.5)
    g = run("VC3D_Food", g, kind="plain", count=2, points=10, grow=1, life=0, shape="ring", color="auto",
            appear=1.0, dice=0.3)
    g = run("VC3D_Food", g, kind="gold", count=1, points=50, grow=3, life=240, shape="star", color="auto",
            appear=0.8, dice=0.3)
    g = run("VC3D_Food", g, kind="random", count=1, points=20, grow=1, life=0, shape="random", color="auto",
            appear=0.6, dice=0.5)
    g = run("VC3D_WormRules", g, lives=3, levels=3, food_to_eat=target, more_each_level=5, blocks_each_level=4,
            faster_each_level=1, dice=0.5)
    return g


def coil_small(seed):
    g = coil(seed, target=3)
    g["name"] = "ComfyWormSmall"
    return g


def brick_small(seed):
    g = brick(seed, rows=2)
    g["name"] = "ComfyBricksSmall"
    return g


CHAINS = {"brick": brick, "brick_small": brick_small, "wave": wave, "wave_small": wave_small,
          "coil": coil, "coil_small": coil_small}
for extra in ("wave", "coil", "dodge"):
    f = globals().get("chain_" + extra)
    if f:
        CHAINS[extra] = f


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    out = sys.argv[3] if len(sys.argv) > 3 else None
    root = os.path.abspath(os.path.join(HERE, "..", ".."))
    for kit in ([c for c in CHAINS if not c.endswith("_small")] if which == "all" else [which]):
        g = CHAINS[kit](seed)
        path, script, gg = vc.assemble.build(g, root, out, "%s%d" % (g["name"], seed))
        print(path)
        print("  parts:", gg["parts"], " notes:", gg["notes"])
        try:
            vc.preview.draw(gg).save(path.replace(".livecodescript", ".png"))
            print("  preview saved")
        except ImportError as e:
            print("  no preview:", e)


if __name__ == "__main__":
    main()
