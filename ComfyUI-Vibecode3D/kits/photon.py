"""photon: Photon Ball's "dangerous mode" (PHOTON_BALL_PLAN.md step 2).

Photon Ball (LIB_GAMES, prefix PB., Engine 1) is a remix game (remix.py GAMES["photon"]): Build Game
copies it and rewrites its constants. On top of that, two seeded things the hand-made game placed by
hand are made here:

  walls   the features on the three walls that are not the camera side: ledges and pillars
          (extrusions), ramps whose high side meets their ledge, kicker slopes against the wall,
          and flat emblems on the wall faces (* far wall: +1 a bank; P / G back walls: mend a
          square). Written as a cellmap (PhotonBall/README.md: exactly 20 x 10 cells of 40), checked
          by validate(); a seed that fails is made again with the next attempt's dice, then made
          mirrored, and in the end the hand-made walls are used. An invalid map is never written.
  breaks  which floor rule (1-4) each match plays and its crumble times (kMatchRules,
          kMatchOffMS, kMatchOnMS, kMatchCatches), by a seeded "danger".

The built game carries its walls inside its script (PB.WallsText), so it is one file that plays
wherever it is copied (LIB_COMFY/games, the Comfy Games app's Data folder, an install). A copy of
the cellmap is written beside it (games/photon_walls/) for the BitEditor; the game never reads it.
No ComfyUI imports: tested without ComfyUI (tests/photon_play_test.py).
"""
import os
import random

COLS, ROWS, CELL = 20, 10, 40
WALL = 200                   # wall cells' floor (hu): the editor's view; the game ignores it
JUMP_HU = 20                 # a jump peaks at 35 units = 23 hu: a ledge 20 hu up (30 units) is jumpable
STEP_HU = 10                 # walked up without a jump (the map's step)
MAX_RISE = 60                # the cellmap's steepest slope between corners (BitEditor checker)
HOMES = ((6, 6), (15, 6))    # the heroes' home squares: always plain
WEST_HALF = range(2, 11)     # PROMPT's half: columns 2..10; GLAZE's: 11..19
CENTRE = (10, 11)            # the centre line columns: only kickers there (row 9)

# the strip of ring cells on PROMPT's half, in walking order: the west wall from the camera side to
# the far corner, then the far wall to the centre. GLAZE's is its mirror (col -> 21 - col).
WEST_STRIP = [(2, r) for r in range(2, 9)] + [(c, 9) for c in range(2, 11)]
EAST_STRIP = [(21 - c, r) for c, r in WEST_STRIP]
RING = set(WEST_STRIP) | set(EAST_STRIP)

WALL_DEFAULTS = {"density": 0.5, "max_height": 60, "ramps": 0.6, "kickers": 0.5, "far_emblems": 1,
                 "back_emblems": 1, "emblem_width": 2, "symmetry": 0.6}
BREAK_DEFAULTS = {"danger": 0.5, "order": "climb", "matches": 4, "crumble_off": 2.5, "crumble_on": 1.5,
                  "catches": 10}
ORDERS = ("climb", "shuffle", "random", "hand-made")
RULE_WORDS = {1: "THE BALL BREAKS A SQUARE", 2: "EVERY BOUNCE BREAKS", 3: "BOUNCES CRACK AROUND",
              4: "BOUNCES PUNCH HOLES"}


# ------------------------------------------------------------ the map
class Walls:
    """floor[r][c] (1-based, hu), slope{(c, r): (nw, ne, se, sw)}, design[r][c] (characters)"""

    def __init__(self):
        self.floor = [[0] * (COLS + 1) for _ in range(ROWS + 1)]
        self.design = [[" "] * (COLS + 1) for _ in range(ROWS + 1)]
        self.slope = {}
        self.kind = {}           # (c, r) -> block | pillar | ramp | kicker (what the generator meant)
        self.name = "photon_ball_walls"
        self.notes = []
        for r in range(2, ROWS + 1):
            for c in range(1, COLS + 1):
                wall = c in (1, COLS) or r == ROWS
                self.floor[r][c] = WALL if wall else 1
                self.design[r][c] = "#" if wall else "."

    def copy(self):
        w = Walls()
        w.floor = [row[:] for row in self.floor]
        w.design = [row[:] for row in self.design]
        w.slope = dict(self.slope)
        w.kind = dict(self.kind)
        w.name = self.name
        w.notes = list(self.notes)
        return w

    def top(self, c, r):
        """a block's top above the floor (hu)"""
        return self.floor[r][c] - 1

    def feature_cells(self):
        return sorted(k for k in arena_cells() if self.floor[k[1]][k[0]] != 1 or k in self.slope)

    def text(self):
        L = ["# cellmap 3 - LIB_BIT/editor (format: editor/CELLMAP_V2.md + CELLMAP_V3.md)",
             "# PHOTON BALL walls made by LIB_COMFY's dangerous mode (kits/photon.py). Format: PhotonBall/README.md",
             "[map]", "name\t" + self.name, "cols\t%d" % COLS, "rows\t%d" % ROWS, "cell\t%d" % CELL,
             "wallH\t150", "unitPx\t16", "font\tAquarius", "tags\ttags_default", "version\t3", "step\t%d" % STEP_HU,
             "[design]"]
        for r in range(1, ROWS + 1):
            L.append("".join(self.design[r][1:]))
        L.append("[tags]")
        for r in range(1, ROWS + 1):
            L.append("".join(" " if r == 1 else "#" if c in (1, COLS) or r == ROWS else "."
                             for c in range(1, COLS + 1)))
        L.append("[floor]")
        for r in range(1, ROWS + 1):
            L.append(" ".join("%3d" % self.floor[r][c] for c in range(1, COLS + 1)))
        L.append("[slope]")
        for (c, r), s in sorted(self.slope.items(), key=lambda kv: (kv[0][1], kv[0][0])):
            L.append("%d,%d\t%d %d %d %d" % ((c, r) + tuple(s)))
        return "\n".join(L) + "\n"


def arena_cells():
    return [(c, r) for r in range(2, ROWS) for c in range(2, COLS)]


def parse(text):
    """a cellmap text -> Walls (only what the game reads), or raise ValueError"""
    w = Walls()
    meta, sec, row = {}, None, 0
    for line in text.replace("\r", "").split("\n"):
        if line.startswith("[") and line.endswith("]"):
            sec, row = line[1:-1], 0
            continue
        if line.startswith("#") and sec in (None, "map"):
            continue
        if sec == "map" and "\t" in line:
            k, v = line.split("\t", 1)
            meta[k] = v
        elif sec == "design":
            row += 1
            if row <= ROWS:
                for c, ch in enumerate(line[:COLS], 1):
                    w.design[row][c] = ch
        elif sec == "floor":
            row += 1
            if row <= ROWS:
                for c, v in enumerate(line.split()[:COLS], 1):
                    w.floor[row][c] = int(v)
        elif sec == "slope" and "\t" in line:
            cell, s = line.split("\t", 1)
            c, r = (int(x) for x in cell.split(","))
            w.slope[(c, r)] = tuple(int(x) for x in s.split())
    if (meta.get("cols"), meta.get("rows"), meta.get("cell")) != (str(COLS), str(ROWS), str(CELL)):
        raise ValueError("not %d x %d cells of %d" % (COLS, ROWS, CELL))
    w.name = meta.get("name", w.name)
    return w


# ------------------------------------------------------------ heights for the walk check
def corner_rise(s, side):
    """the two corners' rise on a side of a slope cell: side n (low z), s (high z), w (low x), e (high x)"""
    nw, ne, se, sw = s
    return {"n": (nw, ne), "s": (sw, se), "w": (nw, sw), "e": (ne, se)}[side]


def edge_h(w, c, r, side):
    """the ground (hu above the arena floor) along one side of a cell: (low, high)"""
    base = w.floor[r][c] - 1
    s = w.slope.get((c, r))
    if s is None:
        return base, base
    a, b = corner_rise(s, side)
    return base + min(a, b), base + max(a, b)


SIDES = {(1, 0): ("e", "w"), (-1, 0): ("w", "e"), (0, 1): ("s", "n"), (0, -1): ("n", "s")}


def can_step(w, a, b):
    """a hero can go from cell a to its neighbour b: down any way; up a step, or a jump onto a flat top"""
    d = (b[0] - a[0], b[1] - a[1])
    sa, sb = SIDES[d]
    _, ha = edge_h(w, a[0], a[1], sa)
    lb, hb = edge_h(w, b[0], b[1], sb)
    if lb != hb:                         # onto a ramp's side that tilts across the move: its low end
        hb = lb
    return hb - ha <= JUMP_HU


def reachable(w, start, cols):
    seen, todo = {start}, [start]
    while todo:
        a = todo.pop()
        for d in SIDES:
            b = (a[0] + d[0], a[1] + d[1])
            if b in seen or b[0] not in cols or not (2 <= b[1] <= ROWS - 1):
                continue
            if can_step(w, a, b):
                seen.add(b)
                todo.append(b)
    return seen


# ------------------------------------------------------------ the fairness rules
def validate(w):
    """[] when the map is one the game reads and the README's fairness rules hold; else the problems"""
    P = []
    for c in range(1, COLS + 1):
        if w.floor[1][c] != 0 or w.design[1][c] != " ":
            P.append("the camera side (row 1) must stay empty: col %d" % c)
            break
    for c, r in arena_cells():
        f = w.floor[r][c]
        if not 1 <= f <= 255:
            P.append("floor %d at %d,%d" % (f, c, r))
        if (c, r) not in RING and (f != 1 or (c, r) in w.slope):
            P.append("a feature off the walls at %d,%d" % (c, r))
    for h in HOMES:
        if w.floor[h[1]][h[0]] != 1 or h in w.slope:
            P.append("home square %d,%d is not plain" % h)
    for c in CENTRE:
        if w.floor[9][c] != 1:
            P.append("a block on the centre line at %d,9" % c)
    for (c, r), s in w.slope.items():
        if len(s) != 4 or min(s) < 0 or max(s) - min(s) > MAX_RISE:
            P.append("ramp %d,%d too steep or odd: %s" % (c, r, s))
            continue
        if w.floor[r][c] != 1:
            P.append("ramp %d,%d is not on the floor" % (c, r))
        # its high side meets what it leads to: a wall, or a block exactly as high
        high = [side for side in "nswe" if min(corner_rise(s, side)) == max(s) and max(s) > 0]
        if not high:
            P.append("ramp %d,%d has no high side" % (c, r))
            continue
        ok = False
        for side in high:
            dc, dr = {"n": (0, -1), "s": (0, 1), "w": (-1, 0), "e": (1, 0)}[side]
            nc, nr = c + dc, r + dr
            if nc in (1, COLS) or nr == ROWS:
                ok = True                   # a kicker against the wall
            elif 2 <= nr <= ROWS - 1 and (nc, nr) not in w.slope and w.top(nc, nr) == max(s):
                ok = True                   # meets its ledge
        if not ok:
            P.append("ramp %d,%d: its high side meets neither a wall nor a ledge as high" % (c, r))
    # every plain square of a half can be reached from that hero's home (no pockets the ball can die in)
    for home, cols in ((HOMES[0], range(2, 11)), (HOMES[1], range(11, 20))):
        seen = reachable(w, home, cols)
        lost = [(c, r) for c in cols for r in range(2, ROWS) if w.floor[r][c] == 1 and (c, r) not in seen]
        if lost:
            P.append("plain squares nobody can reach from %d,%d: %s" % (home + (lost[:4],)))
        lost = [k for k in w.slope if k[0] in cols and k not in seen]
        if lost:
            P.append("ramps nobody can reach: %s" % lost)
    # the halves are about as dangerous: feature cells within 2, pillar cells within 2
    def count(cols, pred):
        return sum(1 for c, r in arena_cells() if c in cols and pred(c, r))
    feat = lambda c, r: w.floor[r][c] != 1 or (c, r) in w.slope  # noqa: E731
    pil = lambda c, r: (c, r) not in w.slope and w.top(c, r) > JUMP_HU and not ramp_next(w, c, r)  # noqa: E731
    if abs(count(range(2, 11), feat) - count(range(11, 20), feat)) > 2:
        P.append("the halves are not fair: %d feature squares west, %d east"
                 % (count(range(2, 11), feat), count(range(11, 20), feat)))
    if abs(count(range(2, 11), pil) - count(range(11, 20), pil)) > 2:
        P.append("the halves are not fair: pillars")
    # emblems: letters only on wall cells, never # . or a quote; each back wall
    # the same width of emblem; no back emblem hidden behind a pillar
    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            ch = w.design[r][c]
            if ch == '"' or ch == "\t":
                P.append("a quote or tab in the design at %d,%d" % (c, r))
            if ch not in "#. =/I" and not (c in (1, COLS) and 2 <= r <= ROWS - 1 or r == ROWS and 2 <= c <= COLS - 1):
                P.append("an emblem off the walls at %d,%d" % (c, r))
    west = [r for r in range(2, ROWS) if w.design[r][1] not in "#. "]
    east = [r for r in range(2, ROWS) if w.design[r][COLS] not in "#. "]
    if len(west) != len(east):
        P.append("back wall emblems differ: %d west, %d east" % (len(west), len(east)))
    for r in west:
        if w.top(2, r) > JUMP_HU and (2, r) not in w.slope:
            P.append("the west emblem at row %d is behind a pillar" % r)
    for r in east:
        if w.top(COLS - 1, r) > JUMP_HU and (COLS - 1, r) not in w.slope:
            P.append("the east emblem at row %d is behind a pillar" % r)
    return P


def ramp_next(w, c, r):
    """a ramp beside this block leads up to it"""
    for dc, dr in SIDES:
        s = w.slope.get((c + dc, r + dr))
        if s and max(s) == w.top(c, r):
            return True
    return False


# ------------------------------------------------------------ making walls
def settings_of(given, dice, rnd):
    """the Walls node's settings, each wandering by dice inside its range"""
    s = dict(WALL_DEFAULTS)
    s.update({k: v for k, v in (given or {}).items() if k in s})

    def wander(v, lo, hi, whole=False):
        u = rnd.uniform(-1, 1) * dice
        v = max(lo, min(hi, v))
        v += u * ((hi - v) if u > 0 else (v - lo))
        return int(round(v)) if whole else v
    s["density"] = wander(s["density"], 0.0, 1.0)
    s["max_height"] = wander(s["max_height"], 20, 120, True)
    s["ramps"] = wander(s["ramps"], 0.0, 1.0)
    s["kickers"] = wander(s["kickers"], 0.0, 1.0)
    if rnd.random() < dice * 0.4:
        s["far_emblems"] = min(4, int(s["far_emblems"]) + 1)
    return s


def strip_side(a, b):
    """the side of cell a that faces its neighbour b"""
    return SIDES[(b[0] - a[0], b[1] - a[1])][0]


def rise_toward(side, h):
    """a slope rising h hu toward one side: (nw, ne, se, sw)"""
    return {"w": (h, 0, 0, h), "e": (0, h, h, 0), "s": (0, 0, h, h), "n": (h, h, 0, 0)}[side]


def wall_side(c, r):
    if r == 9:
        return "s"                      # the far wall is high z
    return "w" if c == 2 else "e"


def place_half(w, strip, s, rnd):
    """features along one half's strip of ring cells (strip in walking order)"""
    n = len(strip)
    groups = int(round(s["density"] * 5 + rnd.uniform(-0.6, 0.6)))
    used = set()
    tries = 0
    while groups > 0 and tries < 60:
        tries += 1
        kinds = ["ledge", "ledge", "pillar" if s["max_height"] > JUMP_HU + 10 else "ledge", "kicker"]
        weights = [1.0, 0.6, 0.5, 0.2 + 1.2 * s["kickers"]]
        kind = rnd.choices(kinds, weights)[0]
        length = 1 if kind == "kicker" else rnd.choice((1, 2, 2, 3))
        ramp = kind == "ledge" and rnd.random() < s["ramps"]
        need = length + (1 if ramp else 0)
        i = rnd.randrange(0, n - need + 1)
        span = list(range(i, i + need))
        # a gap of one plain cell to other groups along the strip
        if any(j in used or (j - 1) in used or (j + 1) in used for j in span):
            continue
        cells = [strip[j] for j in span]
        if any(c in CENTRE for c, _ in cells) and kind != "kicker":
            continue
        if kind == "kicker":
            c, r = cells[0]
            w.slope[(c, r)] = rise_toward(wall_side(c, r), rnd.choice((20, 30, 30, 45)))
            w.kind[(c, r)] = "kicker"
            w.design[r][c] = "/"
        else:
            if kind == "pillar":
                h = rnd.randrange(JUMP_HU + 10, s["max_height"] + 1, 5) if s["max_height"] >= JUMP_HU + 10 else JUMP_HU
            elif ramp:
                h = rnd.choice([x for x in (20, 25, 30, 40, 45) if x <= min(MAX_RISE, max(20, s["max_height"]))])
            else:
                h = rnd.choice([x for x in (10, 15, 20, 20) if x <= max(10, s["max_height"])])
            ramp_at = None
            if ramp:                       # the ramp at the end of the run nearer the strip's middle
                if rnd.random() < 0.5:
                    ramp_at, block = cells[0], cells[1:]
                else:
                    ramp_at, block = cells[-1], cells[:-1]
            else:
                block = cells
            for c, r in block:
                w.floor[r][c] = 1 + h
                w.kind[(c, r)] = "pillar" if kind == "pillar" else "block"
                w.design[r][c] = "I" if kind == "pillar" else "="
            if ramp_at:
                nb = block[0] if ramp_at == cells[0] else block[-1]
                w.slope[ramp_at] = rise_toward(strip_side(ramp_at, nb), h)
                w.kind[ramp_at] = "ramp"
                w.design[ramp_at[1]][ramp_at[0]] = "/"
        used.update(span)
        groups -= 1


def mirror_half(w):
    """GLAZE's half made from PROMPT's (col -> 21 - col; slopes turned east for west)"""
    for c in range(11, 20):
        for r in range(2, ROWS):
            m = 21 - c
            w.floor[r][c] = w.floor[r][m]
            w.design[r][c] = w.design[r][m]
            w.slope.pop((c, r), None)
            w.kind.pop((c, r), None)
            if (m, r) in w.slope:
                nw, ne, se, sw = w.slope[(m, r)]
                w.slope[(c, r)] = (ne, nw, sw, se)
            if (m, r) in w.kind:
                w.kind[(c, r)] = w.kind[(m, r)]


def place_emblems(w, s, rnd):
    width = max(1, min(4, int(s["emblem_width"])))
    far = max(0, min(4, int(s["far_emblems"])))
    back = max(0, min(2, int(s["back_emblems"])))
    # far wall: an odd count puts one across the centre (10-11); the rest in pairs, mirrored
    taken = set()
    if far % 2:
        for c in (10, 11):
            w.design[ROWS][c] = "*"
            taken.add(c)
    for _ in range(far // 2):
        for _try in range(30):
            ww = max(1, min(width, 3))
            c0 = rnd.randint(2, 10 - ww)
            cols = list(range(c0, c0 + ww))
            if any(c in taken or c - 1 in taken or c + 1 in taken for c in cols):
                continue
            for c in cols:
                w.design[ROWS][c] = "*"
                w.design[ROWS][21 - c] = "*"
                taken.update((c, 21 - c))
            break
    # back walls: the same rows on both (P west, G east), never behind a pillar
    taken = set()
    for _ in range(back):
        for _try in range(30):
            r0 = rnd.randint(2, ROWS - width)
            rows = list(range(r0, r0 + width))
            if any(r in taken or r - 1 in taken or r + 1 in taken for r in rows):
                continue
            if any(w.top(2, r) > JUMP_HU or w.top(COLS - 1, r) > JUMP_HU for r in rows):
                continue
            for r in rows:
                w.design[r][1] = "P"
                w.design[r][COLS] = "G"
            taken.update(rows)
            break


def generate(seed, given=None, dice=1.0, attempt=0, mirror=None):
    """one try at a seed's walls (not yet checked)"""
    rnd = random.Random("%s:photon-walls:%s" % (seed, attempt))
    s = settings_of(given, dice, rnd)
    w = Walls()
    w.name = "comfy_photon_%s" % seed
    place_half(w, WEST_STRIP, s, rnd)
    if mirror is None:
        mirror = rnd.random() < s["symmetry"]
    if mirror:
        mirror_half(w)
    else:
        place_half(w, EAST_STRIP, s, rnd)
    place_emblems(w, s, rnd)
    w.settings = s
    w.mirrored = mirror
    return w


def hand_made(projects_root):
    path = os.path.join(projects_root, "LIB_GAMES", "Vibecode3D_Games", "PhotonBall", "walls.cellmap")
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def make_walls(seed, given=None, dice=1.0, projects_root=None):
    """a seed's walls that pass validate(): (Walls, notes). Tries 12 seeded attempts, then 12
    mirrored ones, then the hand-made walls (which are checked too)."""
    first = None
    for attempt in range(24):
        w = generate(seed, given, dice, attempt, True if attempt >= 12 else None)
        p = validate(w)
        if int(w.settings["back_emblems"]) > 0 and all(w.design[r][1] in "#. " for r in range(2, ROWS)):
            p.append("no room for the back wall emblems")
        if int(w.settings["far_emblems"]) > 0 and all(w.design[ROWS][c] in "#. " for c in range(2, COLS)):
            p.append("no room for the far wall emblems")
        if first is None:
            first = p
        if not p:
            # the map must read back as written (the game reads the text, not this object)
            back = parse(w.text())
            if validate(back):
                continue
            notes = [] if attempt == 0 else ["walls: attempt %d of the seed passed (the first failed: %s)"
                                             % (attempt + 1, first[0])]
            return w, notes
    w = hand_made(projects_root) if projects_root else None
    if w is not None and not validate(w):
        return w, ["walls: no try of the seed passed (%s): the hand-made walls are used" % first[0]]
    raise ValueError("photon: no valid walls for seed %s and the hand-made walls are missing or invalid" % seed)


def summary(w):
    kinds = {}
    for k in w.kind.values():
        kinds[k] = kinds.get(k, 0) + 1
    far = "".join(w.design[ROWS][c] for c in range(2, COLS)).replace("#", ".")
    backs = sum(1 for r in range(2, ROWS) if w.design[r][1] not in "#. ")
    return ("%d block, %d pillar, %d ramp, %d kicker squares; far wall %s; back emblems %d tall%s"
            % (kinds.get("block", 0), kinds.get("pillar", 0), kinds.get("ramp", 0), kinds.get("kicker", 0),
               far, backs, "; mirrored" if getattr(w, "mirrored", False) else ""))


# ------------------------------------------------------------ the break rules per match
def make_breaks(seed, given=None, dice=1.0):
    """{"rules": [..], "off": [ms..], "on": [ms..], "catches": n, "danger": d, "order": o, "notes": []}"""
    s = dict(BREAK_DEFAULTS)
    s.update({k: v for k, v in (given or {}).items() if k in s})
    rnd = random.Random("%s:photon-breaks" % seed)
    danger = max(0.0, min(1.0, float(s["danger"]) + rnd.uniform(-0.15, 0.15) * dice))
    n = max(2, min(8, int(s["matches"])))
    order = s["order"]
    notes = []
    if order == "hand-made":
        return {"rules": [1, 2, 3, 4], "off": [], "on": [], "catches": int(s["catches"]), "danger": danger,
                "order": order, "notes": notes}
    if order == "climb":
        # the hand-made climb, started higher and climbing faster the more dangerous
        r = 1 + int(danger * 2.2 + rnd.random() * 0.6 * dice)
        rules = []
        for i in range(n):
            rules.append(min(4, r))
            if rnd.random() < 0.55 + 0.45 * danger:
                r += 1
        if rules[-1] < 3 and n >= 3:     # it must get bad by the end: the last match one worse
            rules[-1] = rules[-1] + 1
    elif order == "shuffle":
        rules = [1, 2, 3, 4]
        rnd.shuffle(rules)
        while len(rules) < n:
            rules.append(rnd.choice([3, 4] if danger > 0.5 else [2, 3, 4]))
        rules = rules[:n]
    else:
        rules = []
        for i in range(n):
            p = min(0.95, danger * 0.7 + 0.3 * i / max(1, n - 1))
            rules.append(1 + sum(1 for _ in range(3) if rnd.random() < p))
    # fair: the first match is never the hole puncher unless the danger is near full
    if rules[0] == 4 and danger < 0.85:
        j = next((i for i, x in enumerate(rules) if x < 4), None)
        if j is not None:
            rules[0], rules[j] = rules[j], rules[0]
        else:
            rules[0] = 3
        notes.append("rules: match 1 does not punch holes (danger under 0.85)")
    off, on = [], []
    for i in range(n):
        late = i / max(1, n - 1)
        f = 1 - danger * (0.25 + 0.35 * late)
        f *= 1 + rnd.uniform(-0.1, 0.1) * dice
        off.append(int(round(max(800, min(6000, s["crumble_off"] * 1000 * f)) / 50.0) * 50))
        on.append(int(round(max(500, min(4000, s["crumble_on"] * 1000 * f)) / 50.0) * 50))
    catches = max(4, min(16, int(round(s["catches"] - danger * 4 + rnd.uniform(-1, 1) * dice))))
    return {"rules": rules, "off": off, "on": on, "catches": catches, "danger": round(danger, 3),
            "order": order, "notes": notes}


def validate_breaks(b):
    P = []
    if not b["rules"] or any(r not in (1, 2, 3, 4) for r in b["rules"]):
        P.append("rules must be 1-4: %s" % b["rules"])
    if b["rules"] and b["rules"][0] == 4 and b["danger"] < 0.85:
        P.append("match 1 punches holes")
    if any(x < 800 for x in b["off"]) or any(x < 500 for x in b["on"]):
        P.append("crumble too quick to step away: %s %s" % (b["off"], b["on"]))
    if not 4 <= b["catches"] <= 16:
        P.append("catches a match %s" % b["catches"])
    return P


def breaks_words(b):
    return "rules %s (the last repeats); falls after stepping off %s ms, after stepping on %s ms; %d catches a match; danger %.2f (%s)" % (
        ",".join(map(str, b["rules"])), ",".join(map(str, b["off"])) or "2500", ",".join(map(str, b["on"])) or "1500",
        b["catches"], b["danger"], b["order"])


# ------------------------------------------------------------ into the game's script
def walls_handler(w):
    """PB.WallsText returning the whole cellmap (xTalk has no multi-line strings: a line at a time)"""
    L = ["function PB.WallsText", "   local tW"]
    for line in w.text().rstrip("\n").split("\n"):
        line = line.replace('"', "'")
        parts = line.split("\t")
        expr = " & tab & ".join('"%s"' % p for p in parts)
        L.append("   put %s & return after tW" % expr)
    L += ["   return tW", "end PB.WallsText"]
    return "\n".join(L)


STUB = "function PB.WallsText\n   return empty\nend PB.WallsText"


def apply(text, g, out_dir, name):
    """the walls and break lists into a copy of the game's text; the cellmap copy beside the game"""
    from . import remix
    p = g["k"]["photon"]
    if p.get("walls_text") is not None:
        if text.count(STUB) != 1:
            raise ValueError("photon: the game's PB.WallsText stub is there %d times (1 expected): has Photon Ball changed?"
                             % text.count(STUB))
        w = parse(p["walls_text"])
        text = text.replace(STUB, walls_handler(w))
        folder = os.path.join(out_dir, "photon_walls")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name + ".cellmap"), "w", encoding="utf-8", newline="\n") as f:
            f.write(p["walls_text"])
    b = p["breaks"]
    text = remix.set_constant(text, "kMatchRules", ",".join(map(str, b["rules"])))
    text = remix.set_constant(text, "kMatchOffMS", ",".join(map(str, b["off"])))
    text = remix.set_constant(text, "kMatchOnMS", ",".join(map(str, b["on"])))
    return text


def header_lines(g):
    p = g["k"]["photon"]
    L = ["## DANGER    " + breaks_words(p["breaks"])]
    if p.get("walls_text") is not None:
        L.append("## WALLS     made by the seed, carried in PB.WallsText (a copy: photon_walls/%s.cellmap): %s"
                 % (g.get("file_name") or g["name"], p["walls_summary"]))
    else:
        L.append("## WALLS     the hand-made walls (PhotonBall/walls.cellmap)")
    return L


# ------------------------------------------------------------ the still
def still(g, d, v, col, W, H):
    """the arena from above: features by kind, emblems on the walls, the homes; the rules list"""
    p = g["k"]["photon"]
    w = parse(p["walls_text"]) if p.get("walls_text") else None
    s = 20
    ox, oy = 50, 90
    X = lambda c: ox + (c - 1) * s * 2  # noqa: E731
    Y = lambda r: oy + (ROWS - r) * s * 2  # noqa: E731
    for r in range(1, ROWS + 1):
        for c in range(1, COLS + 1):
            x0, y0 = X(c), Y(r)
            box = [x0, y0, x0 + 2 * s - 2, y0 + 2 * s - 2]
            if w is None:
                d.rectangle(box, outline=(50, 60, 70))
                continue
            ch = w.design[r][c]
            k = w.kind.get((c, r))
            if r == 1:
                continue
            if c in (1, COLS) or r == ROWS:
                d.rectangle(box, outline=(90, 90, 110))
                if ch not in "#. ":
                    d.text((x0 + 14, y0 + 12), ch, fill=(255, 208, 64) if r == ROWS else
                           (A_rgb(v.get("kPromptColor")) if c == 1 else A_rgb(v.get("kGlazeColor"))))
            elif (c, r) in w.slope:
                d.rectangle(box, outline=(80, 200, 255))
                d.text((x0 + 4, y0 + 12), "/%d" % max(w.slope[(c, r)]), fill=(80, 200, 255))
            elif w.floor[r][c] > 1:
                top = w.floor[r][c] - 1
                d.rectangle(box, fill=(60, 30, 30) if top > JUMP_HU else (20, 70, 30), outline=(120, 255, 140))
                d.text((x0 + 8, y0 + 12), str(top), fill=(255, 255, 255))
            else:
                d.rectangle(box, outline=(40, 50, 60))
    for c, r in HOMES:
        d.ellipse([X(c) + 12, Y(r) + 12, X(c) + 26, Y(r) + 26],
                  fill=A_rgb(v.get("kPromptColor") if c < 11 else v.get("kGlazeColor")))
    d.text((ox, oy + ROWS * 2 * s + 6), "camera side (open)", fill=(120, 130, 140))
    b = p["breaks"]
    y = 520
    for i, r in enumerate(b["rules"]):
        off = b["off"][i] if i < len(b["off"]) else 2500
        on = b["on"][i] if i < len(b["on"]) else 1500
        d.text((50 + 210 * (i % 4), y + 16 * (i // 4)), "M%d: %d %s  %d/%d" % (i + 1, r, RULE_WORDS[r][:16], off, on),
               fill=(255, 220, 90))
    d.text((50, 70), "walls: " + (p.get("walls_summary") or "hand-made"), fill=(200, 200, 200))


def A_rgb(h):
    from .. import assemble as A
    return A.hex_rgb(h or "#FFFFFF") or (255, 255, 255)
