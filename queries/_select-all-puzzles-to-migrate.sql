SELECT pz.id
from Puzzle as pz
JOIN PuzzleFile as pf1 on pz.id = pf1.puzzle and pf1.name = 'pieces'
JOIN PuzzleFile as pf2 on pz.id = pf2.puzzle and pf2.name = 'preview_full'
where pf1.url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%'
or pf2.url like 'https://source.unsplash.com/%';
