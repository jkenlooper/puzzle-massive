SELECT count(*) AS count,
strftime('%s', p.m_date) >= strftime('%s', 'now', '-7 days') as is_recent
FROM Puzzle AS p
-- PUBLIC
WHERE p.permission = 0
AND not (is_recent and p.status == 3) -- not recently complete
-- ACTIVE, IN_QUEUE, COMPLETE
AND p.status IN (1, 2, 3)
;
