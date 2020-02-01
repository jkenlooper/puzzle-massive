-- The piece status should be done with redis data
SELECT pz.id as puzzle
FROM Puzzle AS pz
WHERE pz.puzzle_id = :puzzle_id
and pz.status in (1, 5) -- ACTIVE, BUGGY_UNLISTED
limit 1
;
