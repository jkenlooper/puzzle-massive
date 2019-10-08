SELECT pc.id,
pc.x,
pc.y,
pc.rotate,
pc.parent,
pc.status as piece_status,
pz.id as puzzle,
pz.puzzle_id,
pz.table_width,
pz.table_height,
pz.mask_width,
pz.pieces,
pz.status,
pz.permission FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.puzzle_id = :puzzle_id
and pc.id = :piece
and pz.status in (1, 5) -- ACTIVE, BUGGY_UNLISTED
;
