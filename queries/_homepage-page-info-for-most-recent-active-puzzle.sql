SELECT pf.url, p.puzzle_id, p.pieces, p.table_width, p.table_height, p.description, p.status, p.m_date, p.name,
pv.name as puzzle_variant_name,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 384) AS short,
384.0 AS long

FROM Puzzle AS p
JOIN PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id) -- Get the original
JOIN PuzzleVariant as pv on (pi.variant = pv.id)
WHERE pf.name == 'preview_full'

-- Get the most active (pieces joined by the most players) puzzle in last 5 minutes or fall back on most recently updated one.
AND p.puzzle_id = (
    select puzzle_id from Puzzle as p1
    left outer join Timeline as t1 on (t1.puzzle = p1.id and t1.timestamp > datetime('now', '-5 minutes'))
    where p1.permission = 0
    and p1.status = 1 -- ACTIVE
    group by p1.puzzle_id
    order by count(t1.timestamp) desc, p1.m_date desc
    limit 1
)
GROUP BY p.id
limit 1
;
