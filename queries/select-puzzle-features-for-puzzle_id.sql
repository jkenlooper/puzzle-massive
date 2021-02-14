select
    pzf.slug,
    pzf.name,
    pzf.description,
    pzf.enabled,
    pfd.start_time,
    pfd.stop_time,
    pfd.message,
    pfd.players,
    pfd.pieces,
    pfd.n
from Puzzle as p
join PuzzleFeatureData as pfd on (pfd.puzzle = p.id)
join PuzzleFeature as pzf on (pzf.id = pfd.puzzle_feature)
where p.puzzle_id = :puzzle_id
and pzf.enabled = :enabled
;
