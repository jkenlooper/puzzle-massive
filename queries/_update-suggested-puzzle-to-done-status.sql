update Puzzle
-- SUGGESTED_DONE
set status = -21
where puzzle_id = :puzzle_id
-- SUGGESTED
and status = -20;
