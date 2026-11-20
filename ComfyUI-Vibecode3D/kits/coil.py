"""ccoil: a grid worm. Nodes: Worm Board, Worm, Food (chain several kinds), Worm Rules;
shared: Palette. (The board is its own play area: an Arena node is not used.)"""
import copy

from .. import assemble as A

KIT = "ccoil"
PREFIX = "Coil"
TITLE = "grid worm"
GENRE = "Worm"            # the genre the Comfy Games app files it under
EDGES = ("walls", "wrap")
BLOCKS = ("scatter", "bars", "box")
FOODS = ("plain", "gold", "shrink", "slow")
HEADS = ("tri", "diamond", "ship", "ring", "square")
FOOD_SHAPES = ("ring", "diamond", "star", "plus", "square")


def _kits():
    from .. import kits
    return kits


def board(game, columns, rows, cell, edges, blocks, block_style, floor, wall_color, block_color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["board"] = {"cols": A.roll(g, "bc", columns, 8, 48, dice * 0.5, True),
                       "rows": A.roll(g, "br", rows, 6, 30, dice * 0.5, True),
                       "cell": A.roll(g, "bz", cell, 10, 32, dice * 0.5, True),
                       "wrap": A.roll_choice(g, "be", edges, EDGES, dice * 0.5) == "wrap",
                       "blocks": A.roll(g, "bb", blocks, 0, 40, dice, True),
                       "blockStyle": A.roll_choice(g, "bs", block_style, BLOCKS, dice),
                       "floor": A.roll_choice(g, "bf", floor, ("grid", "dots", "bare"), dice),
                       "wall": A.pick_color(g, wall_color, "wall", "bwc", dice),
                       "block": A.pick_color(g, block_color, "goal", "bbc", dice)}
    return g


def worm(game, control, length, step_frames, speed_up, fastest, head, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["worm"] = {"ctrl": control,
                      "length": A.roll(g, "wl", length, 2, 20, dice * 0.5, True),
                      "step": A.roll(g, "ws", step_frames, 2, 20, dice * 0.5, True),
                      "speedUp": A.roll(g, "wu", speed_up, 0, 1, dice),
                      "minStep": A.roll(g, "wm", fastest, 1, 10, dice * 0.3, True),
                      "head": A.roll_choice(g, "wh", head, HEADS, dice),
                      "color": A.pick_color(g, color, "home", "wc", dice)}
    return g


def food(game, kind, count, points, grow, life, shape, color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    foods = g["k"].setdefault("foods", [])
    n = len(foods) + 1
    if not A.roll_chance(g, "fa%d" % n, appear):
        return g
    kind = A.roll_choice(g, "fk%d" % n, kind, FOODS, dice * 0.5)
    default_colors = {"plain": "ball", "gold": "home", "shrink": "away", "slow": "wall"}
    foods.append({"kind": kind,
                  "count": A.roll(g, "fc%d" % n, count, 1, 6, dice * 0.5, True),
                  "points": A.roll(g, "fp%d" % n, points, 1, 200, dice, True),
                  "grow": A.roll(g, "fg%d" % n, grow, 0, 6, dice * 0.5, True),
                  "life": A.roll(g, "fl%d" % n, life, 0, 900, dice, True),
                  "shape": A.roll_choice(g, "fs%d" % n, shape, FOOD_SHAPES, dice),
                  "color": A.pick_color(g, color, default_colors[kind], "fcl%d" % n, dice)})
    return g


def rules(game, lives, levels, food_to_eat, more_each_level, blocks_each_level, faster_each_level, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "rl", lives, 1, 9, dice * 0.3, True),
                       "levels": A.roll(g, "rv", levels, 1, 9, dice * 0.3, True),
                       "target": A.roll(g, "rt", food_to_eat, 1, 60, dice * 0.5, True),
                       "targetGain": A.roll(g, "rg", more_each_level, 0, 20, dice * 0.5, True),
                       "blocksGain": A.roll(g, "rb", blocks_each_level, 0, 20, dice * 0.5, True),
                       "levelGain": A.roll(g, "rf", faster_each_level, 0, 4, dice * 0.5, True)}
    return g


def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    if g.get("arena"):
        g["notes"].append("the worm has its own board: the Arena node was not used")
    if "board" not in k:
        k["board"] = {"cols": 28, "rows": 16, "cell": 22, "wrap": False, "blocks": 6, "blockStyle": "scatter",
                      "floor": "dots", "wall": K.palette_role(g, "wall"), "block": K.palette_role(g, "goal")}
        g["notes"].append("no Worm Board node: 28 x 16 with walls")
    b = k["board"]
    # the board must fit the window (about 780 x 440 under the HUD)
    cell_was = b["cell"]
    while b["cell"] > 8 and (b["cols"] * b["cell"] > 780 or b["rows"] * b["cell"] > 440):
        b["cell"] -= 1
    if b["cell"] < cell_was:
        g["notes"].append("cells %d, not %d, so the board fits" % (b["cell"], cell_was))
    if "worm" not in k:
        k["worm"] = {"ctrl": "arrows", "length": 4, "step": 6, "speedUp": 0.1, "minStep": 2, "head": "tri",
                     "color": K.palette_role(g, "home")}
        g["notes"].append("no Worm node: arrow keys, 4 long")
    w = k["worm"]
    w["length"] = min(w["length"], max(2, b["cols"] // 3))
    if not k.get("foods"):
        k["foods"] = [{"kind": "plain", "count": 1, "points": 10, "grow": 1, "life": 0, "shape": "ring",
                       "color": K.palette_role(g, "ball")}]
        g["notes"].append("no Food node: one plain food")
    if all(f["kind"] == "shrink" for f in k["foods"]):
        k["foods"].append({"kind": "plain", "count": 1, "points": 10, "grow": 1, "life": 0, "shape": "ring",
                           "color": K.palette_role(g, "ball")})
        g["notes"].append("only shrinking food: a plain one was added")
    if "rules" not in k:
        k["rules"] = {"lives": 3, "levels": 3, "target": 10, "targetGain": 5, "blocksGain": 4, "levelGain": 1}
    # the board, described as an arena for the shared preview (floor drawing)
    k["arena"] = {"hw": b["cols"] * b["cell"] / 2.0, "hh": b["rows"] * b["cell"] / 2.0, "cy": 40,
                  "floor": b["floor"], "grid": b["cell"], "wall": b["wall"], "deco": K.shade(b["wall"], 0.35)}
    for f in k["foods"]:
        if f["kind"] != "gold":
            f["life"] = 0
        elif f["life"] <= 0:
            f["life"] = 240
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    K = _kits()
    return K.keys_words(g["k"]["worm"]["ctrl"]).replace("MOVE", "TURN")


def config(g):
    K = _kits()
    k = g["k"]
    b, w, r = k["board"], k["worm"], k["rules"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g)),
             ('sCfg["seed"]', g["seed"] % 100000 + 1), ('sCfg["cy"]', 40),
             ('sCfg["cols"]', b["cols"]), ('sCfg["rows"]', b["rows"]), ('sCfg["cell"]', b["cell"]),
             ('sCfg["wrap"]', b["wrap"]), ('sCfg["blocks"]', b["blocks"]), ('sCfg["blockStyle"]', b["blockStyle"]),
             ('sCfg["floor"]', b["floor"]), ('sCfg["wallColor"]', b["wall"]),
             ('sCfg["decoColor"]', K.shade(b["wall"], 0.35)), ('sCfg["blockColor"]', b["block"]),
             ('sCfg["ctrl"]', w["ctrl"]), ('sCfg["length"]', w["length"]), ('sCfg["stepFrames"]', w["step"]),
             ('sCfg["speedUp"]', w["speedUp"]), ('sCfg["minStep"]', w["minStep"]), ('sCfg["headShape"]', w["head"]),
             ('sCfg["wormColor"]', w["color"]),
             ('sCfg["lives"]', r["lives"]), ('sCfg["levels"]', r["levels"]), ('sCfg["target"]', r["target"]),
             ('sCfg["targetGain"]', r["targetGain"]), ('sCfg["blocksGain"]', r["blocksGain"]),
             ('sCfg["levelGain"]', r["levelGain"]), ("sFoodN", len(k["foods"]))]
    for i, f in enumerate(k["foods"], 1):
        for key in ("kind", "count", "points", "grow", "life", "shape", "color"):
            items.append(('sFood[%d]["%s"]' % (i, key), f[key]))
    return items, ["sCfg", "sFood"]


def rules_lines(g):
    k = g["k"]
    b, r = k["board"], k["rules"]
    foods = ", ".join("%s x%d" % (f["kind"], f["count"]) for f in k["foods"])
    return ["Board %d x %d (%s edges, %d %s blocks). Food: %s." % (b["cols"], b["rows"], "wrapping" if b["wrap"] else "solid",
                                                                   b["blocks"], b["blockStyle"], foods),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     eat %d to clear level 1 (%d more each level); %d levels, %d lives. Your own body, a block"
            % (r["target"], r["targetGain"], r["levels"], r["lives"]),
            "          %s ends a life." % ("" if b["wrap"] else "or the wall")]


def preview(g, d, P):
    k = g["k"]
    b, w = k["board"], k["worm"]
    cs = b["cell"]
    hw, hh = b["cols"] * cs / 2.0, b["rows"] * cs / 2.0

    def X(c):
        return (c - (b["cols"] + 1) / 2.0) * cs

    def Y(r):
        return (r - (b["rows"] + 1) / 2.0) * cs

    d.rectangle([P(-hw, -hh), P(hw, hh)], outline=tuple(b["wall"]), width=2)
    e = (cs - 3) / 2.0
    mid = round((b["rows"] + 1) / 2.0)
    import random
    rnd = random.Random(g["seed"])
    if b["blocks"]:
        for _ in range(b["blocks"]):
            c, r = rnd.randint(1, b["cols"]), rnd.randint(1, b["rows"])
            if r == mid:
                continue
            d.rectangle([P(X(c) - e, Y(r) - e), P(X(c) + e, Y(r) + e)], outline=tuple(b["block"]))
            d.line([P(X(c) - e, Y(r) - e), P(X(c) + e, Y(r) + e)], fill=tuple(b["block"]))
    c0 = max(w["length"] + 1, round(b["cols"] / 3.0))
    for i in range(w["length"]):
        c = c0 - i
        d.rectangle([P(X(c) - e, mid * 0 + Y(mid) - e), P(X(c) + e, Y(mid) + e)], outline=tuple(w["color"]), width=2 if i == 0 else 1)
    for j, f in enumerate(k["foods"]):
        for n in range(f["count"]):
            c, r = rnd.randint(1, b["cols"]), rnd.randint(1, b["rows"])
            d.ellipse([P(X(c) - e, Y(r) - e), P(X(c) + e, Y(r) + e)], outline=tuple(f["color"]))
