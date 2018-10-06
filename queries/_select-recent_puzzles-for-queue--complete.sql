SELECT p.id, pf.name, pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.link, p.description, p.bg_color, p.m_date, p.status,
-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 124) AS short,
124.0 AS long

FROM Puzzle AS p
JOIN PuzzleFile AS pf ON (pf.puzzle = p.id)
WHERE pf.name == 'preview_full' -- PUBLIC
and :status == 'complete'
AND p.permission = 0
AND p.status == 3
AND strftime('%s', p.m_date) <= strftime('%s', 'now', '-7 days')
GROUP BY p.id
ORDER BY p.m_date desc
LIMIT 10
;
