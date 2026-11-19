"""remix: variants of two big hand-made games, Squad Buggy and Vector Toss.

The genre kits put a game together from parts. These two are too big to cut up, so Build Game
reads the original script (LIB_GAMES/Vibecode3D_Games, never changed) and writes a copy with its
knobs changed. Three kinds of knob, all in the tables below with their safe range and node:

  constant   one `constant kName = value` line: only the value is replaced, the comment stays
  patch      one exact line of the game that has a number written into it (Squad Buggy's enemy
             pacing): the line is replaced by the same sum times a factor (1 = the original)
  colour     Vector Toss: a constant "#RRGGBB"; Squad Buggy: a literal "r,g,b" written into the
             code, replaced everywhere it stands (one literal = one role, see SQUAD_COLORS)

A constant's default is read from the game's file at every build, so dice 0 is the game as the
owner last tuned it. A knob that is missing from the game stops the build with a plain message.

Nodes: Remix Source starts the chain (which game, seed, dice). The per-game nodes (Buggy, Terrain,
Enemies, Squad Palette; Arena, Toss Ball, Heroes, Toss Rules, Toss Palette) set their knobs from
sliders, rolled by the seed inside the safe range. Knobs no node has set are rolled around the
original. Mutate may push 1-3 knobs to the edge of their range and names them in the title.
When nodes add rules ("when a bomber goes down: sparks", "when a catch: crack a tile"): see the
events tables.
Fix-ups then keep every seed a game that can be played.
"""
import colorsys
import copy
import math
import os
import re

from .. import assemble as A

KIT = "remix"


def K(name, node, widget, lo, hi, whole, why, low=None, high=None):
    return {"name": name, "node": node, "widget": widget, "lo": lo, "hi": hi, "whole": whole, "why": why,
            "low": low, "high": high}


SQUAD_KNOBS = [
    K("kGrav", "buggy", "gravity", 0.08, 0.34, False, "gravity: jumps and bombs", "LOW GRAVITY", "HEAVY GRAVITY"),
    K("kJumpV", "buggy", "jump", 4.5, 9.0, False, "jump speed", None, "MOON JUMPS"),
    K("kShotV", "buggy", "shot_speed", 12, 36, False, "your shots' speed", "SLOW SHOTS", "FAST SHOTS"),
    K("kSeg", "terrain", "segment", 20, 30, True, "ground segment length (20 smooth, 30 angular)"),
    K("kCraterR", "terrain", "crater_width", 30, 90, True, "crater half width", None, "WIDE CRATERS"),
    K("kCraterD", "terrain", "crater_depth", 18, 60, True, "crater depth", None, "DEEP CRATERS"),
    K("kFlagGap", "terrain", "flag_gap", 1500, 3600, True, "distance between flags", "SHORT RUNS", "LONG RUNS"),
    K("kTowerGap", "terrain", "tower_gap", 700, 1800, True, "distance between buildings", "TOWER CITY", None),
    K("kHoldSteps", "enemies", "hold_steps", 300, 900, True, "steps to hold a flag (30 a second)", None, "LONG HOLDS"),
    K("kSnipeRange", "enemies", "sniper_range", 380, 800, True, "how near a roof must be for its snipers to fire",
      None, "LONG SNIPERS"),
    K("kRoundV", "enemies", "round_speed", 2.5, 7.0, False, "a sniper round's speed", None, "FAST ROUNDS"),
    K("xWalkerPace", "enemies", "walker_gap", 0.3, 1.5, False, "time between walkers, times this (under 1 = more)",
      "SWARM", None),
    K("xWalkerSpeed", "enemies", "walker_speed", 0.6, 2.2, False, "walkers' speed, times this", None, "RUNNERS"),
    K("xBomberPace", "enemies", "bomber_gap", 0.35, 1.5, False, "time between bombers, times this (under 1 = more)",
      "AIR RAID", None),
]
# patch knobs: the exact line of the original (without its indent) and what replaces it (%s = the factor)
SQUAD_PATCHES = {
    "xWalkerPace": ("put max(25, 90 - sLevel * 12) + random(40) into sNextEnemy",
                    "put round((max(25, 90 - sLevel * 12) + random(40)) * %s) into sNextEnemy"),
    "xWalkerSpeed": ("put 1.6 + pLevel * 0.3 into sESpeed",
                     "put (1.6 + pLevel * 0.3) * %s into sESpeed"),
    "xBomberPace": ("put max(110, 300 - sLevel * 35) + random(90) into sNextFly",
                    "put round((max(110, 300 - sLevel * 35) + random(90)) * %s) into sNextFly"),
}
# Squad Buggy's colours are literals in the code: literal -> role. Every place the literal stands
# (the thing, and its sparks) takes the role's new colour.
SQUAD_COLORS = [("cBuggy", "0,230,255"), ("cFlag", "0,255,100"), ("cGunner", "255,60,60"),
                ("cSquad", "255,150,0"), ("cGround", "120,200,90"), ("cEnemy", "200,80,255"),
                ("cBomber", "255,60,120"), ("cBomb", "255,200,0"), ("cTower", "90,150,190")]

TOSS_KNOBS = [
    K("kTile", "arena", "tile", 30, 60, True, "floor tile size", None, "BIG TILES"),
    K("kHalfW", "arena", "half_width", 280, 440, True, "arena half width", "TIGHT ARENA", "WIDE ARENA"),
    K("kHalfD", "arena", "half_depth", 120, 240, True, "arena half depth", "NARROW LANE", "DEEP ARENA"),
    K("kTop", "arena", "ceiling", 200, 420, True, "ceiling height", "LOW ROOF", "HIGH ROOF"),
    K("kBallR", "ball", "radius", 5, 14, True, "ball radius", "TINY BALL", "BIG BALL"),
    K("kGrav", "ball", "gravity", 0.08, 0.30, False, "the ball's gravity", "FLOATY BALL", "HEAVY BALL"),
    K("kBounce", "ball", "bounce", 0.35, 0.85, False, "floor bounce", "DEAD BALL", "SUPER BOUNCE"),
    K("kFloorDrag", "ball", "floor_drag", 0.70, 0.95, False, "run kept at each floor bounce"),
    K("kRollDrag", "ball", "roll_drag", 0.88, 0.985, False, "run kept each step while rolling", None, "ICE FLOOR"),
    K("kRunSpeed", "heroes", "run_speed", 3.5, 8.0, False, "run speed", "SLOW HEROES", "FAST HEROES"),
    K("kJumpV", "heroes", "jump", 3.6, 7.0, False, "jump speed", None, "HIGH JUMPS"),
    K("kHeroGrav", "heroes", "hero_gravity", 0.18, 0.5, False, "the heroes' gravity"),
    K("kReach", "heroes", "reach", 60, 110, True, "catch reach upward", None, "LONG ARMS"),
    K("kCatchR", "heroes", "catch_radius", 16, 36, True, "catch reach across the floor", "SMALL HANDS", "BIG HANDS"),
    K("kRoofPower", "heroes", "roof_power", 1.5, 5.5, False, "extra upward speed of a full-power throw",
      None, "POWER THROWS"),
    K("kAIWait", "heroes", "ai_wait", 15, 80, True, "steps the companion holds the ball", "QUICK COMPANION", None),
    K("kLevelCatches", "rules", "level_catches", 4, 16, True, "catches a level", "FAST LEVELS", None),
    K("kHangEvery", "rules", "hang_every", 5, 20, True, "points for a new hang"),
    K("kMaxFalls", "rules", "max_falls", 2, 6, True, "fatal falls that end the game", "SUDDEN DEATH", None),
    K("kFallCost", "rules", "fall_cost", 1, 6, True, "points a fall costs"),
]
TOSS_COLORS = [("kPromptColor", None), ("kGlazeColor", None), ("kBallColor", None)]

# ------------------------------------------------------------ events: "when this happens, do that"
# An event is a spot in the original: an exact line (there once) and where the call goes. The
# call only QUEUES the event (Remix.On); the actions run at the top of the next Game.OnUpdate
# (Remix.Flush), so an action never changes the game's lists while the game is looping over them.
# (event: (words, [(anchor line, "after" | "before", the two values handed over)]))
SQUAD_EVENTS = {
    "bomber down": [('Squad.Say "BOMBER DOWN! +100"', "after", 'sShot[tS]["x"], sShot[tS]["h"]')],
    "sniper down": [('Squad.Say "SNIPER DOWN! +75"', "after", 'sShot[tS]["x"], sShot[tS]["h"]')],
    "walker shot": [('FX.Sparks Squad.SX(sEnemy[tK]["x"]), kBase - Squad.H(sEnemy[tK]["x"]) - 18, kZ, 8, "200,80,255"',
                     "before", 'sEnemy[tK]["x"], Squad.H(sEnemy[tK]["x"]) + 18'),
                    ('FX.Sparks Squad.SX(sEnemy[tT]["x"]), kBase - Squad.H(sEnemy[tT]["x"]) - 18, kZ, 8, "200,80,255"',
                     "before", 'sEnemy[tT]["x"], Squad.H(sEnemy[tT]["x"]) + 18')],
    "walker squashed": [('Squad.Say "SQUASHED!"', "after", "sX, sY")],
    "man overboard": [('Squad.Say "MAN OVERBOARD! STOP BESIDE HIM"', "after", "sX, sY + 30")],
    "soldier lost": [('Squad.Say "A SOLDIER IS LOST"', "after", "tEX, Squad.H(tEX)")],
    "flag reached": [('Squad.Say "FLAG REACHED! HOLD IT FOR 20 SECONDS"', "after", "sX, sY + 60")],
    "flag held": [("put tFX into sLastFlagX", "after", "tFX, Squad.H(tFX) + 40")],
    "crater dug": [("put pX into sCrater[sCraterN]", "after", "pX, pH")],
    "jump": [("put true into sJumped", "after", "sX, sY")],
}
# action: the lines it runs (tA, tB = the event's two values; %(n)s amount, %(text)s, %(rgb)s), amount's range
SQUAD_ACTIONS = {
    "sparks": (['FX.Sparks Squad.SX(tA), kBase - tB, kZ, %(n)s, "%(rgb)s"'], 4, 40),
    "score": (["add %(n)s to sScore", "put empty into sHUDWas"], 1, 500),
    "say": (['Squad.Say "%(text)s"'], 1, 1),
    "extra life": (["if sLives < 9 then add 1 to sLives", "put empty into sHUDWas"], 1, 1),
    "bomber comes": (["if the number of lines of the keys of sFly < 4 then Squad.AddFlyer sX - 520, sV + 2 + 0.3 * sLevel"], 1, 1),
    "walkers faster": (["put min(6, sESpeed * (1 + %(n)s / 100)) into sESpeed"], 1, 50),
    "walker rush": (["put 1 into sNextEnemy"], 1, 1),
    "crater ahead": (["Squad.Blast sX + 260, Squad.H(sX + 260), true"], 1, 1),
    "bounce": (["if sOver is not true then", "   put true into sAir", "   put max(sVY, kJumpV) into sVY", "end if"], 1, 1),
}
TOSS_EVENTS = {
    "catch": [('add 1 to sHero[pName]["catches"]', "after", 'pName, empty')],
    "big catch": [('VT.Say "catch_big", pName, 90', "after", 'pName, empty')],
    "rally": [('VT.Say "rally", "*", 100', "after", '"*", empty')],
    "drop": [("on VT.Drop pName", "after", 'pName, empty')],
    "floor broke": [('VT.Message "THE FLOOR BROKE"', "after", '"*", empty')],
    "pit took the ball": [('VT.Message "THE PIT TOOK THE BALL"', "after", 'tOwner, empty')],
    "hero falls": [("on VT.StartFall pName", "after", 'pName, empty')],
    "new level": [('VT.Message "LEVEL " & pLevel', "after", '"*", empty')],
}
# tA = the hero it happened to (PROMPT or GLAZE), or "*" for both
TOSS_ACTIONS = {
    "sparks": (['FX.Sparks sBall["x"], -sBall["h"], sBall["z"], %(n)s, "%(rgb)s"'], 4, 40),
    "score": (['repeat for each item tH in "PROMPT,GLAZE"',
               '   if tA is "*" or tA is tH then add %(n)s to sHero[tH]["score"]', "end repeat"], 1, 20),
    "say": (['VT.Message "%(text)s"'], 1, 1),
    "extra hang": (['repeat for each item tH in "PROMPT,GLAZE"',
                    '   if (tA is "*" or tA is tH) and sHero[tH]["hangs"] < 5 then add 1 to sHero[tH]["hangs"]',
                    "end repeat"], 1, 1),
    "mend the floor": (["VT.MendFloor"], 1, 1),
    "crack a tile": (["VT.HitTile random(2 * kHalfW) - kHalfW, random(2 * kHalfD) - kHalfD"], 1, 1),
}
SAY = {"squad": "NICE!", "toss": "BONUS!"}
MAX_RULES = 8

GAMES = {
    "squad": {"label": "Squad Buggy", "file": "Vibecode3D_Play_SquadBuggy.livecodescript",
              "name": "ComfySquad", "prefix": "Squad", "knobs": SQUAD_KNOBS, "patches": SQUAD_PATCHES,
              "colors": SQUAD_COLORS, "derived": ("kSlices",),
              "events": SQUAD_EVENTS, "actions": SQUAD_ACTIONS, "spark": "cBomb"},
    "toss": {"label": "Vector Toss", "file": "Vibecode3D_Play_VectorToss.livecodescript",
             "name": "ComfyToss", "prefix": "VT", "knobs": TOSS_KNOBS, "patches": {},
             "colors": TOSS_COLORS, "derived": ("kCamUp", "kCamBack"),
             "events": TOSS_EVENTS, "actions": TOSS_ACTIONS, "spark": "kBallColor"},
}
LABELS = tuple(v["label"] for v in GAMES.values())
FREE_DICE = 0.5      # the dice of a knob no node has set
# the originals' numbers on 18 Nov 2026: slider defaults only when the game files can't be read
# when ComfyUI starts (a build always reads the file)
FALLBACK = {"squad": {"kGrav": 0.18, "kJumpV": 6.2, "kShotV": 22, "kSeg": 20, "kCraterR": 52, "kCraterD": 38,
                      "kFlagGap": 2400, "kTowerGap": 1100, "kHoldSteps": 600, "kSnipeRange": 620, "kRoundV": 4.2},
            "toss": {"kTile": 40, "kHalfW": 360, "kHalfD": 160, "kTop": 300, "kBallR": 8, "kGrav": 0.16,
                     "kBounce": 0.62, "kFloorDrag": 0.86, "kRollDrag": 0.95, "kRunSpeed": 5.2, "kJumpV": 4.6,
                     "kHeroGrav": 0.3, "kReach": 78, "kCatchR": 22, "kRoofPower": 3.2, "kAIWait": 40,
                     "kLevelCatches": 10, "kHangEvery": 10, "kMaxFalls": 3, "kFallCost": 3}}
_CONST = r'^(constant[ \t]+%s[ \t]*=[ \t]*)("[^"\n]*"|[^ \t\n]+)(.*)$'


def which_game(label):
    for key, v in GAMES.items():
        if label in (key, v["label"]):
            return key
    return "squad"


def knob(key, name):
    return next(k for k in GAMES[key]["knobs"] if k["name"] == name)


# ------------------------------------------------------------ reading and writing the game
def source_path(projects_root, key):
    return os.path.join(projects_root, "LIB_GAMES", "Vibecode3D_Games", GAMES[key]["file"])


def read_constants(text):
    """every `constant kX = value` line of a script: {name: number, or the string without quotes}"""
    out = {}
    for m in re.finditer(r'^constant[ \t]+(k\w+)[ \t]*=[ \t]*("[^"\n]*"|[^ \t\n]+)', text, re.M):
        raw = m.group(2)
        if raw.startswith('"'):
            out[m.group(1)] = raw[1:-1]
        else:
            try:
                out[m.group(1)] = float(raw) if re.search(r"[.eE]", raw) else int(raw)
            except ValueError:
                out[m.group(1)] = raw
    return out


def read_defaults(key, text):
    """the original's value of every knob and colour: constants from the text, patches 1, colours as #hex"""
    info = GAMES[key]
    d = read_constants(text)
    for name in info["patches"]:
        d[name] = 1.0
    for name, literal in info["colors"]:
        if literal is not None:
            d[name] = "#%02X%02X%02X" % tuple(int(x) for x in literal.split(","))
    return d


def slider_defaults(projects_root, key):
    """for the nodes' sliders when ComfyUI starts: from the game's file, else the table above"""
    d = dict(FALLBACK[key])
    try:
        with open(source_path(projects_root, key), encoding="utf-8") as f:
            d.update({n: v for n, v in read_constants(f.read()).items() if n in d and not isinstance(v, str)})
    except OSError:
        pass
    for name in GAMES[key]["patches"]:
        d[name] = 1.0
    return d


def fmt(v):
    if isinstance(v, str):
        return '"%s"' % v
    if isinstance(v, float):
        return repr(round(v, 3))
    return str(v)


def set_constant(text, name, v):
    text, n = re.subn(_CONST % re.escape(name), lambda m: m.group(1) + fmt(v) + m.group(3), text, flags=re.M)
    if n != 1:
        raise ValueError("remix: the game has %d lines 'constant %s = ...' (1 expected): has the original changed?"
                         % (n, name))
    return text


def set_patch(text, name, old, new, v):
    if text.count(old) != 1:
        raise ValueError("remix: the line for %s is there %d times (1 expected): has the original changed?\n   %s"
                         % (name, text.count(old), old))
    return text.replace(old, new % fmt(float(v)))


def set_literal(text, name, literal, hexcol):
    old = '"%s"' % literal
    if old not in text:
        raise ValueError("remix: the colour %s (%s) is not in the game any more" % (name, old))
    return text.replace(old, '"%d,%d,%d"' % A.hex_rgb(hexcol))


# ------------------------------------------------------------ rolls
def roll_in(g, salt, value, lo, hi, dice, whole):
    """value moved by the seed INSIDE its safe range: dice 1 can reach either end, never past it"""
    d = max(0.0, min(1.0, dice * g["dice"]))
    u = A._rng(g, salt).uniform(-1, 1)
    value = max(lo, min(hi, value))
    value += u * d * ((hi - value) if u > 0 else (value - lo))
    return int(round(value)) if whole else round(value, 3)


def shift_color(hexcol, turn):
    """a colour with its hue turned (turn 1 = all the way round); white becomes a pale tint"""
    rgb = A.hex_rgb(hexcol)
    if rgb is None or abs(turn) < 0.002:
        return hexcol
    h, s, v = colorsys.rgb_to_hsv(*(x / 255.0 for x in rgb))
    if s < 0.1:
        s = min(0.35, abs(turn) * 2)
    r, gg, b = colorsys.hsv_to_rgb((h + turn) % 1.0, s, max(v, 0.75))
    return "#%02X%02X%02X" % (int(r * 255), int(gg * 255), int(b * 255))


# ------------------------------------------------------------ the nodes
def source(label, seed, dice, title, name):
    key = which_game(label)
    info = GAMES[key]
    if not title or title == "auto":
        title = info["label"] + " Remix"
    if not name or name == "auto":
        name = info["name"]
    g = A.new_game(title, name, seed, dice)
    g["kit"] = KIT
    g["k"] = {"remix": {"game": key, "set": {}, "colors": {}, "mutate": None}}
    return g


def _mine(game, key, what):
    """a copy of the game for a node of remix `key`, or None (with a note) when the chain is another game"""
    g = copy.deepcopy(game)
    r = g.get("k", {}).get("remix") if g.get("kit") == KIT else None
    if r is None:
        g["notes"].append("%s needs a Remix Source before it: left out" % what)
        return g, None
    if r["game"] != key:
        g["notes"].append("%s is a %s node, this is %s: left out" % (what, GAMES[key]["label"], GAMES[r["game"]]["label"]))
        return g, None
    return g, r


def set_knobs(game, key, node, dice, **widgets):
    g, r = _mine(game, key, node.title() + " node")
    if r is None:
        return g
    for k in GAMES[key]["knobs"]:
        if k["node"] == node and k["widget"] in widgets:
            r["set"][k["name"]] = roll_in(g, k["name"], widgets[k["widget"]], k["lo"], k["hi"], dice, k["whole"])
    return g


def set_palette(game, key, hue_shift, spread, dice, **given):
    """hue_shift turns every colour together (degrees); spread lets each wander on its own;
    given: {colour name: 'auto' or #rrggbb}"""
    g, r = _mine(game, key, "Palette node")
    if r is None:
        return g
    d = max(0.0, min(1.0, dice * g["dice"]))
    turn = hue_shift / 360.0 + A._rng(g, "pal").uniform(-0.5, 0.5) * d
    for name, _ in GAMES[key]["colors"]:
        own = A._rng(g, name).uniform(-0.5, 0.5) * spread
        r["colors"][name] = {"given": given.get(name, "auto"), "turn": turn + own}
    return g


def mutate(game, chance, most):
    g = copy.deepcopy(game)
    if g.get("kit") != KIT:
        g["notes"].append("Mutate needs a Remix Source before it: left out")
        return g
    g["k"]["remix"]["mutate"] = {"chance": float(chance), "most": int(most)}
    return g


def when(game, key, event, action, amount, text, color, chance, appear):
    """one rule: when `event` happens (each time, by `chance`), do `action`. 'random' = the seed picks."""
    g, r = _mine(game, key, "When node")
    if r is None:
        return g
    info = GAMES[key]
    event = A.roll_choice(g, "we", event, sorted(info["events"]), 0)
    action = A.roll_choice(g, "wa", action, sorted(info["actions"]), 0)
    if not A.roll_chance(g, "wp", appear):
        return g
    rules = r.setdefault("events", [])
    if len(rules) >= MAX_RULES:
        g["notes"].append("more than %d When nodes: the rest are left out" % MAX_RULES)
        return g
    lo, hi = info["actions"][action][1:]
    rules.append({"event": event, "action": action, "n": max(lo, min(hi, int(amount))),
                  "text": text if text and text != "auto" else SAY[key],
                  "color": color if A.hex_rgb(color or "") else None,
                  "chance": max(0.01, min(1.0, float(chance)))})
    return g


def rule_words(e):
    w = "when %s: %s" % (e["event"], e["action"])
    if e["action"] in ("sparks", "score", "walkers faster"):
        w += " %d" % e["n"]
    if e["action"] == "say":
        w += " '%s'" % e["text"]
    if e["chance"] < 1:
        w += " (%d%% of the time)" % round(e["chance"] * 100)
    return w


def add_event_calls(text, info, rules):
    """the Remix.On calls at each used event's spot, and Remix.Flush at the top of Game.OnUpdate"""
    lines = text.split("\n")

    def spot(anchor):
        hits = [i for i, l in enumerate(lines) if l.strip() == anchor]
        if len(hits) != 1:
            raise ValueError("remix: the event line is there %d times (1 expected): has the original changed?\n   %s"
                             % (len(hits), anchor))
        return hits[0]
    for ev in sorted(set(e["event"] for e in rules)):
        for anchor, where, args in info["events"][ev]:
            i = spot(anchor)
            pad = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
            if where == "after" and anchor.startswith("on "):
                pad += "   "
            lines.insert(i + (1 if where == "after" else 0), '%sRemix.On "%s", %s' % (pad, ev, args))
    lines.insert(spot("on Game.OnUpdate") + 1, "   Remix.Flush")
    return "\n".join(lines)


def event_handlers(g, info, rules):
    from .. import kits
    v = g["k"]["vals"]
    L = ["", "## REMIX events (generated by the Build node): what the When nodes asked for.",
         "## Remix.On only notes an event; Remix.Flush acts on them at the top of the next step.",
         "local sRemixQ, sRemixBusy", "",
         "on Remix.On pEvent, pA, pB",
         "   if sRemixBusy is true then exit Remix.On",
         "   put pEvent & tab & pA & tab & pB & return after sRemixQ",
         "end Remix.On", "",
         "on Remix.Flush",
         "   local tQ, tLine, tA, tB, tH",
         "   if sRemixQ is empty then exit Remix.Flush",
         "   put sRemixQ into tQ",
         "   put empty into sRemixQ",
         "   put true into sRemixBusy",
         "   set the itemDelimiter to tab",
         "   repeat for each line tLine in tQ",
         "      put item 2 of tLine into tA",
         "      put item 3 of tLine into tB",
         "      put item 1 of tLine into tH",
         "      set the itemDelimiter to comma",
         "      switch tH"]
    for ev in sorted(set(e["event"] for e in rules)):
        L.append('         case "%s"' % ev)
        for e in rules:
            if e["event"] != ev:
                continue
            vals = {"n": e["n"], "text": kits.hud_safe(e["text"])[:40],
                    "rgb": "%d,%d,%d" % A.hex_rgb(e["color"] or v[info["spark"]])}
            L.append("            if random(100) <= %d then" % round(e["chance"] * 100))
            L += ["               " + a % vals for a in info["actions"][e["action"]][0]]
            L.append("            end if")
        L.append("            break")
    L += ["      end switch", "      set the itemDelimiter to tab", "   end repeat",
          "   set the itemDelimiter to comma", "   put false into sRemixBusy", "end Remix.Flush", ""]
    return "\n".join(L)


# ------------------------------------------------------------ fix-ups
def fixups(game, defaults):
    """a copy with g["k"]["vals"] (every knob's value for this seed) and g["k"]["defaults"]"""
    g = copy.deepcopy(game)
    r = g["k"]["remix"]
    key = r["game"]
    info = GAMES[key]
    vals = {}
    for k in info["knobs"]:
        n = k["name"]
        if n not in defaults:
            raise ValueError("remix: %s has no 'constant %s' any more" % (info["label"], n))
        vals[n] = r["set"][n] if n in r["set"] else roll_in(g, n, defaults[n], k["lo"], k["hi"], FREE_DICE, k["whole"])
    free_turn = A._rng(g, "pal").uniform(-0.5, 0.5) * FREE_DICE * g["dice"]
    for n, _ in info["colors"]:
        if n not in defaults:
            raise ValueError("remix: %s has no 'constant %s' any more" % (info["label"], n))
        c = r["colors"].get(n)
        if c is None:
            c = {"given": "auto", "turn": free_turn + A._rng(g, n).uniform(-0.08, 0.08) * FREE_DICE * g["dice"]}
        base = c["given"] if A.hex_rgb(c["given"] or "") else defaults[n]
        if not base.startswith("#"):
            base = "#" + base
        vals[n] = shift_color(base.upper(), c["turn"])
    # Mutate: some knobs to the edge of their safe range, named in the title
    m = r.get("mutate")
    if m:
        rnd = A._rng(g, "mutate")
        if rnd.random() < m["chance"]:
            can = [k for k in info["knobs"] if k["low"] or k["high"]]
            words = []
            for k in rnd.sample(can, min(len(can), rnd.randint(1, max(1, m["most"])))):
                side = rnd.choice([s for s in ("low", "high") if k[s]])
                vals[k["name"]] = k["lo"] if side == "low" else k["hi"]
                words.append(k[side])
            g["title"] = "%s: %s" % (info["label"], ", ".join(words))
            g["mutated"] = words
    (fix_squad if key == "squad" else fix_toss)(g, vals, defaults)
    g["k"]["vals"] = vals
    g["k"]["defaults"] = {n: defaults.get(n) for n in vals}
    return g


def fix_squad(g, v, d):
    # the jump must clear the deepest crater (craters stack to 70 deep), and stay on the screen
    peak = v["kJumpV"] ** 2 / (2 * v["kGrav"])
    want = max(85.0, min(300.0, peak))
    if abs(want - peak) > 0.5:
        v["kJumpV"] = round(math.sqrt(2 * v["kGrav"] * want), 3)
        g["notes"].append("jump speed set to %.2f: a jump %d high (was %d)" % (v["kJumpV"], want, peak))
    # and stay in the air long enough to cross it at the slowest drive (about 3 a step)
    air = 2 * v["kJumpV"] / v["kGrav"]
    if air * 3 < v["kCraterR"] * 1.3:
        v["kCraterR"] = int(air * 3 / 1.3)
        g["notes"].append("craters narrowed to %d: a jump can cross one" % v["kCraterR"])
    # a round must not outrun a shot by much, or snipers can't be answered
    if v["kRoundV"] > v["kShotV"] * 0.4:
        v["kRoundV"] = round(v["kShotV"] * 0.4, 3)
        g["notes"].append("sniper rounds slowed to %.1f: your shots can catch them" % v["kRoundV"])
    # towers never closer together than a sniper sees, or the buggy is under fire without a break
    if v["kTowerGap"] < v["kSnipeRange"] + 200:
        v["kSnipeRange"] = v["kTowerGap"] - 200
        g["notes"].append("sniper range cut to %d: a gap between towers" % v["kSnipeRange"])
    # the ground strip still has to cover the screen
    v["kSlices"] = max(d["kSlices"], int(math.ceil(d["kSlices"] * d["kSeg"] / float(v["kSeg"]))))


def fix_toss(g, v, d):
    t = v["kTile"] = int(round(v["kTile"] / 10.0)) * 10
    for k in ("kHalfW", "kHalfD"):          # the floor is whole tiles
        v[k] = max(t * 2, int(round(v[k] / float(t))) * t)
    if v["kHalfW"] < 240:                   # the level walls stand up to 120 from the centre
        v["kHalfW"] = int(math.ceil(240.0 / t)) * t
    # a jump must clear the level walls (32 high)
    peak = v["kJumpV"] ** 2 / (2 * v["kHeroGrav"])
    if peak < 34:
        v["kJumpV"] = round(math.sqrt(2 * v["kHeroGrav"] * 35), 3)
        g["notes"].append("jump speed raised to %.2f so a hero clears the walls" % v["kJumpV"])
    if v["kReach"] > v["kTop"] - 70:
        v["kReach"] = v["kTop"] - 70
        g["notes"].append("reach lowered to %d: under the ceiling" % v["kReach"])
    # a hero must be able to get under a roof throw: its time up and down against the run across half a court
    air = 2 * math.sqrt(2 * (v["kTop"] - 52) / v["kGrav"])
    need = (v["kHalfW"] * 0.45 + v["kHalfD"] * 0.5) / (air * 0.8)
    if v["kRunSpeed"] < need:
        v["kRunSpeed"] = round(min(8.0, need), 3)
        g["notes"].append("run speed raised to %.1f: the arena is big for this ball" % v["kRunSpeed"])
    # a ball that can be caught: hands wider than the ball
    if v["kCatchR"] < v["kBallR"] + 10:
        v["kCatchR"] = v["kBallR"] + 10
        g["notes"].append("catch radius raised to %d for the big ball" % v["kCatchR"])
    # the camera backs off as the arena grows, so the whole box stays in view
    s = max(v["kHalfW"] / float(d["kHalfW"]), v["kTop"] / float(d["kTop"]))
    v["kCamUp"] = int(round(d["kCamUp"] * s))
    v["kCamBack"] = max(100, int(round((d["kHalfD"] + d["kCamBack"]) * s - v["kHalfD"])))


# ------------------------------------------------------------ build
def changed(g):
    v, d = g["k"]["vals"], g["k"]["defaults"]
    return [(n, d.get(n), v[n]) for n in v if v[n] != d.get(n)]


def header_lines(g, info):
    L = ["## REMIX     made in ComfyUI from %s (LIB_GAMES, unchanged), seed %s. Changed (was -> now):"
         % (info["label"], g["seed"])]
    row = "##          "
    for n, was, now in changed(g):
        bit = " %s %s -> %s;" % (n, fmt(was) if was is not None else "?", fmt(now))
        if len(row) + len(bit) > 96:
            L.append(row.rstrip())
            row = "##          "
        row += bit
    if row.strip("# "):
        L.append(row.rstrip(";"))
    for e in g["k"]["remix"].get("events") or []:
        L.append("##           " + rule_words(e))
    L.append("##           (the CONTROLS and RULES words above are the original's: its numbers may differ here)")
    for note in g["notes"]:
        L.append("##           note: " + note)
    return L


def build(game, projects_root, out_dir, name):
    from .. import kits
    key = game["k"]["remix"]["game"]
    info = GAMES[key]
    with open(source_path(projects_root, key), encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    defaults = read_defaults(key, text)
    g = fixups(game, defaults)
    for n in info["derived"]:
        g["k"]["defaults"][n] = defaults.get(n)
    rules = g["k"]["remix"].get("events") or []
    if rules:                               # first: the spots are found by the original's own lines
        text = add_event_calls(text, info, rules)
    literal = dict(info["colors"])
    for n, v in g["k"]["vals"].items():
        if n in info["patches"]:
            if v != 1.0:
                text = set_patch(text, n, info["patches"][n][0], info["patches"][n][1], v)
        elif literal.get(n):
            if v != defaults[n]:
                text = set_literal(text, n, literal[n], v)
        else:
            text = set_constant(text, n, v)
    lines = text.split("\n")
    if "CARD SCRIPT" not in lines[1]:
        raise ValueError("remix: line 2 of %s is not its CARD SCRIPT line" % info["file"])
    lines[1] = '## CARD SCRIPT: "Play.%s"   %s  (remixed in ComfyUI from %s, seed %s)' \
               % (name, kits.hud_safe(g["title"]), info["label"], g["seed"])
    end = next(i for i in range(2, len(lines)) if lines[i].startswith("#####"))
    lines[end:end] = header_lines(g, info)
    script = "\n".join(lines)
    if rules:
        script = script.rstrip("\n") + "\n" + event_handlers(g, info, rules)
    if out_dir is None:
        out_dir = os.path.join(projects_root, "LIB_COMFY", "games")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Vibecode3D_Play_%s.livecodescript" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    g["parts"] = [info["file"]]
    g["file_name"] = name
    return path, script, g


# ------------------------------------------------------------ previews: a still of each game
def preview_image(g, im, d):
    key = g["k"]["remix"]["game"]
    v = g["k"]["vals"]
    col = lambda n: A.hex_rgb(v[n])  # noqa: E731
    W, H = im.size
    head = col("cBuggy") if key == "squad" else col("kPromptColor")
    d.text((20, 12), "%s   seed %s   %s" % (g["title"].upper(), g["seed"], g.get("file_name", "")), fill=head)
    d.text((20, 30), "remix of %s: %d numbers changed" % (GAMES[key]["label"], len(changed(g))), fill=(120, 130, 140))
    (still_squad if key == "squad" else still_toss)(g, d, v, col, W, H)
    rules = g["k"]["remix"].get("events") or []
    for i, e in enumerate(rules[:4]):
        d.text((470, 12 + 15 * i), rule_words(e), fill=(120, 255, 160))
    for i, note in enumerate(g["notes"][:3]):
        d.text((20, H - 18 - 15 * i), note, fill=(255, 200, 80))
    return im


def still_squad(g, d, v, col, W, H):
    """top: the buggy, its jump, a crater, a walker, a bomber and a tower at 1 unit a pixel;
    bottom: the course of one level (3 flags) with its towers"""
    def hill(x):
        return 70 + 45 * math.sin(x / 420.0) + 22 * math.sin(x / 170.0 + 1) + 10 * math.sin(x / 61.0)
    cx, R, D = 430.0, v["kCraterR"], v["kCraterD"]

    def ground(x):
        t = abs(x - cx)
        return hill(x) - (D * (1 - (t / R) ** 2) if t < R else 0)
    x0, y0, seg = 20, 330, v["kSeg"]
    P = lambda x, h: (x0 + x, y0 - h)  # noqa: E731
    pts = [P(x, ground(x)) for x in range(0, 861, seg)]
    d.line(pts, fill=col("cGround"), width=2)
    for x, _ in ((p[0] - x0, 0) for p in pts):
        d.line([P(x, ground(x)), P(x + 2, ground(x) - 9)], fill=tuple(c // 2 for c in col("cGround")))
    bx = 150
    bh = ground(bx)
    d.rectangle([P(bx - 32, bh + 34), P(bx + 34, bh + 14)], outline=col("cBuggy"), width=2)
    for wx in (bx - 28, bx + 30):
        d.ellipse([P(wx - 9, ground(wx) + 18), P(wx + 9, ground(wx))], outline=col("cBuggy"))
    for i in range(3):
        mx = bx - 30 + i * 16
        d.line([P(mx, bh + 34), P(mx, bh + 52)], fill=col("cSquad"), width=2)
    d.line([P(bx + 26, bh + 34), P(bx + 26, bh + 56), P(bx + 48, bh + 66)], fill=col("cGunner"), width=2)
    t, peak = 0, 0
    while True:                          # the jump, a dot every 3 steps at a drive of 4 a step
        h = bh + v["kJumpV"] * t - v["kGrav"] * t * t / 2.0
        x = bx + 4 * t
        if t > 0 and (h <= ground(x) or x > 860):
            break
        peak = max(peak, h - bh)
        d.ellipse([P(x - 1, h + 1), P(x + 1, h - 1)], fill=(255, 255, 255))
        t += 3
    d.text((x0 + bx - 30, y0 - bh - peak - 18), "jump %d high, %d steps" % (peak, t), fill=(200, 200, 200))
    d.text((x0 + cx - 40, y0 - ground(cx) + 8), "crater %dx%d" % (R * 2, D), fill=(200, 200, 200))
    ex = 640
    d.line([P(ex, ground(ex)), P(ex, ground(ex) + 22)], fill=col("cEnemy"), width=3)
    d.line([P(ex - 7, ground(ex) + 14), P(ex + 7, ground(ex) + 14)], fill=col("cEnemy"), width=2)
    d.polygon([P(540, 250), P(590, 258), P(540, 266)], outline=col("cBomber"))
    d.ellipse([P(556, 214), P(566, 204)], outline=col("cBomb"), width=2)
    tx = 790
    d.rectangle([P(tx - 30, ground(tx) + 100), P(tx + 30, ground(tx))], outline=col("cTower"), width=2)
    d.line([P(tx - 8, ground(tx) + 100), P(tx - 8, ground(tx) + 116)], fill=col("cEnemy"), width=3)
    # the course of one level
    y = 480
    gap, tg = v["kFlagGap"], v["kTowerGap"]
    span = gap * 3.15
    X = lambda wx: 20 + wx / span * 860  # noqa: E731
    d.line([(20, y), (880, y)], fill=tuple(c // 2 for c in col("cGround")), width=2)
    n = 0
    while n * tg + 440 < span:
        wx = n * tg + 700 + round(260 * math.sin(n * 12.9898))
        if abs(wx - round(wx / float(gap)) * gap) >= 260 and wx < span:
            d.rectangle([X(wx) - 3, y - 22, X(wx) + 3, y], outline=col("cTower"))
            d.line([X(wx - v["kSnipeRange"]), y + 6, X(wx), y + 6], fill=col("cEnemy"))
        n += 1
    for i in (1, 2, 3):
        d.line([X(gap * i), y, X(gap * i), y - 34], fill=col("cFlag"), width=2)
        d.polygon([(X(gap * i), y - 34), (X(gap * i) + 14, y - 28), (X(gap * i), y - 22)], fill=col("cFlag"))
    d.text((20, y + 14), "one level: 3 flags %d apart, hold each %d s; towers about %d apart, sniper range %d (the bars)"
           % (gap, round(v["kHoldSteps"] / 30.0), tg, v["kSnipeRange"]), fill=(200, 200, 200))
    d.text((20, y + 30), "walkers every x%.2f at speed x%.2f, bombers every x%.2f, rounds %.1f, your shots %.1f"
           % (v["xWalkerPace"], v["xWalkerSpeed"], v["xBomberPace"], v["kRoundV"], v["kShotV"]), fill=(200, 200, 200))


def still_toss(g, d, v, col, W, H):
    """left top: the arena from above (tiles, the heroes' catch circles, the ball);
    left bottom: from the side (ceiling, reach, a half-power roof throw); right: what changed"""
    s = 0.6
    hw, hd, top, t = v["kHalfW"], v["kHalfD"], v["kTop"], v["kTile"]
    cx, cy = 300, 60 + 250 * s
    dim = (50, 60, 70)
    T = lambda x, z: (cx + x * s, cy - z * s)  # noqa: E731
    x = -hw
    while x <= hw:
        d.line([T(x, -hd), T(x, hd)], fill=dim)
        x += t
    z = -hd
    while z <= hd:
        d.line([T(-hw, z), T(hw, z)], fill=dim)
        z += t
    d.rectangle([T(-hw, hd), T(hw, -hd)], outline=(200, 200, 200), width=2)
    d.line([T(0, -hd), T(0, hd)], fill=(200, 200, 200))
    for side, cname in ((-1, "kPromptColor"), (1, "kGlazeColor")):
        hx = side * hw * 0.55
        r = v["kCatchR"]
        d.ellipse([T(hx - r, r), T(hx + r, -r)], outline=col(cname), width=2)
        d.ellipse([T(hx - 5, 5), T(hx + 5, -5)], fill=col(cname))
    br = v["kBallR"]
    d.ellipse([T(-hw * 0.55 + 16 - br, br), T(-hw * 0.55 + 16 + br, -br)], outline=col("kBallColor"), width=2)
    d.text((cx - hw * s, cy + hd * s + 4), "from above: %d x %d, tiles %d" % (hw * 2, hd * 2, t), fill=(200, 200, 200))
    fy = H - 60
    S = lambda x, h: (cx + x * s, fy - h * s)  # noqa: E731
    d.rectangle([S(-hw, top), S(hw, 0)], outline=(200, 200, 200), width=2)
    d.line([S(0, 0), S(0, 14)], fill=(200, 200, 200))
    for side, cname in ((-1, "kPromptColor"), (1, "kGlazeColor")):
        hx = side * hw * 0.55
        d.line([S(hx, 0), S(hx, 52)], fill=col(cname), width=3)
        d.line([S(hx - 10, v["kReach"]), S(hx + 10, v["kReach"])], fill=col(cname))
        jump = v["kJumpV"] ** 2 / (2 * v["kHeroGrav"])
        d.line([S(hx - 4, v["kReach"] + jump), S(hx + 4, v["kReach"] + jump)], fill=tuple(c // 2 for c in col(cname)))
    # a half-power roof throw, stepped as the game steps it
    vh = math.sqrt(2 * v["kGrav"] * (top - br - 44)) + 0.5 + 0.5 * v["kRoofPower"]
    hs, h, w = [44.0], 44.0, vh
    for _ in range(600):
        w -= v["kGrav"]
        h += w
        if h > top - br:
            h, w = 2 * (top - br) - h, -abs(w)
        if h <= br:
            break
        hs.append(h)
    n = len(hs)
    d.line([S(-hw * 0.55 + 1.1 * hw * i / max(1, n - 1), hh) for i, hh in enumerate(hs)], fill=col("kBallColor"))
    d.text((cx - hw * s, fy + 4), "from the side: ceiling %d, a roof throw takes %d steps" % (top, n), fill=(200, 200, 200))
    y = 60
    d.text((600, y), "changed (was -> now)", fill=(200, 200, 200))
    for nme, was, now in changed(g)[:28]:
        y += 16
        c = A.hex_rgb(now) if isinstance(now, str) else (255, 220, 90)
        d.text((600, y), "%s  %s -> %s" % (nme[1:], fmt(was).strip('"'), fmt(now).strip('"')), fill=c or (255, 220, 90))
