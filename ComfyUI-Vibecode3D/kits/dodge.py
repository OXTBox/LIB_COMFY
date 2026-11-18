"""cdodge: a lane dodger. Nodes: Runner, Hazard (chain several), Pickup (chain several),
Dodge Rules; shared: Arena, Palette."""
import copy

from .. import assemble as A

KIT = "cdodge"
PREFIX = "Dodge"
TITLE = "lane dodger"
RUNNERS = ("ship", "tri", "saucer", "diamond", "bug")
HAZARDS = ("rock", "diamond", "crab", "bug", "square", "tri", "star", "ring")
PICKUPS = ("coin", "shield", "slow", "life")


def _kits():
    from .. import kits
    return kits


def runner(game, control, lanes, shape, size, speed, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["runner"] = {"ctrl": control,
                        "lanes": A.roll(g, "rl", lanes, 0, 7, dice * 0.3, True),
                        "shape": A.roll_choice(g, "rs", shape, RUNNERS, dice),
                        "size": A.roll(g, "rz", size, 14, 50, dice, True),
                        "speed": A.roll(g, "rv", speed, 3, 30, dice),
                        "color": A.pick_color(g, color, "home", "rc", dice)}
    return g


def hazard(game, shape, size, speed, rate, wobble, in_lane, spin, points, color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    hz = g["k"].setdefault("hazards", [])
    n = len(hz) + 1
    if not A.roll_chance(g, "ha%d" % n, appear):
        return g
    hz.append({"shape": A.roll_choice(g, "hs%d" % n, shape, HAZARDS, dice),
               "size": A.roll(g, "hz%d" % n, size, 10, 80, dice, True),
               "speed": A.roll(g, "hv%d" % n, speed, 1, 16, dice),
               "rate": A.roll(g, "hr%d" % n, rate, 0.001, 0.2, dice),
               "wobble": A.roll(g, "hw%d" % n, wobble, 0, 120, dice, True),
               "inLane": bool(in_lane), "spin": bool(spin),
               "points": A.roll(g, "hp%d" % n, points, 0, 50, dice, True),
               "color": A.pick_color(g, color, "away", "hc%d" % n, dice)})
    return g


def pickup(game, kind, rate, points, color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    pk = g["k"].setdefault("pickups", [])
    n = len(pk) + 1
    if not A.roll_chance(g, "pa%d" % n, appear):
        return g
    kind = A.roll_choice(g, "pk%d" % n, kind, PICKUPS, dice * 0.5)
    colors = {"coin": (255, 220, 60), "shield": (80, 200, 255), "slow": (120, 255, 120), "life": (255, 90, 160)}
    shapes = {"coin": "ring", "shield": "diamond", "slow": "plus", "life": "star"}
    pk.append({"kind": kind, "shape": shapes[kind],
               "rate": A.roll(g, "pr%d" % n, rate, 0, 0.05, dice),
               "points": A.roll(g, "pp%d" % n, points, 0, 200, dice, True),
               "color": colors[kind] if color == "auto" else A.pick_color(g, color, "ball", "pc%d" % n, dice)})
    return g


def rules(game, lives, levels, distance, level_speed_up, scroll, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "ql", lives, 1, 9, dice * 0.3, True),
                       "levels": A.roll(g, "qv", levels, 1, 9, dice * 0.3, True),
                       "distance": A.roll(g, "qd", distance, 100, 9000, dice * 0.5, True),
                       "gain": A.roll(g, "qg", level_speed_up, 0, 1, dice),
                       "scroll": A.roll(g, "qs", scroll, 0, 16, dice)}
    return g


def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    k["arena"] = K.arena_or_default(g, 300, 220, "lanes", 60)
    if "runner" not in k:
        k["runner"] = {"ctrl": "arrows", "lanes": 5, "shape": "ship", "size": 28, "speed": 9,
                       "color": K.palette_role(g, "home")}
        g["notes"].append("no Runner node: five lanes, arrow keys")
    if not k.get("hazards"):
        k["hazards"] = [{"shape": "rock", "size": 36, "speed": 5, "rate": 0.03, "wobble": 0, "inLane": True,
                         "spin": True, "points": 5, "color": K.palette_role(g, "away")}]
        g["notes"].append("no Hazard node: rocks")
    k.setdefault("pickups", [])
    if "rules" not in k:
        k["rules"] = {"lives": 3, "levels": 3, "distance": 1200, "gain": 0.25, "scroll": 6}
    r = k["runner"]
    if r["lanes"] == 1:
        r["lanes"] = 0
    if r["lanes"] > 1:
        # with lanes the game draws the lane lines, not the arena's floor
        k["arena"] = dict(k["arena"], floor="bare")
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    K = _kits()
    r = g["k"]["runner"]
    return K.keys_words(r["ctrl"]) + ("  ONE LANE A PRESS" if r["lanes"] > 1 and r["ctrl"] != "mouse" else "")


def config(g):
    K = _kits()
    k = g["k"]
    rn, r = k["runner"], k["rules"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g))]
    items += K.arena_config(k["arena"])
    items += [('sCfg["ctrl"]', rn["ctrl"]), ('sCfg["lanes"]', rn["lanes"]), ('sCfg["meShape"]', rn["shape"]),
              ('sCfg["meSize"]', rn["size"]), ('sCfg["meSpeed"]', rn["speed"]), ('sCfg["meColor"]', rn["color"]),
              ('sCfg["lives"]', r["lives"]), ('sCfg["levels"]', r["levels"]), ('sCfg["distance"]', r["distance"]),
              ('sCfg["levelGain"]', r["gain"]), ('sCfg["scroll"]', r["scroll"]), ('sCfg["pickSpeed"]', 3),
              ("sHazN", len(k["hazards"])), ("sPickN", len(k["pickups"]))]
    for i, h in enumerate(k["hazards"], 1):
        for key in ("shape", "size", "speed", "rate", "wobble", "inLane", "spin", "points", "color"):
            items.append(('sHaz[%d]["%s"]' % (i, key), h[key]))
    for i, p in enumerate(k["pickups"], 1):
        for key in ("kind", "shape", "rate", "points", "color"):
            items.append(('sPick[%d]["%s"]' % (i, key), p[key]))
    return items, ["sCfg", "sHaz", "sPick"]


def rules_lines(g):
    k = g["k"]
    rn, r = k["runner"], k["rules"]
    hz = ", ".join("%s%s" % (h["shape"], " (wobbling)" if h["wobble"] else "") for h in k["hazards"])
    pk = ", ".join(p["kind"] for p in k["pickups"]) or "none"
    return ["%s. Hazards: %s. Pickups: %s." % (("%d lanes" % rn["lanes"]) if rn["lanes"] > 1 else "Free running", hz, pk),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     last %d steps to clear a level; %d levels, each faster; %d lives. Shield, slow time"
            % (r["distance"], r["levels"], r["lives"]),
            "          and extra lives fall with the hazards."]


def preview(g, d, P):
    from .wave import _shape
    import random
    k = g["k"]
    a, rn = k["arena"], k["runner"]
    hw, hh = a["hw"], a["hh"]
    d.line([P(-hw, -hh), P(-hw, hh)], fill=tuple(a["wall"]), width=2)
    d.line([P(hw, -hh), P(hw, hh)], fill=tuple(a["wall"]), width=2)
    rnd = random.Random(g["seed"])
    lanes = rn["lanes"]
    if lanes > 1:
        lw = hw * 2.0 / lanes
        for i in range(1, lanes):
            x = -hw + i * lw
            y = -hh
            while y < hh:
                d.line([P(x, y), P(x, min(hh, y + lw / 3.0))], fill=tuple(a["deco"]))
                y += lw * 2 / 3.0
    for h in k["hazards"]:
        for _ in range(3):
            x = (-hw + (rnd.randint(1, lanes) - 0.5) * hw * 2.0 / lanes) if lanes > 1 and h["inLane"] else rnd.uniform(-hw + 20, hw - 20)
            _shape(d, P, h["shape"] if h["shape"] != "rock" else "diamond", x, rnd.uniform(-hh + 20, hh - 120), h["size"] / 2.0, tuple(h["color"]))
    for p in k["pickups"]:
        x = rnd.uniform(-hw + 20, hw - 20)
        _shape(d, P, p["shape"] if p["shape"] in ("ring", "diamond", "star") else "square", x, rnd.uniform(-hh + 20, hh - 120), 9, tuple(p["color"]))
    _shape(d, P, rn["shape"], 0, hh - 34, rn["size"] / 2.0, tuple(rn["color"]))
