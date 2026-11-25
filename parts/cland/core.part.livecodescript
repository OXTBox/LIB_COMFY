## PART core (CLAND): a lander. Gravity pulls you down onto rough ground; thrust burns fuel. Set
## down on a flat pad, slowly and upright, for points (narrow pads are worth more); anywhere else,
## or too fast, is a crash. Each level: new ground, stronger pull. The builder adds Lander.Config.

global bPaused, bPlaying

local sCfg, sGround, sGroundN, sPad, sPadN
local sMe, sFlameKey, sFuel, sGrav, sWind, sLanded, sWaitT
local sLevel, sLives, sScore, sOver, sWonAll, sHUDWas, sTick, sMsg, sMsgT, sAuto, sAutoPad

constant kZ = 300

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Lander.Config
   put 0 into sScore
   put sCfg["lives"] into sLives
   put false into sOver
   Lander.StartLevel 1
end Game.OnStart

-- a level change through the loading screen (LIB_LOADING_SCREEN: burn, green text, the player first,
-- then the level draws in) when the host has it; else at once, as before. p1-13, 23 Nov 2026
on Lander.GoLevel pLevel
   if "LIB_LOADING" is among the lines of the stacksInUse then
      Loading.Go pLevel
   else
      Lander.StartLevel pLevel
   end if
end Lander.GoLevel

on Lander.StartLevel pLevel
   local tM
   put pLevel into sLevel
   Scene.ClearAll
   Particles.Clear
   put sCfg["gravity"] * (1 + sCfg["levelGain"] * (pLevel - 1)) into sGrav
   put sCfg["wind"] * (pLevel - 1) / max(1, sCfg["levels"] - 1) into sWind
   put Mesh.New() into tM
   Vec.Decor tM, sCfg["floor"], sCfg["hw"], sCfg["hh"], sCfg["grid"]
   if tM["count"] > 0 then
      Mesh.Define "Lander.Sky", tM
      get Entity.Spawn("Lander.Sky", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"])
   end if
   Lander.MakeGround
   Mesh.Define "Lander.Me", Lander.CraftMesh()
   put Mesh.New() into tM
   Vec.Outline tM, -sCfg["size"] * 0.2 & "," & sCfg["size"] * 0.45 & cr & "0," & sCfg["size"] * 1.1 & cr & sCfg["size"] * 0.2 & "," & sCfg["size"] * 0.45
   Mesh.Define "Lander.Flame", tM
   Lander.NewCraft
   Lander.Say "LEVEL" && pLevel & ": LAND ON A PAD", 80
end Lander.StartLevel

-- a craft: a box of a cabin on two legs, pointing up
function Lander.CraftMesh
   local tM, s
   put Mesh.New() into tM
   put sCfg["size"] / 2 into s
   Vec.Rect tM, -s * 0.6, -s * 0.8, s * 0.6, s * 0.2
   Vec.Line tM, -s * 0.6, s * 0.2, -s, s
   Vec.Line tM, s * 0.6, s * 0.2, s, s
   Vec.Line tM, -s * 1.2, s, -s * 0.8, s
   Vec.Line tM, s * 0.8, s, s * 1.2, s
   Vec.Line tM, 0, -s * 0.8, 0, -s * 1.1
   return tM
end Lander.CraftMesh

-- the ground: a walk of points across the arena with flat pads in it, 1 to 3 segments wide;
-- a narrow pad is worth more (times 3, 2 or 1)
on Lander.MakeGround
   local i, tN, tX, tY, tM, tPadM, tStep, k, tLow, tHigh, tStart, tSpan, tFlat, tTries, j, tFree
   set the randomSeed to sCfg["seed"] + sLevel * 101
   put empty into sGround
   put empty into sPad
   put empty into tFlat
   put sCfg["segments"] into tN
   put sCfg["hw"] * 2 / tN into tStep
   put sCfg["hh"] - 10 into tLow
   put sCfg["hh"] - sCfg["hills"] into tHigh
   put 0 into sPadN
   -- where the pads go: a start segment and a span, never touching another pad
   repeat with k = 1 to sCfg["pads"]
      repeat with tTries = 1 to 30
         put random(3) into tSpan
         put random(tN - tSpan - 1) + 1 into tStart
         put true into tFree
         repeat with j = tStart - 1 to tStart + tSpan
            if tFlat[j] is not empty then put false into tFree
         end repeat
         if tFree then exit repeat
      end repeat
      if not tFree then next repeat
      add 1 to sPadN
      repeat with j = tStart to tStart + tSpan - 1
         put sPadN into tFlat[j]
      end repeat
      put 4 - tSpan into sPad[sPadN]["times"]
   end repeat
   put Mesh.New() into tM
   put Mesh.New() into tPadM
   put -sCfg["hw"] into sGround[0]["x"]
   put tLow - random(max(1, round(tLow - tHigh))) into sGround[0]["y"]
   repeat with i = 1 to tN
      put -sCfg["hw"] + i * tStep into tX
      if tFlat[i] is not empty then
         put sGround[i - 1]["y"] into tY
         put tFlat[i] into k
         if sPad[k]["x1"] is empty then put sGround[i - 1]["x"] into sPad[k]["x1"]
         put tX into sPad[k]["x2"]
         put tY into sPad[k]["y"]
         Vec.Line tPadM, sGround[i - 1]["x"], tY, tX, tY
         Vec.Line tPadM, sGround[i - 1]["x"], tY + 3, tX, tY + 3
      else
         put Vec.Clamp(sGround[i - 1]["y"] + (random(201) - 101) / 100 * sCfg["rough"] * tStep, tHigh, tLow) into tY
         Vec.Line tM, sGround[i - 1]["x"], sGround[i - 1]["y"], tX, tY
      end if
      put tX into sGround[i]["x"]
      put tY into sGround[i]["y"]
   end repeat
   put tN into sGroundN
   Mesh.Define "Lander.Ground", tM
   get Entity.Spawn("Lander.Ground", 0, sCfg["cy"], kZ, sCfg["groundColor"])
   Mesh.Define "Lander.Pads", tPadM
   get Entity.Spawn("Lander.Pads", 0, sCfg["cy"], kZ, sCfg["padColor"])
end Lander.MakeGround

-- the ground's height under x (straight lines between the points)
function Lander.GroundY pX
   local i, tF
   repeat with i = 1 to sGroundN
      if pX <= sGround[i]["x"] then
         put (pX - sGround[i - 1]["x"]) / (sGround[i]["x"] - sGround[i - 1]["x"]) into tF
         return sGround[i - 1]["y"] + tF * (sGround[i]["y"] - sGround[i - 1]["y"])
      end if
   end repeat
   return sGround[sGroundN]["y"]
end Lander.GroundY

on Lander.NewCraft
   put (random(2001) - 1001) / 1000 * sCfg["hw"] * 0.6 into sMe["x"]
   put -sCfg["hh"] + 30 into sMe["y"]
   put sCfg["startVX"] * (random(3) - 2) into sMe["vx"]
   put 0 into sMe["vy"]
   put 0 into sMe["a"]
   put sCfg["fuel"] into sFuel
   put false into sLanded
   put 0 into sWaitT
   put empty into sAutoPad
   put Entity.Spawn("Lander.Me", sMe["x"], sCfg["cy"] + sMe["y"], kZ, sCfg["craftColor"]) into sMe["key"]
   put empty into sFlameKey
end Lander.NewCraft

on Game.OnUpdate
   local tKeys, tThrust, tTurn, tSide
   add 1 to sTick
   put Vec.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put 0 into sScore
         put sCfg["lives"] into sLives
         put false into sOver
         Lander.GoLevel 1
      end if
      Lander.ShowHUD
      exit Game.OnUpdate
   end if
   if sWaitT > 0 then
      subtract 1 from sWaitT
      if sWaitT = 0 then Lander.AfterWait
      Lander.ShowHUD
      exit Game.OnUpdate
   end if
   put 0 into tThrust
   put 0 into tTurn
   put 0 into tSide
   if sAuto is true then
      Lander.Autopilot tThrust, tTurn, tSide
   else
      -- up (or the fire key) burns; left and right turn the craft, or push it sideways
      if item 2 of Vec.Dir(sCfg["ctrl"], tKeys) < 0 or Vec.Fire(sCfg["ctrl"], tKeys) then put 1 into tThrust
      put item 1 of Vec.Dir(sCfg["ctrl"], tKeys) into tSide
      if sCfg["mode"] is "rotate" then
         put tSide into tTurn
         put 0 into tSide
      end if
   end if
   Lander.Fly tThrust, tTurn, tSide
   if sMsgT > 0 then subtract 1 from sMsgT
   Lander.ShowHUD
end Game.OnUpdate

on Lander.Fly pThrust, pTurn, pSide
   local tGround, tPad, k, tFoot
   if sFuel <= 0 then
      put 0 into pThrust
      put 0 into pSide
   end if
   add pTurn * sCfg["turn"] to sMe["a"]
   put Vec.Clamp(sMe["a"], -1.4, 1.4) into sMe["a"]
   if pThrust > 0 then
      add sin(sMe["a"]) * sCfg["thrust"] to sMe["vx"]
      subtract cos(sMe["a"]) * sCfg["thrust"] from sMe["vy"]
      subtract 1 from sFuel
   end if
   if pSide is not 0 then
      add pSide * sCfg["thrust"] * 0.5 to sMe["vx"]
      subtract 0.5 from sFuel
   end if
   add sGrav to sMe["vy"]
   add sWind to sMe["vx"]
   add sMe["vx"] to sMe["x"]
   add sMe["vy"] to sMe["y"]
   -- the sides: a wall of air pushes you back
   if abs(sMe["x"]) > sCfg["hw"] - sCfg["size"] then
      put Vec.Clamp(sMe["x"], -sCfg["hw"] + sCfg["size"], sCfg["hw"] - sCfg["size"]) into sMe["x"]
      put -sMe["vx"] * 0.3 into sMe["vx"]
   end if
   if sMe["y"] < -sCfg["hh"] + 10 then
      put -sCfg["hh"] + 10 into sMe["y"]
      put max(0, sMe["vy"]) into sMe["vy"]
   end if
   Entity.SetPosition sMe["key"], sMe["x"], sCfg["cy"] + sMe["y"], kZ
   Entity.SetRotation sMe["key"], 0, 0, sMe["a"]
   Lander.Flame pThrust > 0 or pSide is not 0
   -- the feet touch the ground?
   put sMe["y"] + sCfg["size"] / 2 into tFoot
   put Lander.GroundY(sMe["x"]) into tGround
   if tFoot < tGround then exit Lander.Fly
   put 0 into tPad
   -- on a pad: the middle of the craft over it, the legs may overhang a little
   repeat with k = 1 to sPadN
      if sMe["x"] - sCfg["size"] * 0.2 >= sPad[k]["x1"] and sMe["x"] + sCfg["size"] * 0.2 <= sPad[k]["x2"] then put k into tPad
   end repeat
   if tPad > 0 and sMe["vy"] <= sCfg["safe"] and abs(sMe["vx"]) <= sCfg["safe"] * 0.7 and abs(sMe["a"]) <= 0.25 then
      Lander.Landed tPad
   else
      Lander.Crash
   end if
end Lander.Fly

on Lander.Flame pOn
   if pOn then
      if sFlameKey is empty then put Entity.Spawn("Lander.Flame", sMe["x"], sCfg["cy"] + sMe["y"], kZ, sCfg["flameColor"]) into sFlameKey
      Entity.SetPosition sFlameKey, sMe["x"], sCfg["cy"] + sMe["y"], kZ
      Entity.SetRotation sFlameKey, 0, 0, sMe["a"]
   else if sFlameKey is not empty then
      Entity.Kill sFlameKey
      put empty into sFlameKey
   end if
end Lander.Flame

on Lander.Landed pPad
   local tGot
   Lander.Flame false
   put sPad[pPad]["y"] - sCfg["size"] / 2 into sMe["y"]
   put 0 into sMe["a"]
   Entity.SetPosition sMe["key"], sMe["x"], sCfg["cy"] + sMe["y"], kZ
   Entity.SetRotation sMe["key"], 0, 0, 0
   put sCfg["points"] * sPad[pPad]["times"] + round(sFuel) into tGot
   add tGot to sScore
   FX.Sparks sMe["x"], sCfg["cy"] + sPad[pPad]["y"], kZ, 12, sCfg["padColor"]
   put true into sLanded
   Sound.Play "Win"
   put 90 into sWaitT
   Lander.Say "LANDED. PAD X" & sPad[pPad]["times"] & ": +" & tGot, 90
end Lander.Landed

on Lander.Crash
   Lander.Flame false
   FX.Sparks sMe["x"], sCfg["cy"] + sMe["y"], kZ, 30, sCfg["craftColor"]
   Sound.Play "PlayerCrash"
   Entity.Kill sMe["key"]
   subtract 1 from sLives
   put false into sLanded
   put 70 into sWaitT
   Lander.Say "CRASHED", 70
end Lander.Crash

on Lander.AfterWait
   if sLanded then
      if sLevel >= sCfg["levels"] then
         put true into sOver
         put true into sWonAll
         put empty into sHUDWas
      else
         Lander.GoLevel sLevel + 1
      end if
      exit Lander.AfterWait
   end if
   if sLives <= 0 then
      put true into sOver
      Sound.Play "Lose"
      put false into sWonAll
      put empty into sHUDWas
      exit Lander.AfterWait
   end if
   Lander.NewCraft
end Lander.AfterWait

-- tests and the demo: pick the nearest pad, get over it, come down gently
on Lander.Autopilot @pThrust, @pTurn, @pSide
   local k, tBest, tD, tMid, dx, tWantVX, tWantVY, tAboveY, tAx, tWantA
   if sAutoPad is empty then
      put 99999 into tBest
      repeat with k = 1 to sPadN
         put abs((sPad[k]["x1"] + sPad[k]["x2"]) / 2 - sMe["x"]) into tD
         if tD < tBest then
            put tD into tBest
            put k into sAutoPad
         end if
      end repeat
   end if
   put (sPad[sAutoPad]["x1"] + sPad[sAutoPad]["x2"]) / 2 into tMid
   put tMid - sMe["x"] into dx
   put Vec.Clamp(dx / 40, -2, 2) into tWantVX
   put sPad[sAutoPad]["y"] - sCfg["size"] / 2 - sMe["y"] into tAboveY
   -- fall fast when high, slowly when low, hold height while not yet over the pad
   put Vec.Clamp(tAboveY / 60, 0.3, 2.5) into tWantVY
   if abs(dx) > (sPad[sAutoPad]["x2"] - sPad[sAutoPad]["x1"]) / 3 and tAboveY < 80 then put 0 into tWantVY
   put min(tWantVY, sCfg["safe"] * 0.6) into tWantVY
   if tAboveY > 60 then put Vec.Clamp(tAboveY / 60, 0.3, 2.5) into tWantVY
   if sCfg["mode"] is "rotate" then
      put Vec.Clamp((tWantVX - sMe["vx"]) * 0.6, -0.5, 0.5) into tWantA
      if tAboveY < 25 then put 0 into tWantA
      if sMe["a"] < tWantA - 0.03 then put 1 into pTurn
      if sMe["a"] > tWantA + 0.03 then put -1 into pTurn
      if sMe["vy"] > tWantVY or (abs(tWantA) > 0.2 and sMe["vy"] > tWantVY - 0.5) then put 1 into pThrust
      exit Lander.Autopilot
   end if
   if sMe["vx"] < tWantVX - 0.2 then put 1 into pSide
   if sMe["vx"] > tWantVX + 0.2 then put -1 into pSide
   if sMe["vy"] > tWantVY then put 1 into pThrust
end Lander.Autopilot

on Lander.TestAuto pOn
   put pOn into sAuto
end Lander.TestAuto

on Lander.Say pText, pSteps
   put pText into sMsg
   put pSteps into sMsgT
   put empty into sHUDWas
end Lander.Say

on Lander.ShowHUD
   local tWords
   put sLevel & "|" & sScore & "|" & sLives & "|" & round(sFuel / 10) & "|" & round(sMe["vy"] * 4) & "|" & sOver & "|" & (sMsgT > 0) into tWords
   if tWords is sHUDWas then exit Lander.ShowHUD
   put tWords into sHUDWas
   HUD.Set "Lander.Score", sCfg["title"] & "   SCORE" && sScore && "  CRAFT" && sLives && "  FUEL" && max(0, round(sFuel)) && "  LEVEL" && sLevel & "/" & sCfg["levels"], 20, 30, 14
   HUD.Set "Lander.Speed", "DOWN" && round(sMe["vy"] * 10) / 10 && "  ACROSS" && round(sMe["vx"] * 10) / 10 && "  SAFE BELOW" && sCfg["safe"], 20, 78, 11
   HUD.Remove "Lander.Msg"
   if sOver and sWonAll then
      HUD.Set "Lander.Msg", "EVERY LEVEL LANDED. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Lander.Msg", "GAME OVER. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sMsgT > 0 then
      HUD.Set "Lander.Msg", sMsg & "    " & sCfg["help"], 20, 56, 12
   end if
end Lander.ShowHUD

-- for tests: level|craft left|score|fuel|x,y|vx,vy|landed|over
function Lander.State
   return sLevel & "|" & sLives & "|" & sScore & "|" & round(sFuel) & "|" & round(sMe["x"]) & "," & round(sMe["y"]) & "|" & round(sMe["vx"], 2) & "," & round(sMe["vy"], 2) & "|" & sLanded & "|" & sOver
end Lander.State

on Game.OnStop
   HUD.Clear
end Game.OnStop

on arrowKey pKey
end arrowKey
