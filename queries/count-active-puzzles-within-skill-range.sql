-- also used in queries/select-puzzle-next-in-queue-to-be-active.sql
select count(distinct p.id) as active_count
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.original)
where p.status = 1 -- ACTIVE
and p.permission = 0 -- PUBLIC
and p.pieces >= :low and p.pieces < :high
;
