-- Should match select-valid-puzzle-for-new-puzzle-instance.sql
select p1.id,
p1.puzzle_id,
p1.name,
p1.link,
p1.permission,
p1.description,
p.id as instance_id,
p.puzzle_id as instance_puzzle_id,
p.pieces,
p.status,
p.rows,
p.cols,
p.piece_width,
p.mask_width,
p.table_width,
p.table_height
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.instance)
join Puzzle as p1 on (p1.id = pi.original)
where p.puzzle_id = :puzzle_id
and p.status in (
    :ACTIVE,
    :IN_QUEUE,
    :COMPLETED,
    :FROZEN
);
