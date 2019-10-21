select p.puzzle_id, p.id, p.pieces, p.status, p.owner,
p1.puzzle_id as original_puzzle_id
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.instance)
join Puzzle as p1 on (p1.id = pi.original)
where p.puzzle_id = :puzzle_id and p.status = :status
and (p.m_date is null or strftime('%s', p.m_date) <= strftime('%s', 'now', '-7 hours'));
