SELECT p.id, pf.name, pf.url, pfo.url as original, p.puzzle_id, p.permission, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date, p.status,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 64) AS short,
64.0 AS long

FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name = 'preview_full') -- Get the original
JOIN PuzzleFile AS pfo ON (pfo.puzzle = p1.id and pfo.name = 'original') -- Get the original

-- rendering statuses
AND p.status in (-5, -6, -7)
GROUP BY p.id
ORDER BY p.status desc
;
