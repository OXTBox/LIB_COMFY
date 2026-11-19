"""remix: variants of two big hand-made games, Squad Buggy and Vector Toss.

The genre kits put a game together from parts. These two are too big to cut up, so Build Game
reads the original script (LIB_GAMES/Vibecode3D_Games, never changed) and writes a copy with its
knobs changed. A knob is one `constant kName = value` line of the game; only its value is
replaced, the comment stays. The tables below say which constants are knobs, their safe range
and which node they belong to; a knob's default is read from the game's file at every build.

Node: Remix Source starts the chain (which game, seed, dice). Knobs no node has set are rolled
by the seed inside their safe range; fix-ups then keep every seed a game that can be played.
"""
import colorsys
import copy
import math
import os
import re

from .. import assemble as A

KIT = "remix"

# (constant, node, safe min, safe max, whole number, why / what it does)
SQUAD_KNOBS = [
    ("kGrav", "buggy", 0.08, 0.34, False, "gravity: jumps and bombs"),
    ("kJumpV", "buggy", 4.5, 9.0, False, "jump speed"),
    ("kShotV", "buggy", 12, 36, False, "your shots' speed"),
    ("kSeg", "terrain", 20, 30, True, "ground segment length (20 = smooth, 30 = angular)"),
    ("kCraterR", "terrain", 30, 90, True, "crater half width"),
    ("kCraterD", "terrain", 18, 60, True, "crater depth"),
    ("kFlagGap", "terrain", 1500, 3600, True, "distance between flags"),
    ("kTowerGap", "terrain", 700, 1800, True, "distance between buildings"),
    ("kHoldSteps", "enemies", 300, 900, True, "steps to hold a flag (30 a second)"),
    ("kSnipeRange", "enemies", 380, 800, True, "how near a roof must be for its snipers to fire"),
    ("kRoundV", "enemies", 2.5, 7.0, False, "a sniper round's speed"),
]
TOSS_KNOBS = [
    ("kTile", "arena", 30, 60, True, "floor tile size"),
    ("kHalfW", "arena", 280, 440, True, "arena half width"),
    ("kHalfD", "arena", 120, 240, True, "arena half depth"),
    ("kTop", "arena", 200, 420, True, "ceiling height"),
    ("kBallR", "ball", 5, 14, True, "ball radius"),
    ("kGrav", "ball", 0.08, 0.30, False, "the ball's gravity"),
    ("kBounce", "ball", 0.35, 0.85, False, "floor bounce"),
    ("kFloorDrag", "ball", 0.70, 0.95, False, "run kept at each floor bounce"),
    ("kRollDrag", "ball", 0.88, 0.985, False, "run kept each step while rolling"),
    ("kRunSpeed", "heroes", 3.5, 8.0, False, "run speed"),
    ("kJumpV", "heroes", 3.6, 7.0, False, "jump speed"),
    ("kHeroGrav", "heroes", 0.18, 0.5, False, "the heroes' gravity"),
    ("kReach", "heroes", 60, 110, True, "catch reach upward"),
    ("kCatchR", "heroes", 16, 36, True, "catch reach across the floor"),
    ("kRoofPower", "heroes", 1.5, 5.5, False, "extra upward speed of a full-power throw"),
    ("kAIWait", "heroes", 15, 80, True, "steps the companion holds the ball"),
    ("kLevelCatches", "rules", 4, 16, True, "catches a level"),
    ("kHangEvery", "rules", 5, 20, True, "points for a new hang"),
    ("kMaxFalls", "rules", 2, 6, True, "fatal falls that end the game"),
    ("kFallCost", "rules", 1, 6, True, "points a fall costs"),
    ("kPromptColor", "palette", None, None, "color", "PROMPT's colour"),
    ("kGlazeColor", "palette", None, None, "color", "GLAZE's colour"),
    ("kBallColor", "palette", None, None, "color", "the ball's colour"),
]
# constants the fix-ups may set, never rolled
SQUAD_DERIVED = ("kSlices",)
TOSS_DERIVED = ("kCamUp", "kCamBack")

GAMES = {
    "squad": {"label": "Squad Buggy", "file": "Vibecode3D_Play_SquadBuggy.livecodescript", "card": "SquadBuggy",
              "name": "ComfySquad", "prefix": "Squad", "knobs": SQUAD_KNOBS, "derived": SQUAD_DERIVED},
    "toss": {"label": "Vector Toss", "file": "Vibecode3D_Play_VectorToss.livecodescript", "card": "VectorToss",
             "name": "ComfyToss", "prefix": "VT", "knobs": TOSS_KNOBS, "derived": TOSS_DERIVED},
}
LABELS = tuple(v["label"] for v in GAMES.values())
FREE_DICE = 0.5      # the dice of a knob no node has set
_CONST = r'^(constant[ \t]+%s[ \t]*=[ \t]*)("[^"\n]*"|[^ \t\n]+)(.*)$'


def which_game(label):
    for key, v in GAMES.items():
        if label in (key, v["label"]):
            return key
    return "squad"


# ------------------------------------------------------------ the Remix Source node
def source(label, seed, dice, title, name):
    key = which_game(label)
    info = GAMES[key]
    if not title or title == "auto":
        title = info["label"] + " Remix"
    if not name or name == "auto":
        name = info["name"]
    g = A.new_game(title, name, seed, dice)
    g["kit"] = KIT
    g["k"] = {"remix": {"game": key, "set": {}}}
    return g


# ------------------------------------------------------------ reading and writing constants
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


# ------------------------------------------------------------ rolls
def roll_in(g, salt, value, lo, hi, dice, whole):
    """value moved by the seed INSIDE its safe range: dice 1 can reach either end, never past it"""
    d = max(0.0, min(1.0, dice * g["dice"]))
    u = A._rng(g, salt).uniform(-1, 1)
    value = max(lo, min(hi, value))
    value += u * d * ((hi - value) if u > 0 else (value - lo))
    return int(round(value)) if whole else round(value, 3)


def roll_color(g, salt, hexcol, dice):
    d = max(0.0, min(1.0, dice * g["dice"]))
    u = A._rng(g, salt).uniform(-0.5, 0.5)
    rgb = A.hex_rgb(hexcol)
    if rgb is None or d == 0:
        return hexcol
    h, s, v = colorsys.rgb_to_hsv(*(x / 255.0 for x in rgb))
    if s < 0.1:          # white stays a pale tint
        s = 0.35 * d
    r, gg, b = colorsys.hsv_to_rgb((h + u * d) % 1.0, s, max(v, 0.85))
    return "#%02X%02X%02X" % (int(r * 255), int(gg * 255), int(b * 255))


# ------------------------------------------------------------ fix-ups
def fixups(game, defaults):
    """the knob values for this seed: {constant: value}, the originals {constant: value}, notes"""
    g = copy.deepcopy(game)
    r = g["k"]["remix"]
    info = GAMES[r["game"]]
    vals = {}
    for name, node, lo, hi, whole, why in info["knobs"]:
        if name not in defaults:
            raise ValueError("remix: %s has no 'constant %s' any more" % (info["label"], name))
        if name in r["set"]:
            vals[name] = r["set"][name]
        elif whole == "color":
            vals[name] = roll_color(g, name, defaults[name], FREE_DICE)
        else:
            vals[name] = roll_in(g, name, defaults[name], lo, hi, FREE_DICE, whole)
    (fix_squad if r["game"] == "squad" else fix_toss)(g, vals, defaults)
    g["k"]["vals"] = vals
    g["k"]["defaults"] = {n: defaults[n] for n in vals}
    return g


def fix_squad(g, v, d):
    # the jump must clear the deepest crater (craters stack to 70 deep), and stay on the screen
    peak = v["kJumpV"] ** 2 / (2 * v["kGrav"])
    want = max(85.0, min(300.0, peak))
    if abs(want - peak) > 0.5:
        v["kJumpV"] = round(math.sqrt(2 * v["kGrav"] * want), 3)
        g["notes"].append("jump speed set to %.2f: a jump of %d high (was %d)" % (v["kJumpV"], want, peak))
    # the ground strip still has to cover the screen: 24 slices behind the buggy, the rest ahead
    v["kSlices"] = max(d["kSlices"], int(math.ceil(d["kSlices"] * d["kSeg"] / float(v["kSeg"]))))


def fix_toss(g, v, d):
    t = v["kTile"] = int(round(v["kTile"] / 10.0)) * 10
    for k in ("kHalfW", "kHalfD"):          # the floor is whole tiles
        v[k] = max(t * 2, int(round(v[k] / float(t))) * t)
    if v["kHalfW"] < 240:                   # the level walls stand up to 155 from the centre
        v["kHalfW"] = int(math.ceil(240.0 / t)) * t
    # a jump must clear the level walls (32 high)
    peak = v["kJumpV"] ** 2 / (2 * v["kHeroGrav"])
    if peak < 34:
        v["kJumpV"] = round(math.sqrt(2 * v["kHeroGrav"] * 35), 3)
        g["notes"].append("jump speed raised to %.2f so a hero clears the walls" % v["kJumpV"])
    if v["kReach"] > v["kTop"] - 70:
        v["kReach"] = v["kTop"] - 70
        g["notes"].append("reach lowered to %d: under the ceiling" % v["kReach"])
    # the camera backs off as the arena grows, so the whole box stays in view
    s = max(v["kHalfW"] / float(d["kHalfW"]), v["kTop"] / float(d["kTop"]))
    v["kCamUp"] = int(round(d["kCamUp"] * s))
    v["kCamBack"] = max(100, int(round((d["kHalfD"] + d["kCamBack"]) * s - v["kHalfD"])))


# ------------------------------------------------------------ build
def changed(g):
    v, d = g["k"]["vals"], g["k"]["defaults"]
    return [(n, d.get(n), v[n]) for n in v if n not in d or v[n] != d[n]]


def header_lines(g, info):
    L = ["## REMIX     made in ComfyUI from %s (LIB_GAMES, unchanged), seed %s. Constants changed:"
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
    for note in g["notes"]:
        L.append("##           note: " + note)
    return L


def build(game, projects_root, out_dir, name):
    from .. import kits
    key = game["k"]["remix"]["game"]
    info = GAMES[key]
    with open(source_path(projects_root, key), encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    defaults = read_constants(text)
    g = fixups(game, defaults)
    for n in info["derived"]:
        g["k"]["defaults"][n] = defaults.get(n)
    for n, v in g["k"]["vals"].items():
        text = set_constant(text, n, v)
    lines = text.split("\n")
    if "CARD SCRIPT" not in lines[1]:
        raise ValueError("remix: line 2 of %s is not its CARD SCRIPT line" % info["file"])
    lines[1] = '## CARD SCRIPT: "Play.%s"   %s  (remixed in ComfyUI from %s, seed %s)' \
               % (name, kits.hud_safe(g["title"]), info["label"], g["seed"])
    end = next(i for i in range(2, len(lines)) if lines[i].startswith("#####"))
    lines[end:end] = header_lines(g, info)
    script = "\n".join(lines)
    if out_dir is None:
        out_dir = os.path.join(projects_root, "LIB_COMFY", "games")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "Vibecode3D_Play_%s.livecodescript" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(script)
    g["parts"] = [info["file"]]
    g["file_name"] = name
    return path, script, g


# ------------------------------------------------------------ preview (step 1: the knobs as bars)
def preview_image(g, im, d):
    """one bar a knob across its safe range: a tick where the original sits, the bar where this
    seed put it. (Step 2 draws a still of each game instead.)"""
    info = GAMES[g["k"]["remix"]["game"]]
    v, df = g["k"]["vals"], g["k"]["defaults"]
    d.text((20, 14), "%s   seed %s   %s" % (g["title"].upper(), g["seed"], g.get("file_name", "")), fill=(0, 230, 255))
    d.text((20, 32), "remix of %s: bar = this seed, white tick = the original" % info["label"], fill=(0, 110, 130))
    y = 60
    step = min(24, (im.size[1] - 150) // max(1, len(info["knobs"])))
    for name, node, lo, hi, whole, why in info["knobs"]:
        if whole == "color":
            d.text((20, y), name, fill=(200, 200, 200))
            for i, hx in enumerate((df[name], v[name])):
                d.rectangle([230 + i * 70, y, 290 + i * 70, y + step - 8], fill=A.hex_rgb(hx) or (90, 90, 90))
        else:
            x0, x1 = 230, 760
            f = lambda val: x0 + (x1 - x0) * (min(hi, max(lo, val)) - lo) / float(hi - lo)  # noqa: E731
            moved = v[name] != df[name]
            d.text((20, y), name, fill=(255, 220, 90) if moved else (130, 130, 130))
            d.rectangle([x0, y + 3, x1, y + step - 10], outline=(50, 60, 70))
            d.rectangle([x0, y + 3, f(v[name]), y + step - 10], fill=(0, 170, 200) if moved else (60, 70, 80))
            d.line([f(df[name]), y, f(df[name]), y + step - 7], fill=(255, 255, 255))
            d.text((770, y), fmt(v[name]), fill=(200, 200, 200))
        y += step
    for i, note in enumerate(g["notes"][:4]):
        d.text((20, im.size[1] - 20 - 16 * i), note, fill=(255, 200, 80))
    return im
