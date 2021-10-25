insert into User_Puzzle
select :player as player, null as puzzle
from User as u
where u.id = :player
and u.score >= :score_threshold
and ( select count(player) as slot_count from User_Puzzle where player = :player ) = 0
;
