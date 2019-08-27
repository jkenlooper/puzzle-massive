select count(p.id) as value
from PuzzleFile as pf
join Puzzle as p on (p.id = pf.puzzle)
where pf.name == 'preview_full'
and p.permission = 0 -- PUBLIC
and p.status in (1, 2, 3, -3, -5, -6, -7) -- ACTIVE, IN_QUEUE, COMPLETED, REBUILD, IN_RENDER_QUEUE, RENDERING, RENDERING_FAILED
;
