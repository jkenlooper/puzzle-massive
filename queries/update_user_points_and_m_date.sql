update User set
points = min(cast(ifnull(points, 0) as integer) + :points, :POINTS_CAP),
score = cast(ifnull(score, 0) as integer) + :score,
m_date = datetime('now')
where id = :id
;
