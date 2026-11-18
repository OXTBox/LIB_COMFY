"""Build games from the genre kits without ComfyUI, through the node classes themselves.

    python tests/kit_test.py KIT SEED [out_dir] [small]     KIT: brick wave coil dodge, or all

The chains are tools/kit_chains.py (the same ones the workflow files hold). Run it with Comfy's
python.exe (it has PIL) to get a preview PNG beside each game; without PIL the scripts are still
written. Without out_dir the games go to LIB_COMFY/games, as Build Game's do."""
import os, sys, types, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "ComfyUI-Vibecode3D")
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import kit_chains  # noqa: E402

for mod in ("torch", "numpy"):
    try:
        __import__(mod)
    except ImportError:
        sys.modules[mod] = types.ModuleType(mod)


def load_pack():
    spec = importlib.util.spec_from_file_location("vc3d", os.path.join(PACK, "__init__.py"),
                                                  submodule_search_locations=[PACK])
    vc = importlib.util.module_from_spec(spec)
    sys.modules["vc3d"] = vc
    spec.loader.exec_module(vc)
    return vc


def run_chain(vc, steps):
    """the game dict at the end of a chain (Build Game not included)"""
    g = None
    for key, widgets in steps:
        node = vc.NODE_CLASS_MAPPINGS[key]()
        g = node.run(**widgets)[0] if g is None else node.run(g, **widgets)[0]
    return g


def build(vc, kit, seed, out=None, small=False, root=None):
    g = run_chain(vc, kit_chains.chain(kit, seed, small))
    root = root or os.path.abspath(os.path.join(HERE, "..", ".."))
    return vc.assemble.build(g, root, out, "%s%d" % (g["name"], seed))


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    out = sys.argv[3] if len(sys.argv) > 3 else None
    small = len(sys.argv) > 4 and sys.argv[4] == "small"
    vc = load_pack()
    for kit in (kit_chains.KITS if which == "all" else [which]):
        path, script, gg = build(vc, kit, seed, out, small)
        print(path)
        print("  parts:", gg["parts"], " notes:", gg["notes"])
        try:
            vc.preview.draw(gg).save(path.replace(".livecodescript", ".png"))
            print("  preview saved")
        except ImportError as e:
            print("  no preview:", e)


if __name__ == "__main__":
    main()
