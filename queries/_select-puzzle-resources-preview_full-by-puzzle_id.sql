SELECT pf.name, pf.url FROM Puzzle AS pz
JOIN PuzzleFile AS pf ON (pf.puzzle = pz.id)
WHERE puzzle_id = :puzzle_id
AND pf.name = 'preview_full'
;
