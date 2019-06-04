select count(*) as incomplete_puzzle_count
from Puzzle
where permission = 0
and status in (1, 2)
;
