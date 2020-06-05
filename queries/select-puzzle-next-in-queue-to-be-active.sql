select puzzle_id from Puzzle
where status = 2 -- IN_QUEUE
and permission = 0 -- PUBLIC
and pieces >= :low and pieces < :high
and id in (
    select distinct p.id
    from Puzzle as p
    join PuzzleInstance as pi on (p.id = pi.original)
)
order by queue, m_date is not null, strftime('%s','now') - strftime('%s', m_date) desc -- FILO for m_date
limit :active_count - (
    -- count-active-puzzles-within-skill-range.sql
    select count(distinct p.id) as active_count
    from Puzzle as p
    join PuzzleInstance as pi on (p.id = pi.original)
    where p.status = 1 -- ACTIVE
    and p.permission = 0 -- PUBLIC
    and p.pieces >= :low and p.pieces < :high
)
;
