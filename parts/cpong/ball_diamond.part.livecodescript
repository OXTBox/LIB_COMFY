## PART ball_diamond: a wire diamond with a cross inside.
function Cpong.BallMesh pS
   local tM, tH
   put Mesh.New() into tM
   put pS / 2 + 2 into tH
   Cpong.Line tM, 0, -tH, tH, 0
   Cpong.Line tM, tH, 0, 0, tH
   Cpong.Line tM, 0, tH, -tH, 0
   Cpong.Line tM, -tH, 0, 0, -tH
   Cpong.Line tM, 0, -tH, 0, tH
   Cpong.Line tM, -tH, 0, tH, 0
   return tM
end Cpong.BallMesh
