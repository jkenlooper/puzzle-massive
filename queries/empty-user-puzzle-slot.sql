-- Use to free up a slot for that player
update User_Puzzle set
puzzle = null
where player = :player
and puzzle = :puzzle
;

