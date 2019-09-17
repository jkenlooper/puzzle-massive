select player from User_Puzzle where puzzle is null
order by random()
limit 1;
