select count(*) as active_count
from Puzzle
where status = 1 -- ACTIVE
and pieces >= :low and pieces < :high
;
