"""The starter chain of every genre kit, as data: [(node key, its widget values by name)].
tests/kit_test.py runs them through the node classes; tools/make_kit_workflows.py writes them
as ComfyUI workflow files. A chain's "small" form (fewer bricks / foes / food / steps) is for
tests that play a game to its end."""

AUTO = "auto"


def start(title, name):
    return [("VC3D_GameStart", {"title": title, "name": name, "seed": 1, "dice": 1.0}),
            ("VC3D_Palette", {"hue": 190, "scheme": "random", "dice": 0.5})]


def arena(width, height, floor, spacing, dice=0.5):
    return ("VC3D_Arena", {"width": width, "height": height, "floor": floor, "spacing": spacing,
                           "wall_color": AUTO, "dice": dice})


def brick(small=False):
    rows = 2 if small else 6
    return start("Comfy Bricks", "ComfyBricksSmall" if small else "ComfyBricks") + [
        arena(720, 440, "random", 40),
        ("VC3D_BrickWall", {"rows": rows, "columns": 10, "pattern": "random", "next_patterns": "pyramid, random",
                            "brick_height": 16, "gap": 4, "tough_rows": 1, "top_color": AUTO, "bottom_color": AUTO,
                            "dice": 0.5}),
        ("VC3D_Bat", {"control": "arrows", "width": 100, "speed": 10.0, "color": AUTO, "dice": 0.5}),
        ("VC3D_Ball", {"size": 12, "speed": 6.0, "speed_up": 1.02, "top_speed": 13.0, "count": 1, "shape": "random",
                       "color": AUTO, "dice": 0.5}),
        ("VC3D_PowerUp", {"kind": "wide", "chance": 0.08, "color": AUTO, "appear": 1.0, "dice": 0.3}),
        ("VC3D_PowerUp", {"kind": "multi", "chance": 0.06, "color": AUTO, "appear": 0.7, "dice": 0.3}),
        ("VC3D_PowerUp", {"kind": "random", "chance": 0.05, "color": AUTO, "appear": 0.6, "dice": 0.3}),
        ("VC3D_BreakerRules", {"lives": 3, "levels": 3, "level_speed_up": 0.12, "points": 10, "dice": 0.5})]


def wave(small=False):
    rows = 1 if small else 4
    return start("Comfy Waves", "ComfyWavesSmall" if small else "ComfyWaves") + [
        arena(720, 440, "stars", 50),
        ("VC3D_ShooterShip", {"control": "arrows", "shape": "random", "size": 26, "speed": 6.0, "fire_delay": 12,
                              "shot_speed": 11.0, "max_shots": 2, "color": AUTO, "dice": 0.5}),
        ("VC3D_EnemyWave", {"formation": "block", "foe": "crab", "rows": rows, "columns": 8, "size": 24, "gap": 12,
                            "speed": 1.0, "drop": 14, "fire": 0.002, "dive": 0.0, "points": 10, "top_color": AUTO,
                            "bottom_color": AUTO, "appear": 1.0, "dice": 0.4}),
        ("VC3D_EnemyWave", {"formation": "random", "foe": "random", "rows": rows, "columns": 9, "size": 22, "gap": 12,
                            "speed": 1.4, "drop": 12, "fire": 0.003, "dive": 0.002, "points": 20, "top_color": AUTO,
                            "bottom_color": AUTO, "appear": 1.0, "dice": 0.6}),
        ("VC3D_EnemyWave", {"formation": "swarm", "foe": "random", "rows": max(1, rows - 1), "columns": 7, "size": 26,
                            "gap": 16, "speed": 1.8, "drop": 10, "fire": 0.004, "dive": 0.004, "points": 30,
                            "top_color": AUTO, "bottom_color": AUTO, "appear": 0.8, "dice": 0.6}),
        ("VC3D_Shields", {"count": 4, "columns": 6, "rows": 3, "cell": 8, "hits": 2, "color": AUTO, "dice": 0.5}),
        ("VC3D_WaveRules", {"ships": 3, "waves_to_win": 0, "round_speed_up": 0.25, "rush": 1.5, "dice": 0.5})]


def coil(small=False):
    return start("Comfy Worm", "ComfyWormSmall" if small else "ComfyWorm") + [
        ("VC3D_WormBoard", {"columns": 28, "rows": 16, "cell": 22, "edges": "random", "blocks": 6,
                            "block_style": "random", "floor": "random", "wall_color": AUTO, "block_color": AUTO,
                            "dice": 0.5}),
        ("VC3D_Worm", {"control": "arrows", "length": 4, "step_frames": 5, "speed_up": 0.1, "fastest": 2,
                       "head": "tri", "color": AUTO, "dice": 0.5}),
        ("VC3D_Food", {"kind": "plain", "count": 2, "points": 10, "grow": 1, "life": 0, "shape": "ring",
                       "color": AUTO, "appear": 1.0, "dice": 0.3}),
        ("VC3D_Food", {"kind": "gold", "count": 1, "points": 50, "grow": 3, "life": 240, "shape": "star",
                       "color": AUTO, "appear": 0.8, "dice": 0.3}),
        ("VC3D_Food", {"kind": "random", "count": 1, "points": 20, "grow": 1, "life": 0, "shape": "random",
                       "color": AUTO, "appear": 0.6, "dice": 0.5}),
        ("VC3D_WormRules", {"lives": 3, "levels": 3, "food_to_eat": 3 if small else 10, "more_each_level": 5,
                            "blocks_each_level": 4, "faster_each_level": 1, "dice": 0.5})]


def dodge(small=False):
    return start("Comfy Dodge", "ComfyDodgeSmall" if small else "ComfyDodge") + [
        arena(600, 440, "lanes", 60, 0.3),
        ("VC3D_Runner", {"control": "arrows", "lanes": 0 if small else 5, "shape": "ship", "size": 28, "speed": 9.0,
                         "color": AUTO, "dice": 0.5}),
        ("VC3D_Hazard", {"shape": "rock", "size": 36, "speed": 5.0, "rate": 0.03, "wobble": 0, "in_lane": True,
                         "spin": True, "points": 5, "color": AUTO, "appear": 1.0, "dice": 0.5}),
        ("VC3D_Hazard", {"shape": "random", "size": 24, "speed": 7.0, "rate": 0.015, "wobble": 40, "in_lane": False,
                         "spin": False, "points": 10, "color": AUTO, "appear": 0.8, "dice": 0.5}),
        ("VC3D_Pickup", {"kind": "coin", "rate": 0.008, "points": 25, "color": AUTO, "appear": 1.0, "dice": 0.3}),
        ("VC3D_Pickup", {"kind": "random", "rate": 0.003, "points": 10, "color": AUTO, "appear": 0.7, "dice": 0.3}),
        ("VC3D_DodgeRules", {"lives": 3, "levels": 3, "distance": 200 if small else 1200, "level_speed_up": 0.25,
                             "scroll": 6.0, "dice": 0.5})]


KITS = {"brick": brick, "wave": wave, "coil": coil, "dodge": dodge}
# what each kit's game is called in xTalk, for tests that read its state
PREFIX = {"brick": "Brick", "wave": "Wave", "coil": "Coil", "dodge": "Dodge"}


def chain(kit, seed=1, small=False):
    steps = [(key, dict(widgets)) for key, widgets in KITS[kit](small)]
    steps[0][1]["seed"] = seed
    steps[1][1]["hue"] = (seed * 37) % 360
    return steps
