select count(*) as total,
p.status
from Puzzle as p
group by p.status
;
