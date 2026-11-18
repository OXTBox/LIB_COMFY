## PART common/vec: wire shapes, floor styles, keys and the mouse, shared by every kit but cpong.
## Flat on the play plane: x right, y down, z 0 (the kit puts things at z = 300, one unit a pixel).

local sVecTestKeys, sVecTestMouse

-- a wire line in a mesh
on Vec.Line @pM, pX1, pY1, pX2, pY2
   local tA
   Mesh.AddVertex pM, pX1, pY1, 0
   put the result into tA
   Mesh.AddVertex pM, pX2, pY2, 0
   Mesh.AddLine pM, tA, the result
end Vec.Line

-- a wire rectangle, corners x1,y1 and x2,y2
on Vec.Rect @pM, pX1, pY1, pX2, pY2
   Vec.Line pM, pX1, pY1, pX2, pY1
   Vec.Line pM, pX2, pY1, pX2, pY2
   Vec.Line pM, pX2, pY2, pX1, pY2
   Vec.Line pM, pX1, pY2, pX1, pY1
end Vec.Rect

-- a wire circle of pN sides
on Vec.Ring @pM, pX, pY, pR, pN
   local i, tA, tB
   repeat with i = 0 to pN - 1
      put i * 2 * pi / pN into tA
      put (i + 1) * 2 * pi / pN into tB
      Vec.Line pM, pX + pR * cos(tA), pY + pR * sin(tA), pX + pR * cos(tB), pY + pR * sin(tB)
   end repeat
end Vec.Ring

-- a closed outline through "x,y" points, one a line
on Vec.Outline @pM, pPoints
   local tPrev, tFirst, tP
   repeat for each line tP in pPoints
      if tFirst is empty then
         put tP into tFirst
      else
         Vec.Line pM, item 1 of tPrev, item 2 of tPrev, item 1 of tP, item 2 of tP
      end if
      put tP into tPrev
   end repeat
   if tFirst is not empty and tPrev is not tFirst then Vec.Line pM, item 1 of tPrev, item 2 of tPrev, item 1 of tFirst, item 2 of tFirst
end Vec.Outline

-- a shape about pSize across, centred on 0,0, pointing up (-y) when it points:
-- square diamond ring tri ship saucer crab bug rock star plus capsule
function Vec.Shape pShape, pSize
   local tM, h, q
   put Mesh.New() into tM
   put pSize / 2 into h
   put pSize / 4 into q
   switch pShape
      case "diamond"
         Vec.Outline tM, "0," & -h & cr & h & ",0" & cr & "0," & h & cr & -h & ",0"
         Vec.Line tM, 0, -h, 0, h
         break
      case "ring"
         Vec.Ring tM, 0, 0, h, 10
         break
      case "tri"
         Vec.Outline tM, "0," & -h & cr & h & "," & h & cr & -h & "," & h
         break
      case "ship"
         Vec.Outline tM, "0," & -h & cr & h & "," & h & cr & "0," & q & cr & -h & "," & h
         break
      case "saucer"
         Vec.Outline tM, -h & ",0" & cr & -q & "," & -q & cr & q & "," & -q & cr & h & ",0" & cr & q & "," & q & cr & -q & "," & q
         Vec.Line tM, -h, 0, h, 0
         Vec.Outline tM, -q & "," & -q & cr & "0," & -h & cr & q & "," & -q
         break
      case "crab"
         Vec.Rect tM, -q * 1.4, -q, q * 1.4, q
         Vec.Line tM, -q * 1.4, -q * 0.3, -h, -h
         Vec.Line tM, q * 1.4, -q * 0.3, h, -h
         Vec.Line tM, -q, q, -h, h
         Vec.Line tM, q, q, h, h
         Vec.Line tM, -q * 0.5, 0, -q * 0.5, -q * 0.4
         Vec.Line tM, q * 0.5, 0, q * 0.5, -q * 0.4
         break
      case "bug"
         Vec.Outline tM, "0," & -q & cr & q & ",0" & cr & "0," & h & cr & -q & ",0"
         Vec.Line tM, 0, -q, -q, -h
         Vec.Line tM, 0, -q, q, -h
         Vec.Line tM, -q, 0, -h, q * 0.5
         Vec.Line tM, q, 0, h, q * 0.5
         break
      case "rock"
         Vec.Outline tM, "0," & -h & cr & h * 0.7 & "," & -h * 0.8 & cr & h & "," & -q * 0.4 & cr & h * 0.8 & "," & h * 0.6 & cr & q * 0.2 & "," & h & cr & -h * 0.6 & "," & h * 0.8 & cr & -h & "," & q * 0.5 & cr & -h * 0.75 & "," & -h * 0.55 & cr & -q & "," & -h * 0.7
         break
      case "star"
         Vec.Star tM, h
         break
      case "plus"
         Vec.Outline tM, -q * 0.5 & "," & -h & cr & q * 0.5 & "," & -h & cr & q * 0.5 & "," & -q * 0.5 & cr & h & "," & -q * 0.5 & cr & h & "," & q * 0.5 & cr & q * 0.5 & "," & q * 0.5 & cr & q * 0.5 & "," & h & cr & -q * 0.5 & "," & h & cr & -q * 0.5 & "," & q * 0.5 & cr & -h & "," & q * 0.5 & cr & -h & "," & -q * 0.5 & cr & -q * 0.5 & "," & -q * 0.5
         break
      case "capsule"
         Vec.Rect tM, -h, -q, h, q
         Vec.Line tM, -q, -q, -q, q
         Vec.Line tM, q, -q, q, q
         break
      default
         Vec.Rect tM, -h, -h, h, h
   end switch
   return tM
end Vec.Shape

on Vec.Star @pM, pR
   local i, tA, tPts
   repeat with i = 0 to 9
      put -pi / 2 + i * pi / 5 into tA
      if i mod 2 = 0 then
         put pR * cos(tA) & "," & pR * sin(tA) & cr after tPts
      else
         put pR * 0.45 * cos(tA) & "," & pR * 0.45 * sin(tA) & cr after tPts
      end if
   end repeat
   delete the last char of tPts
   Vec.Outline pM, tPts
end Vec.Star

-- the floor under a play area pHW x pHH (half sizes): grid, rings, stars, dots, lanes or bare.
-- pStep is the spacing; nothing is added for bare.
on Vec.Decor @pM, pStyle, pHW, pHH, pStep
   local tX, tY, tS, i, tN
   put max(16, pStep) into tS
   switch pStyle
      case "grid"
         put 0 into tX
         repeat while tX < pHW
            Vec.Line pM, tX, -pHH, tX, pHH
            if tX > 0 then Vec.Line pM, -tX, -pHH, -tX, pHH
            add tS to tX
         end repeat
         put 0 into tY
         repeat while tY < pHH
            Vec.Line pM, -pHW, tY, pHW, tY
            if tY > 0 then Vec.Line pM, -pHW, -tY, pHW, -tY
            add tS to tY
         end repeat
         break
      case "rings"
         put tS into tX
         repeat while tX < min(pHW, pHH)
            Vec.Ring pM, 0, 0, tX, 28
            add tS to tX
         end repeat
         break
      case "stars"
         -- the same sky every time: a fixed walk, not the random numbers
         put round(pHW * pHH / (tS * tS) * 2) into tN
         repeat with i = 1 to tN
            put ((i * 7919) mod 1000) / 1000 * 2 * pHW - pHW into tX
            put ((i * 104729) mod 997) / 997 * 2 * pHH - pHH into tY
            Vec.Line pM, tX - 1.5, tY, tX + 1.5, tY
            if i mod 3 = 0 then Vec.Line pM, tX, tY - 1.5, tX, tY + 1.5
         end repeat
         break
      case "dots"
         put -pHW + tS / 2 into tX
         repeat while tX < pHW
            put -pHH + tS / 2 into tY
            repeat while tY < pHH
               Vec.Line pM, tX - 1, tY, tX + 1, tY
               add tS to tY
            end repeat
            add tS to tX
         end repeat
         break
      case "lanes"
         put -pHW + tS into tX
         repeat while tX < pHW - 1
            put -pHH into tY
            repeat while tY < pHH
               Vec.Line pM, tX, tY, tX, min(pHH, tY + tS / 3)
               add tS * 2 / 3 to tY
            end repeat
            add tS to tX
         end repeat
         break
   end switch
end Vec.Decor

-- keys: the keys held now (a test can set them with Vec.TestKeys)
function Vec.Keys
   if sVecTestKeys is not empty then return sVecTestKeys
   return the keysDown
end Vec.Keys

on Vec.TestKeys pKeys
   put pKeys into sVecTestKeys
end Vec.TestKeys

function Vec.AnyKey pList, pKeys
   local tK
   repeat for each item tK in pList
      if tK is among the items of pKeys then return true
   end repeat
   return false
end Vec.AnyKey

-- "dx,dy" (-1, 0 or 1 each) for a control: arrows or wasd
function Vec.Dir pCtrl, pKeys
   -- (a one-line if just before an else would take the else: so no else here)
   if pCtrl is "wasd" then return Vec.DirOf(pKeys, "97,65", "100,68", "119,87", "115,83")
   return Vec.DirOf(pKeys, "65361", "65363", "65362", "65364")
end Vec.Dir

function Vec.DirOf pKeys, pLeft, pRight, pUp, pDown
   local dx, dy
   put 0 into dx
   put 0 into dy
   if Vec.AnyKey(pLeft, pKeys) then subtract 1 from dx
   if Vec.AnyKey(pRight, pKeys) then add 1 to dx
   if Vec.AnyKey(pUp, pKeys) then subtract 1 from dy
   if Vec.AnyKey(pDown, pKeys) then add 1 to dy
   return dx & "," & dy
end Vec.DirOf

-- the fire key (Space, or Z / Enter with the arrows, F with wasd)
function Vec.Fire pCtrl, pKeys
   if 32 is among the items of pKeys then return true
   if pCtrl is "wasd" then return Vec.AnyKey("102,70", pKeys)
   return Vec.AnyKey("122,90,65293", pKeys)
end Vec.Fire

-- the mouse as "x,y" on the play plane (pZ deep), or empty: no mouse, or a test turned it off
function Vec.MousePoint pZ
   local tM, tP
   if sVecTestMouse is not empty then
      if sVecTestMouse is "none" then return empty
      return sVecTestMouse
   end if
   put Engine.Mouse() into tM
   if tM is empty then return empty
   put Engine.Info("projection") into tP
   if item 1 of tP is not a number or item 1 of tP <= 0 then return empty
   return ((item 1 of tM - item 2 of tP) * pZ / item 1 of tP) & "," & ((item 2 of tM - item 3 of tP) * pZ / item 1 of tP)
end Vec.MousePoint

on Vec.TestMouse pXY
   put pXY into sVecTestMouse
end Vec.TestMouse

-- a number between pLo and pHi
function Vec.Clamp pV, pLo, pHi
   return max(pLo, min(pHi, pV))
end Vec.Clamp
