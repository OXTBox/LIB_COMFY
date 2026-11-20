"""cbrick: a brick breaker. Nodes: Brick Wall, Bat, Power-Up (chain several), Breaker Rules;
shared: Arena, Palette, Ball."""
import copy

from .. import assemble as A

KIT = "cbrick"
PREFIX = "Brick"
TITLE = "brick breaker"
GENRE = "Bricks"            # the genre the Comfy Games app files it under
PATTERNS = ("solid", "checker", "pyramid", "columns", "frame", "holes")
POWERS = ("wide", "multi", "slow", "life")


def _kits():
    from .. import kits
    return kits


# ------------------------------------------------------------ what the nodes set
def wall(game, rows, cols, pattern, next_patterns, brick_height, gap, tough_rows, top_color, bottom_color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    first = A.roll_choice(g, "wp", pattern, PATTERNS, dice)
    later = [p.strip() for p in str(next_patterns).split(",") if p.strip() in PATTERNS + ("random",)]
    later = [A.roll_choice(g, "wn%d" % i, p, PATTERNS, dice) for i, p in enumerate(later)]
    g["k"]["wall"] = {
        "rows": A.roll(g, "wr", rows, 1, 12, dice * 0.5, True),
        "cols": A.roll(g, "wc", cols, 3, 16, dice * 0.5, True),
        "patterns": [first] + later,
        "bh": A.roll(g, "wh", brick_height, 8, 30, dice, True),
        "gap": A.roll(g, "wg", gap, 1, 12, dice, True),
        "tough": A.roll(g, "wt", tough_rows, 0, 12, dice * 0.5, True),
        "colorTop": A.pick_color(g, top_color, "away", "wct", dice),
        "colorBottom": A.pick_color(g, bottom_color, "home", "wcb", dice),
    }
    return g


def bat(game, control, width, speed, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["bat"] = {"ctrl": control,
                     "half": A.roll(g, "bw", width, 30, 260, dice, True) // 2,
                     "speed": A.roll(g, "bv", speed, 3, 24, dice),
                     "color": A.pick_color(g, color, "home", "bc", dice)}
    return g


def power(game, kind, chance, color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    n = len(g["k"].setdefault("powers", [])) + 1
    if not A.roll_chance(g, "pa%d" % n, appear):
        return g
    colors = {"wide": (80, 200, 255), "multi": (255, 220, 60), "slow": (120, 255, 120), "life": (255, 90, 160)}
    kind = A.roll_choice(g, "pk%d" % n, kind, POWERS, dice * 0.5)
    c = colors[kind] if color == "auto" else A.pick_color(g, color, "ball", "pc%d" % n, dice)
    g["k"]["powers"].append({"kind": kind, "chance": A.roll(g, "pp%d" % n, chance, 0, 1, dice), "color": c})
    return g


def rules(game, lives, levels, level_speed_up, points, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "rl", lives, 1, 9, dice * 0.3, True),
                       "levels": A.roll(g, "rv", levels, 1, 9, dice * 0.3, True),
                       "gain": A.roll(g, "rg", level_speed_up, 0, 0.6, dice),
                       "points": A.roll(g, "rp", points, 1, 100, dice, True)}
    return g


# ------------------------------------------------------------ build
def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    a = K.arena_or_default(g, 360, 220, "dots", 40)
    if "wall" not in k:
        k["wall"] = {"rows": 6, "cols": 10, "patterns": ["solid", "pyramid", "checker"], "bh": 16, "gap": 4,
                     "tough": 1, "colorTop": K.palette_role(g, "away"), "colorBottom": K.palette_role(g, "home")}
        g["notes"].append("no Brick Wall node: 6 rows of 10")
    if "bat" not in k:
        k["bat"] = {"ctrl": "arrows", "half": 50, "speed": 10, "color": K.palette_role(g, "home")}
        g["notes"].append("no Bat node: an arrow-key bat")
    if "rules" not in k:
        k["rules"] = {"lives": 3, "levels": 3, "gain": 0.12, "points": 10}
    if g.get("ball") is None:
        g["ball"] = {"size": 12, "speed": 6, "gain": 1.02, "max": 13, "count": 1, "shape": "square",
                     "color": K.palette_role(g, "ball")}
        g["notes"].append("no Ball node: one square ball")
    w = k["wall"]
    side = 20
    top = 50
    # the wall may not reach the bat: rows shrink until it leaves room
    pitch_y = w["bh"] + w["gap"]
    rows_were = w["rows"]
    while w["rows"] > 1 and top + w["rows"] * pitch_y > a["hh"] * 2 - 140:
        w["rows"] -= 1
    if w["rows"] < rows_were:
        g["notes"].append("the wall was too tall for the arena: %d rows, not %d" % (w["rows"], rows_were))
    pitch_x = (a["hw"] * 2 - side * 2) / float(w["cols"])
    w["bw"] = max(6, round(pitch_x - w["gap"], 2))
    w["pitchX"] = round(pitch_x, 3)
    w["pitchY"] = pitch_y
    w["side"], w["top"] = side, top
    w["tough"] = min(w["tough"], w["rows"])
    k["arena"] = a
    k["rowColors"] = K.ramp(w["colorTop"], w["colorBottom"], w["rows"])
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    K = _kits()
    return K.keys_words(g["k"]["bat"]["ctrl"], "SPACE SERVES")


def config(g):
    K = _kits()
    k, b = g["k"], g["ball"]
    w, bt, r = k["wall"], k["bat"], k["rules"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g)),
             ('sCfg["seed"]', g["seed"] % 100000 + 1)]
    items += K.arena_config(k["arena"])
    items += [('sCfg["rows"]', w["rows"]), ('sCfg["cols"]', w["cols"]), ('sCfg["bw"]', w["bw"]),
              ('sCfg["bh"]', w["bh"]), ('sCfg["pitchX"]', w["pitchX"]), ('sCfg["pitchY"]', w["pitchY"]),
              ('sCfg["side"]', w["side"]), ('sCfg["top"]', w["top"]), ('sCfg["tough"]', w["tough"]),
              ('sCfg["patterns"]', ",".join(w["patterns"])),
              ('sCfg["ctrl"]', bt["ctrl"]), ('sCfg["batHalf"]', bt["half"]), ('sCfg["batSpeed"]', bt["speed"]),
              ('sCfg["batColor"]', bt["color"]),
              ('sCfg["ballSize"]', b["size"]), ('sCfg["ballSpeed"]', b["speed"]), ('sCfg["ballGain"]', b["gain"]),
              ('sCfg["ballMax"]', b["max"]), ('sCfg["ballShape"]', b["shape"]), ('sCfg["ballColor"]', b["color"]),
              ('sCfg["lives"]', r["lives"]), ('sCfg["levels"]', r["levels"]), ('sCfg["levelGain"]', r["gain"]),
              ('sCfg["points"]', r["points"]), ('sCfg["levelBonus"]', r["points"] * 20),
              ('sCfg["serveWait"]', 120)]
    for i, c in enumerate(k["rowColors"], 1):
        items.append(('sRow[%d]' % i, c))
    powers = k.get("powers", [])
    items.append(("sPowN", len(powers)))
    for i, p in enumerate(powers, 1):
        items += [('sPow[%d]["kind"]' % i, p["kind"]), ('sPow[%d]["chance"]' % i, p["chance"]),
                  ('sPow[%d]["color"]' % i, p["color"])]
    return items, ["sCfg", "sRow", "sPow"]


def rules_lines(g):
    k = g["k"]
    w, r = k["wall"], k["rules"]
    pw = ", ".join("%s %d%%" % (p["kind"], round(p["chance"] * 100)) for p in k.get("powers", [])) or "none"
    return ["Wall %d x %d, levels: %s. Power-ups: %s." % (w["rows"], w["cols"], ", ".join(w["patterns"]), pw),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     break every brick to clear the level; %d levels, %d lives, a ball past the bat is a"
            % (r["levels"], r["lives"]),
            "          life lost. Tough bricks (with a cross) take two hits."]


def preview(g, d, P):
    k = g["k"]
    a, w, bt, b = k["arena"], k["wall"], k["bat"], g["ball"]
    hw, hh = a["hw"], a["hh"]
    d.line([P(-hw, hh), P(-hw, -hh), P(hw, -hh), P(hw, hh)], fill=tuple(a["wall"]), width=2)
    pat = w["patterns"][0]
    for r in range(1, w["rows"] + 1):
        for c in range(1, w["cols"] + 1):
            mid = (w["cols"] + 1) / 2.0
            want = {"checker": (r + c) % 2 == 0, "pyramid": abs(c - mid) < r * w["cols"] / (2.0 * w["rows"]) + 0.5,
                    "columns": c % 3 != 0, "frame": r in (1, w["rows"]) or c in (1, w["cols"]),
                    "holes": (r * 7 + c * 13) % 4 != 0}.get(pat, True)
            if not want:
                continue
            x = -hw + w["side"] + (c - 0.5) * w["pitchX"]
            y = -hh + w["top"] + (r - 0.5) * w["pitchY"]
            col = tuple(k["rowColors"][r - 1])
            box = [P(x - w["bw"] / 2, y - w["bh"] / 2), P(x + w["bw"] / 2, y + w["bh"] / 2)]
            d.rectangle(box, outline=col, width=1)
            if r <= w["tough"]:
                d.line([box[0], box[1]], fill=col)
    by = hh - 30
    d.rectangle([P(-bt["half"], by - 6), P(bt["half"], by + 6)], outline=tuple(bt["color"]), width=2)
    s = b["size"] / 2
    d.rectangle([P(-s, by - 6 - 2 * s), P(s, by - 6)], outline=tuple(b["color"]), width=2)
    for i, p in enumerate(k.get("powers", [])):
        x = -hw + 60 + i * 60
        d.rectangle([P(x - 11, 40), P(x + 11, 46)], outline=tuple(p["color"]))
        d.text(P(x - 11, 50), p["kind"], fill=tuple(p["color"]))
