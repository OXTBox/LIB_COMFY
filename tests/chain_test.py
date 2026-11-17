"""Run a node chain without ComfyUI: python3 tests/chain_test.py SEED [out_dir]"""
import os, sys, types, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "..", "ComfyUI-Vibecode3D")
for mod in ("torch", "numpy"):
    try:
        __import__(mod)
    except ImportError:
        sys.modules[mod] = types.ModuleType(mod)
spec = importlib.util.spec_from_file_location("vc3d", os.path.join(PACK, "__init__.py"),
                                              submodule_search_locations=[PACK])
vc = importlib.util.module_from_spec(spec); sys.modules["vc3d"] = vc; spec.loader.exec_module(vc)
A = vc.assemble
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1
out = sys.argv[2] if len(sys.argv) > 2 else None
g = vc.GameStart().run("Comfy Pong", "ComfyPong", seed, 1.0)[0]
g = vc.Palette().run(g, 190, "random", 0.5)[0]
g = vc.Court().run(g, 760, 440, "random", 60, "auto", "auto", 0.5)[0]
g = vc.Paddle().run(g, "L", "arrows", "auto", 90, 9, 24, 0.6, "auto", 1.0, 0.5)[0]
g = vc.Paddle().run(g, "R", "cpu", "auto", 90, 8, 24, 0.6, "auto", 1.0, 0.5)[0]
g = vc.Paddle().run(g, "T", "cpu", "auto", 120, 8, 24, 0.6, "auto", 0.5, 0.5)[0]
g = vc.Paddle().run(g, "R", "cpu", "auto", 60, 8, 220, 0.5, "auto", 0.4, 0.5)[0]
g = vc.Ball().run(g, 14, 7, 1.05, 16, 1, "random", "auto", 0.5)[0]
g = vc.MatchRules().run(g, 5, 3, 0.15, 0.5)[0]
root = os.path.abspath(os.path.join(HERE, "..", ".."))
path, script, gg = A.build(g, root, out, "ComfyPong%d" % seed)
print(path); print("parts:", gg["parts"]); print("paddles:", [(p["side"], p["ctrl"], p["team"], p["half"]) for p in gg["paddles"]])
print("notes:", gg["notes"])
try:
    vc.preview.draw(gg).save(os.path.join(out or "/tmp", "ComfyPong%d.png" % seed)); print("preview saved")
except Exception as e:
    print("preview:", e)
