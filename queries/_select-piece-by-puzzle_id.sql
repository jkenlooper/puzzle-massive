SELECT pc.id, pc.x, pc.y, pc.rotate, pc.bg, pc.parent FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.puzzle_id = :puzzle_id
;
