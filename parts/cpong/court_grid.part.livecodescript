## PART court_grid: a floor grid, one line every sCfg["grid"] units.
on Cpong.Decor @pM
   local tX, tY, tG
   put max(20, sCfg["grid"]) into tG
   put tG into tX
   repeat while tX < sCfg["hw"]
      Cpong.Line pM, tX, -sCfg["hh"], tX, sCfg["hh"]
      Cpong.Line pM, -tX, -sCfg["hh"], -tX, sCfg["hh"]
      add tG to tX
   end repeat
   Cpong.Line pM, 0, -sCfg["hh"], 0, sCfg["hh"]
   put tG into tY
   repeat while tY < sCfg["hh"]
      Cpong.Line pM, -sCfg["hw"], tY, sCfg["hw"], tY
      Cpong.Line pM, -sCfg["hw"], -tY, sCfg["hw"], -tY
      add tG to tY
   end repeat
   Cpong.Line pM, -sCfg["hw"], 0, sCfg["hw"], 0
end Cpong.Decor
