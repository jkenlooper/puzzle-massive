SELECT pc.id, pc.x, pc.y, pc.rotate, pc.parent, pc.status as piece_status, pz.table_width, pz.table_height, pz.pieces, pz.status, pz.permission FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.puzzle_id = :puzzle_id
and pc.id = :piece
;
