## PART control_keys: a player paddle. "arrows": up/down (side paddles) or left/right
## (top and bottom paddles). "wasd": W/S or A/D the same way, for a second player.

on Cpong.PlayerMove pJ, pKeys
   local tLess, tMore, tSide
   put sPad[pJ]["side"] is "L" or sPad[pJ]["side"] is "R" into tSide
   if sPad[pJ]["ctrl"] is "arrows" then
      if tSide then
         put "65362" into tLess
         put "65364" into tMore
      else
         put "65361" into tLess
         put "65363" into tMore
      end if
   else
      if tSide then
         put "119,87" into tLess
         put "115,83" into tMore
      else
         put "97,65" into tLess
         put "100,68" into tMore
      end if
   end if
   if Cpong.AnyKey(tLess, pKeys) then subtract sPad[pJ]["speed"] from sPad[pJ]["pos"]
   if Cpong.AnyKey(tMore, pKeys) then add sPad[pJ]["speed"] to sPad[pJ]["pos"]
end Cpong.PlayerMove
