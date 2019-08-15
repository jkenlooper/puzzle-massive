SELECT pf.name, pf.url FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
WHERE p.puzzle_id = :puzzle_id
AND pf.name = 'preview_full'
;
