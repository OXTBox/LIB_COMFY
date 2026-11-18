## PART core (CWAVE): a wave shooter. Your ship at the bottom, a formation marching above;
## it steps down at each wall, drops bombs, and some leave it to dive at you. Shields soak up
## shots from both sides. Clear the wave for the next one. The builder adds Wave.Config.

global bPaused, bPlaying

local sCfg, sWave, sWaveN
local sShip, sShot, sShotSeq, sBomb, sBombSeq, sFoe, sFoeN, sAlive, sShield, sShieldTop, sShieldBottom
local sMarchX, sMarchDir, sMarchY, sRush
local sLevel, sLives, sScore, sOver, sWonAll, sHUDWas, sTick, sMsg, sMsgT, sCool, sDeadT, sAuto, sNow

constant kZ = 300

on Game.OnStart
   focus on nothing
   Camera.Reset
   Scene.ClearAll
   Particles.Clear
   HUD.Clear
   Collision.ClearRules
   Wave.Config
   put 0 into sScore
   put sCfg["lives"] into sLives
   put false into sOver
   Wave.StartLevel 1
end Game.OnStart

-- level n flies wave ((n - 1) mod waves) + 1; each time round the list it is faster
on Wave.StartLevel pLevel
   local tM, w, tRound
   put pLevel into sLevel
   put ((pLevel - 1) mod sWaveN) + 1 into w
   put (pLevel - 1) div sWaveN into tRound
   Scene.ClearAll
   Particles.Clear
   put empty into sShot
   put empty into sBomb
   put empty into sFoe
   put 0 into sCool
   put 0 into sDeadT
   put Mesh.New() into tM
   Vec.Decor tM, sCfg["floor"], sCfg["hw"], sCfg["hh"], sCfg["grid"]
   if tM["count"] > 0 then
      Mesh.Define "Wave.Floor", tM
      get Entity.Spawn("Wave.Floor", 0, sCfg["cy"], kZ + 1, sCfg["decoColor"])
   end if
   put Mesh.New() into tM
   Vec.Rect tM, -sCfg["hw"], -sCfg["hh"], sCfg["hw"], sCfg["hh"]
   Mesh.Define "Wave.Frame", tM
   get Entity.Spawn("Wave.Frame", 0, sCfg["cy"], kZ, sCfg["wallColor"])
   Mesh.Define "Wave.Ship", Vec.Shape(sCfg["shipShape"], sCfg["shipSize"])
   put Mesh.New() into tM
   Vec.Line tM, 0, -7, 0, 7
   Mesh.Define "Wave.Shot", tM
   put Mesh.New() into tM
   Vec.Outline tM, "0,-6" & cr & "4,0" & cr & "0,6" & cr & "-4,0"
   Mesh.Define "Wave.Bomb", tM
   put Mesh.New() into tM
   Vec.Rect tM, -sCfg["cell"] / 2, -sCfg["cell"] / 2, sCfg["cell"] / 2, sCfg["cell"] / 2
   Mesh.Define "Wave.Cell", tM
   Mesh.Define "Wave.Foe" & w, Vec.Shape(sWave[w]["shape"], sWave[w]["size"])
   put 0 into sShip["x"]
   put sCfg["hh"] - 30 into sShip["y"]
   put Entity.Spawn("Wave.Ship", 0, sCfg["cy"] + sShip["y"], kZ, sCfg["shipColor"]) into sShip["key"]
   Wave.BuildShields
   put sWave[w]["speed"] * (1 + sCfg["roundGain"] * tRound) into sNow["speed"]
   put sWave[w]["fire"] * (1 + sCfg["roundGain"] * tRound) into sNow["fire"]
   put sWave[w]["dive"] * (1 + sCfg["roundGain"] * tRound) into sNow["dive"]
   put w into sNow["wave"]
   Wave.BuildFormation w
   Wave.Say "WAVE" && pLevel & ": " & toUpper(sWave[w]["formation"]), 70
end Wave.StartLevel

-- where each foe sits in its formation (offsets from the formation's middle)
on Wave.BuildFormation pW
   local r, c, tRows, tCols, tSX, tSY, tX, tY, tWant, n, tMidC
   put sWave[pW]["rows"] into tRows
   put sWave[pW]["cols"] into tCols
   put sWave[pW]["size"] + sWave[pW]["gap"] into tSX
   put sWave[pW]["size"] * 0.9 + sWave[pW]["gap"] into tSY
   put (tCols + 1) / 2 into tMidC
   put 0 into n
   repeat with r = 1 to tRows
      repeat with c = 1 to tCols
         switch sWave[pW]["formation"]
            case "vee"
               -- two arms, wide at the top, meeting at the bottom row
               put abs(abs(c - tMidC) - (tRows - r) * (tCols - 1) / (2 * max(1, tRows - 1))) < 1 into tWant
               break
            case "diamond"
               put abs(c - tMidC) / tCols + abs(r - (tRows + 1) / 2) / tRows <= 0.5 into tWant
               break
            case "ragged"
               put (r * 7 + c * 3) mod 5 is not 0 into tWant
               break
            default
               put true into tWant
         end switch
         if not tWant then next repeat
         add 1 to n
         put (c - tMidC) * tSX into sFoe[n]["ox"]
         put (r - 1) * tSY into sFoe[n]["oy"]
         put "line" into sFoe[n]["mode"]
         put r into sFoe[n]["row"]
         put Entity.Spawn("Wave.Foe" & pW, 0, 0, kZ, sWave[pW]["color"][r]) into sFoe[n]["key"]
      end repeat
   end repeat
   put n into sFoeN
   put n into sAlive
   put 0 into sMarchX
   put 1 into sMarchDir
   put -sCfg["hh"] + 50 into sMarchY
   repeat with n = 1 to sFoeN
      put true into sFoe[n]["live"]
      Wave.PlaceFoe n
   end repeat
end Wave.BuildFormation

on Wave.BuildShields
   local s, r, c, tN, tX0, tY0, k
   put empty into sShield
   put 0 into k
   put sShip["y"] - 70 - sCfg["cell"] into sShieldTop
   put sShip["y"] - 70 + sCfg["shieldRows"] * sCfg["cell"] into sShieldBottom
   if sCfg["shields"] <= 0 then exit Wave.BuildShields
   repeat with s = 1 to sCfg["shields"]
      put -sCfg["hw"] + s * (2 * sCfg["hw"]) / (sCfg["shields"] + 1) into tX0
      put sShip["y"] - 70 into tY0
      repeat with r = 1 to sCfg["shieldRows"]
         repeat with c = 1 to sCfg["shieldCols"]
            add 1 to k
            put tX0 + (c - (sCfg["shieldCols"] + 1) / 2) * sCfg["cell"] into sShield[k]["x"]
            put tY0 + (r - 1) * sCfg["cell"] into sShield[k]["y"]
            put sCfg["shieldHits"] into sShield[k]["hp"]
            put Entity.Spawn("Wave.Cell", sShield[k]["x"], sCfg["cy"] + sShield[k]["y"], kZ, sCfg["shieldColor"]) into sShield[k]["key"]
         end repeat
      end repeat
   end repeat
end Wave.BuildShields

on Wave.PlaceFoe pN
   if sFoe[pN]["mode"] is "line" then
      put sMarchX + sFoe[pN]["ox"] into sFoe[pN]["x"]
      put sMarchY + sFoe[pN]["oy"] into sFoe[pN]["y"]
      if sWave[sNow["wave"]]["formation"] is "swarm" then
         add 10 * sin(sTick / 13 + pN) to sFoe[pN]["x"]
         add 6 * cos(sTick / 17 + pN * 2) to sFoe[pN]["y"]
      end if
   end if
   Entity.SetPosition sFoe[pN]["key"], sFoe[pN]["x"], sCfg["cy"] + sFoe[pN]["y"], kZ
end Wave.PlaceFoe

on Game.OnUpdate
   local tKeys
   add 1 to sTick
   put Vec.Keys() into tKeys
   if sOver then
      if 32 is among the items of tKeys then
         put 0 into sScore
         put sCfg["lives"] into sLives
         put false into sOver
         Wave.StartLevel 1
      end if
      Wave.ShowHUD
      exit Game.OnUpdate
   end if
   if sDeadT > 0 then
      subtract 1 from sDeadT
      if sDeadT = 0 then
         Wave.Respawn
      end if
   else
      Wave.MoveShip tKeys
   end if
   Wave.MoveShots
   Wave.March
   Wave.MoveBombs
   if sAlive = 0 and not sOver then
      add sCfg["waveBonus"] * sLevel to sScore
      if sCfg["levels"] > 0 and sLevel >= sCfg["levels"] then
         put true into sOver
         put true into sWonAll
      else
         Wave.StartLevel sLevel + 1
      end if
   end if
   if sMsgT > 0 then subtract 1 from sMsgT
   Wave.ShowHUD
end Game.OnUpdate

on Wave.MoveShip pKeys
   local tD, tFire, tTarget, tShots
   if sAuto is true then
      put Wave.AutoTarget() into tTarget
      put Vec.Clamp(tTarget - sShip["x"], -sCfg["shipSpeed"], sCfg["shipSpeed"]) into tD
      add tD to sShip["x"]
      put abs(tTarget - sShip["x"]) < 20 into tFire
   else
      put item 1 of Vec.Dir(sCfg["ctrl"], pKeys) into tD
      add tD * sCfg["shipSpeed"] to sShip["x"]
      put Vec.Fire(sCfg["ctrl"], pKeys) into tFire
   end if
   put Vec.Clamp(sShip["x"], -sCfg["hw"] + 20, sCfg["hw"] - 20) into sShip["x"]
   Entity.SetPosition sShip["key"], sShip["x"], sCfg["cy"] + sShip["y"], kZ
   if sCool > 0 then subtract 1 from sCool
   put Wave.Count(sShot) into tShots
   if tFire and sCool = 0 and tShots < sCfg["maxShots"] then
      add 1 to sShotSeq
      put sShip["x"] into sShot[sShotSeq]["x"]
      put sShip["y"] - sCfg["shipSize"] / 2 into sShot[sShotSeq]["y"]
      put Entity.Spawn("Wave.Shot", sShip["x"], sCfg["cy"] + sShot[sShotSeq]["y"], kZ, sCfg["shotColor"]) into sShot[sShotSeq]["key"]
      put sCfg["coolSteps"] into sCool
      Sound.Play "shot"
   end if
end Wave.MoveShip

-- tests and the demo: the x of the lowest living foe
function Wave.AutoTarget
   local n, tY, tX
   put -9999 into tY
   put 0 into tX
   repeat with n = 1 to sFoeN
      if sFoe[n]["live"] and sFoe[n]["y"] > tY then
         put sFoe[n]["y"] into tY
         put sFoe[n]["x"] into tX
      end if
   end repeat
   return tX
end Wave.AutoTarget

on Wave.TestAuto pOn
   put pOn into sAuto
end Wave.TestAuto

on Wave.MoveShots
   local k, tKeys, n, tHalf
   put the keys of sShot into tKeys
   repeat for each line k in tKeys
      subtract sCfg["shotSpeed"] from sShot[k]["y"]
      if sShot[k]["y"] < -sCfg["hh"] then
         Wave.EndShot k
         next repeat
      end if
      if Wave.ShieldAt(sShot[k]["x"], sShot[k]["y"]) then
         Wave.EndShot k
         next repeat
      end if
      repeat with n = 1 to sFoeN
         if not sFoe[n]["live"] then next repeat
         put sWave[sNow["wave"]]["size"] / 2 + 2 into tHalf
         if abs(sFoe[n]["x"] - sShot[k]["x"]) <= tHalf and abs(sFoe[n]["y"] - sShot[k]["y"]) <= tHalf + 6 then
            Wave.KillFoe n
            Wave.EndShot k
            exit repeat
         end if
      end repeat
      if sShot[k] is an array then Entity.SetPosition sShot[k]["key"], sShot[k]["x"], sCfg["cy"] + sShot[k]["y"], kZ
   end repeat
end Wave.MoveShots

on Wave.EndShot pK
   Entity.Kill sShot[pK]["key"]
   delete variable sShot[pK]
end Wave.EndShot

on Wave.KillFoe pN
   put false into sFoe[pN]["live"]
   Entity.Kill sFoe[pN]["key"]
   FX.Sparks sFoe[pN]["x"], sCfg["cy"] + sFoe[pN]["y"], kZ, 12, sCfg["shotColor"]
   Sound.Play "boom"
   subtract 1 from sAlive
   if sFoe[pN]["mode"] is "dive" then
      add sWave[sNow["wave"]]["points"] * 3 to sScore
   else
      add sWave[sNow["wave"]]["points"] to sScore
   end if
end Wave.KillFoe

-- the formation marches; at a wall it steps down and turns; fewer left, faster it goes
on Wave.March
   local n, tMin, tMax, tSpeed, tDiveFrom
   if sAlive <= 0 then exit Wave.March
   put sNow["speed"] * (1 + sCfg["rush"] * (1 - sAlive / sFoeN)) into tSpeed
   add sMarchDir * tSpeed to sMarchX
   put 9999 into tMin
   put -9999 into tMax
   repeat with n = 1 to sFoeN
      if sFoe[n]["live"] and sFoe[n]["mode"] is "line" then
         put min(tMin, sMarchX + sFoe[n]["ox"]) into tMin
         put max(tMax, sMarchX + sFoe[n]["ox"]) into tMax
      end if
   end repeat
   if tMax + sWave[sNow["wave"]]["size"] / 2 > sCfg["hw"] - 10 and sMarchDir > 0 then
      put -1 into sMarchDir
      add sWave[sNow["wave"]]["drop"] to sMarchY
   else if tMin - sWave[sNow["wave"]]["size"] / 2 < -sCfg["hw"] + 10 and sMarchDir < 0 then
      put 1 into sMarchDir
      add sWave[sNow["wave"]]["drop"] to sMarchY
   end if
   repeat with n = 1 to sFoeN
      if not sFoe[n]["live"] then next repeat
      if sFoe[n]["mode"] is "dive" then
         Wave.Dive n
      else
         Wave.PlaceFoe n
         if random(100000) <= sNow["fire"] * 100000 then Wave.DropBomb sFoe[n]["x"], sFoe[n]["y"]
      end if
      if sFoe[n]["live"] and sFoe[n]["y"] >= sShip["y"] - 10 and sFoe[n]["mode"] is "line" then
         -- they reached you
         put 1 into sLives
         Wave.HitShip
         exit Wave.March
      end if
   end repeat
   -- one roll a step: does a foe (any one still in line) dive?
   if random(100000) <= sNow["dive"] * 100000 then
      put random(sFoeN) into n
      if sFoe[n]["live"] and sFoe[n]["mode"] is "line" then put n into tDiveFrom
   end if
   if tDiveFrom is not empty then
      put "dive" into sFoe[tDiveFrom]["mode"]
      put 0 into sFoe[tDiveFrom]["t"]
      put sFoe[tDiveFrom]["x"] into sFoe[tDiveFrom]["x0"]
   end if
end Wave.March

-- a diver swoops down at where the ship is, then comes back in at the top
on Wave.Dive pN
   local tSpeed
   add 1 to sFoe[pN]["t"]
   put sNow["speed"] * 2.2 + 2 into tSpeed
   add tSpeed to sFoe[pN]["y"]
   add Vec.Clamp((sShip["x"] - sFoe[pN]["x"]) * 0.04, -3, 3) + 3 * sin(sFoe[pN]["t"] / 8) to sFoe[pN]["x"]
   if sFoe[pN]["t"] mod 25 = 0 then Wave.DropBomb sFoe[pN]["x"], sFoe[pN]["y"]
   if sDeadT = 0 and abs(sFoe[pN]["x"] - sShip["x"]) < sCfg["shipSize"] / 2 + 6 and abs(sFoe[pN]["y"] - sShip["y"]) < sCfg["shipSize"] / 2 + 6 then
      Wave.KillFoe pN
      Wave.HitShip
      exit Wave.Dive
   end if
   if sFoe[pN]["y"] > sCfg["hh"] + 20 then
      put "line" into sFoe[pN]["mode"]
   end if
   Entity.SetPosition sFoe[pN]["key"], sFoe[pN]["x"], sCfg["cy"] + sFoe[pN]["y"], kZ
end Wave.Dive

on Wave.DropBomb pX, pY
   -- never more than a few in the air: 3, and one more each time round the waves
   if Wave.Count(sBomb) >= 3 + (sLevel - 1) div sWaveN then exit Wave.DropBomb
   add 1 to sBombSeq
   put pX into sBomb[sBombSeq]["x"]
   put pY + 8 into sBomb[sBombSeq]["y"]
   put Entity.Spawn("Wave.Bomb", pX, sCfg["cy"] + pY + 8, kZ, sCfg["bombColor"]) into sBomb[sBombSeq]["key"]
end Wave.DropBomb

on Wave.MoveBombs
   local k, tKeys
   put the keys of sBomb into tKeys
   repeat for each line k in tKeys
      add sCfg["bombSpeed"] to sBomb[k]["y"]
      if sBomb[k]["y"] > sCfg["hh"] or Wave.ShieldAt(sBomb[k]["x"], sBomb[k]["y"]) then
         Entity.Kill sBomb[k]["key"]
         delete variable sBomb[k]
         next repeat
      end if
      if sDeadT = 0 and abs(sBomb[k]["x"] - sShip["x"]) < sCfg["shipSize"] / 2 and abs(sBomb[k]["y"] - sShip["y"]) < sCfg["shipSize"] / 2 then
         Entity.Kill sBomb[k]["key"]
         delete variable sBomb[k]
         Wave.HitShip
         next repeat
      end if
      Entity.SetPosition sBomb[k]["key"], sBomb[k]["x"], sCfg["cy"] + sBomb[k]["y"], kZ
   end repeat
end Wave.MoveBombs

-- true when a shield cell is at x,y (and it takes the hit)
function Wave.ShieldAt pX, pY
   local k, tH
   if sShield is not an array or pY < sShieldTop or pY > sShieldBottom then return false
   put sCfg["cell"] / 2 + 1 into tH
   repeat for each key k in sShield
      if sShield[k]["hp"] <= 0 then next repeat
      if abs(sShield[k]["x"] - pX) <= tH and abs(sShield[k]["y"] - pY) <= tH + 3 then
         subtract 1 from sShield[k]["hp"]
         if sShield[k]["hp"] <= 0 then Entity.Kill sShield[k]["key"]
         return true
      end if
   end repeat
   return false
end Wave.ShieldAt

on Wave.HitShip
   FX.Sparks sShip["x"], sCfg["cy"] + sShip["y"], kZ, 30, sCfg["shipColor"]
   Sound.Play "boom"
   subtract 1 from sLives
   Entity.Kill sShip["key"]
   if sLives <= 0 then
      put true into sOver
      put false into sWonAll
      put empty into sHUDWas
      exit Wave.HitShip
   end if
   put 60 into sDeadT
   Wave.Say "SHIP LOST", 60
end Wave.HitShip

on Wave.Respawn
   local k, tKeys
   put the keys of sBomb into tKeys
   repeat for each line k in tKeys
      Entity.Kill sBomb[k]["key"]
   end repeat
   put empty into sBomb
   put 0 into sShip["x"]
   put Entity.Spawn("Wave.Ship", 0, sCfg["cy"] + sShip["y"], kZ, sCfg["shipColor"]) into sShip["key"]
end Wave.Respawn

on Wave.Say pText, pSteps
   put pText into sMsg
   put pSteps into sMsgT
   put empty into sHUDWas
end Wave.Say

on Wave.ShowHUD
   local tWords, tLevels
   put sLevel & "|" & sScore & "|" & sLives & "|" & sOver & "|" & (sMsgT > 0) into tWords
   if tWords is sHUDWas then exit Wave.ShowHUD
   put tWords into sHUDWas
   if sCfg["levels"] > 0 then
      put sLevel & "/" & sCfg["levels"] into tLevels
   else
      put sLevel into tLevels
   end if
   HUD.Set "Wave.Score", sCfg["title"] & "   SCORE" && sScore && "  SHIPS" && sLives && "  WAVE" && tLevels, 20, 30, 14
   HUD.Remove "Wave.Msg"
   if sOver and sWonAll then
      HUD.Set "Wave.Msg", "EVERY WAVE BEATEN. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sOver then
      HUD.Set "Wave.Msg", "GAME OVER. SCORE" && sScore & ". SPACE TO PLAY AGAIN", 20, 56, 12
   else if sMsgT > 0 then
      HUD.Set "Wave.Msg", sMsg & "    " & sCfg["help"], 20, 56, 12
   end if
end Wave.ShowHUD

-- for tests: wave|ships|score|foes left|shots|bombs|over
function Wave.State
   return sLevel & "|" & sLives & "|" & sScore & "|" & sAlive & "|" & Wave.Count(sShot) & "|" & Wave.Count(sBomb) & "|" & sOver
end Wave.State

function Wave.Count pArr
   local tKeys
   if pArr is not an array then return 0
   put the keys of pArr into tKeys
   return the number of lines of tKeys
end Wave.Count

on Game.OnStop
   HUD.Clear
end Game.OnStop

on arrowKey pKey
end arrowKey
