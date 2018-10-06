-- TODO: This is inline in jobs/pieceTranslate.py as UPDATE_BIT_ICON_EXPIRATION

-- Ran each time a player earns a point, but only if last_viewed has been at
-- least 1 day ago. This will potentially increase the bit expiration to the
-- next tier if the player meets the score requirements. New players that don't
-- get past the initial tier within a day will have their bit expire.

UPDATE BitIcon SET
expiration = (
  SELECT datetime('now', (
    SELECT be.extend FROM BitExpiration AS be
      JOIN User AS u
       WHERE u.score >= be.score AND u.id = 1917 --:user
       ORDER BY be.score DESC LIMIT 1
    )
  )
),
last_viewed = datetime('now')
WHERE user = 1917 --:user
and (last_viewed < datetime('now', '-50 minutes') or last_viewed isnull)
;
