SELECT u.score, b.name as icon, u.id FROM User as u
JOIN BitIcon as b on u.id = b.user
WHERE u.score != 0
AND u.id != 2 -- ANONYMOUS_USER_ID
ORDER BY score DESC LIMIT 15;
