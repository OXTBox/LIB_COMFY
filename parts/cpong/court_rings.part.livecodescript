## PART court_rings: rings round the centre, out to the nearest wall.
on Cpong.Decor @pM
   local tR, tG
   put max(20, sCfg["grid"]) into tG
   put tG into tR
   repeat while tR < min(sCfg["hw"], sCfg["hh"])
      Cpong.Ring pM, 0, 0, tR, 28
      add tG to tR
   end repeat
end Cpong.Decor
