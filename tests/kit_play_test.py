"""Build every genre kit's game and play it headless, with no ComfyUI and no window.

    python3 -I tests/kit_play_test.py [--projects DIR] [--seed N] [--kit KIT] [--keep DIR]

For each kit: the small chain plays on the engine stand-ins (LIB_GAMES/tools/engine_stubs plus
LIB_ig3d's alias file) with its autopilot (PREFIX.TestAuto) and must get past level 1; the full
chain must play 900 steps without an error; then the full game runs in LIB_DEV's Game Player on
the bridge's generated engine and must draw. Runs through OXT-Beyond's headless engine
(OXT-BEYOND/tests/oxt_headless.py, under its lock). Exit 1 on any FAIL.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import kit_chains  # noqa: E402
import kit_test  # noqa: E402


def body_stubs(script, prefix, stubs, aliases, frames_plan):
    b = ["local tS, tSt, tErr",
         'put textDecode(url ("binfile:%s"), "UTF-8") into tSt' % stubs,
         "delete line 1 of tSt",
         'put tSt & return & textDecode(url ("binfile:%s"), "UTF-8") into tSt' % aliases,
         'create stack "KitPlay"', 'set the script of stack "KitPlay" to tSt',
         'set the script of card 1 of stack "KitPlay" to textDecode(url ("binfile:%s"), "UTF-8")' % script,
         'put ck("compiles", the result, empty) & return after tLog',
         'put the long id of card 1 of stack "KitPlay" into tS', 'set the defaultStack to "KitPlay"',
         "set the randomSeed to 99", "try",
         '   dispatch "Stub.NoMouse" to tS', '   dispatch "Game.OnStart" to tS',
         '   dispatch "Vec.TestMouse" to tS with "none"',
         '   dispatch "%s.TestAuto" to tS with true' % prefix]
    for n in frames_plan:
        b += ["   repeat %d" % n, '      dispatch "Game.OnUpdate" to tS', "   end repeat",
              '   put "STATE " & value("%s.State()", tS) & return after tLog' % prefix]
    b += ["catch tE", '   put "FAIL threw: " & line 1 to 3 of tE & return after tLog', "end try", "return tLog"]
    return "\n".join(b)


def body_real(script, prefix, engine, player, frames):
    b = ["local tS, tErr", "global gNoMouse", "put true into gNoMouse",
         'start using stack "%s"' % engine,
         'create invisible stack "KitReal"',
         'set the script of stack "KitReal" to textDecode(url ("binfile:%s"), "UTF-8")' % player,
         'set the name of card 1 of stack "KitReal" to "Play.Kit"',
         'set the script of card 1 of stack "KitReal" to textDecode(url ("binfile:%s"), "UTF-8")' % script,
         'put ck("real: compiles", the result, empty) & return after tLog',
         'put the long id of card 1 of stack "KitReal" into tS',
         'set the uScriptFile of stack "KitReal" to "%s"' % script,
         'set the uGame of stack "KitReal" to "Kit"', 'set the rect of stack "KitReal" to "0,0,900,600"',
         'set the defaultStack to "KitReal"', "try",
         '   dispatch "Player.Start" to stack "KitReal"', '   dispatch "Player.StopTimer" to stack "KitReal"',
         '   dispatch "Vec.TestMouse" to tS with "none"',
         '   dispatch "%s.TestAuto" to tS with true' % prefix,
         "   repeat %d" % frames, "      Vibe.Step", '      dispatch "Player.Draw" to stack "KitReal"', "   end repeat",
         '   put "STATE " & value("%s.State()", tS) & return after tLog' % prefix,
         "catch tE", '   put "FAIL real threw: " & line 1 to 3 of tE & return after tLog', "end try",
         'put ck("real: draws", the number of graphics of card 1 of stack "KitReal" > 1, true) & return after tLog',
         "return tLog"]
    return "\n".join(b)


def run_body(projects, text, tmp, name):
    path = os.path.join(tmp, name + ".txt")
    with open(path, "w") as f:
        f.write(text)
    runner = os.path.join(projects, "OXT-BEYOND", "tests")
    out = subprocess.run(["flock", "/tmp/oxt_headless.lock", sys.executable, "-I", "oxt_headless.py", path],
                         cwd=runner, capture_output=True, text=True, timeout=900)
    return out.stdout + out.stderr


def level_of(state):
    try:
        return int(state.split("|")[0])
    except ValueError:
        return 0


def main(argv):
    projects = os.path.abspath(os.path.join(HERE, "..", ".."))
    seed, only, keep = 7, None, None
    it = iter(argv)
    for a in it:
        if a == "--projects":
            projects = os.path.abspath(next(it))
        elif a == "--seed":
            seed = int(next(it))
        elif a == "--kit":
            only = next(it)
        elif a == "--keep":
            keep = os.path.abspath(next(it))
    stubs = os.path.join(projects, "LIB_GAMES", "tools", "engine_stubs.livecodescript")
    aliases = os.path.join(projects, "LIB_ig3d", "livecode", "contract_aliases.livecodescript")
    engine = os.path.join(projects, "xt3D_Raylib_Livecode_Bridge", "testbench", "vibe_engine_xt3d.livecodescript")
    player = os.path.join(projects, "LIB_DEV", "livecode", "game_player.livecodescript")
    vc = kit_test.load_pack()
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        out_dir = keep or tmp
        for kit in ([only] if only else kit_chains.KITS):
            prefix = kit_chains.PREFIX[kit]
            small, _, _ = kit_test.build(vc, kit, seed, out_dir, small=True, root=projects)
            full, _, _ = kit_test.build(vc, kit, seed, out_dir, small=False, root=projects)
            text = run_body(projects, body_stubs(small, prefix, stubs, aliases, [600, 1200, 1800, 2400]), tmp, kit + "_small")
            states = [l[6:] for l in text.splitlines() if l.startswith("STATE ")]
            ok = "PASS compiles" in text and "FAIL" not in text and states and max(level_of(s) for s in states) >= 2
            print("%s %s small: gets past level 1 (%s)" % ("PASS" if ok else "FAIL", kit, " / ".join(states) or text.strip()[-300:]))
            fails += not ok
            text = run_body(projects, body_stubs(full, prefix, stubs, aliases, [300, 600]), tmp, kit + "_full")
            states = [l[6:] for l in text.splitlines() if l.startswith("STATE ")]
            ok = "PASS compiles" in text and "FAIL" not in text and len(states) == 2
            print("%s %s full: plays 900 steps (%s)" % ("PASS" if ok else "FAIL", kit, " / ".join(states) or text.strip()[-300:]))
            fails += not ok
            if os.path.exists(engine) and os.path.exists(player):
                text = run_body(projects, body_real(full, prefix, engine, player, 300), tmp, kit + "_real")
                ok = "PASS real: compiles" in text and "PASS real: draws" in text and "FAIL" not in text
                states = [l[6:] for l in text.splitlines() if l.startswith("STATE ")]
                print("%s %s real engine: runs and draws (%s)" % ("PASS" if ok else "FAIL", kit, " / ".join(states) or text.strip()[-300:]))
                fails += not ok
            else:
                print("SKIP %s real engine: no engine or Game Player script" % kit)
    print("%d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
