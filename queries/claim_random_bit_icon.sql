-- Only used when generating test data with the testdata script.
update BitIcon set user = :user,
expiration = datetime('now', '+20 minutes'),
last_viewed = datetime('now', '-50 minutes')

where ((user not null and (expiration <= datetime('now') or expiration isnull))
or user isnull)
and name = ( -- select the first random bit icon available
select b.name from BitIcon as b
left outer join User as u on b.user = u.id
where ((b.user not null and (expiration <= datetime('now') or expiration isnull))
or b.user isnull)

-- filter out any that are in the current high score
and (u.score <= (
  select score from User
  where id != 2 -- ANONYMOUS_USER_ID
  order by score desc limit 1 offset 15
) or u.score isnull)

order by b.last_viewed, b.name limit 1
)
;
