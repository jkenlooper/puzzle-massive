select
p.id,
p.puzzle_id,
p.pieces,
p.rows,
p.cols,
p.piece_width,
p.mask_width,
p.table_width,
p.table_height,
p.name,
p.link,
p.description,
p.bg_color,
p.m_date,
p.owner,
p.queue,
p.status,
p.permission,
pf.url as preview_full
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
left outer JOIN PuzzleFile AS pf ON (pf.puzzle = p.id and pf.name = 'preview_full') -- Get the original
where p.status = :status
and strftime('%s', p.m_date) <= strftime('%s', 'now', '-21 days')
and p.permission = 0 -- public
and p.pieces >= :low and p.pieces < :high
and pi.original == pi.instance
order by random()
limit 5
;
