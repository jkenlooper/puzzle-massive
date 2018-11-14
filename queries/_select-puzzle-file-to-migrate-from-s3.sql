select puzzle, name, url from PuzzleFile
where puzzle = :puzzle and
name in ('pieces', 'preview_full') and url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%'
