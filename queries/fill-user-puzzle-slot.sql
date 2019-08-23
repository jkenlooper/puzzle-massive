-- Use to fill an available slot with a puzzle for that player
update User_Puzzle set
puzzle = 114
where player = 607
and puzzle is null
limit 1;
