select player,
sum(points) / 4 as points,
strftime('%s', timestamp) as timestamp
from Timeline
where puzzle = :puzzle
group by player
;
