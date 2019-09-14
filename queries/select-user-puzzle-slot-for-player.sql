-- Get filled player instance slots puzzle images to show in header
select p.puzzle_id, pf.url as src,
strftime('%s','now') - strftime('%s', p.m_date) as seconds_from_now,
(select p.m_date is null) as not_modified

from User_Puzzle as up
join Puzzle as p on (up.puzzle = p.id)
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
join PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name = 'preview_full') -- Get the original

where up.player = :player
order by not_modified, seconds_from_now asc
limit 4
;
