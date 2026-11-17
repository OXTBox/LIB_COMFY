## PART control_cpu: a computer paddle. It watches the ball coming at its face soonest,
## guesses where it will land (walls folded in), and moves there no faster than its speed.
## skill 0..1: how far ahead it looks and how close its guess is; levels add to it.

on Cpong.CpuMove pJ
   local tS, tDir, tB, tN, tV, tAlong, tVA, tT, tBestT, tWant, tLen, tSkill, tSp
   put sPad[pJ]["side"] into tS
   if tS is "L" or tS is "T" then
      put 1 into tDir
   else
      put -1 into tDir
   end if
   if tS is "L" or tS is "R" then
      put sCfg["hh"] into tLen
   else
      put sCfg["hw"] into tLen
   end if
   put min(1, sPad[pJ]["skill"] + sSkillAdd) into tSkill
   put 0 into tWant
   put 999999 into tBestT
   repeat with tB = 1 to sCfg["ballCount"]
      if tS is "L" or tS is "R" then
         put sBall[tB]["x"] into tN
         put sBall[tB]["dx"] into tV
         put sBall[tB]["y"] into tAlong
         put sBall[tB]["dy"] into tVA
      else
         put sBall[tB]["y"] into tN
         put sBall[tB]["dy"] into tV
         put sBall[tB]["x"] into tAlong
         put sBall[tB]["dx"] into tVA
      end if
      if tV * tDir < 0 and (tN - sPad[pJ]["fx"]) * tDir > 0 then
         put abs(tN - sPad[pJ]["fx"]) / abs(tV) into tT
         if tT < tBestT then
            put tT into tBestT
            put tAlong + (Cpong.Fold(tAlong + tVA * tT, tLen) - tAlong) * tSkill into tWant
            add sPad[pJ]["err"] * sPad[pJ]["half"] * (1 - tSkill) to tWant
         end if
      end if
   end repeat
   put sPad[pJ]["speed"] * (0.55 + 0.45 * tSkill) into tSp
   add max(-tSp, min(tSp, tWant - sPad[pJ]["pos"])) to sPad[pJ]["pos"]
end Cpong.CpuMove

-- a straight path folded back between two walls at -pL and pL
function Cpong.Fold pX, pL
   local tP
   put pX + pL into tP
   put tP - 4 * pL * trunc(tP / (4 * pL)) into tP
   if tP < 0 then add 4 * pL to tP
   if tP > 2 * pL then put 4 * pL - tP into tP
   return tP - pL
end Cpong.Fold
