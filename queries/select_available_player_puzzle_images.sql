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
l.title as license_title,

pfd.puzzle_feature is not null as has_hidden_preview

from Puzzle as p
left outer join User_Puzzle as up on (up.puzzle = p.id and up.player = p.owner)
left outer join PuzzleInstance as pi on (pi.instance = p.id)
left outer join Puzzle as p1 on (pi.original = p1.id)
left outer join PuzzleFile as pf on (p1.id = pf.puzzle and pf.name = 'preview_full')
left outer join Attribution as a on (a.id = pf.attribution)
left outer join License as l on (l.id = a.license)
left outer join PuzzleFeature as pzf on (pzf.slug = 'hidden-preview' and pzf.enabled = 1)
left outer join PuzzleFeatureData as pfd on (pfd.puzzle = p.id and pfd.puzzle_feature = pzf.id)

where p.owner = :player
-- any of the puzzle status except deleted and suggested
and p.status in (0, 1, 2, 3, 4, 5, -1, -2, -3, -5, -6, -7, -30)
order by p.m_date desc
limit :count
;
