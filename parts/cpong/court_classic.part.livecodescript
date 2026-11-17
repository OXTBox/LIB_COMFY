## PART court_classic: a dashed middle line across the long way, and a centre ring.
on Cpong.Decor @pM
   local i, tN
   put 14 into tN
   repeat with i = 0 to tN - 1
      if sCfg["axis"] is "x" then
         Cpong.Line pM, 0, -sCfg["hh"] + (i + 0.25) * 2 * sCfg["hh"] / tN, 0, -sCfg["hh"] + (i + 0.75) * 2 * sCfg["hh"] / tN
      else
         Cpong.Line pM, -sCfg["hw"] + (i + 0.25) * 2 * sCfg["hw"] / tN, 0, -sCfg["hw"] + (i + 0.75) * 2 * sCfg["hw"] / tN, 0
      end if
   end repeat
   Cpong.Ring pM, 0, 0, 40, 20
end Cpong.Decor
