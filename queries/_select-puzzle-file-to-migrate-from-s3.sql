select distinct puzzle, name, url from PuzzleFile
where puzzle = :puzzle and
name in ('original', 'pieces', 'preview_full', 'pzz') and url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%';
