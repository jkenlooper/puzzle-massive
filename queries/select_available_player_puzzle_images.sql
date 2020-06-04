select pf.url as src, p.puzzle_id, p.status, p.pieces, p.permission,

strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
p.m_date is not null and strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') as is_recent,
strftime('%s','now') - strftime('%s', p.m_date) as seconds_from_now,
p.m_date is not null and not strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') and p.status in (1, 2) as is_active,
p.m_date is null and p.status in (1, 2) as is_new, -- ACTIVE, IN_QUEUE
pi.original == pi.instance as is_original,
CAST(p.owner as integer) as owner,
pi.instance = up.puzzle as is_in_puzzle_instance_slot,

a.title,
a.author_link,
a.author_name,
a.source,
l.source as license_source,
l.name as license_name,
l.title as license_title

from Puzzle as p
left outer join User_Puzzle as up on (up.puzzle = p.id and up.player = p.owner)
left outer join PuzzleInstance as pi on (pi.instance = p.id)
left outer join Puzzle as p1 on (pi.original = p1.id)
left outer join PuzzleFile as pf on (p1.id = pf.puzzle and pf.name = 'preview_full')
left outer join Attribution as a on (a.id = pf.attribution)
left outer join License as l on (l.id = a.license)

where p.owner = :player
order by p.m_date desc
;
