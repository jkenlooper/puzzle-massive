select count(*) as active_puzzle_count
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
where p.permission = 0
and p.status in (1, 2)
and pi.original == pi.instance
;
