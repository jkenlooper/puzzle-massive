SELECT pf.name, pf.url FROM Puzzle AS p
JOIN PuzzleFile AS pf ON (pf.puzzle = p.id)
WHERE p.puzzle_id = :puzzle_id
AND pf.name = 'pzz'
;
