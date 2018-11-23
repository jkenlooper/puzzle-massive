-- Get a selection of 10 bit icons ordered by last_viewed and name.  This is
-- offset based on time and the offset_time param which allows different
-- tracks.  A user would use the same offset_time param for each call.  Other
-- users would use a different offset_time to prevent the two users from seeing
-- the same icons at the same time.
--
-- The last group of 10 is not shown as it may be less then 10 because of the
-- offset. This is also beneficial as the most recently expired icons will be
-- hidden.

select b.name as icon from BitIcon as b
left outer join User as u on b.user = u.id
where ((b.user not null and (expiration <= datetime('now') or expiration isnull))
or b.user isnull)

-- filter out any that are in the current high score
and (u.score <= (
  select score from User
  where id != 2 -- ANONYMOUS_USER_ID
  order by score desc limit 1 offset 15
) or u.score isnull)

order by b.last_viewed, b.name limit 10 offset (
  -- time based offset to only show these 10 results at a specific datetime
  select abs(strftime('%s', 'now', :offset_time) % ((
    select count(*) from BitIcon as b
      where (b.user not null and (expiration <= datetime('now') or expiration isnull))
      or b.user isnull
  ) - 10)) + 10
) - 10 -- Hide the remainder
;
