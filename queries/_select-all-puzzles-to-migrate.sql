select distinct puzzle from PuzzleFile
where (
    (name = 'pieces' and url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%')
or (name = 'preview_full' and url like 'https://source.unsplash.com/%')
or (name = 'original' and url = '')
)
-- Don't include deleted puzzles
and puzzle not in (select id from Puzzle where status in (-10, -11, -12, -13))
limit 40 -- Unsplash limit is 50 per hour when in development
;
