update BitIcon set user = null,
expiration = null,
last_viewed = datetime('now')
where user = :user
;
