select player,
sum(points) / 4 as points
from Timeline
where puzzle = :puzzle
and player not null
group by player
;
