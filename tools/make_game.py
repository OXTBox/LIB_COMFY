"""Build one new game of a genre without ComfyUI: what the Comfy Games app's "Make a new one" runs.

    python3 -I tools/make_game.py GENRE [--seed N] [--out DIR] [--projects DIR]
    python3 -I tools/make_game.py --list

GENRE is a line of LIB_COMFY/genres.tsv (Pong, Bricks, Waves, Worm, Dodge, Lander, Rocks, Squad, Toss,
and any added later). The game is built through the node classes themselves, with each genre's starter
chain (tools/kit_chains.py: the same chains the workflow files hold), so a game made here is one the
starter workflow would make with that seed. No seed: a random one that has no game yet.
No torch, numpy or PIL needed (no preview is drawn). Any Python 3.8+ will do: WSL's, Comfy's
standalone-env\\python.exe, or one shipped beside the app.

Prints "OK <path of the new game>" as its last line, or "ERROR <why>" (exit 1).
"""
import importlib.util
import os
import random
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
COMFY = os.path.dirname(HERE)
PACK = os.path.join(COMFY, "ComfyUI-Vibecode3D")
sys.path.insert(0, HERE)
import kit_chains  # noqa: E402


def genres():
    """[(genre, maker, about, workflow)] from genres.tsv"""
    out = []
    with open(os.path.join(COMFY, "genres.tsv"), encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            cells = (line.split("\t") + ["", "", "", ""])[:4]
            out.append(tuple(cells))
    return out


def load_pack():
    # stand-ins, always: only Build Game's preview tensor uses them, and importing torch takes seconds
    for mod in ("torch", "numpy"):
        sys.modules.setdefault(mod, types.ModuleType(mod))
    spec = importlib.util.spec_from_file_location("vc3d", os.path.join(PACK, "__init__.py"),
                                                  submodule_search_locations=[PACK])
    vc = importlib.util.module_from_spec(spec)
    sys.modules["vc3d"] = vc
    spec.loader.exec_module(vc)
    return vc


def chain(vc, maker, seed):
    if maker == "pong":
        steps = [(k, dict(w)) for k, w in kit_chains.pong()]
        steps[0][1]["seed"] = seed
        steps[1][1]["hue"] = (seed * 37) % 360
        return steps
    if maker.startswith("kit:"):
        return kit_chains.chain(maker[4:], seed)
    if maker.startswith("remix:"):
        return kit_chains.remix_chain(vc, maker[6:], seed)
    raise ValueError("genres.tsv: unknown maker %r" % maker)


def run_chain(vc, steps):
    g = None
    for key, widgets in steps:
        node = vc.NODE_CLASS_MAPPINGS[key]()
        g = node.run(**widgets)[0] if g is None else node.run(g, **widgets)[0]
    return g


def make(genre, seed=None, out=None, projects=None):
    """-> path of the new game"""
    row = next((r for r in genres() if r[0].lower() == genre.lower()), None)
    if row is None:
        raise ValueError("no genre %r in genres.tsv (there are: %s)" % (genre, ", ".join(r[0] for r in genres())))
    projects = projects or os.path.dirname(COMFY)
    out = out or os.path.join(COMFY, "games")
    vc = load_pack()
    rnd = random.Random()
    for _ in range(50):
        s = seed if seed is not None else rnd.randint(2, 2 ** 31 - 1)
        g = run_chain(vc, chain(vc, row[1], s))
        name = vc.assemble.safe_name(g["name"]) + str(s)
        if seed is not None or not os.path.exists(os.path.join(out, "Vibecode3D_Play_%s.livecodescript" % name)):
            break
    path, _script, _g = vc.assemble.build(g, projects, out, name)
    return path


def main(argv):
    if argv[:1] == ["--list"]:
        for r in genres():
            print("\t".join(r))
        return 0
    args = {"--seed": None, "--out": None, "--projects": None}
    genre = None
    i = 0
    while i < len(argv):
        if argv[i] in args and i + 1 < len(argv):
            args[argv[i]] = argv[i + 1]
            i += 2
            continue
        genre = argv[i]
        i += 1
    if not genre:
        print("ERROR say which genre: " + ", ".join(r[0] for r in genres()))
        return 1
    try:
        seed = int(args["--seed"]) if args["--seed"] else None
        path = make(genre, seed, args["--out"], args["--projects"])
    except Exception as e:  # the app shows this line to the player
        print("ERROR %s: %s" % (type(e).__name__, e))
        return 1
    print("OK " + path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
