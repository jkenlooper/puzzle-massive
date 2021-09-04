SELECT
p.id,
p.puzzle_id,
p.pieces,
p.queue,
p.owner,
u.points as user_points,
p.status,
p.permission,
p.m_date,
-- use url here to find out if it is a local resources file or not.
pf.url,
strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
strftime('%s', p.m_date, '+7 hours') >= strftime('%s', 'now') as is_recent,
strftime('%s', p.m_date, '+4 days') <= strftime('%s', 'now') as is_old,
u.id == p.owner as is_owner,
pi.original == pi.instance as is_original
FROM Puzzle as p
JOIN PuzzleInstance as pi on (p.id = pi.instance)
JOIN User as u on (u.id = p.owner)
left outer JOIN PuzzleFile AS pf ON (pf.puzzle = p.id and pf.name in ('original', 'pieces'))
WHERE p.puzzle_id = :puzzle_id
limit 1;
