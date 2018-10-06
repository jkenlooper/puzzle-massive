update BitIcon set user = :user,
expiration = (
  SELECT datetime('now', (
    SELECT be.extend FROM BitExpiration AS be
      JOIN User AS u
       WHERE u.score >= be.score AND u.id = :user
       ORDER BY be.score DESC LIMIT 1
    )
  )
),
last_viewed = datetime('now', '-50 minutes')

where ((user not null and (expiration <= datetime('now') or expiration isnull))
or user isnull)
and name = :icon
;
