select count(*) as in_queue_puzzle_count
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
where p.permission = 0
and p.status == 2 -- IN_QUEUE
and p.pieces >= :low and p.pieces < :high
and pi.original == pi.instance
;
