SELECT :puzzle_id as cache_key, p.id, pf.name, pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date,
p.status,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 124) AS short,
124.0 AS long

FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
WHERE pf.name == 'preview_full'
-- Don't show the puzzle that is in the preview
AND p.puzzle_id != :puzzle_id
-- PUBLIC
AND p.permission = 0
-- ACTIVE, IN_QUEUE
AND p.status IN (1, 2)
GROUP BY p.id
ORDER BY p.m_date DESC
LIMIT 8;
