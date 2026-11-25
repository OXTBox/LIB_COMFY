## PART core (CPONG): the court, serve, ball flight, paddle faces, points, levels, HUD.
## Always used. The builder adds the config handler (Cpong.Config) and the parts the
## nodes ask for: one court style (Cpong.Decor), one ball shape (Cpong.BallMesh),
## player keys (Cpong.PlayerMove) and/or the computer (Cpong.CpuMove).

global bPaused, bPlaying

local sCfg, sPad, sPadN, sBall, sGoal
local sLevel, sHome, sAway, sOver, sWonAll, sServeT, sTestKeys, sHUDWas, sSpeedNow, sSkillAdd

constant kZ = 300          -- screen scale 300/z: 1 unit = 1 pixel
constant kT = 5            -- half thickness of a paddle

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Cpong.Config
   put false into sOver
   Cpong.StartLevel 1
end Game.OnStart

-- the level: ball speed and computer skill grow with it
-- a level change through the loading screen (LIB_LOADING_SCREEN: burn, green text, the player first,
-- then the level draws in) when the host has it; else at once, as before. p1-13, 23 Nov 2026
on Cpong.GoLevel pLevel
   if "LIB_LOADING" is among the lines of the stacksInUse then
      Loading.Go pLevel
   else
      Cpong.StartLevel pLevel
   end if
end Cpong.GoLevel

on Cpong.StartLevel pLevel
   local tM, i, tN
   put pLevel into sLevel
   put 0 into sHome
   put 0 into sAway
   put sCfg["ballSpeed"] * (1 + sCfg["levelGain"] * (pLevel - 1)) into sSpeedNow
   put 0.08 * (pLevel - 1) into sSkillAdd
   Scene.ClearAll
   -- the floor decoration (dim), the walls, the goal mouths: one mesh each
   put Mesh.New() into tM
   Cpong.Decor tM
   if tM["count"] > 0 then
      Mesh.Define "Cpong.Decor", tM
      get Entity.Spawn("Cpong.Decor", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"])
   end if
   put Mesh.New() into tM
   Cpong.Walls tM, false
   Mesh.Define "Cpong.Court", tM
   get Entity.Spawn("Cpong.Court", 0, sCfg["cy"], kZ, sCfg["wallColor"])
   put Mesh.New() into tM
   Cpong.Walls tM, true
   Mesh.Define "Cpong.Goals", tM
   get Entity.Spawn("Cpong.Goals", 0, sCfg["cy"], kZ, sCfg["goalColor"])
   repeat with i = 1 to sPadN
      if sPad[i]["side"] is "L" or sPad[i]["side"] is "R" then
         Mesh.Define "Cpong.Pad" & i, Mesh.Box(kT * 2, sPad[i]["half"] * 2, 6)
      else
         Mesh.Define "Cpong.Pad" & i, Mesh.Box(sPad[i]["half"] * 2, kT * 2, 6)
      end if
      put 0 into sPad[i]["pos"]
      put Entity.Spawn("Cpong.Pad" & i, 0, 0, kZ, sPad[i]["color"]) into sPad[i]["key"]
      Cpong.PlacePad i
   end repeat
   Mesh.Define "Cpong.Ball", Cpong.BallMesh(sCfg["ballSize"])
   repeat with tN = 1 to sCfg["ballCount"]
      put Entity.Spawn("Cpong.Ball", 0, sCfg["cy"], kZ, sCfg["ballColor"]) into sBall[tN]["key"]
   end repeat
   Cpong.Serve
end Cpong.StartLevel

-- one edge of the court: walls (pGoals false) or goal mouths (pGoals true)
on Cpong.Walls @pM, pGoals
   local tW, tH
   put sCfg["hw"] into tW
   put sCfg["hh"] into tH
   if (sGoal["T"] is not empty) is pGoals then Cpong.Line pM, -tW, -tH, tW, -tH
   if (sGoal["B"] is not empty) is pGoals then Cpong.Line pM, -tW, tH, tW, tH
   if (sGoal["L"] is not empty) is pGoals then Cpong.Line pM, -tW, -tH, -tW, tH
   if (sGoal["R"] is not empty) is pGoals then Cpong.Line pM, tW, -tH, tW, tH
end Cpong.Walls

-- a wire line in a mesh, flat on the court
on Cpong.Line @pM, pX1, pY1, pX2, pY2
   local tA
   Mesh.AddVertex pM, pX1, pY1, 0
   put the result into tA
   Mesh.AddVertex pM, pX2, pY2, 0
   Mesh.AddLine pM, tA, the result
end Cpong.Line

-- a wire circle of pN sides
on Cpong.Ring @pM, pX, pY, pR, pN
   local i, tA
   repeat with i = 0 to pN - 1
      put i * 2 * pi / pN into tA
      Cpong.Line pM, pX + pR * cos(tA), pY + pR * sin(tA), pX + pR * cos(tA + 2 * pi / pN), pY + pR * sin(tA + 2 * pi / pN)
   end repeat
end Cpong.Ring

-- every ball back to the middle; play starts after a short wait (Space starts it at once)
on Cpong.Serve
   local tN, tSpread, tSign
   put 45 into sServeT
   put empty into sHUDWas
   repeat with tN = 1 to sCfg["ballCount"]
      put 0 into sBall[tN]["x"]
      put (tN - (sCfg["ballCount"] + 1) / 2) * sCfg["ballSize"] * 3 into sBall[tN]["y"]
      put (random(1001) - 501) / 500 * 0.6 into tSpread
      if random(2) = 1 then
         put 1 into tSign
      else
         put -1 into tSign
      end if
      if sCfg["axis"] is "x" then
         put tSign * sSpeedNow into sBall[tN]["dx"]
         put tSpread * sSpeedNow into sBall[tN]["dy"]
      else
         put tSpread * sSpeedNow into sBall[tN]["dx"]
         put tSign * sSpeedNow into sBall[tN]["dy"]
      end if
      Cpong.PlaceBall tN
   end repeat
   repeat with tN = 1 to sPadN
      put (random(2001) - 1001) / 1000 into sPad[tN]["err"]
   end repeat
end Cpong.Serve

function Cpong.Keys
   if sTestKeys is not empty then return sTestKeys
   return the keysDown
end Cpong.Keys

on Cpong.TestKeys pKeys
   put pKeys into sTestKeys
end Cpong.TestKeys

function Cpong.AnyKey pList, pKeys
   local tK
   repeat for each item tK in pList
      if tK is among the items of pKeys then return true
   end repeat
   return false
end Cpong.AnyKey

on Game.OnUpdate
   local tKeys, i
   put Cpong.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put false into sOver
         Cpong.GoLevel 1
      end if
      Cpong.ShowHUD
      exit Game.OnUpdate
   end if
   repeat with i = 1 to sPadN
      if sPad[i]["ctrl"] is "cpu" then
         Cpong.CpuMove i
      else
         Cpong.PlayerMove i, tKeys
      end if
      Cpong.PlacePad i
   end repeat
   if sServeT > 0 then
      subtract 1 from sServeT
      if 32 is among the items of tKeys then put 0 into sServeT
      Cpong.ShowHUD
      exit Game.OnUpdate
   end if
   repeat with i = 1 to sCfg["ballCount"]
      Cpong.MoveBall i
      if sServeT > 0 or sOver then exit repeat
   end repeat
   Cpong.ShowHUD
end Game.OnUpdate

-- keep a paddle on its track and show it there
on Cpong.PlacePad pJ
   local tRoom
   if sPad[pJ]["side"] is "L" or sPad[pJ]["side"] is "R" then
      put sCfg["hh"] - sPad[pJ]["half"] into tRoom
      put max(-tRoom, min(tRoom, sPad[pJ]["pos"])) into sPad[pJ]["pos"]
      Entity.SetPosition sPad[pJ]["key"], sPad[pJ]["fx"], sCfg["cy"] + sPad[pJ]["pos"], kZ
   else
      put sCfg["hw"] - sPad[pJ]["half"] into tRoom
      put max(-tRoom, min(tRoom, sPad[pJ]["pos"])) into sPad[pJ]["pos"]
      Entity.SetPosition sPad[pJ]["key"], sPad[pJ]["pos"], sCfg["cy"] + sPad[pJ]["fx"], kZ
   end if
end Cpong.PlacePad

on Cpong.PlaceBall pB
   Entity.SetPosition sBall[pB]["key"], sBall[pB]["x"], sCfg["cy"] + sBall[pB]["y"], kZ
end Cpong.PlaceBall

on Cpong.MoveBall pB
   local tR, j
   put sCfg["ballSize"] / 2 into tR
   add sBall[pB]["dx"] to sBall[pB]["x"]
   add sBall[pB]["dy"] to sBall[pB]["y"]
   repeat with j = 1 to sPadN
      Cpong.HitPad j, pB, tR
   end repeat
   Cpong.Edges pB, tR
   if sServeT > 0 or sOver then exit Cpong.MoveBall
   Cpong.PlaceBall pB
end Cpong.MoveBall

-- a paddle only meets a ball coming at its face; where it lands sets the angle
on Cpong.HitPad pJ, pB, pR
   local tS, tDir, tN, tAlong, tV, tFace, tSp, tTan
   put sPad[pJ]["side"] into tS
   if tS is "L" or tS is "T" then
      put 1 into tDir
   else
      put -1 into tDir
   end if
   if tS is "L" or tS is "R" then
      put sBall[pB]["x"] into tN
      put sBall[pB]["y"] into tAlong
      put sBall[pB]["dx"] into tV
   else
      put sBall[pB]["y"] into tN
      put sBall[pB]["x"] into tAlong
      put sBall[pB]["dy"] into tV
   end if
   if tV * tDir >= 0 then exit Cpong.HitPad
   put sPad[pJ]["fx"] + tDir * kT into tFace
   -- the ball's leading edge reached the face this step, and not from behind
   if (tN - tDir * pR - tFace) * tDir > 0 then exit Cpong.HitPad
   if (tN - tV - tDir * pR - tFace) * tDir < -2 then exit Cpong.HitPad
   if abs(tAlong - sPad[pJ]["pos"]) > sPad[pJ]["half"] + pR then exit Cpong.HitPad
   put min(sCfg["ballMax"], abs(tV) * sCfg["ballGain"]) into tSp
   put (tAlong - sPad[pJ]["pos"]) / sPad[pJ]["half"] * tSp * 0.8 into tTan
   if tS is "L" or tS is "R" then
      put tFace + tDir * pR into sBall[pB]["x"]
      put tDir * tSp into sBall[pB]["dx"]
      put tTan into sBall[pB]["dy"]
   else
      put tFace + tDir * pR into sBall[pB]["y"]
      put tDir * tSp into sBall[pB]["dy"]
      put tTan into sBall[pB]["dx"]
   end if
   FX.Sparks sBall[pB]["x"], sCfg["cy"] + sBall[pB]["y"], kZ, 5, sPad[pJ]["color"]
   Sound.Play "Hit"
end Cpong.HitPad

-- walls bounce the ball; past a goal mouth it is a point
on Cpong.Edges pB, pR
   local tW, tH
   put sCfg["hw"] into tW
   put sCfg["hh"] into tH
   if sBall[pB]["x"] < -tW + pR then
      if sGoal["L"] is empty then
         put -tW + pR into sBall[pB]["x"]
         put abs(sBall[pB]["dx"]) into sBall[pB]["dx"]
         Sound.Play "Bounce"
      else if sBall[pB]["x"] < -tW - 30 then
         Cpong.Point "L"
         exit Cpong.Edges
      end if
   end if
   if sBall[pB]["x"] > tW - pR then
      if sGoal["R"] is empty then
         put tW - pR into sBall[pB]["x"]
         put -abs(sBall[pB]["dx"]) into sBall[pB]["dx"]
         Sound.Play "Bounce"
      else if sBall[pB]["x"] > tW + 30 then
         Cpong.Point "R"
         exit Cpong.Edges
      end if
   end if
   if sBall[pB]["y"] < -tH + pR then
      if sGoal["T"] is empty then
         put -tH + pR into sBall[pB]["y"]
         put abs(sBall[pB]["dy"]) into sBall[pB]["dy"]
         Sound.Play "Bounce"
      else if sBall[pB]["y"] < -tH - 30 then
         Cpong.Point "T"
         exit Cpong.Edges
      end if
   end if
   if sBall[pB]["y"] > tH - pR then
      if sGoal["B"] is empty then
         put tH - pR into sBall[pB]["y"]
         put -abs(sBall[pB]["dy"]) into sBall[pB]["dy"]
         Sound.Play "Bounce"
      else if sBall[pB]["y"] > tH + 30 then
         Cpong.Point "B"
         exit Cpong.Edges
      end if
   end if
end Cpong.Edges

on Cpong.Point pSide
   if sGoal[pSide] is "home" then
      add 1 to sAway
      Sound.Play "Hurt"
   else
      add 1 to sHome
      Sound.Play "Pickup"
   end if
   put empty into sHUDWas
   if sHome >= sCfg["win"] then
      if sLevel >= sCfg["levels"] then
         put true into sOver
         put true into sWonAll
         Sound.Play "Win"
      else
         Sound.Play "Win"
         Cpong.GoLevel sLevel + 1
      end if
      exit Cpong.Point
   end if
   if sAway >= sCfg["win"] then
      put true into sOver
      put false into sWonAll
      Sound.Play "Lose"
      exit Cpong.Point
   end if
   Cpong.Serve
end Cpong.Point

on Cpong.ShowHUD
   local tWords
   put sLevel & "|" & sHome & "|" & sAway & "|" & (sServeT > 0) & "|" & sOver into tWords
   if tWords is sHUDWas then exit Cpong.ShowHUD
   put tWords into sHUDWas
   HUD.Set "Cpong.Score", sCfg["title"] & "   HOME" && sHome && "  AWAY" && sAway && "  FIRST TO" && sCfg["win"] && "  LEVEL" && sLevel & "/" & sCfg["levels"], 20, 30, 14
   HUD.Remove "Cpong.Msg"
   if sOver and sWonAll then
      HUD.Set "Cpong.Msg", "ALL LEVELS WON.  SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Cpong.Msg", "MATCH LOST.  SPACE TO PLAY AGAIN", 20, 56, 12
   else if sServeT > 0 then
      HUD.Set "Cpong.Msg", sCfg["help"], 20, 56, 12
   end if
end Cpong.ShowHUD

function Cpong.State
   return sLevel & "|" & sHome & "|" & sAway & "|" & round(sBall[1]["x"]) & "," & round(sBall[1]["y"]) & "|" & (sServeT > 0) & "|" & sOver
end Cpong.State

on Game.OnStop
   HUD.Clear
end Game.OnStop

-- the arrows move you; a focused menu or field must never get them
on arrowKey pKey
end arrowKey
