## PART ball_ring: a wire ring with a dot of a cross in the middle.
function Cpong.BallMesh pS
   local tM
   put Mesh.New() into tM
   Cpong.Ring tM, 0, 0, pS / 2 + 1, 10
   Cpong.Line tM, -2, 0, 2, 0
   Cpong.Line tM, 0, -2, 0, 2
   return tM
end Cpong.BallMesh
