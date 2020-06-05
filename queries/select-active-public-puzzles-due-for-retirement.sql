select puzzle_id from Puzzle
where status = 1 -- ACTIVE
and permission = 0 -- PUBLIC
and id in (
    select distinct p.id
    from Puzzle as p
    join PuzzleInstance as pi on (p.id = pi.original)
)
and (m_date is null or strftime('%s', m_date) < strftime('%s', 'now', '-7 days'));
