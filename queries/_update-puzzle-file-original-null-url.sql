-- For puzzles that didn't have the original url set.  Update to match the
-- puzzle_id.
-- 788
update PuzzleFile
set url = (
    select '/resources/' || puzzle_id || '/original.jpg' as url from Puzzle
    where id = :puzzle
) where puzzle = :puzzle and name = 'original' and url = '';
