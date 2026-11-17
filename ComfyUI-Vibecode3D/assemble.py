"""Vibecode3D game assembler: no ComfyUI needed, so it can be tested on its own.

A "game" is a plain dict the nodes pass along (the VC3D_GAME socket). Each node adds
settings and names the script parts it needs. build() picks those parts up from
LIB_COMFY/parts/<kit>/, writes the generated config handler, and saves one
Vibecode3D_Play_<Name>.livecodescript the game launcher can open.

Seed and dice: every number a node sets can wander from its value when the game has a
seed. dice 0 = exactly as set; 1 = up to 60% either way. Same seed, same game.
"""
import colorsys
import os
import random
import re

KIT = "cpong"
SIDES = ("L", "R", "T", "B")
STYLES = ("classic", "grid", "rings", "bare")
SHAPES = ("square", "diamond", "ring")


# ---------------------------------------------------------------- seed dice
def new_game(title, name, seed, dice):
    return {"kit": KIT, "title": title, "name": name, "seed": int(seed), "dice": float(dice),
            "court": None, "paddles": [], "ball": None, "rules": None, "palette": None,
            "rolls": 0, "notes": []}


def _rng(game, salt):
    game["rolls"] += 1
    return random.Random("%s:%s:%s" % (game["seed"], salt, game["rolls"]))


def roll(game, salt, value, lo, hi, dice, whole=False):
    """value nudged by the seed; dice (0..1, times the game's master dice) sets how far:
    at dice 1 up to 60% of the value either way (at least a tenth of the slider)."""
    d = max(0.0, min(1.0, dice * game["dice"]))
    r = _rng(game, salt)
    if d > 0:
        value = value + r.uniform(-1, 1) * d * max(abs(value) * 0.6, (hi - lo) * 0.1)
    value = max(lo, min(hi, value))
    return int(round(value)) if whole else round(value, 3)


def roll_choice(game, salt, value, choices, dice):
    d = max(0.0, min(1.0, dice * game["dice"]))
    r = _rng(game, salt)
    if value == "random" or r.random() < d:
        return r.choice(list(choices))
    return value


def roll_chance(game, salt, chance):
    """True when a thing should appear (chance 1 = always)."""
    return _rng(game, salt).random() < chance


# ---------------------------------------------------------------- colours
def hex_rgb(h):
    h = h.strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", h):
        return None
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def palette(game, base_hue, scheme, dice):
    """five colours from one hue: walls, goals, home, away, ball."""
    hue = roll(game, "hue", base_hue, 0, 360, dice) / 360.0
    scheme = roll_choice(game, "scheme", scheme, ("neon", "mono", "split", "warm"), dice)

    def c(h, s, v):
        return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h % 1.0, s, v))

    if scheme == "mono":
        p = [c(hue, .5, .9), c(hue, .6, .35), c(hue, .2, 1), c(hue, .9, .8), (255, 255, 255)]
    elif scheme == "split":
        p = [c(hue, .8, .9), c(hue, .8, .3), c(hue + .42, .8, 1), c(hue + .58, .8, 1), c(hue + .5, .2, 1)]
    elif scheme == "warm":
        p = [c(.08, .7, .9), c(.0, .7, .35), c(.14, .8, 1), c(.97, .8, 1), (255, 240, 200)]
    else:  # neon
        p = [c(hue, 1, 1), c(hue, 1, .35), c(hue + .33, 1, 1), c(hue + .66, 1, 1), (255, 255, 255)]
    game["palette"] = {"wall": p[0], "goal": p[1], "home": p[2], "away": p[3], "ball": p[4],
                       "scheme": scheme, "hue": round(hue * 360)}
    return game


def pick_color(game, given, role, salt, dice):
    """'auto' = from the palette; '#rrggbb' = that colour, hue nudged by dice."""
    rgb = hex_rgb(given) if given and given != "auto" else None
    if rgb is None:
        if game["palette"] is None:
            palette(game, 190, "neon", 1.0)
        return game["palette"][role]
    d = max(0.0, min(1.0, dice * game["dice"]))
    if d > 0:
        h, s, v = colorsys.rgb_to_hsv(*(x / 255.0 for x in rgb))
        h += _rng(game, salt).uniform(-0.5, 0.5) * d
        rgb = tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h % 1.0, s, v))
    return rgb


# ---------------------------------------------------------------- build
def _fixups(game):
    """make the game playable whatever the nodes said."""
    g = dict(game)
    g["notes"] = list(game["notes"])
    if g["court"] is None:
        g["court"] = {"hw": 380, "hh": 210, "cy": 40, "style": "classic", "grid": 60,
                      "wall": (0, 255, 255), "goal": (0, 80, 90)}
        g["notes"].append("no Court node: a classic court was used")
    if g["ball"] is None:
        g["ball"] = {"size": 14, "speed": 7, "gain": 1.05, "max": 16, "count": 1,
                     "shape": "square", "color": (255, 255, 255)}
        g["notes"].append("no Ball node: one square ball was used")
    if g["rules"] is None:
        g["rules"] = {"win": 5, "levels": 3, "levelGain": 0.15}
    pads = [dict(p) for p in g["paddles"]]
    has_cpu = any(p["ctrl"] == "cpu" for p in pads)
    for p in pads:
        if p["team"] == "auto":
            p["team"] = "away" if p["ctrl"] == "cpu" or (p["ctrl"] == "wasd" and not has_cpu) else "home"
    if not any(p["team"] == "home" for p in pads):
        pads.append({"side": "L", "ctrl": "arrows", "team": "home", "half": 45, "speed": 9,
                     "inset": 24, "color": g["court"]["wall"], "skill": 0.5})
        g["notes"].append("no home paddle: an arrow-key paddle was put on the left")
    goals = {}
    for side in SIDES:
        here = sorted([p for p in pads if p["side"] == side], key=lambda p: p["inset"])
        if here:
            goals[side] = here[0]["team"]
    if "away" not in goals.values():
        home_sides = [s for s in SIDES if goals.get(s) == "home"]
        opposite = {"L": "R", "R": "L", "T": "B", "B": "T"}
        free = [opposite[s] for s in home_sides if opposite[s] not in goals] or \
               [s for s in SIDES if s not in goals]
        if free:
            pads.append({"side": free[0], "ctrl": "cpu", "team": "away", "half": 45, "speed": 8,
                         "inset": 24, "color": (255, 80, 80), "skill": 0.5})
            goals[free[0]] = "away"
            g["notes"].append("no away goal: a computer paddle was put on side " + free[0])
    for p in pads:
        hw, hh = g["court"]["hw"], g["court"]["hh"]
        p["fx"] = {"L": -hw + p["inset"], "R": hw - p["inset"],
                   "T": -hh + p["inset"], "B": hh - p["inset"]}[p["side"]]
    g["paddles"] = pads
    g["goals"] = goals
    g["axis"] = "x" if ("L" in goals or "R" in goals) else "y"
    return g


def _rgb(c):
    return "%d,%d,%d" % tuple(c)


def _q(s):
    return '"' + str(s).replace('"', "'") + '"'


def _hud_safe(s):
    return re.sub(r"[|%()]", " ", str(s)).upper()


def help_line(g):
    keys = []
    if any(p["ctrl"] == "arrows" for p in g["paddles"]):
        keys.append("ARROWS MOVE")
    if any(p["ctrl"] == "wasd" for p in g["paddles"]):
        keys.append("W A S D MOVE")
    keys.append("SPACE SERVES")
    return "  ".join(keys)


def config_handler(g):
    c, b, r = g["court"], g["ball"], g["rules"]
    L = ["on Cpong.Config", "   put empty into sCfg", "   put empty into sPad", "   put empty into sGoal"]

    def put(v, key):
        L.append("   put %s into %s" % (v, key))
    put(_q(_hud_safe(g["title"])), 'sCfg["title"]')
    put(_q(help_line(g)), 'sCfg["help"]')
    put(c["hw"], 'sCfg["hw"]')
    put(c["hh"], 'sCfg["hh"]')
    put(c["cy"], 'sCfg["cy"]')
    put(c["grid"], 'sCfg["grid"]')
    put(_q(_rgb(c["wall"])), 'sCfg["wallColor"]')
    put(_q(_rgb(c["goal"])), 'sCfg["goalColor"]')
    put(_q(_rgb([int(v * 0.4) for v in c["wall"]])), 'sCfg["decoColor"]')
    put(_q(g["axis"]), 'sCfg["axis"]')
    put(b["size"], 'sCfg["ballSize"]')
    put(b["speed"], 'sCfg["ballSpeed"]')
    put(b["gain"], 'sCfg["ballGain"]')
    put(b["max"], 'sCfg["ballMax"]')
    put(b["count"], 'sCfg["ballCount"]')
    put(_q(_rgb(b["color"])), 'sCfg["ballColor"]')
    put(r["win"], 'sCfg["win"]')
    put(r["levels"], 'sCfg["levels"]')
    put(r["levelGain"], 'sCfg["levelGain"]')
    put(len(g["paddles"]), "sPadN")
    for i, p in enumerate(g["paddles"], 1):
        for key, val in (("side", _q(p["side"])), ("ctrl", _q(p["ctrl"])), ("team", _q(p["team"])),
                         ("half", p["half"]), ("speed", p["speed"]), ("fx", p["fx"]),
                         ("skill", p["skill"]), ("color", _q(_rgb(p["color"])))):
            put(val, 'sPad[%d]["%s"]' % (i, key))
    for side, team in g["goals"].items():
        put(_q(team), 'sGoal["%s"]' % side)
    L.append("end Cpong.Config")
    return "\n".join(L)


def parts_needed(g):
    parts = ["core", "court_" + g["court"]["style"], "ball_" + g["ball"]["shape"]]
    if any(p["ctrl"] != "cpu" for p in g["paddles"]):
        parts.append("control_keys")
    if any(p["ctrl"] == "cpu" for p in g["paddles"]):
        parts.append("control_cpu")
    return parts


def safe_name(name):
    n = re.sub(r"[^A-Za-z0-9]", "", name or "")
    return n or "ComfyPong"


def header(g, name, parts):
    pads = ", ".join("%s %s %s" % (p["side"], p["ctrl"], p["team"]) for p in g["paddles"])
    return "\n".join([
        "#" * 86,
        '## CARD SCRIPT: "Play.%s"   %s  (made in ComfyUI, seed %s)' % (name, _hud_safe(g["title"]), g["seed"]),
        "## Put together by the Vibecode3D nodes from LIB_COMFY/parts/%s: %s." % (g["kit"], ", ".join(parts)),
        "## Paddles: %s. Court %s, ball %s x%s." % (pads, g["court"]["style"], g["ball"]["shape"], g["ball"]["count"]),
        "## CONTROLS  %s   Escape: stop" % help_line(g).title(),
        "## RULES     a ball past a goal mouth is a point for the other team. First to %s wins the"
        % g["rules"]["win"],
        "##           level; %s levels, each one faster." % g["rules"]["levels"],
        "#" * 86, ""])


def build(game, projects_root, out_dir=None, name=None):
    """returns (path, script, g) with g the fixed-up game (for the preview)."""
    g = _fixups(game)
    name = safe_name(name or g["name"])
    parts = parts_needed(g)
    pdir = os.path.join(projects_root, "LIB_COMFY", "parts", g["kit"])
    chunks = [header(g, name, parts)]
    for part in parts:
        with open(os.path.join(pdir, part + ".part.livecodescript"), encoding="utf-8") as f:
            chunks.append(f.read().rstrip() + "\n")
    chunks.append("## PART config (generated by the Build node)\n" + config_handler(g) + "\n")
    script = "\n".join(chunks)
    if out_dir is None:
        out_dir = os.path.join(projects_root, "LIB_GAMES", "Vibecode3D_Games")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Vibecode3D_Play_%s.livecodescript" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    g["parts"] = parts
    g["file_name"] = name
    return path, script, g
