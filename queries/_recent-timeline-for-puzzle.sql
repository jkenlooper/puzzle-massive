SELECT t.player,
sum(t.points) / 4 AS points,
min(strftime('%s','now') - strftime('%s', t.timestamp)) AS seconds_from_now,
b.name as icon,
b.expiration,
u.id
FROM Timeline AS t
JOIN Puzzle AS p ON (t.puzzle = p.id)
JOIN User AS u ON (t.player = u.id)
JOIN BitIcon AS b ON (u.id = b.user)
WHERE p.puzzle_id = :puzzle_id
and b.expiration > datetime('now')
and t.timestamp > datetime('now', '-14 days')
GROUP BY player
ORDER BY timestamp DESC
;
