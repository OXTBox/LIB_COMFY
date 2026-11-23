## PART core (CDODGE): a lane dodger. You run along the bottom; hazards pour down the arena and
## pickups with them. Last the level's distance to go on; each level is faster. Hazard and
## Pickup kinds come from their nodes. The builder adds Dodge.Config.

global bPaused, bPlaying

local sCfg, sHaz, sHazN, sPick, sPickN
local sMe, sThing, sSeq, sDist, sSpeedNow, sShieldT, sSlowT, sLaneT, sScroll, sScrollStep, sFloorKey
local sLevel, sLives, sScore, sOver, sWonAll, sHUDWas, sTick, sMsg, sMsgT, sAuto, sHurtT

constant kZ = 300

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Dodge.Config
   put 0 into sScore
   put sCfg["lives"] into sLives
   put false into sOver
   Dodge.StartLevel 1
end Game.OnStart

-- a level change through the loading screen (LIB_LOADING_SCREEN: burn, green text, the player first,
-- then the level draws in) when the host has it; else at once, as before. p1-13, 23 Nov 2026
on Dodge.GoLevel pLevel
   if "LIB_LOADING" is among the lines of the stacksInUse then
      Loading.Go pLevel
   else
      Dodge.StartLevel pLevel
   end if
end Dodge.GoLevel

on Dodge.StartLevel pLevel
   local tM, k, tLaneW
   put pLevel into sLevel
   Scene.ClearAll
   Particles.Clear
   put empty into sThing
   put 0 into sDist
   put 0 into sShieldT
   put 0 into sSlowT
   put 0 into sHurtT
   put 0 into sScroll
   put 1 + sCfg["levelGain"] * (pLevel - 1) into sSpeedNow
   -- the floor scrolls: a strip twice as tall as one floor step, moved down and wrapped
   put Mesh.New() into tM
   if sCfg["lanes"] > 1 then
      put sCfg["hw"] * 2 / sCfg["lanes"] into tLaneW
      Vec.Decor tM, "lanes", sCfg["hw"], sCfg["hh"] + tLaneW, tLaneW
      -- the dashes repeat every two thirds of a lane's width: scroll by that and wrap
      put max(16, tLaneW) * 2 / 3 into sScrollStep
   else
      Vec.Decor tM, sCfg["floor"], sCfg["hw"], sCfg["hh"] + sCfg["grid"], sCfg["grid"]
      put 0 into sScrollStep
      if sCfg["floor"] is among the items of "grid,dots" then put max(16, sCfg["grid"]) into sScrollStep
   end if
   if tM["count"] > 0 then
      Mesh.Define "Dodge.Floor", tM
      put Entity.Spawn("Dodge.Floor", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"]) into sFloorKey
   else
      put empty into sFloorKey
   end if
   put Mesh.New() into tM
   Vec.Line tM, -sCfg["hw"], -sCfg["hh"], -sCfg["hw"], sCfg["hh"]
   Vec.Line tM, sCfg["hw"], -sCfg["hh"], sCfg["hw"], sCfg["hh"]
   Mesh.Define "Dodge.Sides", tM
   get Entity.Spawn("Dodge.Sides", 0, sCfg["cy"], kZ, sCfg["wallColor"])
   Mesh.Define "Dodge.Me", Vec.Shape(sCfg["meShape"], sCfg["meSize"])
   put Mesh.New() into tM
   Vec.Ring tM, 0, 0, sCfg["meSize"] * 0.8, 14
   Mesh.Define "Dodge.Bubble", tM
   repeat with k = 1 to sHazN
      Mesh.Define "Dodge.Haz" & k, Vec.Shape(sHaz[k]["shape"], sHaz[k]["size"])
   end repeat
   repeat with k = 1 to sPickN
      Mesh.Define "Dodge.Pick" & k, Vec.Shape(sPick[k]["shape"], 18)
   end repeat
   put sCfg["hh"] - 34 into sMe["y"]
   put Dodge.LaneX(round((sCfg["lanes"] + 1) / 2)) into sMe["x"]
   if sCfg["lanes"] <= 1 then put 0 into sMe["x"]
   put sMe["x"] into sMe["tx"]
   put Entity.Spawn("Dodge.Me", sMe["x"], sCfg["cy"] + sMe["y"], kZ, sCfg["meColor"]) into sMe["key"]
   put empty into sMe["bubble"]
   Dodge.Say "LEVEL" && pLevel & ": GO" && sCfg["distance"] && "STEPS", 70
end Dodge.StartLevel

function Dodge.LaneX pLane
   if sCfg["lanes"] <= 1 then return 0
   return -sCfg["hw"] + (pLane - 0.5) * sCfg["hw"] * 2 / sCfg["lanes"]
end Dodge.LaneX

function Dodge.LaneOf pX
   return Vec.Clamp(floor((pX + sCfg["hw"]) / (sCfg["hw"] * 2 / sCfg["lanes"])) + 1, 1, sCfg["lanes"])
end Dodge.LaneOf

on Game.OnUpdate
   local tKeys, tF
   add 1 to sTick
   put Vec.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put 0 into sScore
         put sCfg["lives"] into sLives
         put false into sOver
         Dodge.GoLevel 1
      end if
      Dodge.ShowHUD
      exit Game.OnUpdate
   end if
   put sSpeedNow into tF
   if sSlowT > 0 then
      subtract 1 from sSlowT
      put tF * 0.55 into tF
   end if
   Dodge.MoveMe tKeys
   Dodge.Spawn tF
   Dodge.MoveThings tF
   Dodge.ScrollFloor tF
   if sShieldT > 0 then subtract 1 from sShieldT
   if sHurtT > 0 then subtract 1 from sHurtT
   Dodge.Bubble
   add 1 to sDist
   if sTick mod 10 = 0 then add sLevel to sScore
   if sDist >= sCfg["distance"] and not sOver then
      add 100 * sLevel to sScore
      if sLevel >= sCfg["levels"] then
         put true into sOver
         put true into sWonAll
         put empty into sHUDWas
      else
         Dodge.GoLevel sLevel + 1
      end if
   end if
   if sMsgT > 0 then subtract 1 from sMsgT
   Dodge.ShowHUD
end Game.OnUpdate

-- lanes: a press moves one lane (held: one lane every few steps); free: slide
on Dodge.MoveMe pKeys
   local tD, tM, tLane
   if sAuto is true then
      put Dodge.AutoX() into tM
      if sCfg["lanes"] > 1 then
         put Dodge.LaneX(Dodge.LaneOf(tM)) into sMe["tx"]
      else
         put tM into sMe["tx"]
      end if
   else if sCfg["ctrl"] is "mouse" then
      put Vec.MousePoint(kZ) into tM
      if tM is not empty then
         if sCfg["lanes"] > 1 then
            put Dodge.LaneX(Dodge.LaneOf(item 1 of tM)) into sMe["tx"]
         else
            put item 1 of tM into sMe["tx"]
         end if
      end if
   else
      put item 1 of Vec.Dir(sCfg["ctrl"], pKeys) into tD
      if sCfg["lanes"] > 1 then
         if sLaneT > 0 then subtract 1 from sLaneT
         if tD = 0 then put 0 into sLaneT
         if tD is not 0 and sLaneT = 0 then
            put Vec.Clamp(Dodge.LaneOf(sMe["tx"]) + tD, 1, sCfg["lanes"]) into tLane
            put Dodge.LaneX(tLane) into sMe["tx"]
            put 8 into sLaneT
         end if
      else
         put sMe["x"] + tD * sCfg["meSpeed"] into sMe["tx"]
      end if
   end if
   put Vec.Clamp(sMe["tx"], -sCfg["hw"] + sCfg["meSize"] / 2, sCfg["hw"] - sCfg["meSize"] / 2) into sMe["tx"]
   add Vec.Clamp(sMe["tx"] - sMe["x"], -sCfg["meSpeed"], sCfg["meSpeed"]) to sMe["x"]
   Entity.SetPosition sMe["key"], sMe["x"], sCfg["cy"] + sMe["y"], kZ
   Entity.SetRotation sMe["key"], 0, 0, Vec.Clamp((sMe["tx"] - sMe["x"]) / 60, -0.4, 0.4)
end Dodge.MoveMe

-- each hazard and pickup kind rolls its own chance every step
on Dodge.Spawn pF
   local k, tX
   repeat with k = 1 to sHazN
      if random(100000) <= sHaz[k]["rate"] * pF * 100000 then
         if sCfg["lanes"] > 1 and sHaz[k]["inLane"] then
            put Dodge.LaneX(random(sCfg["lanes"])) into tX
         else
            put (random(2001) - 1001) / 1000 * (sCfg["hw"] - sHaz[k]["size"] / 2) into tX
         end if
         Dodge.AddThing "haz", k, tX, "Dodge.Haz" & k, sHaz[k]["color"], sHaz[k]["size"]
      end if
   end repeat
   repeat with k = 1 to sPickN
      if random(100000) <= sPick[k]["rate"] * 100000 then
         if sCfg["lanes"] > 1 then
            put Dodge.LaneX(random(sCfg["lanes"])) into tX
         else
            put (random(2001) - 1001) / 1000 * (sCfg["hw"] - 12) into tX
         end if
         Dodge.AddThing "pick", k, tX, "Dodge.Pick" & k, sPick[k]["color"], 18
      end if
   end repeat
end Dodge.Spawn

on Dodge.AddThing pWhat, pK, pX, pMesh, pColor, pSize
   add 1 to sSeq
   put pWhat into sThing[sSeq]["what"]
   put pK into sThing[sSeq]["k"]
   put pX into sThing[sSeq]["x"]
   put pX into sThing[sSeq]["x0"]
   put -sCfg["hh"] - pSize into sThing[sSeq]["y"]
   put pSize into sThing[sSeq]["size"]
   put random(628) / 100 into sThing[sSeq]["ph"]
   put Entity.Spawn(pMesh, pX, sCfg["cy"] + sThing[sSeq]["y"], kZ, pColor) into sThing[sSeq]["key"]
   if pWhat is "haz" and sHaz[pK]["spin"] then Entity.SetRotationSpeed sThing[sSeq]["key"], 0, 0, 0.05
end Dodge.AddThing

on Dodge.MoveThings pF
   local tSeq, tSeqs, k, tR, tSpeed
   put the keys of sThing into tSeqs
   repeat for each line tSeq in tSeqs
      put sThing[tSeq]["k"] into k
      if sThing[tSeq]["what"] is "haz" then
         put sHaz[k]["speed"] * pF into tSpeed
         if sHaz[k]["wobble"] > 0 then
            put sThing[tSeq]["x0"] + sHaz[k]["wobble"] * sin(sThing[tSeq]["y"] / 40 + sThing[tSeq]["ph"]) into sThing[tSeq]["x"]
         end if
      else
         put sCfg["pickSpeed"] * pF into tSpeed
      end if
      add tSpeed to sThing[tSeq]["y"]
      if sThing[tSeq]["y"] > sCfg["hh"] + sThing[tSeq]["size"] then
         if sThing[tSeq]["what"] is "haz" then add sHaz[k]["points"] to sScore
         Dodge.Drop tSeq
         next repeat
      end if
      put (sThing[tSeq]["size"] + sCfg["meSize"]) * 0.4 into tR
      if abs(sThing[tSeq]["x"] - sMe["x"]) < tR and abs(sThing[tSeq]["y"] - sMe["y"]) < tR then
         if sThing[tSeq]["what"] is "pick" then
            Dodge.Take k
            Dodge.Drop tSeq
            next repeat
         end if
         if sShieldT = 0 and sHurtT = 0 then
            FX.Sparks sThing[tSeq]["x"], sCfg["cy"] + sThing[tSeq]["y"], kZ, 20, sHaz[k]["color"]
            Dodge.Drop tSeq
            Dodge.Hurt
            if sOver then exit Dodge.MoveThings
            next repeat
         end if
      end if
      Entity.SetPosition sThing[tSeq]["key"], sThing[tSeq]["x"], sCfg["cy"] + sThing[tSeq]["y"], kZ
   end repeat
end Dodge.MoveThings

on Dodge.Drop pSeq
   Entity.Kill sThing[pSeq]["key"]
   delete variable sThing[pSeq]
end Dodge.Drop

on Dodge.Take pK
   FX.Sparks sMe["x"], sCfg["cy"] + sMe["y"], kZ, 8, sPick[pK]["color"]
   add sPick[pK]["points"] to sScore
   switch sPick[pK]["kind"]
      case "shield"
         put 300 into sShieldT
         Dodge.Say "SHIELD", 40
         break
      case "slow"
         put 240 into sSlowT
         Dodge.Say "SLOW TIME", 40
         break
      case "life"
         add 1 to sLives
         Dodge.Say "EXTRA LIFE", 40
         break
   end switch
   put empty into sHUDWas
end Dodge.Take

on Dodge.Hurt
   Sound.Play "boom"
   subtract 1 from sLives
   put empty into sHUDWas
   if sLives <= 0 then
      put true into sOver
      put false into sWonAll
      exit Dodge.Hurt
   end if
   put 60 into sHurtT
   Dodge.Say "HIT", 40
end Dodge.Hurt

-- a ring round you while a shield (or the moment after a hit) protects you
on Dodge.Bubble
   if sShieldT > 0 or sHurtT > 0 then
      if sMe["bubble"] is empty then put Entity.Spawn("Dodge.Bubble", sMe["x"], sCfg["cy"] + sMe["y"], kZ, sCfg["meColor"]) into sMe["bubble"]
      Entity.SetPosition sMe["bubble"], sMe["x"], sCfg["cy"] + sMe["y"], kZ
   else if sMe["bubble"] is not empty then
      Entity.Kill sMe["bubble"]
      put empty into sMe["bubble"]
   end if
end Dodge.Bubble

on Dodge.ScrollFloor pF
   if sFloorKey is empty or sScrollStep <= 0 then exit Dodge.ScrollFloor
   add sCfg["scroll"] * pF to sScroll
   put sScroll mod sScrollStep into sScroll
   Entity.SetPosition sFloorKey, 0, sCfg["cy"] + sScroll - sScrollStep / 2, kZ + 1
end Dodge.ScrollFloor

-- tests and the demo: the x along the bottom with the most room from what is coming down
function Dodge.AutoX
   local tTry, tX, tBest, tBestScore, tSeq, tScore, dy, tGap
   put -99999 into tBestScore
   put sMe["x"] into tBest
   repeat with tTry = 0 to 20
      -- with lanes only the middles of the lanes are places to be
      if sCfg["lanes"] > 1 then
         if tTry >= sCfg["lanes"] then exit repeat
         put Dodge.LaneX(tTry + 1) into tX
      else
         put -sCfg["hw"] + sCfg["meSize"] + tTry * (sCfg["hw"] * 2 - sCfg["meSize"] * 2) / 20 into tX
      end if
      put 0 - abs(tX - sMe["x"]) / 50 into tScore
      repeat for each key tSeq in sThing
         put sMe["y"] - sThing[tSeq]["y"] into dy
         if dy < -20 or dy > 260 then next repeat
         put abs(sThing[tSeq]["x"] - tX) into tGap
         if sThing[tSeq]["what"] is "pick" then
            if tGap < 30 then
               add 3 to tScore
            end if
         else if tGap < (sThing[tSeq]["size"] + sCfg["meSize"]) * 0.6 + 10 then
            subtract 100 - dy / 4 from tScore
         end if
      end repeat
      if tScore > tBestScore then
         put tScore into tBestScore
         put tX into tBest
      end if
   end repeat
   return tBest
end Dodge.AutoX

on Dodge.TestAuto pOn
   put pOn into sAuto
end Dodge.TestAuto

on Dodge.Say pText, pSteps
   put pText into sMsg
   put pSteps into sMsgT
   put empty into sHUDWas
end Dodge.Say

on Dodge.ShowHUD
   local tWords, tLeft
   put max(0, sCfg["distance"] - sDist) into tLeft
   put sLevel & "|" & sScore & "|" & sLives & "|" & (tLeft div 30) & "|" & sOver & "|" & (sMsgT > 0) into tWords
   if tWords is sHUDWas then exit Dodge.ShowHUD
   put tWords into sHUDWas
   HUD.Set "Dodge.Score", sCfg["title"] & "   SCORE" && sScore && "  LIVES" && sLives && "  TO GO" && tLeft && "  LEVEL" && sLevel & "/" & sCfg["levels"], 20, 30, 14
   HUD.Remove "Dodge.Msg"
   if sOver and sWonAll then
      HUD.Set "Dodge.Msg", "ALL THE WAY. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Dodge.Msg", "GAME OVER. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sMsgT > 0 then
      HUD.Set "Dodge.Msg", sMsg & "    " & sCfg["help"], 20, 56, 12
   end if
end Dodge.ShowHUD

-- for tests: level|lives|score|distance|things falling|over|x
function Dodge.State
   local tN, tKeys
   put the keys of sThing into tKeys
   put the number of lines of tKeys into tN
   return sLevel & "|" & sLives & "|" & sScore & "|" & sDist & "|" & tN & "|" & sOver & "|" & round(sMe["x"])
end Dodge.State

on Game.OnStop
   HUD.Clear
end Game.OnStop

on arrowKey pKey
end arrowKey
