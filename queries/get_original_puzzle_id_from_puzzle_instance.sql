select p1.puzzle_id as original_puzzle_id
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.instance)
join Puzzle as p1 on (p1.id = pi.original)
where p.id = :puzzle;
