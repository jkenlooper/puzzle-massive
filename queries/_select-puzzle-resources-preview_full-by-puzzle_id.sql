SELECT pf.name, pf.url FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
WHERE p.puzzle_id = :puzzle_id
AND pf.name = 'preview_full'
AND p.status not in (0, -1, -2, -10, -11, -12, -20, -21)
-- NEEDS_MODERATION FAILED_LICENSE NO_ATTRIBUTION DELETED_LICENSE DELETED_INAPT DELETED_OLD SUGGESTED SUGGESTED_DONE
;
