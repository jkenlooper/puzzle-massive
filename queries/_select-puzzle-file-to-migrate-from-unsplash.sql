select distinct pf.puzzle, pf.name, pf.url, p.puzzle_id, p.name as unsplash_id, p.description
from PuzzleFile as pf
join Puzzle as p on (pf.puzzle = p.id)
where pf.puzzle = :puzzle and
pf.name = 'preview_full' and pf.url like 'https://source.unsplash.com/%';
