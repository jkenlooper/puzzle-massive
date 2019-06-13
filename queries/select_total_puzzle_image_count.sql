select count(p.id) as value from PuzzleFile as pf
join Puzzle as p on (p.id = pf.puzzle)
where pf.name = 'original'
and p.permission = 0 -- PUBLIC
;
