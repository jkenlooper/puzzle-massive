SELECT
p.id,
p.puzzle_id,
p.pieces,
p.owner,
p.status,
p.permission,
strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
strftime('%s', p.m_date, '+7 hours') >= strftime('%s', 'now') as is_recent,
pi.original == pi.instance as is_original
FROM Puzzle as p
JOIN PuzzleInstance as pi on (p.id = pi.instance)
WHERE p.puzzle_id = :puzzle_id;
