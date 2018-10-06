select t.puzzle, t.player, u.icon, (sum(t.points) / 4) as score from Timeline as t
join User as u on (t.player = u.id)
where timestamp >= :start_date and timestamp <= :end_date
and u.icon != ''
group by player order by score desc limit :limit;
