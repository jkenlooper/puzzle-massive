select p1.puzzle_id as original_puzzle_id,
pf.url as preview_full
from Puzzle as p
join PuzzleInstance as pi on (p.id = pi.instance)
join Puzzle as p1 on (p1.id = pi.original)
left outer JOIN PuzzleFile AS pf ON (pf.puzzle = p1.id and pf.name == 'preview_full') -- Get the original
where p.id = :puzzle;
