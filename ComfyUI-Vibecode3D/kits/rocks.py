"""crock: a rock blaster. Nodes: Blaster Ship, Rock Field, Saucer, Rock Rules; shared: Arena, Palette."""
import copy
import math
import random

from .. import assemble as A

KIT = "crock"
PREFIX = "Rocks"
TITLE = "rock blaster"
GENRE = "Rocks"            # the genre the Comfy Games app files it under
SHIPS = ("ship", "tri", "diamond")


def _kits():
    from .. import kits
    return kits


def ship(game, control, shape, size, thrust, turn, drag, top_speed, fire_delay, shot_speed, shot_life, max_shots, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["ship"] = {"ctrl": control, "shape": A.roll_choice(g, "ss", shape, SHIPS, dice),
                      "size": A.roll(g, "sz", size, 14, 40, dice, True),
                      "thrust": A.roll(g, "st", thrust, 0.05, 1.0, dice),
                      "turn": A.roll(g, "sr", turn, 0.03, 0.25, dice),
                      "drag": A.roll(g, "sd", drag, 0.9, 1.0, dice * 0.3),
                      "top": A.roll(g, "sv", top_speed, 2, 16, dice),
                      "cool": A.roll(g, "sc", fire_delay, 2, 30, dice, True),
                      "shotSpeed": A.roll(g, "sp", shot_speed, 4, 20, dice),
                      "shotLife": A.roll(g, "sl", shot_life, 10, 120, dice, True),
                      "maxShots": A.roll(g, "sm", max_shots, 1, 8, dice * 0.5, True),
                      "color": A.pick_color(g, color, "home", "scl", dice)}
    return g


def field(game, rocks, more_each_level, size, speed, points, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["field"] = {"rocks": A.roll(g, "fr", rocks, 1, 12, dice * 0.5, True),
                       "more": A.roll(g, "fm", more_each_level, 0, 4, dice * 0.5, True),
                       "size": A.roll(g, "fz", size, 20, 70, dice, True),
                       "speed": A.roll(g, "fv", speed, 0.3, 4, dice),
                       "points": A.roll(g, "fp", points, 5, 100, dice, True),
                       "color": A.pick_color(g, color, "wall", "fc", dice)}
    return g


def saucer(game, chance, points, color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    if not A.roll_chance(g, "ua", appear):
        return g
    g["k"]["saucer"] = {"chance": A.roll(g, "uc", chance, 0, 0.02, dice),
                        "points": A.roll(g, "up", points, 50, 2000, dice, True),
                        "color": A.pick_color(g, color, "away", "ucl", dice)}
    return g


def rules(game, ships, level_speed_up, extra_ship_every, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "rl", ships, 1, 9, dice * 0.3, True),
                       "gain": A.roll(g, "rg", level_speed_up, 0, 1, dice),
                       "extra": A.roll(g, "re", extra_ship_every, 0, 50000, dice * 0.3, True)}
    return g


def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    k["arena"] = K.arena_or_default(g, 380, 220, "stars", 60)
    if "ship" not in k:
        k["ship"] = {"ctrl": "arrows", "shape": "ship", "size": 22, "thrust": 0.25, "turn": 0.09, "drag": 0.99,
                     "top": 8, "cool": 8, "shotSpeed": 9, "shotLife": 50, "maxShots": 4,
                     "color": K.palette_role(g, "home")}
        g["notes"].append("no Blaster Ship node: an arrow-key ship")
    if "field" not in k:
        k["field"] = {"rocks": 4, "more": 1, "size": 44, "speed": 1.2, "points": 20, "color": K.palette_role(g, "wall")}
        g["notes"].append("no Rock Field node: four big rocks")
    k.setdefault("saucer", {"chance": 0, "points": 0, "color": K.palette_role(g, "away")})
    if "rules" not in k:
        k["rules"] = {"lives": 3, "gain": 0.15, "extra": 10000}
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    s = g["k"]["ship"]
    keys = "W A S D" if s["ctrl"] == "wasd" else "ARROWS"
    return "%s: LEFT RIGHT TURN, UP THRUSTS  SPACE FIRES" % keys


def config(g):
    K = _kits()
    k = g["k"]
    s, f, u, r = k["ship"], k["field"], k["saucer"], k["rules"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g))]
    items += K.arena_config(k["arena"])
    items += [('sCfg["ctrl"]', s["ctrl"]), ('sCfg["shipShape"]', s["shape"]), ('sCfg["shipSize"]', s["size"]),
              ('sCfg["thrust"]', s["thrust"]), ('sCfg["turn"]', s["turn"]), ('sCfg["drag"]', s["drag"]),
              ('sCfg["topSpeed"]', s["top"]), ('sCfg["cool"]', s["cool"]), ('sCfg["shotSpeed"]', s["shotSpeed"]),
              ('sCfg["shotLife"]', s["shotLife"]), ('sCfg["maxShots"]', s["maxShots"]),
              ('sCfg["shipColor"]', s["color"]), ('sCfg["shotColor"]', K.shade(s["color"], 1.3)),
              ('sCfg["flameColor"]', (255, 160, 40)),
              ('sCfg["rocks"]', f["rocks"]), ('sCfg["moreEach"]', f["more"]), ('sCfg["rockSize"]', f["size"]),
              ('sCfg["rockSpeed"]', f["speed"]), ('sCfg["points"]', f["points"]), ('sCfg["rockColor"]', f["color"]),
              ('sCfg["ufoChance"]', u["chance"]), ('sCfg["ufoPoints"]', u["points"]), ('sCfg["ufoColor"]', u["color"]),
              ('sCfg["lives"]', r["lives"]), ('sCfg["levelGain"]', r["gain"]), ('sCfg["extraLife"]', r["extra"])]
    return items, ["sCfg"]


def rules_lines(g):
    k = g["k"]
    f, u, r = k["field"], k["saucer"], k["rules"]
    return ["%d rocks to start, %d more each level%s." % (f["rocks"], f["more"], ", a saucer now and then" if u["chance"] else ""),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     shoot every rock to clear the level: big ones split in two, then two again. %d ships%s."
            % (r["lives"], (", one more every %d points" % r["extra"]) if r["extra"] else "")]


def preview(g, d, P):
    k = g["k"]
    a, s, f = k["arena"], k["ship"], k["field"]
    hw, hh = a["hw"], a["hh"]
    d.rectangle([P(-hw, -hh), P(hw, hh)], outline=tuple(a["wall"]), width=2)
    rnd = random.Random(g["seed"])
    for i in range(f["rocks"]):
        ang = rnd.uniform(0, 2 * math.pi)
        rr = min(hw, hh) * 0.9
        x, y = rr * math.cos(ang) * hw / min(hw, hh), rr * math.sin(ang)
        pts = []
        for j in range(10):
            t = j * 2 * math.pi / 10
            r = f["size"] * (0.75 + ((j * 37 + 33) % 10) / 30.0)
            pts.append(P(x + r * math.cos(t), y + r * math.sin(t)))
        d.polygon(pts, outline=tuple(f["color"]))
    h = s["size"] / 2.0
    d.polygon([P(0, -h), P(h, h), P(0, h / 2), P(-h, h)], outline=tuple(s["color"]))
    if k["saucer"]["chance"]:
        d.ellipse([P(-hw + 40, -hh + 30), P(-hw + 74, -hh + 42)], outline=tuple(k["saucer"]["color"]))
