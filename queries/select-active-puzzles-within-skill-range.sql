select id, puzzle_id
from Puzzle
where status = 1 -- ACTIVE
and pieces >= :low and pieces < :high
order by m_date
limit :active_count
;
