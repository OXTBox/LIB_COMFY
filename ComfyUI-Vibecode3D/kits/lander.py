"""cland: a lander. Nodes: Lander Craft, Ground, Lander Rules; shared: Arena, Palette."""
import copy
import math
import random

from .. import assemble as A

KIT = "cland"
PREFIX = "Lander"
TITLE = "lander"
GENRE = "Lander"            # the genre the Comfy Games app files it under
MODES = ("rotate", "slide")


def _kits():
    from .. import kits
    return kits


def craft(game, mode, control, thrust, turn, fuel, size, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["craft"] = {"mode": A.roll_choice(g, "cm", mode, MODES, dice * 0.3), "ctrl": control,
                       "thrust": A.roll(g, "ct", thrust, 0.05, 0.6, dice),
                       "turn": A.roll(g, "cr", turn, 0.01, 0.15, dice),
                       "fuel": A.roll(g, "cf", fuel, 100, 3000, dice, True),
                       "size": A.roll(g, "cz", size, 14, 40, dice, True),
                       "color": A.pick_color(g, color, "home", "cc", dice)}
    return g


def ground(game, segments, roughness, hills, pads, ground_color, pad_color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["ground"] = {"segments": A.roll(g, "gs", segments, 8, 60, dice * 0.5, True),
                        "rough": A.roll(g, "gr", roughness, 0.1, 2.5, dice),
                        "hills": A.roll(g, "gh", hills, 40, 300, dice, True),
                        "pads": A.roll(g, "gp", pads, 1, 6, dice * 0.5, True),
                        "ground": A.pick_color(g, ground_color, "wall", "gc", dice),
                        "pad": A.pick_color(g, pad_color, "ball", "gpc", dice)}
    return g


def rules(game, craft_count, levels, gravity, gravity_gain, safe_speed, wind, points, start_drift, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "rl", craft_count, 1, 9, dice * 0.3, True),
                       "levels": A.roll(g, "rv", levels, 1, 9, dice * 0.3, True),
                       "gravity": A.roll(g, "rg", gravity, 0.005, 0.2, dice),
                       "gain": A.roll(g, "rgg", gravity_gain, 0, 1, dice),
                       "safe": A.roll(g, "rs", safe_speed, 0.5, 5, dice),
                       "wind": A.roll(g, "rw", wind, 0, 0.05, dice),
                       "points": A.roll(g, "rp", points, 10, 500, dice, True),
                       "drift": A.roll(g, "rd", start_drift, 0, 4, dice)}
    return g


def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    k["arena"] = K.arena_or_default(g, 360, 220, "stars", 60)
    if "craft" not in k:
        k["craft"] = {"mode": "rotate", "ctrl": "arrows", "thrust": 0.16, "turn": 0.05, "fuel": 900, "size": 24,
                      "color": K.palette_role(g, "home")}
        g["notes"].append("no Lander Craft node: a turning craft")
    if "ground" not in k:
        k["ground"] = {"segments": 24, "rough": 0.9, "hills": 150, "pads": 3, "ground": K.palette_role(g, "wall"),
                       "pad": K.palette_role(g, "ball")}
        g["notes"].append("no Ground node: rough ground, three pads")
    if "rules" not in k:
        k["rules"] = {"lives": 3, "levels": 3, "gravity": 0.04, "gain": 0.3, "safe": 1.6, "wind": 0.0,
                      "points": 50, "drift": 1.0}
    c, gr, r = k["craft"], k["ground"], k["rules"]
    # thrust must beat gravity, or nothing can land
    if c["thrust"] < r["gravity"] * (1 + r["gain"] * (r["levels"] - 1)) * 1.6:
        c["thrust"] = round(r["gravity"] * (1 + r["gain"] * (r["levels"] - 1)) * 1.6, 3)
        g["notes"].append("thrust raised to %.3f so the craft can beat the pull" % c["thrust"])
    gr["hills"] = min(gr["hills"], k["arena"]["hh"] * 2 - 120)
    gr["pads"] = min(gr["pads"], max(1, gr["segments"] // 5))
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    c = g["k"]["craft"]
    keys = "W A S D" if c["ctrl"] == "wasd" else "ARROWS"
    return "%s: UP BURNS, %s" % (keys, "LEFT RIGHT TURN" if c["mode"] == "rotate" else "LEFT RIGHT PUSH")


def config(g):
    K = _kits()
    k = g["k"]
    c, gr, r = k["craft"], k["ground"], k["rules"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g)),
             ('sCfg["seed"]', g["seed"] % 100000 + 1)]
    items += K.arena_config(k["arena"])
    items += [('sCfg["mode"]', c["mode"]), ('sCfg["ctrl"]', c["ctrl"]), ('sCfg["thrust"]', c["thrust"]),
              ('sCfg["turn"]', c["turn"]), ('sCfg["fuel"]', c["fuel"]), ('sCfg["size"]', c["size"]),
              ('sCfg["craftColor"]', c["color"]), ('sCfg["flameColor"]', (255, 160, 40)),
              ('sCfg["segments"]', gr["segments"]), ('sCfg["rough"]', gr["rough"]), ('sCfg["hills"]', gr["hills"]),
              ('sCfg["pads"]', gr["pads"]), ('sCfg["groundColor"]', gr["ground"]), ('sCfg["padColor"]', gr["pad"]),
              ('sCfg["lives"]', r["lives"]), ('sCfg["levels"]', r["levels"]), ('sCfg["gravity"]', r["gravity"]),
              ('sCfg["levelGain"]', r["gain"]), ('sCfg["safe"]', r["safe"]), ('sCfg["wind"]', r["wind"]),
              ('sCfg["points"]', r["points"]), ('sCfg["startVX"]', r["drift"])]
    return items, ["sCfg"]


def rules_lines(g):
    k = g["k"]
    c, gr, r = k["craft"], k["ground"], k["rules"]
    return ["A %s craft, %d fuel; ground of %d segments with %d pads; pull %.3f, %d%% stronger each level."
            % (c["mode"], c["fuel"], gr["segments"], gr["pads"], r["gravity"], round(r["gain"] * 100)),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     land on a pad, upright, slower than %.1f down: narrow pads score up to three times."
            % r["safe"],
            "          %d levels, %d craft; leftover fuel is points." % (r["levels"], r["lives"])]


def preview(g, d, P):
    k = g["k"]
    a, c, gr = k["arena"], k["craft"], k["ground"]
    hw, hh = a["hw"], a["hh"]
    rnd = random.Random(g["seed"])
    n = gr["segments"]
    step = hw * 2.0 / n
    low, high = hh - 10, hh - gr["hills"]
    y = low - rnd.uniform(0, low - high)
    pads = set()
    for _ in range(gr["pads"]):
        s = rnd.randint(2, n - 3)
        span = rnd.randint(1, 3)
        pads.update(range(s, s + span))
    x0 = -hw
    for i in range(1, n + 1):
        x = -hw + i * step
        if i in pads:
            ny = y
            d.line([P(x0, y), P(x, ny)], fill=tuple(gr["pad"]), width=3)
        else:
            ny = max(high, min(low, y + rnd.uniform(-1, 1) * gr["rough"] * step))
            d.line([P(x0, y), P(x, ny)], fill=tuple(gr["ground"]))
        x0, y = x, ny
    s = c["size"] / 2.0
    cy = -hh + 30
    col = tuple(c["color"])
    d.rectangle([P(-s * 0.6, cy - s * 0.8), P(s * 0.6, cy + s * 0.2)], outline=col)
    d.line([P(-s * 0.6, cy + s * 0.2), P(-s, cy + s)], fill=col)
    d.line([P(s * 0.6, cy + s * 0.2), P(s, cy + s)], fill=col)
    d.line([P(-s * 0.2, cy + s * 0.45), P(0, cy + s * 1.1), P(s * 0.2, cy + s * 0.45)], fill=(255, 160, 40))
