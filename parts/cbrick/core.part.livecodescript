## PART core (CBRICK): a brick breaker. A bat at the bottom, a wall of bricks at the top, balls
## between; the bottom is open. Break every brick to clear the level. Power-ups fall from broken
## bricks when the chain has Power-Up nodes. The builder adds Brick.Config (the node settings).

global bPaused, bPlaying

local sCfg, sRow, sPow, sPowN
local sCell, sLeft, sBall, sBallN, sBat, sDrop, sDropSeq
local sLevel, sLives, sScore, sOver, sWonAll, sServeT, sHUDWas, sSpeedNow, sWideT, sSlowT, sTick, sMsg, sMsgT, sAuto

constant kZ = 300

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Brick.Config
   put 0 into sScore
   put sCfg["lives"] into sLives
   put false into sOver
   Brick.StartLevel 1
end Game.OnStart

-- a level change through the loading screen (LIB_LOADING_SCREEN: burn, green text, the player first,
-- then the level draws in) when the host has it; else at once, as before. p1-13, 23 Nov 2026
on Brick.GoLevel pLevel
   if "LIB_LOADING" is among the lines of the stacksInUse then
      Loading.Go pLevel
   else
      Brick.StartLevel pLevel
   end if
end Brick.GoLevel

on Brick.StartLevel pLevel
   local tM, tPattern
   put pLevel into sLevel
   put sCfg["ballSpeed"] * (1 + sCfg["levelGain"] * (pLevel - 1)) into sSpeedNow
   put 0 into sWideT
   put 0 into sSlowT
   put empty into sDrop
   put empty into sCell
   put empty into sBall
   Scene.ClearAll
   Particles.Clear
   put Mesh.New() into tM
   Vec.Decor tM, sCfg["floor"], sCfg["hw"], sCfg["hh"], sCfg["grid"]
   if tM["count"] > 0 then
      Mesh.Define "Brick.Floor", tM
      get Entity.Spawn("Brick.Floor", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"])
   end if
   put Mesh.New() into tM
   Vec.Line tM, -sCfg["hw"], sCfg["hh"], -sCfg["hw"], -sCfg["hh"]
   Vec.Line tM, -sCfg["hw"], -sCfg["hh"], sCfg["hw"], -sCfg["hh"]
   Vec.Line tM, sCfg["hw"], -sCfg["hh"], sCfg["hw"], sCfg["hh"]
   Mesh.Define "Brick.Walls", tM
   get Entity.Spawn("Brick.Walls", 0, sCfg["cy"], kZ, sCfg["wallColor"])
   -- the bricks: one mesh for plain ones, one with a cross for tough ones
   put Mesh.New() into tM
   Vec.Rect tM, -sCfg["bw"] / 2, -sCfg["bh"] / 2, sCfg["bw"] / 2, sCfg["bh"] / 2
   Mesh.Define "Brick.Plain", tM
   Vec.Line tM, -sCfg["bw"] / 2, -sCfg["bh"] / 2, sCfg["bw"] / 2, sCfg["bh"] / 2
   Vec.Line tM, -sCfg["bw"] / 2, sCfg["bh"] / 2, sCfg["bw"] / 2, -sCfg["bh"] / 2
   Mesh.Define "Brick.Tough", tM
   put item ((pLevel - 1) mod the number of items of sCfg["patterns"] + 1) of sCfg["patterns"] into tPattern
   Brick.BuildWall tPattern
   -- the bat, plain and wide
   put Mesh.New() into tM
   Vec.Rect tM, -sCfg["batHalf"], -6, sCfg["batHalf"], 6
   Mesh.Define "Brick.Bat", tM
   put Mesh.New() into tM
   Vec.Rect tM, -sCfg["batHalf"] * 1.6, -6, sCfg["batHalf"] * 1.6, 6
   Vec.Line tM, -sCfg["batHalf"] * 1.6, 0, sCfg["batHalf"] * 1.6, 0
   Mesh.Define "Brick.BatWide", tM
   put sCfg["batHalf"] into sBat["half"]
   put 0 into sBat["x"]
   put sCfg["hh"] - 30 into sBat["y"]
   put Entity.Spawn("Brick.Bat", 0, sCfg["cy"] + sBat["y"], kZ, sCfg["batColor"]) into sBat["key"]
   Mesh.Define "Brick.Ball", Vec.Shape(sCfg["ballShape"], sCfg["ballSize"])
   Mesh.Define "Brick.Drop", Vec.Shape("capsule", 22)
   put 0 into sBallN
   Brick.AddBall
   Brick.Serve
   Brick.Say "LEVEL" && pLevel & ": " & toUpper(tPattern), 60
end Brick.StartLevel

-- a brick wanted at row pR, column pC in this pattern?
function Brick.Wants pPattern, pR, pC
   local tRows, tCols, tMid
   put sCfg["rows"] into tRows
   put sCfg["cols"] into tCols
   put (tCols + 1) / 2 into tMid
   switch pPattern
      case "checker"
         return (pR + pC) mod 2 = 0
      case "pyramid"
         return abs(pC - tMid) < pR * tCols / (2 * tRows) + 0.5
      case "columns"
         return pC mod 3 is not 0
      case "frame"
         return pR = 1 or pR = tRows or pC = 1 or pC = tCols
      case "holes"
         return random(100) > 25
      default
         return true
   end switch
end Brick.Wants

on Brick.BuildWall pPattern
   local r, c, tX, tY, tHP, tKey
   put 0 into sLeft
   if pPattern is "holes" then set the randomSeed to sCfg["seed"] + sLevel
   repeat with r = 1 to sCfg["rows"]
      repeat with c = 1 to sCfg["cols"]
         if not Brick.Wants(pPattern, r, c) then next repeat
         put Brick.CellX(c) into tX
         put Brick.CellY(r) into tY
         if r <= sCfg["tough"] then
            put 2 into tHP
            put Entity.Spawn("Brick.Tough", tX, sCfg["cy"] + tY, kZ, sRow[r]) into tKey
         else
            put 1 into tHP
            put Entity.Spawn("Brick.Plain", tX, sCfg["cy"] + tY, kZ, sRow[r]) into tKey
         end if
         put tKey into sCell[r][c]["key"]
         put tHP into sCell[r][c]["hp"]
         add 1 to sLeft
      end repeat
   end repeat
end Brick.BuildWall

function Brick.CellX pC
   return -sCfg["hw"] + sCfg["side"] + (pC - 0.5) * sCfg["pitchX"]
end Brick.CellX

function Brick.CellY pR
   return -sCfg["hh"] + sCfg["top"] + (pR - 0.5) * sCfg["pitchY"]
end Brick.CellY

on Brick.AddBall
   if sBallN >= 3 then exit Brick.AddBall
   add 1 to sBallN
   put true into sBall[sBallN]["live"]
   put sBat["x"] into sBall[sBallN]["x"]
   put sBat["y"] - 6 - sCfg["ballSize"] / 2 into sBall[sBallN]["y"]
   put 0 into sBall[sBallN]["dx"]
   put 0 into sBall[sBallN]["dy"]
   put Entity.Spawn("Brick.Ball", sBall[sBallN]["x"], sCfg["cy"] + sBall[sBallN]["y"], kZ, sCfg["ballColor"]) into sBall[sBallN]["key"]
end Brick.AddBall

-- the ball rests on the bat until Space (or a while passes)
on Brick.Serve
   put sCfg["serveWait"] into sServeT
   put empty into sHUDWas
end Brick.Serve

on Brick.Launch
   local i, tA
   put 0 into sServeT
   repeat with i = 1 to sBallN
      if not sBall[i]["live"] then next repeat
      if sBall[i]["dy"] is not 0 then next repeat
      put (random(61) - 31) / 100 into tA
      put sSpeedNow * sin(tA) into sBall[i]["dx"]
      put -sSpeedNow * cos(tA) into sBall[i]["dy"]
   end repeat
end Brick.Launch

on Game.OnUpdate
   local tKeys, i, tLive
   add 1 to sTick
   put Vec.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put 0 into sScore
         put sCfg["lives"] into sLives
         put false into sOver
         Brick.GoLevel 1
      end if
      Brick.ShowHUD
      exit Game.OnUpdate
   end if
   Brick.MoveBat tKeys
   if sWideT > 0 then
      subtract 1 from sWideT
      if sWideT = 0 then
         Entity.SetMesh sBat["key"], "Brick.Bat"
         put sCfg["batHalf"] into sBat["half"]
      end if
   end if
   if sSlowT > 0 then subtract 1 from sSlowT
   if sServeT > 0 then
      subtract 1 from sServeT
      if Vec.Fire(sCfg["ctrl"], tKeys) or sServeT = 0 then Brick.Launch
   end if
   put 0 into tLive
   repeat with i = 1 to sBallN
      if not sBall[i]["live"] then next repeat
      Brick.MoveBall i
      if sBall[i]["live"] then add 1 to tLive
      if sOver or sLeft = 0 then exit repeat
   end repeat
   Brick.MoveDrops
   if sLeft = 0 and not sOver then
      add sCfg["levelBonus"] * sLevel to sScore
      if sLevel >= sCfg["levels"] then
         put true into sOver
         put true into sWonAll
      else
         Brick.GoLevel sLevel + 1
      end if
   else if tLive = 0 and not sOver then
      Brick.LoseLife
   end if
   if sMsgT > 0 then subtract 1 from sMsgT
   Brick.ShowHUD
end Game.OnUpdate

on Brick.MoveBat pKeys
   local tDir, tM, tRoom, i
   put sCfg["hw"] - sBat["half"] into tRoom
   if sAuto is true then
      Brick.AutoBat
   else if sCfg["ctrl"] is "mouse" then
      put Vec.MousePoint(kZ) into tM
      if tM is not empty then
         put item 1 of tM into sBat["x"]
      end if
   else
      put item 1 of Vec.Dir(sCfg["ctrl"], pKeys) into tDir
      add tDir * sCfg["batSpeed"] to sBat["x"]
   end if
   put Vec.Clamp(sBat["x"], -tRoom, tRoom) into sBat["x"]
   Entity.SetPosition sBat["key"], sBat["x"], sCfg["cy"] + sBat["y"], kZ
   -- a ball waiting on the bat rides along
   repeat with i = 1 to sBallN
      if sBall[i]["live"] and sBall[i]["dy"] = 0 then
         put sBat["x"] into sBall[i]["x"]
         Brick.PlaceBall i
      end if
   end repeat
end Brick.MoveBat

-- tests (and a demo): the bat follows the lowest ball coming down, aiming a little off centre
on Brick.TestAuto pOn
   put pOn into sAuto
end Brick.TestAuto

on Brick.AutoBat
   local i, tBest, tY, tTarget, r, c, tAim, tGo, tDX, tDY
   put -9999 into tY
   repeat with i = 1 to sBallN
      if sBall[i]["live"] and sBall[i]["dy"] > 0 and sBall[i]["y"] > tY then
         put sBall[i]["y"] into tY
         put i into tBest
      end if
   end repeat
   if tBest is empty then exit Brick.AutoBat
   -- aim: the lowest brick still standing (the first found), hit where the bounce sends the ball at it
   repeat with r = sCfg["rows"] down to 1
      repeat with c = 1 to sCfg["cols"]
         if sCell[r][c]["hp"] is a number and sCell[r][c]["hp"] > 0 then
            put c & "," & r into tAim
            exit repeat
         end if
      end repeat
      if tAim is not empty then exit repeat
   end repeat
   put 0 into tGo
   if tAim is not empty then
      put Brick.CellX(item 1 of tAim) - sBall[tBest]["x"] into tDX
      put sBat["y"] - Brick.CellY(item 2 of tAim) into tDY
      -- the bounce angle is (where it lands on the bat / half the bat) * 1.05, 0 straight up
      put Vec.Clamp(atan2(tDX, tDY) / 1.05, -0.9, 0.9) * sBat["half"] into tGo
   end if
   put sBall[tBest]["x"] - tGo into tTarget
   add Vec.Clamp(tTarget - sBat["x"], -sCfg["batSpeed"] * 1.5, sCfg["batSpeed"] * 1.5) to sBat["x"]
end Brick.AutoBat

on Brick.PlaceBall pB
   Entity.SetPosition sBall[pB]["key"], sBall[pB]["x"], sCfg["cy"] + sBall[pB]["y"], kZ
end Brick.PlaceBall

on Brick.MoveBall pB
   local tR, tF, tOff, tSp, tA
   if sBall[pB]["dy"] = 0 then exit Brick.MoveBall
   put sCfg["ballSize"] / 2 into tR
   put 1 into tF
   if sSlowT > 0 then put 0.65 into tF
   put sBall[pB]["x"] into sBall[pB]["px"]
   put sBall[pB]["y"] into sBall[pB]["py"]
   add sBall[pB]["dx"] * tF to sBall[pB]["x"]
   add sBall[pB]["dy"] * tF to sBall[pB]["y"]
   -- walls
   if sBall[pB]["x"] < -sCfg["hw"] + tR then
      put -sCfg["hw"] + tR into sBall[pB]["x"]
      put abs(sBall[pB]["dx"]) into sBall[pB]["dx"]
   end if
   if sBall[pB]["x"] > sCfg["hw"] - tR then
      put sCfg["hw"] - tR into sBall[pB]["x"]
      put -abs(sBall[pB]["dx"]) into sBall[pB]["dx"]
   end if
   if sBall[pB]["y"] < -sCfg["hh"] + tR then
      put -sCfg["hh"] + tR into sBall[pB]["y"]
      put abs(sBall[pB]["dy"]) into sBall[pB]["dy"]
   end if
   -- the bat: only a ball coming down, landing on its top; where it lands sets the angle
   if sBall[pB]["dy"] > 0 and sBall[pB]["y"] + tR >= sBat["y"] - 6 and sBall[pB]["py"] + tR <= sBat["y"] - 6 + 1 then
      put sBall[pB]["x"] - sBat["x"] into tOff
      if abs(tOff) <= sBat["half"] + tR then
         put min(sCfg["ballMax"], sqrt(sBall[pB]["dx"] ^ 2 + sBall[pB]["dy"] ^ 2) * sCfg["ballGain"]) into tSp
         put Vec.Clamp(tOff / sBat["half"], -1, 1) * 1.05 into tA
         put tSp * sin(tA) into sBall[pB]["dx"]
         put -tSp * cos(tA) into sBall[pB]["dy"]
         put sBat["y"] - 6 - tR into sBall[pB]["y"]
         FX.Sparks sBall[pB]["x"], sCfg["cy"] + sBall[pB]["y"] + tR, kZ, 4, sCfg["batColor"]
      end if
   end if
   Brick.HitBricks pB, tR
   if sBall[pB]["y"] > sCfg["hh"] + 40 then
      put false into sBall[pB]["live"]
      Entity.Kill sBall[pB]["key"]
      exit Brick.MoveBall
   end if
   Brick.PlaceBall pB
end Brick.MoveBall

-- the bricks the ball's box touches; the first one hit turns it round and the step ends
on Brick.HitBricks pB, pR
   local r, c, r1, r2, c1, c2, tX, tY, tHX, tHY, tWasX, tWasY
   put sCfg["bw"] / 2 into tHX
   put sCfg["bh"] / 2 into tHY
   put floor((sBall[pB]["x"] - pR + sCfg["hw"] - sCfg["side"]) / sCfg["pitchX"]) + 1 into c1
   put floor((sBall[pB]["x"] + pR + sCfg["hw"] - sCfg["side"]) / sCfg["pitchX"]) + 1 into c2
   put floor((sBall[pB]["y"] - pR + sCfg["hh"] - sCfg["top"]) / sCfg["pitchY"]) + 1 into r1
   put floor((sBall[pB]["y"] + pR + sCfg["hh"] - sCfg["top"]) / sCfg["pitchY"]) + 1 into r2
   repeat with r = max(1, r1) to min(sCfg["rows"], r2)
      repeat with c = max(1, c1) to min(sCfg["cols"], c2)
         if sCell[r][c]["hp"] is not a number or sCell[r][c]["hp"] <= 0 then next repeat
         put Brick.CellX(c) into tX
         put Brick.CellY(r) into tY
         if abs(sBall[pB]["x"] - tX) > tHX + pR or abs(sBall[pB]["y"] - tY) > tHY + pR then next repeat
         -- which face: where the ball was a step ago
         put abs(sBall[pB]["px"] - tX) <= tHX + pR into tWasX
         put abs(sBall[pB]["py"] - tY) <= tHY + pR into tWasY
         if tWasX or not tWasY then
            put -sBall[pB]["dy"] into sBall[pB]["dy"]
            put sBall[pB]["py"] into sBall[pB]["y"]
         else
            put -sBall[pB]["dx"] into sBall[pB]["dx"]
            put sBall[pB]["px"] into sBall[pB]["x"]
         end if
         Brick.HitOne r, c
         exit Brick.HitBricks
      end repeat
   end repeat
end Brick.HitBricks

on Brick.HitOne pR, pC
   local tX, tY
   subtract 1 from sCell[pR][pC]["hp"]
   put Brick.CellX(pC) into tX
   put sCfg["cy"] + Brick.CellY(pR) into tY
   if sCell[pR][pC]["hp"] > 0 then
      Entity.SetMesh sCell[pR][pC]["key"], "Brick.Plain"
      FX.Sparks tX, tY, kZ, 3, sRow[pR]
      add sCfg["points"] to sScore
      exit Brick.HitOne
   end if
   Entity.Kill sCell[pR][pC]["key"]
   FX.Sparks tX, tY, kZ, 10, sRow[pR]
   add sCfg["points"] * sLevel to sScore
   subtract 1 from sLeft
   Brick.MaybeDrop tX, tY
end Brick.HitOne

-- a power-up may fall from a broken brick: the first kind whose chance comes up
on Brick.MaybeDrop pX, pY
   local i, n
   repeat with i = 1 to sPowN
      if random(1000) <= sPow[i]["chance"] * 1000 then
         add 1 to sDropSeq
         put sDropSeq into n
         put sPow[i]["kind"] into sDrop[n]["kind"]
         put pX into sDrop[n]["x"]
         put pY - sCfg["cy"] into sDrop[n]["y"]
         put Entity.Spawn("Brick.Drop", pX, pY, kZ, sPow[i]["color"]) into sDrop[n]["key"]
         exit Brick.MaybeDrop
      end if
   end repeat
end Brick.MaybeDrop

on Brick.MoveDrops
   local n, tKeys
   put the keys of sDrop into tKeys
   repeat for each line n in tKeys
      add 2.5 to sDrop[n]["y"]
      if abs(sDrop[n]["y"] - sBat["y"]) < 12 and abs(sDrop[n]["x"] - sBat["x"]) < sBat["half"] + 11 then
         Brick.TakePower sDrop[n]["kind"]
         Entity.Kill sDrop[n]["key"]
         delete variable sDrop[n]
      else if sDrop[n]["y"] > sCfg["hh"] + 20 then
         Entity.Kill sDrop[n]["key"]
         delete variable sDrop[n]
      else
         Entity.SetPosition sDrop[n]["key"], sDrop[n]["x"], sCfg["cy"] + sDrop[n]["y"], kZ
      end if
   end repeat
end Brick.MoveDrops

on Brick.TakePower pKind
   local i, tFrom, tA
   switch pKind
      case "wide"
         put 600 into sWideT
         put sCfg["batHalf"] * 1.6 into sBat["half"]
         Entity.SetMesh sBat["key"], "Brick.BatWide"
         Brick.Say "WIDE BAT", 50
         break
      case "multi"
         put 0 into tFrom
         repeat with i = 1 to sBallN
            if sBall[i]["live"] and sBall[i]["dy"] is not 0 then put i into tFrom
         end repeat
         repeat 2
            if tFrom = 0 or sBallN >= 3 then exit repeat
            Brick.AddBall
            put sBall[tFrom]["x"] into sBall[sBallN]["x"]
            put sBall[tFrom]["y"] into sBall[sBallN]["y"]
            put (random(121) - 61) / 100 into tA
            put sSpeedNow * sin(tA) into sBall[sBallN]["dx"]
            put -sSpeedNow * cos(tA) into sBall[sBallN]["dy"]
         end repeat
         Brick.Say "MORE BALLS", 50
         break
      case "slow"
         put 420 into sSlowT
         Brick.Say "SLOW BALL", 50
         break
      case "life"
         add 1 to sLives
         Brick.Say "EXTRA LIFE", 50
         break
   end switch
   add 25 to sScore
   put empty into sHUDWas
end Brick.TakePower

on Brick.LoseLife
   local n
   subtract 1 from sLives
   repeat for each key n in sDrop
      Entity.Kill sDrop[n]["key"]
   end repeat
   put empty into sDrop
   if sLives <= 0 then
      put true into sOver
      put false into sWonAll
      exit Brick.LoseLife
   end if
   put 0 into sBallN
   put empty into sBall
   if sWideT > 0 then
      put 0 into sWideT
      Entity.SetMesh sBat["key"], "Brick.Bat"
      put sCfg["batHalf"] into sBat["half"]
   end if
   Brick.AddBall
   Brick.Serve
   Brick.Say "BALL LOST", 50
end Brick.LoseLife

on Brick.Say pText, pSteps
   put pText into sMsg
   put pSteps into sMsgT
   put empty into sHUDWas
end Brick.Say

on Brick.ShowHUD
   local tWords
   put sLevel & "|" & sScore & "|" & sLives & "|" & (sServeT > 0) & "|" & sOver & "|" & (sMsgT > 0) into tWords
   if tWords is sHUDWas then exit Brick.ShowHUD
   put tWords into sHUDWas
   HUD.Set "Brick.Score", sCfg["title"] & "   SCORE" && sScore && "  LIVES" && sLives && "  LEVEL" && sLevel & "/" & sCfg["levels"], 20, 30, 14
   HUD.Remove "Brick.Msg"
   if sOver and sWonAll then
      HUD.Set "Brick.Msg", "EVERY WALL BROKEN. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Brick.Msg", "GAME OVER. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sMsgT > 0 then
      HUD.Set "Brick.Msg", sMsg, 20, 56, 12
   else if sServeT > 0 then
      HUD.Set "Brick.Msg", sCfg["help"], 20, 56, 12
   end if
end Brick.ShowHUD

-- for tests: level|lives|score|bricks left|balls in play|serving|over|first live ball x,y,dx,dy
function Brick.State
   local i, tLive, tBall
   put 0 into tLive
   repeat with i = 1 to sBallN
      if sBall[i]["live"] then
         add 1 to tLive
         if tBall is empty then put round(sBall[i]["x"]) & "," & round(sBall[i]["y"]) & "," & round(sBall[i]["dx"], 2) & "," & round(sBall[i]["dy"], 2) into tBall
      end if
   end repeat
   return sLevel & "|" & sLives & "|" & sScore & "|" & sLeft & "|" & tLive & "|" & (sServeT > 0) & "|" & sOver & "|" & tBall
end Brick.State

on Game.OnStop
   HUD.Clear
end Game.OnStop

on arrowKey pKey
end arrowKey
