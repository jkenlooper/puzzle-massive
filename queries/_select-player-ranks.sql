-- http://www.1keydata.com/sql/sql-rank.html

/*
SELECT u1.id, u1.score, u1.icon, count(u2.score) AS rank FROM User AS u1,
User AS u2
WHERE u1.score <= u2.score OR (u1.score = u2.score AND u1.id = u2.id)
GROUP BY u1.id, u1.score
ORDER BY u1.score DESC, u1.id
;
*/

/*
TODO: how to do a limit and use grouping?
*/
SELECT u1.id, u1.score, b.name as icon, count(u2.score) AS rank
FROM User AS u1
JOIN User AS u2
JOIN BitIcon as b on u1.id = b.user
WHERE (u1.score <= u2.score OR (u1.score = u2.score AND u1.id = u2.id))
AND (b.expiration > datetime('now') OR (u1.score >= (
      select score from User
      where id != 2 -- ANONYMOUS_USER_ID
      order by score desc limit 1 offset 15
)))
AND u1.id != 2 -- ANONYMOUS_USER_ID
GROUP BY u1.id, u1.score
ORDER BY u1.score DESC, u1.id
;

/*
SELECT u.id, u.score, b.name as icon
FROM User AS u
JOIN BitIcon as b on u.id = b.user
--WHERE u1.score <= u2.score OR (u1.score = u2.score AND u1.id = u2.id)
--GROUP BY u1.id, u1.score
ORDER BY u.score DESC
;
*/
