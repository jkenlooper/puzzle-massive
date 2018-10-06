SELECT pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.description, p.status, p.m_date, p.name,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 384) AS short,
384.0 AS long

FROM Puzzle AS p
JOIN PuzzleFile AS pf ON (pf.puzzle = p.id)
WHERE pf.name == 'preview_full'
AND p.puzzle_id = (
select puzzle_id from Puzzle where permission = 0
and status in (1, 2)
order by m_date desc limit 1)
GROUP BY p.id
