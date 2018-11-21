select distinct pz.puzzle, pz.name, pz.url, p.puzzle_id from PuzzleFile as pz
join Puzzle as p on (pz.puzzle = p.id)
where pz.puzzle = :puzzle and
pz.name in ('original', 'pieces', 'preview_full', 'pzz') and pz.url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%';
