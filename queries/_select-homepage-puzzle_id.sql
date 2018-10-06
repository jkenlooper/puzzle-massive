-- pass the puzzle_id for front pages to be available to the template.
select puzzle_id from Puzzle where permission = 0
and status in (1, 2)
order by m_date desc limit 1;
