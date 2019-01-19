SELECT
id,
puzzle_id,
pieces,
rows,
cols,
piece_width,
mask_width,
table_width,
table_height,
name,
link,
description,
bg_color,
m_date,
owner,
queue,
status,
permission,
strftime('%Y-%m-%d %H:%M', m_date, '+7 hours') as redo_date,
strftime('%s', m_date, '+7 hours') >= strftime('%s', 'now') as is_recent
FROM Puzzle
WHERE puzzle_id = :puzzle_id;
