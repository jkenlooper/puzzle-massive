select distinct puzzle from PuzzleFile
where (name = 'pieces' and url like 'http://puzzle.massive.xyz.s3-website-us-east-1.amazonaws.com/3/%')
or (name = 'preview_full' and url like 'https://source.unsplash.com/%')
or (name = 'original' and url = '')
;
