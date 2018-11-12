SELECT
puzzle_id,
pieces,
link,
description,
bg_color,
owner,
permission
FROM Puzzle
WHERE puzzle_id = :puzzle_id;
