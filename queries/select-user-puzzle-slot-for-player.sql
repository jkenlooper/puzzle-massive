-- Get empty and filled player instance slots
select p.puzzle_id, pf.url as src, p.table_width, p.table_height,

-- Find the short and long dimensions of the preview img by checking the table_width
-- and table_height since the img width and height is not currently stored.
round((min(CAST(p.table_width AS float), CAST(p.table_height AS float)) / max(CAST(p.table_width AS float), CAST(p.table_height AS float))) * 30) AS short,
30.0 AS long

from User_Puzzle as up
left outer join Puzzle as p on (up.puzzle = p.id)
left outer join PuzzleInstance as pi on (pi.instance = p.id)
left outer join Puzzle as p1 on (p1.id = pi.original)
left outer join PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name = 'preview_full') -- Get the original
where up.player = :player
order by p.m_date
;
