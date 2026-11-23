"""Photon Ball dangerous mode: build several seeds, check every map, play each headless.

    python3 -I tests/photon_play_test.py [--seeds 1-8] [--keep DIR] [--real] [--walls 1-500]

1. Walls alone (no engine): every seed in --walls (default 1-300) gives a map that passes
   photon.validate() and reads back the same from its text; the hand-made map passes too; the
   break rules pass validate_breaks for every order and danger.
2. Dice 0 with Remix Source alone: the hand-made game (no constant changed, walls not replaced).
3. Each seed of --seeds through the photon_dangerous starter chain (tools/kit_chains.py): the game
   compiles on the engine stand-ins, reads its OWN walls (PB.WallsFrom = embedded, no problem),
   the ground at every feature square is the map's (floor - 1 + rise) x 1.5, every match plays the
   built rule list with its crumble times, and both heroes play 3000 steps by themselves with no
   error. --real: the first seed also runs and draws in the Game Player on the generated engine.
Runs through OXT-Beyond's headless engine under its lock. Exit 1 on FAIL.
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


def span(s):
    lo, _, hi = s.partition("-")
    return range(int(lo), int(hi or lo) + 1)


def ground_points(ph, w):
    """(x, z, expected ground) at the middle of every feature square"""
    out = []
    for c, r in w.feature_cells():
        x = (c - 1 - ph.COLS / 2) * ph.CELL + ph.CELL / 2
        z = (r - 1 - ph.ROWS / 2) * ph.CELL + ph.CELL / 2
        s = w.slope.get((c, r))
        rise = sum(s) / 4.0 if s else 0
        out.append((int(x), int(z), (w.floor[r][c] - 1 + rise) * 1.5))
    return out


def body(projects, script, cellmap, points, breaks, steps):
    stubs = os.path.join(projects, "LIB_GAMES", "tools", "engine_stubs.livecodescript")
    aliases = os.path.join(projects, "LIB_ig3d", "livecode", "contract_aliases.livecodescript")
    stamina = os.path.join(projects, "LIB_GAMES", "Vibecode3D_Games", "PromptGlaze", "stamina.livecodescript")
    cellmap_lib = os.path.join(projects, "LIB_BIT", "editor", "livecode", "lib_cellmap.livecodescript")
    b = ["local tS, tSt, i, tR, tFile, tMap, tBad, tG",
         'put textDecode(url ("binfile:%s"), "UTF-8") into tSt' % stubs, "delete line 1 of tSt",
         'put tSt & return & textDecode(url ("binfile:%s"), "UTF-8") into tSt' % aliases,
         'create stack "PhotonPlay"', 'set the script of stack "PhotonPlay" to tSt',
         'set the script of card 1 of stack "PhotonPlay" to textDecode(url ("binfile:%s"), "UTF-8")' % script,
         'put ck("compiles", the result, empty) & return after tLog',
         'start using stack "%s"' % stamina,
         'put specialFolderPath("temporary") & "/photon_play_stamina.txt" into tFile',
         "if there is a file tFile then delete file tFile", "Stamina.UseFile tFile",
         'put the long id of card 1 of stack "PhotonPlay" into tS', 'set the defaultStack to "PhotonPlay"',
         "set the randomSeed to 99", "try",
         '   dispatch "Stub.NoMouse" to tS', '   dispatch "PB.TestKeys" to tS with "0"',
         '   dispatch "Game.OnStart" to tS',
         '   put ck("walls carried in the script", value("PB.WallsFrom()", tS), "embedded") & return after tLog',
         '   set the itemDelimiter to "|"',
         '   put ck("walls read with no problem", item 1 of value("PB.WallsInfo()", tS), empty) & return after tLog',
         '   put "INFO walls " & value("PB.WallsInfo()", tS) & return after tLog',
         '   put ck("rule lists as built", item 1 to 4 of value("PB.RulesInfo()", tS), "%s") & return after tLog'
         % "|".join([",".join(map(str, breaks["rules"])), ",".join(map(str, breaks["off"])),
                     ",".join(map(str, breaks["on"])), str(breaks["catches"])]),
         '   set the itemDelimiter to comma',
         "   put empty into tBad"]
    for x, z, h in points:
        b.append('   put value("PB.GroundAt(%d,%d)", tS) into tG' % (x, z))
        b.append('   if abs(tG - %s) > 0.01 then put "%d,%d game " & tG & " map %s; " after tBad' % (h, x, z, h))
    b.append('   put ck("the ground at %d feature squares is the map\'s", tBad, empty) & return after tLog' % len(points))
    for i, r in enumerate(breaks["rules"], 1):
        off = breaks["off"][i - 1] if breaks["off"] else 2500
        on = breaks["on"][i - 1] if breaks["on"] else 1500
        b += ['   dispatch "PB.TestMatch" to tS with %d' % i,
              '   set the itemDelimiter to "|"',
              '   put item 1 of value("PB.MatchState()", tS) & "|" & item 5 of value("PB.RulesInfo()", tS) into tR',
              '   set the itemDelimiter to comma',
              '   put ck("match %d: rule %d, crumble %d/%d", tR, "%d,%d,0|%d,%d") & return after tLog'
              % (i, r, off, on, i, r, off, on)]
        ring = breaks.get("ring") or [1]
        shows = ring[min(i, len(ring)) - 1] != 0
        b.append('   put ck("match %d: landing ring %s", value("PB.ShowLand()", tS), "%s") & return after tLog'
                 % (i, "shown" if shows else "hidden", "true" if shows else "false"))
    b += ['   dispatch "Game.OnStart" to tS', '   dispatch "PB.TestAuto" to tS with true',
          '   dispatch "PB.TestLives" to tS with 99',
          "   repeat with i = 1 to %d" % steps, '      dispatch "Game.OnUpdate" to tS',
          '      if i mod 1000 is 0 then put "STATE " & value("PB.MatchState()", tS) & " falls " & value("PB.HeroField(" & quote & "PROMPT" & quote & "," & quote & "falls" & quote & ")", tS) & "/" & value("PB.HeroField(" & quote & "GLAZE" & quote & "," & quote & "falls" & quote & ")", tS) & " over " & value("PB.Over()", tS) & return after tLog',
          "   end repeat",
          '   dispatch "PB.TestAuto" to tS with false',
          "catch tE", '   put "FAIL threw: " & line 1 to 3 of tE & return after tLog', "end try",
          'start using stack "%s"' % cellmap_lib,
          'put CellMap.Read("%s") into tMap' % cellmap,
          'put ck("the cellmap copy reads in LIB_BIT (20x10 v3)", tMap["meta"]["cols"] & "x" & tMap["meta"]["rows"] & " v" & tMap["meta"]["version"], "20x10 v3") & return after tLog',
          'put CellMap.Check(tMap, empty) into tR',
          'put "INFO CellMap.Check: " & the number of lines of tR & " line(s): " & line 1 to 2 of tR & return after tLog',
          "if there is a file tFile then delete file tFile",
          'set the script of card 1 of stack "PhotonPlay" to empty',
          "lock messages", 'delete stack "PhotonPlay"', "unlock messages",
          "return tLog"]
    return "\n".join(b)


def main(argv):
    projects = os.path.abspath(os.path.join(HERE, "..", ".."))
    seeds, walls, keep, real, steps = span("1-8"), span("1-300"), None, False, 3000
    it = iter(argv)
    for a in it:
        if a == "--seeds":
            seeds = span(next(it))
        elif a == "--walls":
            walls = span(next(it))
        elif a == "--keep":
            keep = os.path.abspath(next(it))
        elif a == "--real":
            real = True
        elif a == "--steps":
            steps = int(next(it))
    vc = kit_test.load_pack()
    ph, remix = vc.kits.photon, vc.kits.remix
    fails = 0

    def report(ok, words, more=""):
        nonlocal fails
        print("%s %s%s" % ("PASS" if ok else "FAIL", words, "" if ok else "\n   " + more))
        fails += not ok

    # 1. maps and rules without the engine
    hm = ph.hand_made(projects)
    report(not ph.validate(hm), "the hand-made walls pass the checks", str(ph.validate(hm)))
    bad, redo, hand = [], 0, 0
    for seed in walls:
        for dice in (0.3, 1.0):
            w, notes = ph.make_walls(seed, None, dice, projects)
            p = ph.validate(ph.parse(w.text()))
            if p or ph.parse(w.text()).text() != w.text():
                bad.append((seed, dice, p[:1]))
            redo += bool(notes)
            hand += any("hand-made" in n for n in notes)
    report(not bad, "walls for %d seeds x 2 dice all valid and read back the same (%d made again, %d fell back to "
           "hand-made)" % (len(walls), redo, hand), str(bad[:3]))
    extremes = [{"density": 1.0, "max_height": 120, "ramps": 1.0, "kickers": 1.0, "far_emblems": 4, "back_emblems": 2,
                 "emblem_width": 4, "symmetry": 0.0}, {"density": 0.0, "far_emblems": 0, "back_emblems": 0},
                {"density": 1.0, "max_height": 20, "ramps": 0.0, "symmetry": 1.0}]
    bad = []
    for i, given in enumerate(extremes):
        for seed in range(1, 41):
            w, notes = ph.make_walls(seed, given, 1.0, projects)
            if ph.validate(w):
                bad.append((i, seed))
    report(not bad, "walls at the sliders' ends (3 settings x 40 seeds) all valid", str(bad[:3]))
    bad = []
    for order in ph.ORDERS:
        for d10 in range(0, 11):
            for seed in range(1, 21):
                b = ph.make_breaks(seed, {"danger": d10 / 10.0, "order": order, "matches": 2 + seed % 7,
                                          "ring": ph.RINGS[seed % len(ph.RINGS)]}, 1.0)
                if ph.validate_breaks(b):
                    bad.append((order, d10, seed, ph.validate_breaks(b)))
                if b["ring"][0] == 0 and b["danger"] < 0.85 and b["ring"] != [0]:
                    bad.append((order, d10, seed, "match 1 without the ring", b["ring"]))
    report(not bad, "break rules valid for every order, danger 0-1, 20 seeds, every ring kind", str(bad[:3]))
    rings = {k: [ph.make_breaks(s, {"ring": k, "danger": 0.6, "matches": 5}, 1.0)["ring"] for s in range(1, 21)]
             for k in ph.RINGS}
    report(all(r == [1] for r in rings["always"]) and all(r == [0] for r in rings["never"])
           and any(0 in r for r in rings["fades"]) and any(0 in r for r in rings["random"])
           and all(r == sorted(r, reverse=True) for r in rings["fades"]),
           "landing ring: always / never as said, fades only goes, random varies", str(rings)[:300])
    lo = [ph.make_breaks(s, {"danger": 0.0}, 0.0) for s in range(1, 21)]
    hi = [ph.make_breaks(s, {"danger": 1.0}, 0.0) for s in range(1, 21)]
    harder = sum(sum(b["rules"]) for b in hi) > sum(sum(b["rules"]) for b in lo) and \
        sum(sum(b["on"]) for b in hi) < sum(sum(b["on"]) for b in lo)
    report(harder, "danger 1 gives worse rules and quicker crumbles than danger 0")

    with tempfile.TemporaryDirectory() as tmp:
        out = keep or tmp
        # 2. dice 0: the hand-made game
        src = vc.NODE_CLASS_MAPPINGS["VC3D_RemixSource"]
        g = src().run("Photon Ball", 5, 0.0, "auto", "auto")[0]
        path, script, gg = vc.assemble.build(g, projects, tmp, "Zero")
        report(not remix.changed(gg) and gg["k"]["photon"]["walls_text"] is None
               and 'constant kMatchRules = "1,2,3,4"' in script and ph.STUB in script,
               "dice 0: the hand-made game (numbers, rules and walls)", str(remix.changed(gg)))
        # 3. seeds through the starter chain, played
        seen = set()
        for seed in seeds:
            g = kit_test.run_chain(vc, kit_chains.remix_chain(vc, "photon", seed, 0.7, 0.6))
            path, script, gg = vc.assemble.build(g, projects, out, "%s%d" % (g["name"], seed))
            p = gg["k"]["photon"]
            w = ph.parse(p["walls_text"])
            cellmap = os.path.join(out, "photon_walls", "%s%d.cellmap" % (g["name"], seed))
            seen.add((p["walls_text"], tuple(p["breaks"]["rules"])))
            ok = not ph.validate(w) and os.path.exists(cellmap) and "-- comfy: genre=Photon seed=%d " % seed in script
            text = kp.run_body(projects, body(projects, path, cellmap, ground_points(ph, w), p["breaks"], steps), tmp,
                               "photon_%d" % seed)
            states = [l[6:] for l in text.splitlines() if l.startswith("STATE ")]
            ok = ok and "PASS compiles" in text and "FAIL" not in text and "THREW" not in text and len(states) == steps // 1000
            info = [l for l in text.splitlines() if l.startswith("INFO")]
            report(ok, "seed %d: %s | %s | %s | last %s%s" % (
                seed, gg["title"], p["walls_summary"], ph.breaks_words(p["breaks"]), states[-1] if states else "?",
                "".join(" [%s]" % n for n in gg["notes"])), text.strip()[-600:])
            if info and not ok:
                print("   " + "\n   ".join(info))
            if real and seed == seeds[0]:
                engine = os.path.join(projects, "xt3D_Raylib_Livecode_Bridge", "testbench", "vibe_engine_xt3d.livecodescript")
                player = os.path.join(projects, "LIB_DEV", "livecode", "game_player.livecodescript")
                text = kp.run_body(projects, kp.body_real(path, "PB", engine, player, 300), tmp, "photon_real")
                ok = "PASS real: compiles" in text and "PASS real: draws" in text and "FAIL" not in text
                report(ok, "seed %d real engine: runs and draws" % seed, text.strip()[-400:])
        report(len(seen) == len(seeds), "%d seeds gave %d different games" % (len(seeds), len(seen)))
    print("%d failed" % fails)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
