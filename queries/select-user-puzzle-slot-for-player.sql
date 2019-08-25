-- Get empty and filled player instance slots
select p.puzzle_id, pf.url as src
from User_Puzzle as up
left outer join Puzzle as p on (up.puzzle = p.id)
left outer join PuzzleInstance as pi on (pi.instance = p.id)
left outer join Puzzle as p1 on (p1.id = pi.original)
left outer join PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name = 'preview_full') -- Get the original
where up.player = :player
order by p.m_date, up.puzzle asc
;
