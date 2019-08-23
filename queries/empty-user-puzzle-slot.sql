-- Use to free up a slot for that player
update User_Puzzle set
puzzle = null
where player = 607
and puzzle = 114
;

