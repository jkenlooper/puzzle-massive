-- puzzle, table_width, table_height, puzzle_id, pieces
-- piece data should be taken from redis instead.
SELECT
pz.id as puzzle,
pz.puzzle_id,
pz.table_width,
pz.table_height,
pz.pieces,
pz.status,
pz.permission FROM Puzzle AS pz
WHERE pz.puzzle_id = :puzzle_id
and pz.status in (1, 5) -- ACTIVE, BUGGY_UNLISTED
;
