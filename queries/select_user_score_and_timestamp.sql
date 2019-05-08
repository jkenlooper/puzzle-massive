SELECT id, score,
strftime('%s', m_date) as timestamp
FROM User
WHERE score != 0
AND id != 2 -- ANONYMOUS_USER_ID
;
