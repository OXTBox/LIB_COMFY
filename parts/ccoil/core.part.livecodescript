## PART core (CCOIL): a grid worm. The worm moves one cell every few steps; food makes it longer;
## its own body, the obstacles and (unless the edges wrap) the walls end a life. Eat enough to
## clear the level. Food kinds come from the Food nodes. The builder adds Coil.Config.

global bPaused, bPlaying

local sCfg, sFood, sFoodN
local sOcc, sBody, sKeys, sDir, sNextDir, sWait, sGrow, sStepNow, sSlowT, sEaten, sOnBoard, sSeq
local sLevel, sLives, sScore, sOver, sWonAll, sHUDWas, sTick, sMsg, sMsgT, sAuto, sDeadT

constant kZ = 300

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Coil.Config
   put 0 into sScore
   put sCfg["lives"] into sLives
   put false into sOver
   Coil.StartLevel 1
end Game.OnStart

function Coil.X pC
   return (pC - (sCfg["cols"] + 1) / 2) * sCfg["cell"]
end Coil.X

function Coil.Y pR
   return (pR - (sCfg["rows"] + 1) / 2) * sCfg["cell"]
end Coil.Y

-- a level change through the loading screen (LIB_LOADING_SCREEN: burn, green text, the player first,
-- then the level draws in) when the host has it; else at once, as before. p1-13, 23 Nov 2026
on Coil.GoLevel pLevel
   if "LIB_LOADING" is among the lines of the stacksInUse then
      Loading.Go pLevel
   else
      Coil.StartLevel pLevel
   end if
end Coil.GoLevel

on Coil.StartLevel pLevel
   local tM, tHW, tHH, k, i, tCell
   put pLevel into sLevel
   Scene.ClearAll
   Particles.Clear
   put empty into sOcc
   put empty into sOnBoard
   put 0 into sEaten
   put 0 into sSlowT
   put max(sCfg["minStep"], sCfg["stepFrames"] - sCfg["levelGain"] * (pLevel - 1)) into sStepNow
   put sCfg["cols"] * sCfg["cell"] / 2 into tHW
   put sCfg["rows"] * sCfg["cell"] / 2 into tHH
   put Mesh.New() into tM
   Vec.Decor tM, sCfg["floor"], tHW, tHH, sCfg["cell"]
   if tM["count"] > 0 then
      Mesh.Define "Coil.Floor", tM
      get Entity.Spawn("Coil.Floor", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"])
   end if
   put Mesh.New() into tM
   Vec.Rect tM, -tHW, -tHH, tHW, tHH
   if sCfg["wrap"] then
      -- open edges: gaps in the middle of each side show the way through
      put Mesh.New() into tM
      Vec.Line tM, -tHW, -tHH, -tHW * 0.3, -tHH
      Vec.Line tM, tHW * 0.3, -tHH, tHW, -tHH
      Vec.Line tM, -tHW, tHH, -tHW * 0.3, tHH
      Vec.Line tM, tHW * 0.3, tHH, tHW, tHH
      Vec.Line tM, -tHW, -tHH, -tHW, -tHH * 0.3
      Vec.Line tM, -tHW, tHH * 0.3, -tHW, tHH
      Vec.Line tM, tHW, -tHH, tHW, -tHH * 0.3
      Vec.Line tM, tHW, tHH * 0.3, tHW, tHH
   end if
   Mesh.Define "Coil.Walls", tM
   get Entity.Spawn("Coil.Walls", 0, sCfg["cy"], kZ, sCfg["wallColor"])
   put sCfg["cell"] - 3 into tCell
   put Mesh.New() into tM
   Vec.Rect tM, -tCell / 2, -tCell / 2, tCell / 2, tCell / 2
   Mesh.Define "Coil.Seg", tM
   Mesh.Define "Coil.Head", Vec.Shape(sCfg["headShape"], tCell + 2)
   put Mesh.New() into tM
   Vec.Rect tM, -tCell / 2, -tCell / 2, tCell / 2, tCell / 2
   Vec.Line tM, -tCell / 2, -tCell / 2, tCell / 2, tCell / 2
   Vec.Line tM, -tCell / 2, tCell / 2, tCell / 2, -tCell / 2
   Mesh.Define "Coil.Block", tM
   repeat with k = 1 to sFoodN
      Mesh.Define "Coil.Food" & k, Vec.Shape(sFood[k]["shape"], tCell)
   end repeat
   Coil.Obstacles
   Coil.PlaceWorm
   repeat with k = 1 to sFoodN
      repeat sFood[k]["count"]
         Coil.AddFood k
      end repeat
   end repeat
   Coil.Say "LEVEL" && pLevel & ": EAT" && Coil.Target(), 70
end Coil.StartLevel

function Coil.Target
   return sCfg["target"] + sCfg["targetGain"] * (sLevel - 1)
end Coil.Target

-- blocks on the board, more each level; never on the worm's start row
on Coil.Obstacles
   local n, c, r, tTries, tMid, i
   set the randomSeed to sCfg["seed"] + sLevel
   put sCfg["blocks"] + sCfg["blocksGain"] * (sLevel - 1) into n
   put round((sCfg["rows"] + 1) / 2) into tMid
   switch sCfg["blockStyle"]
      case "bars"
         repeat with i = 1 to min(n, sCfg["rows"] div 4)
            put i * 4 - 1 into r
            if r = tMid then next repeat
            repeat with c = 3 + (i mod 2) * 3 to sCfg["cols"] - 3 - ((i + 1) mod 2) * 3
               Coil.Block c, r
            end repeat
         end repeat
         break
      case "box"
         if n > 0 then
            repeat with c = 4 to sCfg["cols"] - 3
               if abs(c - (sCfg["cols"] + 1) / 2) < 2 then next repeat
               Coil.Block c, 3
               Coil.Block c, sCfg["rows"] - 2
            end repeat
            repeat with r = 4 to sCfg["rows"] - 3
               if abs(r - tMid) < 2 then next repeat
               Coil.Block 3, r
               Coil.Block sCfg["cols"] - 2, r
            end repeat
         end if
         break
      default
         repeat n
            put 0 into tTries
            repeat until tTries > 50
               add 1 to tTries
               put random(sCfg["cols"]) into c
               put random(sCfg["rows"]) into r
               if r = tMid or sOcc[c & "," & r] is not empty then next repeat
               Coil.Block c, r
               exit repeat
            end repeat
         end repeat
   end switch
end Coil.Obstacles

on Coil.Block pC, pR
   if pC < 1 or pR < 1 or pC > sCfg["cols"] or pR > sCfg["rows"] then exit Coil.Block
   if sOcc[pC & "," & pR] is not empty then exit Coil.Block
   put "x" into sOcc[pC & "," & pR]
   get Entity.Spawn("Coil.Block", Coil.X(pC), sCfg["cy"] + Coil.Y(pR), kZ, sCfg["blockColor"])
end Coil.Block

-- the worm starts in the middle row heading right, its tail to the left
on Coil.PlaceWorm
   local i, c, r, tKey
   put empty into sBody
   put empty into sKeys
   put round((sCfg["rows"] + 1) / 2) into r
   put max(sCfg["length"] + 1, round(sCfg["cols"] / 3)) into c
   repeat with i = 0 to sCfg["length"] - 1
      if sOcc[(c - i) & "," & r] is "x" then exit repeat
      put (c - i) & "," & r & cr after sBody
      if i = 0 then
         put Entity.Spawn("Coil.Head", Coil.X(c - i), sCfg["cy"] + Coil.Y(r), kZ, sCfg["wormColor"]) into tKey
      else
         put Entity.Spawn("Coil.Seg", Coil.X(c - i), sCfg["cy"] + Coil.Y(r), kZ, sCfg["wormColor"]) into tKey
      end if
      put tKey & cr after sKeys
      put "w" into sOcc[(c - i) & "," & r]
   end repeat
   delete the last char of sBody
   delete the last char of sKeys
   put "1,0" into sDir
   put "1,0" into sNextDir
   put 0 into sGrow
   put sStepNow into sWait
   Coil.TurnHead
end Coil.PlaceWorm

on Coil.AddFood pK
   local c, r, tTries
   repeat with tTries = 1 to 200
      put random(sCfg["cols"]) into c
      put random(sCfg["rows"]) into r
      if sOcc[c & "," & r] is empty then exit repeat
   end repeat
   if sOcc[c & "," & r] is not empty then exit Coil.AddFood
   add 1 to sSeq
   put "f" & sSeq into sOcc[c & "," & r]
   put pK into sOnBoard[sSeq]["kind"]
   put c & "," & r into sOnBoard[sSeq]["at"]
   put sFood[pK]["life"] into sOnBoard[sSeq]["life"]
   put Entity.Spawn("Coil.Food" & pK, Coil.X(c), sCfg["cy"] + Coil.Y(r), kZ, sFood[pK]["color"]) into sOnBoard[sSeq]["key"]
   if sFood[pK]["kind"] is "gold" then Entity.SetRotationSpeed sOnBoard[sSeq]["key"], 0, 0, 0.08
end Coil.AddFood

on Game.OnUpdate
   local tKeys, tD
   add 1 to sTick
   put Vec.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put 0 into sScore
         put sCfg["lives"] into sLives
         put false into sOver
         Coil.GoLevel 1
      end if
      Coil.ShowHUD
      exit Game.OnUpdate
   end if
   if sDeadT > 0 then
      subtract 1 from sDeadT
      if sDeadT = 0 then
         Coil.StartLevel sLevel
      end if
      Coil.ShowHUD
      exit Game.OnUpdate
   end if
   -- the next turn: never straight back
   if sAuto is true then
      put Coil.AutoDir() into tD
   else
      put Vec.Dir(sCfg["ctrl"], tKeys) into tD
      if item 1 of tD is not 0 and item 2 of tD is not 0 then put 0 into item 2 of tD
   end if
   if tD is not "0,0" and (item 1 of tD is not -item 1 of sDir or item 2 of tD is not -item 2 of sDir) then put tD into sNextDir
   Coil.FoodClock
   if sSlowT > 0 then subtract 1 from sSlowT
   subtract 1 from sWait
   if sWait <= 0 then
      put sStepNow into sWait
      if sSlowT > 0 then add 3 to sWait
      Coil.Step
   end if
   if sMsgT > 0 then subtract 1 from sMsgT
   Coil.ShowHUD
end Game.OnUpdate

-- the worm moves one cell
on Coil.Step
   local tHead, c, r, tWhat, tTail, tKey
   put sNextDir into sDir
   put line 1 of sBody into tHead
   put item 1 of tHead + item 1 of sDir into c
   put item 2 of tHead + item 2 of sDir into r
   if sCfg["wrap"] then
      put Coil.Wrap(c, sCfg["cols"]) into c
      put Coil.Wrap(r, sCfg["rows"]) into r
   else if c < 1 or r < 1 or c > sCfg["cols"] or r > sCfg["rows"] then
      Coil.Die
      exit Coil.Step
   end if
   put sOcc[c & "," & r] into tWhat
   -- the tail leaves its cell this step unless the worm is growing
   put the last line of sBody into tTail
   if tWhat is "x" or (tWhat is "w" and (c & "," & r is not tTail or sGrow > 0)) then
      Coil.Die
      exit Coil.Step
   end if
   if char 1 of tWhat is "f" then Coil.Eat char 2 to -1 of tWhat
   -- the old head becomes a body segment
   Entity.SetMesh line 1 of sKeys, "Coil.Seg"
   if sGrow > 0 then
      subtract 1 from sGrow
      put Entity.Spawn("Coil.Head", Coil.X(c), sCfg["cy"] + Coil.Y(r), kZ, sCfg["wormColor"]) into tKey
      put c & "," & r & cr before sBody
      put tKey & cr before sKeys
   else
      -- the tail's entity becomes the new head
      put the last line of sKeys into tKey
      if sOcc[tTail] is "w" then put empty into sOcc[tTail]
      delete the last line of sBody
      delete the last line of sKeys
      Entity.SetMesh tKey, "Coil.Head"
      Entity.SetPosition tKey, Coil.X(c), sCfg["cy"] + Coil.Y(r), kZ
      put c & "," & r & cr before sBody
      put tKey & cr before sKeys
   end if
   if the last char of sBody is cr then delete the last char of sBody
   if the last char of sKeys is cr then delete the last char of sKeys
   put "w" into sOcc[c & "," & r]
   Coil.TurnHead
   if sEaten >= Coil.Target() then Coil.LevelDone
end Coil.Step

-- the head points the way it goes. (One colour for the whole worm: an entity keeps the colour it
-- was spawned with, and the tail's entity is reused as the new head; the head shows by its shape.)
on Coil.TurnHead
   local tA
   switch sDir
      case "1,0"
         put pi / 2 into tA
         break
      case "-1,0"
         put -pi / 2 into tA
         break
      case "0,1"
         put pi into tA
         break
      default
         put 0 into tA
   end switch
   Entity.SetRotation line 1 of sKeys, 0, 0, tA
end Coil.TurnHead

on Coil.Eat pSeq
   local k, tAt
   put sOnBoard[pSeq]["kind"] into k
   put sOnBoard[pSeq]["at"] into tAt
   Entity.Kill sOnBoard[pSeq]["key"]
   delete variable sOnBoard[pSeq]
   put empty into sOcc[tAt]
   FX.Sparks Coil.X(item 1 of tAt), sCfg["cy"] + Coil.Y(item 2 of tAt), kZ, 8, sFood[k]["color"]
   add sFood[k]["points"] * sLevel to sScore
   Sound.Play "Pickup"
   add 1 to sEaten
   switch sFood[k]["kind"]
      case "shrink"
         Coil.Shrink 2
         break
      case "slow"
         put 240 into sSlowT
         add sFood[k]["grow"] to sGrow
         break
      default
         add sFood[k]["grow"] to sGrow
   end switch
   if sCfg["speedUp"] > 0 then put max(sCfg["minStep"], sStepNow - sCfg["speedUp"]) into sStepNow
   Coil.AddFood k
   put empty into sHUDWas
end Coil.Eat

on Coil.Shrink pN
   local tCell
   repeat pN
      if the number of lines of sBody <= 2 then exit repeat
      put the last line of sBody into tCell
      put empty into sOcc[tCell]
      Entity.Kill the last line of sKeys
      delete the last line of sBody
      delete the last line of sKeys
   end repeat
end Coil.Shrink

-- gold food does not wait: it moves elsewhere when its time is up
on Coil.FoodClock
   local tSeq, tSeqs, k
   put the keys of sOnBoard into tSeqs
   repeat for each line tSeq in tSeqs
      if sOnBoard[tSeq]["life"] is not a number or sOnBoard[tSeq]["life"] <= 0 then next repeat
      subtract 1 from sOnBoard[tSeq]["life"]
      if sOnBoard[tSeq]["life"] <= 0 then
         put sOnBoard[tSeq]["kind"] into k
         Entity.Kill sOnBoard[tSeq]["key"]
         put empty into sOcc[sOnBoard[tSeq]["at"]]
         delete variable sOnBoard[tSeq]
         Coil.AddFood k
      end if
   end repeat
end Coil.FoodClock

on Coil.Die
   FX.Sparks Coil.X(item 1 of line 1 of sBody), sCfg["cy"] + Coil.Y(item 2 of line 1 of sBody), kZ, 25, sCfg["wormColor"]
   Sound.Play "PlayerCrash"
   subtract 1 from sLives
   if sLives <= 0 then
      put true into sOver
      Sound.Play "Lose"
      put false into sWonAll
      put empty into sHUDWas
      exit Coil.Die
   end if
   put 45 into sDeadT
   Coil.Say "OUCH", 45
end Coil.Die

on Coil.LevelDone
   Sound.Play "Win"
   add 50 * sLevel to sScore
   if sLevel >= sCfg["levels"] then
      put true into sOver
      put true into sWonAll
      put empty into sHUDWas
      exit Coil.LevelDone
   end if
   Coil.GoLevel sLevel + 1
end Coil.LevelDone

-- tests and the demo: the first step of a shortest way to the nearest food (not shrinking food),
-- found breadth first; with no way to any, a step into the most open neighbour
function Coil.AutoDir
   local tHead, tQ, tHeadQ, tTailQ, tFrom, tCell, tD, c, r, tNext, tSeq, tGoal, tStep, tBest, tRoom, tMost
   put line 1 of sBody into tHead
   repeat for each key tSeq in sOnBoard
      if sFood[sOnBoard[tSeq]["kind"]]["kind"] is not "shrink" then put true into tGoal[sOnBoard[tSeq]["at"]]
   end repeat
   put 1 into tHeadQ
   put 1 into tTailQ
   put tHead into tQ[1]
   put "start" into tFrom[tHead]
   repeat while tHeadQ <= tTailQ
      put tQ[tHeadQ] into tCell
      add 1 to tHeadQ
      if tGoal[tCell] is true then
         -- walk back to the cell next to the head
         repeat while tFrom[tCell] is not tHead and tFrom[tCell] is not "start"
            put tFrom[tCell] into tCell
         end repeat
         return Coil.DirTo(tHead, tCell)
      end if
      repeat for each line tD in ("1,0" & cr & "-1,0" & cr & "0,1" & cr & "0,-1")
         put Coil.Wrap(item 1 of tCell + item 1 of tD, sCfg["cols"]) into c
         put Coil.Wrap(item 2 of tCell + item 2 of tD, sCfg["rows"]) into r
         if not sCfg["wrap"] and (item 1 of tCell + item 1 of tD is not c or item 2 of tCell + item 2 of tD is not r) then next repeat
         put c & "," & r into tNext
         if tFrom[tNext] is not empty then next repeat
         if not Coil.Free(c, r) then next repeat
         if tCell is tHead and item 1 of tD = -item 1 of sDir and item 2 of tD = -item 2 of sDir then next repeat
         put tCell into tFrom[tNext]
         add 1 to tTailQ
         put tNext into tQ[tTailQ]
      end repeat
   end repeat
   -- no way to food: the free neighbour with the most free cells around it
   put -1 into tMost
   repeat for each line tD in ("1,0" & cr & "-1,0" & cr & "0,1" & cr & "0,-1")
      if item 1 of tD = -item 1 of sDir and item 2 of tD = -item 2 of sDir then next repeat
      put Coil.Wrap(item 1 of tHead + item 1 of tD, sCfg["cols"]) into c
      put Coil.Wrap(item 2 of tHead + item 2 of tD, sCfg["rows"]) into r
      if not Coil.Free(c, r) then next repeat
      put 0 into tRoom
      repeat for each line tStep in ("1,0" & cr & "-1,0" & cr & "0,1" & cr & "0,-1")
         if Coil.Free(c + item 1 of tStep, r + item 2 of tStep) then add 1 to tRoom
      end repeat
      if tRoom > tMost then
         put tRoom into tMost
         put tD into tBest
      end if
   end repeat
   if tBest is empty then return sDir
   return tBest
end Coil.AutoDir

-- the heading from cell pA to the next cell pB (wrapping counts)
function Coil.DirTo pA, pB
   local dx, dy
   put item 1 of pB - item 1 of pA into dx
   put item 2 of pB - item 2 of pA into dy
   if dx > 1 then put -1 into dx
   if dx < -1 then put 1 into dx
   if dy > 1 then put -1 into dy
   if dy < -1 then put 1 into dy
   return dx & "," & dy
end Coil.DirTo

-- a cell number past an edge comes back in on the other side
function Coil.Wrap pN, pMax
   if pN < 1 then return pMax
   if pN > pMax then return 1
   return pN
end Coil.Wrap

function Coil.Free pC, pR
   if pC < 1 or pR < 1 or pC > sCfg["cols"] or pR > sCfg["rows"] then return sCfg["wrap"]
   return sOcc[pC & "," & pR] is empty or char 1 of sOcc[pC & "," & pR] is "f"
end Coil.Free

on Coil.TestAuto pOn
   put pOn into sAuto
end Coil.TestAuto

on Coil.Say pText, pSteps
   put pText into sMsg
   put pSteps into sMsgT
   put empty into sHUDWas
end Coil.Say

on Coil.ShowHUD
   local tWords
   put sLevel & "|" & sScore & "|" & sLives & "|" & sEaten & "|" & sOver & "|" & (sMsgT > 0) into tWords
   if tWords is sHUDWas then exit Coil.ShowHUD
   put tWords into sHUDWas
   HUD.Set "Coil.Score", sCfg["title"] & "   SCORE" && sScore && "  LIVES" && sLives && "  EATEN" && sEaten & "/" & Coil.Target() && "  LEVEL" && sLevel & "/" & sCfg["levels"], 20, 30, 14
   HUD.Remove "Coil.Msg"
   if sOver and sWonAll then
      HUD.Set "Coil.Msg", "EVERY LEVEL EATEN. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Coil.Msg", "GAME OVER. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sMsgT > 0 then
      HUD.Set "Coil.Msg", sMsg & "    " & sCfg["help"], 20, 56, 12
   end if
end Coil.ShowHUD

-- for tests: level|lives|score|eaten|length|over|head cell|heading|steps to the next move|food cells
function Coil.State
   return sLevel & "|" & sLives & "|" & sScore & "|" & sEaten & "|" & the number of lines of sBody & "|" & sOver & "|" & line 1 of sBody & "|" & sDir & "|" & sWait & "|" & Coil.FoodList()
end Coil.State

-- for tests: where the food is, "c,r" a word
function Coil.FoodList
   local tSeq, tOut
   repeat for each key tSeq in sOnBoard
      put sOnBoard[tSeq]["at"] & " " after tOut
   end repeat
   return word 1 to -1 of tOut
end Coil.FoodList

on Game.OnStop
   HUD.Clear
end Game.OnStop

on arrowKey pKey
end arrowKey
