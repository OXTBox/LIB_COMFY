"""ComfyUI-Vibecode3D: game parts as nodes. Chain them like Blueprint nodes:

  Game Start -> Palette -> Court -> Paddle -> Paddle ... -> Ball -> Match Rules -> Build Game

Each node passes the game along (the VC3D_GAME wire) and adds its settings. Build Game
picks up the script parts the chain needs from LIB_COMFY/parts, writes a playable
Vibecode3D game card script, and shows a still frame of it.
Set "control after generate" on Game Start's seed to randomize and every Queue gives a new
variant; each node's dice says how far its settings may wander from what you set.
"""
import copy
import json
import os

import numpy as np
import torch

from . import assemble, preview

CAT = "Vibecode3D/Vectors"
GAME = ("VC3D_GAME",)
_HERE = os.path.dirname(os.path.abspath(__file__))


def projects_root():
    cfg = os.path.join(_HERE, "config.json")
    if os.path.exists(cfg):
        with open(cfg, encoding="utf-8") as f:
            root = json.load(f).get("projects")
        if root:
            return root
    if os.name == "nt":
        return r"\\wsl$\Ubuntu\home\igame3d\projects"
    return os.path.dirname(os.path.dirname(_HERE))


def _dice():
    return ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.05,
                      "tooltip": "how far the seed may move this node's settings (0 = exactly as set)"})


def _color(default="auto"):
    return ("STRING", {"default": default, "tooltip": "auto = from the palette, or #rrggbb"})


class GameStart:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "title": ("STRING", {"default": "Comfy Pong"}),
            "name": ("STRING", {"default": "ComfyPong", "tooltip": "file name: Vibecode3D_Play_<name>.livecodescript"}),
            "seed": ("INT", {"default": 1, "min": 0, "max": 2 ** 31 - 1, "control_after_generate": True}),
            "dice": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                               "tooltip": "master dice: multiplies every node's dice"}),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "Starts a game chain: the seed every later node rolls its dice with."

    def run(self, title, name, seed, dice):
        return (assemble.new_game(title, name, seed, dice),)


class Palette:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "hue": ("INT", {"default": 190, "min": 0, "max": 360}),
            "scheme": (["neon", "mono", "split", "warm", "random"], {"default": "neon"}),
            "dice": _dice(),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "Five colours from one hue (walls, goals, home, away, ball); 'auto' colours use them."

    def run(self, game, hue, scheme, dice):
        g = copy.deepcopy(game)
        return (assemble.palette(g, hue, scheme, dice),)


class Court:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "width": ("INT", {"default": 760, "min": 300, "max": 840, "step": 10}),
            "height": ("INT", {"default": 420, "min": 200, "max": 440, "step": 10}),
            "style": (["classic", "grid", "rings", "bare", "random"], {"default": "classic"}),
            "grid": ("INT", {"default": 60, "min": 20, "max": 200, "step": 5}),
            "wall_color": _color(),
            "goal_color": _color(),
            "dice": _dice(),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "The court: its size and floor style. A side with a paddle is a goal mouth, the rest are walls."

    def run(self, game, width, height, style, grid, wall_color, goal_color, dice):
        g = copy.deepcopy(game)
        g["court"] = {
            "hw": assemble.roll(g, "cw", width, 300, 840, dice, True) // 2,
            "hh": assemble.roll(g, "ch", height, 200, 440, dice, True) // 2,
            "cy": 40,
            "style": assemble.roll_choice(g, "cs", style, assemble.STYLES, dice),
            "grid": assemble.roll(g, "cg", grid, 20, 200, dice, True),
            "wall": assemble.pick_color(g, wall_color, "wall", "cwc", dice),
            "goal": assemble.pick_color(g, goal_color, "goal", "cgc", dice),
        }
        return (g,)


class Paddle:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "side": (["L", "R", "T", "B", "random"], {"default": "L"}),
            "control": (["arrows", "wasd", "cpu"], {"default": "arrows"}),
            "team": (["auto", "home", "away"], {"default": "auto"}),
            "length": ("INT", {"default": 90, "min": 20, "max": 300, "step": 5}),
            "speed": ("FLOAT", {"default": 9.0, "min": 2.0, "max": 24.0, "step": 0.5}),
            "inset": ("INT", {"default": 24, "min": 10, "max": 300, "step": 2,
                              "tooltip": "distance from its goal line; bigger = further up the court"}),
            "skill": ("FLOAT", {"default": 0.6, "min": 0.0, "max": 1.0, "step": 0.05,
                                "tooltip": "computer paddles: how well it reads the ball"}),
            "color": _color(),
            "appear": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05,
                                 "tooltip": "chance this paddle is in the game for a seed (1 = always)"}),
            "dice": _dice(),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "One paddle. Chain several; the paddle nearest a side's goal line owns that goal."

    def run(self, game, side, control, team, length, speed, inset, skill, color, appear, dice):
        g = copy.deepcopy(game)
        n = len(g["paddles"]) + 1
        if not assemble.roll_chance(g, "pa%d" % n, appear):
            return (g,)
        side = assemble.roll_choice(g, "ps%d" % n, side, assemble.SIDES, dice * 0.3)
        if team == "auto":
            role = "away" if control == "cpu" else "home"
        else:
            role = team
        g["paddles"].append({
            "side": side, "ctrl": control, "team": team,
            "half": assemble.roll(g, "pl%d" % n, length, 20, 300, dice, True) // 2,
            "speed": assemble.roll(g, "pv%d" % n, speed, 2, 24, dice),
            "inset": assemble.roll(g, "pi%d" % n, inset, 10, 300, dice * 0.3, True),
            "skill": assemble.roll(g, "pk%d" % n, skill, 0, 1, dice),
            "color": assemble.pick_color(g, color, role, "pc%d" % n, dice),
        })
        return (g,)


class Ball:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "size": ("INT", {"default": 14, "min": 4, "max": 40}),
            "speed": ("FLOAT", {"default": 7.0, "min": 2.0, "max": 20.0, "step": 0.5}),
            "speed_up": ("FLOAT", {"default": 1.05, "min": 1.0, "max": 1.3, "step": 0.01,
                                   "tooltip": "speed times this at every paddle hit"}),
            "top_speed": ("FLOAT", {"default": 16.0, "min": 4.0, "max": 30.0, "step": 0.5}),
            "count": ("INT", {"default": 1, "min": 1, "max": 3}),
            "shape": (["square", "diamond", "ring", "random"], {"default": "square"}),
            "color": _color(),
            "dice": _dice(),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "The ball (or up to three)."

    def run(self, game, size, speed, speed_up, top_speed, count, shape, color, dice):
        g = copy.deepcopy(game)
        g["ball"] = {
            "size": assemble.roll(g, "bs", size, 4, 40, dice, True),
            "speed": assemble.roll(g, "bv", speed, 2, 20, dice),
            "gain": assemble.roll(g, "bg", speed_up, 1.0, 1.3, dice),
            "max": assemble.roll(g, "bm", top_speed, 4, 30, dice),
            "count": assemble.roll(g, "bn", count, 1, 3, dice * 0.5, True),
            "shape": assemble.roll_choice(g, "bh", shape, assemble.SHAPES, dice),
            "color": assemble.pick_color(g, color, "ball", "bc", dice),
        }
        return (g,)


class MatchRules:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "points_to_win": ("INT", {"default": 5, "min": 1, "max": 21}),
            "levels": ("INT", {"default": 3, "min": 1, "max": 9}),
            "level_speed_up": ("FLOAT", {"default": 0.15, "min": 0.0, "max": 0.6, "step": 0.05}),
            "dice": _dice(),
        }}
    RETURN_TYPES = GAME
    RETURN_NAMES = ("game",)
    FUNCTION = "run"
    CATEGORY = CAT
    DESCRIPTION = "How a match is won, and how many levels."

    def run(self, game, points_to_win, levels, level_speed_up, dice):
        g = copy.deepcopy(game)
        g["rules"] = {
            "win": assemble.roll(g, "rw", points_to_win, 1, 21, dice * 0.3, True),
            "levels": assemble.roll(g, "rl", levels, 1, 9, dice * 0.3, True),
            "levelGain": assemble.roll(g, "rg", level_speed_up, 0, 0.6, dice),
        }
        return (g,)


class BuildGame:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "game": GAME,
            "add_seed_to_name": ("BOOLEAN", {"default": True}),
            "save_to": (["LIB_GAMES (the game launcher sees it)", "ComfyUI output folder"],),
        }}
    RETURN_TYPES = ("STRING", "IMAGE", "STRING")
    RETURN_NAMES = ("script_path", "preview", "script")
    FUNCTION = "run"
    OUTPUT_NODE = True
    CATEGORY = CAT
    DESCRIPTION = "Picks up the script parts the chain needs, writes a playable Vibecode3D game, shows a still of it."

    def run(self, game, add_seed_to_name, save_to):
        out_dir = None
        if save_to.startswith("ComfyUI"):
            import folder_paths
            out_dir = os.path.join(folder_paths.get_output_directory(), "vibecode3d")
        name = assemble.safe_name(game["name"])
        if add_seed_to_name:
            name += str(game["seed"])
        path, script, g = assemble.build(game, projects_root(), out_dir, name)
        im = preview.draw(g)
        tensor = torch.from_numpy(np.asarray(im).astype(np.float32) / 255.0)[None, ]
        ui = {"text": [path]}
        try:
            import folder_paths
            tmp = folder_paths.get_temp_directory()
            os.makedirs(tmp, exist_ok=True)
            fn = "vc3d_%s.png" % name
            im.save(os.path.join(tmp, fn))
            ui["images"] = [{"filename": fn, "subfolder": "", "type": "temp"}]
        except Exception:
            pass
        return {"ui": ui, "result": (path, tensor, script)}


# ---------------------------------------------------------------- the genre kits
# Every kit but Pong: a node is made from (key, display name, category, description, inputs, run).
# Inputs are (name, ComfyUI spec) in widget order; run(game, **widgets) returns the new game.
from . import kits  # noqa: E402
from .kits import brick, wave  # noqa: E402,F401

CAT_SHARED = "Vibecode3D/Shared"


def _node(key, display, category, description, inputs, run):
    spec = {"required": dict([("game", GAME)] + list(inputs))}

    def INPUT_TYPES(cls):
        return spec

    def go(self, game, **kw):
        return (run(game, **kw),)
    cls = type(key, (), {"INPUT_TYPES": classmethod(INPUT_TYPES), "RETURN_TYPES": GAME,
                         "RETURN_NAMES": ("game",), "FUNCTION": "run", "CATEGORY": category,
                         "DESCRIPTION": description, "run": go})
    _GENRE_NODES.append((key, display, cls))
    return cls


_GENRE_NODES = []


def _int(default, lo, hi, step=1, tip=None):
    d = {"default": default, "min": lo, "max": hi, "step": step}
    if tip:
        d["tooltip"] = tip
    return ("INT", d)


def _float(default, lo, hi, step=0.05, tip=None):
    d = {"default": default, "min": lo, "max": hi, "step": step}
    if tip:
        d["tooltip"] = tip
    return ("FLOAT", d)


def _pick(choices, default, tip=None):
    d = {"default": default}
    if tip:
        d["tooltip"] = tip
    return (list(choices), d)


def _chance(default=1.0, tip="chance this node is in the game for a seed (1 = always)"):
    return _float(default, 0.0, 1.0, 0.05, tip)


_node("VC3D_Arena", "Arena (Vibecode3D)", CAT_SHARED,
      "The play area for every kit but Pong: its size, the floor drawn under it, the wall colour.",
      [("width", _int(720, 300, 780, 10)), ("height", _int(420, 240, 460, 10)),
       ("floor", _pick(assemble.FLOORS + ("random",), "grid")),
       ("spacing", _int(60, 16, 160, 2, "the floor's grid / ring / lane spacing")),
       ("wall_color", _color()), ("dice", _dice())],
      lambda game, **k: assemble.arena(game, **k))

# -------- Brick Breaker
CAT_BRICK = "Vibecode3D/Brick Breaker"
_node("VC3D_BrickWall", "Brick Wall (Vibecode3D)", CAT_BRICK,
      "The wall of bricks: rows, columns, the pattern for level 1 and the patterns after it.",
      [("rows", _int(6, 1, 12)), ("columns", _int(10, 3, 16)),
       ("pattern", _pick(brick.PATTERNS + ("random",), "solid")),
       ("next_patterns", ("STRING", {"default": "pyramid, checker", "tooltip": "levels 2, 3...: names from the pattern list, commas between (random allowed); they repeat"})),
       ("brick_height", _int(16, 8, 30)), ("gap", _int(4, 1, 12)),
       ("tough_rows", _int(1, 0, 12, 1, "top rows that take two hits")),
       ("top_color", _color()), ("bottom_color", _color()), ("dice", _dice())],
      lambda game, rows, columns, **k: brick.wall(game, rows, columns, **k))
_node("VC3D_Bat", "Bat (Vibecode3D)", CAT_BRICK,
      "The player's bat at the bottom: keys or the mouse, width, speed.",
      [("control", _pick(("arrows", "wasd", "mouse"), "arrows")), ("width", _int(100, 30, 260, 5)),
       ("speed", _float(10.0, 3.0, 24.0, 0.5)), ("color", _color()), ("dice", _dice())],
      lambda game, **k: brick.bat(game, **k))
_node("VC3D_PowerUp", "Power-Up (Vibecode3D)", CAT_BRICK,
      "Something that may fall from a broken brick. Chain several for several kinds.",
      [("kind", _pick(brick.POWERS + ("random",), "wide")),
       ("chance", _float(0.08, 0.0, 1.0, 0.01, "chance a broken brick drops it")),
       ("color", _color()), ("appear", _chance()), ("dice", _dice())],
      lambda game, **k: brick.power(game, **k))
_node("VC3D_BreakerRules", "Breaker Rules (Vibecode3D)", CAT_BRICK,
      "Lives, levels, how much faster each level is, points a brick.",
      [("lives", _int(3, 1, 9)), ("levels", _int(3, 1, 9)), ("level_speed_up", _float(0.12, 0.0, 0.6)),
       ("points", _int(10, 1, 100)), ("dice", _dice())],
      lambda game, **k: brick.rules(game, **k))

# -------- Wave Shooter
CAT_WAVE = "Vibecode3D/Wave Shooter"
_node("VC3D_ShooterShip", "Shooter Ship (Vibecode3D)", CAT_WAVE,
      "Your ship along the bottom: control, shape, speed, how fast it fires.",
      [("control", _pick(("arrows", "wasd"), "arrows")), ("shape", _pick(wave.SHIPS + ("random",), "ship")),
       ("size", _int(26, 14, 48)), ("speed", _float(6.0, 2.0, 16.0, 0.5)),
       ("fire_delay", _int(12, 2, 40, 1, "steps between shots")), ("shot_speed", _float(11.0, 4.0, 24.0, 0.5)),
       ("max_shots", _int(2, 1, 6, 1, "shots in the air at once")), ("color", _color()), ("dice", _dice())],
      lambda game, **k: wave.ship(game, **k))
_node("VC3D_EnemyWave", "Enemy Wave (Vibecode3D)", CAT_WAVE,
      "One wave: its formation and foes. Chain several: level 1 is the first, and round they go, faster each time.",
      [("formation", _pick(wave.FORMATIONS + ("random",), "block")), ("foe", _pick(wave.FOES + ("random",), "crab")),
       ("rows", _int(4, 1, 7)), ("columns", _int(8, 2, 14)), ("size", _int(24, 12, 44)), ("gap", _int(12, 2, 30)),
       ("speed", _float(1.0, 0.2, 6.0, 0.1, "march speed")), ("drop", _int(14, 0, 40, 1, "step down at each wall")),
       ("fire", _float(0.002, 0.0, 0.02, 0.0005, "chance a foe drops a bomb each step")),
       ("dive", _float(0.001, 0.0, 0.02, 0.0005, "chance each step that one foe dives at you")),
       ("points", _int(10, 1, 200)), ("top_color", _color()), ("bottom_color", _color()),
       ("appear", _chance()), ("dice", _dice())],
      lambda game, **k: wave.wave(game, **k))
_node("VC3D_Shields", "Shields (Vibecode3D)", CAT_WAVE,
      "Blocks between you and the wave that wear away under shots and bombs.",
      [("count", _int(4, 0, 6)), ("columns", _int(6, 1, 10)), ("rows", _int(3, 1, 5)),
       ("cell", _int(8, 4, 16, 1, "size of one block")), ("hits", _int(2, 1, 5, 1, "hits a block takes")),
       ("color", _color()), ("dice", _dice())],
      lambda game, **k: wave.shields(game, **k))
_node("VC3D_WaveRules", "Wave Rules (Vibecode3D)", CAT_WAVE,
      "Ships, how many waves win (0 = play on), how much faster each time round, how much the last few rush.",
      [("ships", _int(3, 1, 9)), ("waves_to_win", _int(0, 0, 30)), ("round_speed_up", _float(0.25, 0.0, 1.0)),
       ("rush", _float(1.5, 0.0, 4.0, 0.1, "speed added as the wave thins out")), ("dice", _dice())],
      lambda game, **k: wave.rules(game, **k))

NODE_CLASS_MAPPINGS = {
    "VC3D_GameStart": GameStart,
    "VC3D_Palette": Palette,
    "VC3D_Court": Court,
    "VC3D_Paddle": Paddle,
    "VC3D_Ball": Ball,
    "VC3D_MatchRules": MatchRules,
    "VC3D_BuildGame": BuildGame,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "VC3D_GameStart": "Game Start (Vibecode3D)",
    "VC3D_Palette": "Palette (Vibecode3D)",
    "VC3D_Court": "Pong Court (Vibecode3D)",
    "VC3D_Paddle": "Paddle (Vibecode3D)",
    "VC3D_Ball": "Ball (Vibecode3D)",
    "VC3D_MatchRules": "Match Rules (Vibecode3D)",
    "VC3D_BuildGame": "Build Game (Vibecode3D)",
}
for _key, _display, _cls in _GENRE_NODES:
    NODE_CLASS_MAPPINGS[_key] = _cls
    NODE_DISPLAY_NAME_MAPPINGS[_key] = _display
