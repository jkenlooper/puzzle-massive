update Puzzle set queue = 2 -- QUEUE_BUMPED_BID
where status = 2 -- IN_QUEUE
and queue = 1 -- QUEUE_WINNING_BID
and pieces >= :low and pieces < :high
and id in (
    select distinct p.id
    from Puzzle as p
    join PuzzleInstance as pi on (p.id = pi.original)
)
;
