select t.player as p, t.message as m, t.points as c, t.timestamp as t
from Timeline as t
join Puzzle as pz on (pz.id = t.puzzle)
where t.puzzle = :puzzle
;
