update Puzzle set status = 1 -- ACTIVE
where status = 2 -- IN_QUEUE
and pieces >= :low and pieces < :high
order by queue, m_date
limit :active_count - (
    -- count-active-puzzles-within-skill-range.sql
    select count(*) as active_count
    from Puzzle
    where status = 1 -- ACTIVE
    and pieces >= :low and pieces < :high
)
;
