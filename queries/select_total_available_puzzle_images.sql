select count(p.id) as total_puzzle_count,
max(p.pieces) as max_pieces

from Puzzle as p
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (pi.original = p1.id)
join PuzzleFile as pf on (p1.id = pf.puzzle)

where pf.name == 'preview_full'
and p.permission = 0 -- PUBLIC
and p.status in (1, 2, 3, 4, -3, -5, -6, -7) -- ACTIVE, IN_QUEUE, COMPLETED, FROZEN, REBUILD, IN_RENDER_QUEUE, RENDERING, RENDERING_FAILED
;
