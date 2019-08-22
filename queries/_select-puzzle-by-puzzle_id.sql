SELECT
p.id,
p.puzzle_id,
p1.puzzle_id as original_puzzle_id,
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
strftime('%Y-%m-%d %H:%M', p.m_date, '+7 hours') as redo_date,
strftime('%s', p.m_date, '+7 hours') >= strftime('%s', 'now') as is_recent,
pi.original == pi.instance as is_original
FROM Puzzle as p
JOIN PuzzleInstance as pi on (p.id = pi.instance)
join Puzzle as p1 on (p1.id = pi.original)
WHERE p.puzzle_id = :puzzle_id;
