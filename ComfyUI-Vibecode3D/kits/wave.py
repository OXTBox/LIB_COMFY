"""cwave: a wave shooter. Nodes: Shooter Ship, Enemy Wave (chain several: one a level, round
and round), Shields, Wave Rules; shared: Arena, Palette."""
import copy

from .. import assemble as A

KIT = "cwave"
PREFIX = "Wave"
TITLE = "wave shooter"
GENRE = "Waves"            # the genre the Comfy Games app files it under
FORMATIONS = ("block", "vee", "diamond", "ragged", "swarm")
FOES = ("crab", "bug", "saucer", "diamond", "tri", "star", "ring")
SHIPS = ("ship", "tri", "saucer", "diamond")


def _kits():
    from .. import kits
    return kits


def ship(game, control, shape, size, speed, fire_delay, shot_speed, max_shots, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["ship"] = {"ctrl": control,
                      "shape": A.roll_choice(g, "ss", shape, SHIPS, dice),
                      "size": A.roll(g, "sz", size, 14, 48, dice, True),
                      "speed": A.roll(g, "sv", speed, 2, 16, dice),
                      "cool": A.roll(g, "sc", fire_delay, 2, 40, dice, True),
                      "shotSpeed": A.roll(g, "sp", shot_speed, 4, 24, dice),
                      "maxShots": A.roll(g, "sm", max_shots, 1, 6, dice * 0.5, True),
                      "color": A.pick_color(g, color, "home", "scl", dice)}
    return g


def wave(game, formation, foe, rows, columns, size, gap, speed, drop, fire, dive, points, top_color, bottom_color, appear, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    waves = g["k"].setdefault("waves", [])
    n = len(waves) + 1
    if not A.roll_chance(g, "wa%d" % n, appear):
        return g
    w = {"formation": A.roll_choice(g, "wf%d" % n, formation, FORMATIONS, dice),
         "shape": A.roll_choice(g, "wh%d" % n, foe, FOES, dice),
         "rows": A.roll(g, "wr%d" % n, rows, 1, 7, dice * 0.5, True),
         "cols": A.roll(g, "wc%d" % n, columns, 2, 14, dice * 0.5, True),
         "size": A.roll(g, "wz%d" % n, size, 12, 44, dice, True),
         "gap": A.roll(g, "wg%d" % n, gap, 2, 30, dice, True),
         "speed": A.roll(g, "wv%d" % n, speed, 0.2, 6, dice),
         "drop": A.roll(g, "wd%d" % n, drop, 0, 40, dice, True),
         "fire": A.roll(g, "wb%d" % n, fire, 0, 0.02, dice),
         "dive": A.roll(g, "wk%d" % n, dive, 0, 0.02, dice),
         "points": A.roll(g, "wp%d" % n, points, 1, 200, dice, True),
         "top": A.pick_color(g, top_color, "away", "wt%d" % n, dice),
         "bottom": A.pick_color(g, bottom_color, "wall", "wb%d" % n, dice)}
    waves.append(w)
    return g


def shields(game, count, columns, rows, cell, hits, color, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["shields"] = {"count": A.roll(g, "hn", count, 0, 6, dice * 0.5, True),
                         "cols": A.roll(g, "hc", columns, 1, 10, dice * 0.5, True),
                         "rows": A.roll(g, "hr", rows, 1, 5, dice * 0.5, True),
                         "cell": A.roll(g, "hs", cell, 4, 16, dice, True),
                         "hits": A.roll(g, "hh", hits, 1, 5, dice * 0.5, True),
                         "color": A.pick_color(g, color, "goal", "hcl", dice)}
    return g


def rules(game, ships, waves_to_win, round_speed_up, rush, dice):
    K = _kits()
    g = K.use_kit(copy.deepcopy(game), KIT)
    g["k"]["rules"] = {"lives": A.roll(g, "rl", ships, 1, 9, dice * 0.3, True),
                       "levels": A.roll(g, "rw", waves_to_win, 0, 30, dice * 0.3, True),
                       "roundGain": A.roll(g, "rg", round_speed_up, 0, 1, dice),
                       "rush": A.roll(g, "rr", rush, 0, 4, dice)}
    return g


def fixups(game):
    K = _kits()
    g = copy.deepcopy(game)
    k = g["k"]
    k["arena"] = K.arena_or_default(g, 360, 220, "stars", 50)
    hw, hh = k["arena"]["hw"], k["arena"]["hh"]
    if "ship" not in k:
        k["ship"] = {"ctrl": "arrows", "shape": "ship", "size": 26, "speed": 6, "cool": 12, "shotSpeed": 11,
                     "maxShots": 2, "color": K.palette_role(g, "home")}
        g["notes"].append("no Shooter Ship node: an arrow-key ship")
    if not k.get("waves"):
        k["waves"] = [{"formation": "block", "shape": "crab", "rows": 4, "cols": 8, "size": 24, "gap": 12,
                       "speed": 1.0, "drop": 14, "fire": 0.002, "dive": 0.0, "points": 10,
                       "top": K.palette_role(g, "away"), "bottom": K.palette_role(g, "wall")}]
        g["notes"].append("no Enemy Wave node: one block of crabs")
    if "rules" not in k:
        k["rules"] = {"lives": 3, "levels": 0, "roundGain": 0.25, "rush": 1.5}
    if "shields" not in k:
        k["shields"] = {"count": 0, "cols": 6, "rows": 3, "cell": 8, "hits": 2, "color": K.palette_role(g, "goal")}
    for w in k["waves"]:
        # a formation must fit across the arena with room to march, and above the shields
        while w["cols"] > 2 and w["cols"] * (w["size"] + w["gap"]) > hw * 2 - 80:
            w["cols"] -= 1
        while w["rows"] > 1 and 50 + w["rows"] * (w["size"] * 0.9 + w["gap"]) > hh * 2 - 200:
            w["rows"] -= 1
        w["colors"] = K.ramp(w["top"], w["bottom"], w["rows"])
    return g


def parts_needed(g):
    return ["common/vec", "core"]


def help_line(g):
    K = _kits()
    s = g["k"]["ship"]
    fire = "SPACE FIRES" if s["ctrl"] != "wasd" else "SPACE OR F FIRES"
    return K.keys_words(s["ctrl"], fire)


def config(g):
    K = _kits()
    k = g["k"]
    s, r, sh = k["ship"], k["rules"], k["shields"]
    items = [('sCfg["title"]', K.hud_safe(g["title"])), ('sCfg["help"]', help_line(g))]
    items += K.arena_config(k["arena"])
    items += [('sCfg["ctrl"]', s["ctrl"]), ('sCfg["shipShape"]', s["shape"]), ('sCfg["shipSize"]', s["size"]),
              ('sCfg["shipSpeed"]', s["speed"]), ('sCfg["coolSteps"]', s["cool"]),
              ('sCfg["shotSpeed"]', s["shotSpeed"]), ('sCfg["maxShots"]', s["maxShots"]),
              ('sCfg["shipColor"]', s["color"]), ('sCfg["shotColor"]', K.shade(s["color"], 1.3)),
              ('sCfg["bombColor"]', K.palette_role(g, "away")), ('sCfg["bombSpeed"]', 4),
              ('sCfg["shields"]', sh["count"]), ('sCfg["shieldCols"]', sh["cols"]),
              ('sCfg["shieldRows"]', sh["rows"]), ('sCfg["cell"]', sh["cell"]),
              ('sCfg["shieldHits"]', sh["hits"]), ('sCfg["shieldColor"]', sh["color"]),
              ('sCfg["lives"]', r["lives"]), ('sCfg["levels"]', r["levels"]),
              ('sCfg["roundGain"]', r["roundGain"]), ('sCfg["rush"]', r["rush"]),
              ('sCfg["waveBonus"]', 100), ("sWaveN", len(k["waves"]))]
    for i, w in enumerate(k["waves"], 1):
        for key in ("formation", "shape", "rows", "cols", "size", "gap", "speed", "drop", "fire", "dive", "points"):
            items.append(('sWave[%d]["%s"]' % (i, key), w[key]))
        for r_, c in enumerate(w["colors"], 1):
            items.append(('sWave[%d]["color"][%d]' % (i, r_), c))
    return items, ["sCfg", "sWave"]


def rules_lines(g):
    k = g["k"]
    waves = "; ".join("%s of %s %dx%d" % (w["formation"], w["shape"], w["rows"], w["cols"]) for w in k["waves"])
    r = k["rules"]
    goal = ("beat %d waves" % r["levels"]) if r["levels"] > 0 else "as many waves as you can (they come round faster)"
    return ["Waves: %s. Shields: %d." % (waves, k["shields"]["count"]),
            "CONTROLS  %s   Escape: stop" % help_line(g).title(),
            "RULES     %s; %d ships. A bomb, a diver or the formation reaching you costs a ship." % (goal, r["lives"])]


def preview(g, d, P):
    k = g["k"]
    a, s, sh = k["arena"], k["ship"], k["shields"]
    hw, hh = a["hw"], a["hh"]
    d.rectangle([P(-hw, -hh), P(hw, hh)], outline=tuple(a["wall"]), width=2)
    w = k["waves"][0]
    sx, sy = w["size"] + w["gap"], w["size"] * 0.9 + w["gap"]
    mid = (w["cols"] + 1) / 2.0
    for r in range(1, w["rows"] + 1):
        for c in range(1, w["cols"] + 1):
            want = {"vee": abs(abs(c - mid) - (w["rows"] - r) * (w["cols"] - 1) / (2.0 * max(1, w["rows"] - 1))) < 1,
                    "diamond": abs(c - mid) / w["cols"] + abs(r - (w["rows"] + 1) / 2.0) / w["rows"] <= 0.5,
                    "ragged": (r * 7 + c * 3) % 5 != 0}.get(w["formation"], True)
            if not want:
                continue
            x, y, h = (c - mid) * sx, -hh + 50 + (r - 1) * sy, w["size"] / 2.0
            col = tuple(w["colors"][r - 1])
            _shape(d, P, w["shape"], x, y, h, col)
    shy = hh - 30
    for i in range(1, sh["count"] + 1):
        x0 = -hw + i * 2 * hw / (sh["count"] + 1.0)
        for r in range(sh["rows"]):
            for c in range(sh["cols"]):
                x = x0 + (c + 1 - (sh["cols"] + 1) / 2.0) * sh["cell"]
                y = shy - 70 + r * sh["cell"]
                e = sh["cell"] / 2.0
                d.rectangle([P(x - e, y - e), P(x + e, y + e)], outline=tuple(sh["color"]))
    _shape(d, P, s["shape"], 0, shy, s["size"] / 2.0, tuple(s["color"]))
    for i, w2 in enumerate(k["waves"][1:6]):
        _shape(d, P, w2["shape"], hw - 30 - i * 34, hh + 30, 12, tuple(w2["colors"][0]))


def _shape(d, P, shape, x, y, h, col):
    q = h / 2.0
    if shape in ("ship", "tri"):
        pts = [(0, -h), (h, h), (0, q), (-h, h)] if shape == "ship" else [(0, -h), (h, h), (-h, h)]
        d.polygon([P(x + a, y + b) for a, b in pts], outline=col)
    elif shape == "diamond":
        d.polygon([P(x, y - h), P(x + h, y), P(x, y + h), P(x - h, y)], outline=col)
    elif shape == "ring":
        d.ellipse([P(x - h, y - h), P(x + h, y + h)], outline=col)
    elif shape == "saucer":
        d.ellipse([P(x - h, y - q), P(x + h, y + q)], outline=col)
        d.arc([P(x - q, y - h), P(x + q, y)], 180, 360, fill=col)
    elif shape == "crab":
        d.rectangle([P(x - q * 1.4, y - q), P(x + q * 1.4, y + q)], outline=col)
        for sx in (-1, 1):
            d.line([P(x + sx * q * 1.4, y - q * 0.3), P(x + sx * h, y - h)], fill=col)
            d.line([P(x + sx * q, y + q), P(x + sx * h, y + h)], fill=col)
    elif shape == "bug":
        d.polygon([P(x, y - q), P(x + q, y), P(x, y + h), P(x - q, y)], outline=col)
        d.line([P(x, y - q), P(x - q, y - h)], fill=col)
        d.line([P(x, y - q), P(x + q, y - h)], fill=col)
    elif shape == "star":
        import math
        pts = [P(x + (h if i % 2 == 0 else h * .45) * math.cos(-math.pi / 2 + i * math.pi / 5),
                 y + (h if i % 2 == 0 else h * .45) * math.sin(-math.pi / 2 + i * math.pi / 5)) for i in range(10)]
        d.polygon(pts, outline=col)
    else:
        d.rectangle([P(x - h, y - h), P(x + h, y + h)], outline=col)
