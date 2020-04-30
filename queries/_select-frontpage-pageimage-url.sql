select pf.url as pageimage from Puzzle as p
join PuzzleFile as pf on (pf.puzzle = p1.id) -- Get the original
join PuzzleInstance as pi on (pi.instance = p.id)
join Puzzle as p1 on (p1.id = pi.original)
where pf.name == 'preview_full'
and p.puzzle_id = :puzzle_id
group by p.id;
