select count(distinct id) as queue_count
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
where status = 2 -- IN_QUEUE
and queue <= 2 -- QUEUE_BUMPED_BID
and pieces >= :low and pieces < :high
;

