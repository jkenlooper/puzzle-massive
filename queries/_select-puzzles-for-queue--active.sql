SELECT p.id, pf.name, pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date, p.status,
-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 124) AS short,
124.0 AS long
--strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 days') as is_recent

FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
WHERE pf.name == 'preview_full'
AND p.permission = 0 -- PUBLIC
AND p.status IN (1, 2) -- ACTIVE, IN_QUEUE
-- Filter out the 10 most recent puzzles
AND not (p.id in (select id from Puzzle where permission = 0 and status in (1, 2) and strftime('%s', m_date) >= strftime('%s', 'now', '-7 hours') order by m_date desc ))
GROUP BY p.id
ORDER BY p.pieces asc
-- Can't limit or offset since it varies what is actually visible to each player depending on dots
;
