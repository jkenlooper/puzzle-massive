SELECT pz.puzzle_id, pc.id, pc.parent, pc.status as piece_status, pc.x, pc.y, pz.status as puzzle_status
FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.id = :id AND pc.col = 0 AND pc.row = 0 AND pc.parent IS NOT NULL
and pc.status = 1;
