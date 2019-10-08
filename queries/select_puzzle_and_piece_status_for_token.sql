SELECT pz.id as puzzle, pc.status as piece_status, pz.status as puzzle_status
FROM Puzzle AS pz
JOIN Piece AS pc ON (pz.id = pc.puzzle)
WHERE pz.puzzle_id = :puzzle_id
and pc.id = :piece
and pz.status in (1, 5) -- ACTIVE, BUGGY_UNLISTED
-- The piece status should be done with redis data
--and (pc.status isnull or pc.status = '') -- not isimmovable
limit 1
;
