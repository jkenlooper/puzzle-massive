-- Similiar to select_available_puzzle_image_count.sql,
-- select_available_puzzle_images--orderby-pieces.sql
-- select_available_puzzle_images--orderby-queue.sql
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
l.title as license_title

from Puzzle as p
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (pi.original = p1.id)
join PuzzleFile as pf on (p1.id = pf.puzzle)
left outer join Attribution as a on (a.id = pf.attribution)
left outer join License as l on (l.id = a.license)

where pf.name == 'preview_full'

-- Get the most active (pieces joined by the most players) puzzle in last 5 minutes or fall back on most recently updated one.
AND p.puzzle_id in (
    select puzzle_id from Puzzle as p
    left outer join Timeline as t1 on (t1.puzzle = p.id and t1.timestamp > datetime('now', '-5 minutes'))
    where p.permission = 0 -- PUBLIC
    and p.status = 1 -- ACTIVE
    and p.pieces >= :pieces_min
    and p.pieces < :pieces_max
    group by p.puzzle_id
    order by count(t1.timestamp) desc, p.m_date desc
    limit :count
)

order by p.m_date desc

limit :count
;

