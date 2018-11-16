-- For old s3 stored original puzzle files the url was set to '0'.  This updates
-- the url for these to be the same as the pieces.png root.
-- 336
update PuzzleFile
set url = (
    select replace(url, 'pieces.png', 'original.jpg') as url from PuzzleFile
    where puzzle = :puzzle and name = 'pieces'
) where puzzle = :puzzle and name = 'original' and url = '0';
