select pf.url as src, p.puzzle_id, p.status, p.pieces,

strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') as is_recent,
strftime('%s','now') - strftime('%s', p.m_date) as seconds_from_now,
pi.original == pi.instance as is_original,
p.owner,

a.title,
a.author_link,
a.author_name,
a.source,
l.source as license_source,
l.name as license_name,
l.title as license_title

from Puzzle as p
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (pi.original = p1.id)
join PuzzleFile as pf on (p1.id = pf.puzzle)
left outer join Attribution as a on (a.id = pf.attribution)
left outer join License as l on (l.id = a.license)

where pf.name == 'preview_full'
and p.permission = 0 -- PUBLIC
and p.status in (1, 2, 3, -3, -5, -6, -7) -- ACTIVE, IN_QUEUE, COMPLETED, REBUILD, IN_RENDER_QUEUE, RENDERING, RENDERING_FAILED
order by p.m_date desc
;
