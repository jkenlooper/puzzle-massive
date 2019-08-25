-- Remove an empty puzzle instance slot for a player.  Note that this is
-- different then the empty-user-puzzle-slot.sql
delete from User_Puzzle
where player = :player
and puzzle is null
limit 1;
