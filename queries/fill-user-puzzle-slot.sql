-- Use to fill an available slot with a puzzle for that player
update User_Puzzle set
puzzle = :puzzle
where player = :player
and puzzle is null
limit 1;
