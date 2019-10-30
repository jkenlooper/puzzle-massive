update Puzzle set status = 2, -- IN_QUEUE
queue = 10 -- QUEUE_INACTIVE
where status = 1 -- ACTIVE
and id in (
    select distinct p.id
    from Puzzle as p
    join PuzzleInstance as pi on (p.id = pi.original)
)
and (m_date is null or strftime('%s', m_date) < strftime('%s', 'now', '-7 days'));