update Puzzle set
pieces = :pieces,
rows = :rows,
cols = :cols,
piece_width = :piece_width,
mask_width = :mask_width,
table_width = :table_width,
table_height = :table_height,
name = :name,
link = :link,
description = :description,
bg_color = :bg_color,
m_date = :m_date,
owner = :owner,
queue = :queue,
status = :status,
permission = :permission
where puzzle_id = :puzzle_id;
