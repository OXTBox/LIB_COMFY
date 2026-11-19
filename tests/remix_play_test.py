"""Build remixes of Squad Buggy and Vector Toss for several seeds and play each headless.

    python3 -I tests/remix_play_test.py [--seeds 1-10] [--game squad|toss] [--keep DIR] [--real]

Each variant must compile and play 600 steps on the engine stand-ins
(LIB_GAMES/tools/engine_stubs plus LIB_ig3d's alias file) without an error: Squad Buggy drives right, jumps and fires and
must get forward; Vector Toss plays itself (VT.TestAuto) and must make a catch. --real also runs
seed 1 of each in LIB_DEV's Game Player on the bridge's generated engine. Dice 0 must give the
original's numbers back. Runs through OXT-Beyond's headless engine under its lock. Exit 1 on FAIL.
"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kit_play_test as kp  # noqa: E402
import kit_test  # noqa: E402
sys.path.insert(0, os.path.join(HERE, "..", "tools"))
import kit_chains  # noqa: E402

LABEL = {"squad": "Squad Buggy", "toss": "Vector Toss"}
PREFIX = {"squad": "Squad", "toss": "VT"}


def body(game, script, stubs, aliases):
    b = ["local tS, tSt, i",
         'put textDecode(url ("binfile:%s"), "UTF-8") into tSt' % stubs, "delete line 1 of tSt",
         'put tSt & return & textDecode(url ("binfile:%s"), "UTF-8") into tSt' % aliases,
         'create stack "RemixPlay"', 'set the script of stack "RemixPlay" to tSt',
         'set the script of card 1 of stack "RemixPlay" to textDecode(url ("binfile:%s"), "UTF-8")' % script,
         'put ck("compiles", the result, empty) & return after tLog',
         'put the long id of card 1 of stack "RemixPlay" into tS', 'set the defaultStack to "RemixPlay"',
         "set the randomSeed to 99", "try"]
    if game == "squad":
        b += ['   dispatch "Squad.TestKeys" to tS with "100"', '   dispatch "Game.OnStart" to tS',
              '   dispatch "Squad.TestAim" to tS with 200, 60', '   dispatch "Squad.TestMouse" to tS with true',
              "   repeat with i = 1 to 600",
              "      if i mod 45 is 0 then",
              '         dispatch "Squad.TestKeys" to tS with "100,32"',
              "      else",
              '         dispatch "Squad.TestKeys" to tS with "100"',
              "      end if",
              '      dispatch "Game.OnUpdate" to tS',
              '      if i mod 300 is 0 then put "STATE " & value("Squad.State()", tS) & return after tLog',
              "   end repeat"]
    else:
        b += ['   dispatch "VT.TestKeys" to tS with "0"', '   dispatch "Game.OnStart" to tS',
              '   dispatch "VT.TestAuto" to tS with true',
              "   repeat with i = 1 to 600", '      dispatch "Game.OnUpdate" to tS',
              '      if i mod 300 is 0 then put "STATE " & value("VT.State()", tS) & return after tLog',
              "   end repeat"]
    b += ["catch tE", '   put "FAIL threw: " & line 1 to 3 of tE & return after tLog', "end try", "return tLog"]
    return "\n".join(b)


def judge(game, states):
    """did the game really play?"""
    if len(states) != 2:
        return False, "no state"
    f = states[-1].split("|")
    try:
        if game == "squad":
            x = int(f[3].split()[1])
            return x > 300, "drove to x %d, level %s, lives %s" % (x, f[0], f[1])
        catches = int(f[1].split(",")[1]) + int(f[2].split(",")[1])
        return catches >= 1, "%d catches, best rally %s" % (catches, f[4].split(",")[1])
    except (IndexError, ValueError):
        return False, "odd state: " + states[-1][:80]


def main(argv):
    projects = os.path.abspath(os.path.join(HERE, "..", ".."))
    seeds, only, keep, real = range(1, 11), None, None, False
    it = iter(argv)
    for a in it:
        if a == "--seeds":
            lo, _, hi = next(it).partition("-")
            seeds = range(int(lo), int(hi or lo) + 1)
        elif a == "--game":
            only = next(it)
        elif a == "--keep":
            keep = os.path.abspath(next(it))
        elif a == "--real":
            real = True
    stubs = os.path.join(projects, "LIB_GAMES", "tools", "engine_stubs.livecodescript")
    aliases = os.path.join(projects, "LIB_ig3d", "livecode", "contract_aliases.livecodescript")
    engine = os.path.join(projects, "xt3D_Raylib_Livecode_Bridge", "testbench", "vibe_engine_xt3d.livecodescript")
    player = os.path.join(projects, "LIB_DEV", "livecode", "game_player.livecodescript")
    vc = kit_test.load_pack()
    remix = vc.kits.remix
    node = vc.NODE_CLASS_MAPPINGS["VC3D_RemixSource"]
    fails = 0
    with tempfile.TemporaryDirectory() as tmp:
        out = keep or tmp
        for game in ([only] if only else ["squad", "toss"]):
            g = node().run(LABEL[game], 5, 0.0, "auto", "auto")[0]
            _, _, gg = vc.assemble.build(g, projects, tmp, "Zero")
            ok = not remix.changed(gg)
            print("%s %s dice 0: the original's numbers (%s)" % ("PASS" if ok else "FAIL", game, remix.changed(gg) or "none changed"))
            fails += not ok
            seen = set()
            for seed in seeds:
                # even seeds: the whole chain (every node, Mutate always); odd seeds: Remix Source alone
                if seed % 2 == 0:
                    g = kit_test.run_chain(vc, kit_chains.remix_chain(vc, game, seed, 1.0, 1.0))
                else:
                    g = node().run(LABEL[game], seed, 1.0, "auto", "auto")[0]
                path, script, gg = vc.assemble.build(g, projects, out, "%s%d" % (g["name"], seed))
                seen.add(tuple(sorted(gg["k"]["vals"].items())))
                text = kp.run_body(projects, body(game, path, stubs, aliases), tmp, "%s_%d" % (game, seed))
                states = [l[6:] for l in text.splitlines() if l.startswith("STATE ")]
                played, why = judge(game, states)
                ok = "PASS compiles" in text and "FAIL" not in text and "THREW" not in text and played
                print("%s %s seed %d: %d changed%s; %s%s" % ("PASS" if ok else "FAIL", game, seed, len(remix.changed(gg)),
                                                              " [%s]" % ", ".join(gg["mutated"]) if gg.get("mutated") else "", why,
                                                              "" if ok else "\n   " + text.strip()[-400:]))
                fails += not ok
                if real and seed == seeds[0] and os.path.exists(engine) and os.path.exists(player):
                    text = kp.run_body(projects, kp.body_real(path, PREFIX[game], engine, player, 200), tmp, game + "_real")
                    ok = "PASS real: compiles" in text and "PASS real: draws" in text and "FAIL" not in text
                    print("%s %s seed %d real engine: runs and draws%s" % ("PASS" if ok else "FAIL", game, seed,
                                                                          "" if ok else "\n   " + text.strip()[-400:]))
                    fails += not ok
            ok = len(seen) == len(seeds)
            print("%s %s: %d seeds gave %d different games" % ("PASS" if ok else "FAIL", game, len(seeds), len(seen)))
            fails += not ok
    print("%d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
