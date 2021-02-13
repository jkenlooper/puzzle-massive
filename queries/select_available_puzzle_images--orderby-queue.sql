-- should match results from select_available_puzzle_image_count.sql,
-- select_available_puzzle_images--orderby-pieces.sql
-- select_available_puzzle_images--orderby-m_date.sql

select pf.url as src, p.puzzle_id, p.status, p.pieces, p.queue,

strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
p.m_date is not null and strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') and p.status in (1, 3, 4) as is_recent, -- ACTIVE, COMPLETED, FROZEN
strftime('%s','now') - strftime('%s', p.m_date) as seconds_from_now,
p.m_date is not null and not strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 hours') and p.status = 1 as is_active, -- ACTIVE
p.m_date is null and p.status in (1, 2) as is_new, -- ACTIVE, IN_QUEUE
pi.original == pi.instance as is_original,
CAST(p.owner as integer) as owner,

a.title,
a.author_link,
a.author_name,
a.source,
l.source as license_source,
l.name as license_name,
l.title as license_title,

pfd.puzzle_feature is not null as has_hidden_preview

from Puzzle as p
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (pi.original = p1.id)
join PuzzleFile as pf on (p1.id = pf.puzzle)
left outer join Attribution as a on (a.id = pf.attribution)
left outer join License as l on (l.id = a.license)
left outer join PuzzleFeature as pzf on (pzf.slug = 'hidden-preview' and pzf.enabled = 1)
left outer join PuzzleFeatureData as pfd on (pfd.puzzle = p.id and pfd.puzzle_feature = pzf.id)

where pf.name == 'preview_full'
and p.permission = 0 -- PUBLIC
and is_recent in {recent_status}
and is_active in {active_status}
and is_original in {original_type}
and p.status in {status}
and p.pieces >= :pieces_min
and p.pieces < :pieces_max

order by p.queue, p.m_date is not null, strftime('%s','now') - strftime('%s', p.m_date) desc -- FILO for m_date

limit :page_size offset :offset
;

