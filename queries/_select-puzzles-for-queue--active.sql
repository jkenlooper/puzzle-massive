SELECT p.id, pf.name, pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date, p.status,
-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 124) AS short,
124.0 AS long
--strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 days') as is_recent

FROM Puzzle AS p
JOIN PuzzleFile AS pf ON (pf.puzzle = p.id)
WHERE pf.name == 'preview_full' -- PUBLIC
and :status == 'active'
AND p.permission = 0
-- ACTIVE, IN_QUEUE
AND p.status IN (1, 2)
-- Filter out the 10 most recent puzzles
AND not (p.id in (select id from Puzzle where permission = 0 and status in (1, 2) and strftime('%s', m_date) >= strftime('%s', 'now', '-7 days') order by m_date desc limit 10))
GROUP BY p.id
ORDER BY p.pieces asc
-- Can't limit or offset since it varies what is actually visible to each player depending on dots
-- LIMIT 10 OFFSET (:offset * 10)
;
