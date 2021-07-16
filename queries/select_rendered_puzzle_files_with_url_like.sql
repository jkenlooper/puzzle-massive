select p.puzzle_id, pf.url, pf.name
from PuzzleFile as pf
join Puzzle as p on (pf.puzzle = p.id)

where pf.url like :url_match
and p.status in (1,2,3,4,5) -- ACTIVE, IN_QUEUE, COMPLETED, FROZEN, BUGGY_UNLISTED
;
