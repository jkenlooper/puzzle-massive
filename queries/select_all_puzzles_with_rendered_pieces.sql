SELECT pz.puzzle_id, pz.id,
pc.id as top_left_piece,
pc.parent as top_left_piece_parent,
pc.status as piece_status,
pc.x,
pc.y,
pz.status as puzzle_status
FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pc.col = 0 AND pc.row = 0 AND pc.parent IS NOT NULL
and pz.status in (1,2,3,4,5,-30) -- ACTIVE, IN_QUEUE, COMPLETED, FROZEN, BUGGY_UNLISTED, MAINTENANCE
;
